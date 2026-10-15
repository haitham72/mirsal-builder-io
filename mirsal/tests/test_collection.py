"""Export to the AddCollection API (services/collection.py): a fake CMS on localhost receives the multipart form; never the real one."""
import base64
import email.parser
import email.policy
import http.client
import http.server
import io
import json
import os
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import cv2
from mirsal.engine.config import EngineConfig
from mirsal.flow import batches, pipeline as pl
from mirsal.generation import higgsfield as hf
from mirsal.services import collection as col
from tests import synth


class FakeCMS(http.server.BaseHTTPRequestHandler):
    seen: list = []
    answer = (200, b'{"id": 7, "message": "created"}', "application/json")

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        FakeCMS.seen.append({"path": self.path, "auth": self.headers.get("Authorization"), "ctype": self.headers.get("Content-Type"), "body": body})
        st, data, ctype = FakeCMS.answer
        self.send_response(st)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def form(seen: dict) -> list:
    """[(field name, filename or None, content type, bytes)] in the order sent."""
    msg = email.parser.BytesParser(policy=email.policy.HTTP).parsebytes(b"Content-Type: " + seen["ctype"].encode() + b"\r\n\r\n" + seen["body"])
    return [(p.get_param("name", header="content-disposition"), p.get_filename(), p.get_content_type(), p.get_payload(decode=True)) for p in msg.iter_parts()]


class CollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from mirsal.console.server import serve
        cls.cms = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeCMS)
        threading.Thread(target=cls.cms.serve_forever, daemon=True).start()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.env = patch.dict(os.environ, {"MIRSAL_API_TOKEN": "collection-test-owner", "MIRSAL_COLLECTION_API_URL": f"http://127.0.0.1:{cls.cms.server_address[1]}",
                                          "MIRSAL_COLLECTION_API_CREDENTIALS": "me@nadi.ae:secret"})
        cls.hf = patch.object(hf, "available", return_value=False)
        cls.env.start(); cls.hf.start()
        cls.srv, cls.c = serve(Path(cls.tmp.name) / "out", Path(cls.tmp.name) / "in", 0, cfg=EngineConfig(min_sheet_px=256), block=False, stdlib=False)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        _, cls.member = cls.c.users.create("Member")
        data = cv2.imencode(".png", cv2.cvtColor(synth.make_sheet(), cv2.COLOR_RGB2BGR))[1].tobytes()
        s, j = cls.req(cls, "/api/import?name=own.png", data)
        assert s == 202, j
        cls.gid = j["id"]
        cls.c.wait_jobs()

    @classmethod
    def tearDownClass(cls):
        cls.c.wait_jobs()
        cls.srv.shutdown(); cls.c.release_writer(); cls.cms.shutdown()
        cls.hf.stop(); cls.env.stop(); cls.tmp.cleanup()

    def setUp(self):
        FakeCMS.seen = []
        FakeCMS.answer = (200, b'{"id": 7, "message": "created"}', "application/json")

    def req(self, path, body=b"", token="collection-test-owner", method="POST"):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        conn.request(method, path, body if isinstance(body, bytes) else json.dumps(body).encode(), {"Authorization": "Bearer " + token, "Content-Type": "application/octet-stream"})
        r = conn.getresponse()
        result = r.status, json.loads(r.read())
        conn.close()
        return result

    def export(self, path, body=b"", token="collection-test-owner"):
        """POST an export; a queued one (202) is waited for and its final state answered as (200, state), as the page's polling sees it."""
        s, j = self.req(path, body, token)
        if s != 202:
            return s, j
        self.assertEqual(j["state"], "queued", j)
        self.assertTrue(col.wait(60), "the export finished")
        s, st = self.req(f"/api/collection/exports/{j['id']}", token=token, method="GET")
        self.assertEqual(s, 200, st)
        self.assertIn(st["state"], col.FINAL)
        return s, st

    def test_an_export_is_queued_its_state_is_its_senders_and_a_restart_is_a_failure(self):
        g = f"G{self.gid:03d}"
        FakeCMS.answer = (200, b'{"Success": true, "Result": {"CollectionId": 9}}', "application/json")
        s, j = self.req(f"/api/generations/{g}/export-collection", {"name": "Queued pack", "description": "later"})
        self.assertEqual((s, j["state"], j["collection"]), (202, "queued", "Queued pack"), j)
        self.assertTrue(col.wait(60))
        s, st = self.req(f"/api/v1/collection/exports/{j['id']}", method="GET")
        self.assertEqual((s, st["state"], st["ok"], st["result"]), (200, "done", True, {"CollectionId": 9}), st)
        self.assertEqual(self.req(f"/api/collection/exports/{j['id']}", token=self.member, method="GET")[0], 404, "only its sender sees it")
        self.assertEqual(self.req("/api/collection/exports/X0", method="GET")[0], 404)
        self.assertEqual(self.req("/api/collection/exports/..%2Fsecret", method="GET")[0], 404)
        p = col._state_path(self.c.out, "Xdead")                             # an export an earlier server run never finished
        p.write_text(json.dumps({"id": "Xdead", "by": st["by"], "state": "sending"}), encoding="utf-8")
        s, st2 = self.req("/api/collection/exports/Xdead", method="GET")
        self.assertEqual((st2["state"], st2["ok"]), ("failed", False))
        self.assertIn("restarted", st2["error"])
        from mirsal.flow import notifications as nt
        texts = [n["text"] for n in nt.listing(self.c.out, st["by"])["notifications"]]
        self.assertTrue(any('"Queued pack" was sent' in t for t in texts), texts)

    def test_a_batch_is_sent_as_the_zip_holds_it_media_paired_with_metadata_by_index(self):
        g = f"G{self.gid:03d}"
        s, j = self.export(f"/api/generations/{g}/export-collection", {"name": "Blob pack", "description": "made in Mirsal"})
        self.assertEqual((s, j["ok"], j["collection"], j["response"]["id"]), (200, True, "Blob pack", 7), j)
        sent = FakeCMS.seen[-1]
        self.assertEqual(sent["path"], col.ENDPOINT)
        self.assertEqual(sent["auth"], "Basic " + base64.b64encode(b"me@nadi.ae:secret").decode())     # "user:password" is encoded for you
        parts = form(sent)
        fields = {n: v for n, f, _, v in parts if f is None}
        media = [(f, t, v) for n, f, t, v in parts if n == "Media"]
        meta = json.loads(fields["MediaMetadata"].decode())
        self.assertEqual((fields["CollectionName"].decode(), fields["Description"].decode()), ("Blob pack", "made in Mirsal"))
        self.assertEqual(fields["ContentSubType"].decode(), "png", "stills only: their own type")
        self.assertEqual(col.content_subtype([{"filename": "a.webm"}, {"filename": "b.png"}]), "webm")
        self.assertEqual(col.content_subtype([{"filename": "a.webm"}]), "webm")
        self.export(f"/api/generations/{g}/export-collection", {"name": "No words"})
        self.assertEqual({n: v for n, f, _, v in form(FakeCMS.seen[-1]) if f is None}["Description"].decode(), "No words")    # never an empty description
        self.assertEqual(len(media), len(meta))
        self.assertEqual(j["count"], len(media))
        zdata, _ = batches.export_zip(self.c.out, self.gid)                 # the same stickers, the same order, the same bytes as Download .zip
        with zipfile.ZipFile(io.BytesIO(zdata)) as z:
            man = json.loads(z.read("manifest.json"))
            self.assertEqual([f for f, _, _ in media], [a["filename"] for a in man["assets"]])
            self.assertEqual([v for _, _, v in media], [z.read(a["filename"]) for a in man["assets"]])
            self.assertEqual([m["emoji_utf"] for m in meta], [a["emoji"] for a in man["assets"]])
        self.assertTrue(all(t == "image/png" for _, t, _ in media))
        thumbs = [(f, t, v) for n, f, t, v in parts if n == "MediaThumbnails"]      # one PNG per Media part, by index; a PNG sticker is its own thumbnail
        self.assertEqual([f for f, _, _ in thumbs], [Path(f).stem + ".png" for f, _, _ in media])
        self.assertEqual([v for _, _, v in thumbs], [v for _, _, v in media])
        self.assertTrue(all(t == "image/png" for _, t, _ in thumbs))
        for m in meta:
            self.assertRegex(m["tags"], r"^[a-z0-9]+(_[a-z0-9]+)*$")
        log = [json.loads(x) for x in (self.c.out / "collection_exports.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual((log[-1]["what"], log[-1]["ok"], log[-1]["count"]), (g, True, len(media)))
        self.assertNotIn("secret", json.dumps(log))                                                       # never the credentials

    def test_a_pack_is_sent_and_only_the_owner_may(self):
        from mirsal.flow import pipeline as pl
        res = pl.read_result(self.c.out, self.gid)
        ready = [s["index"] for s in res["stickers"] if s.get("status") == "READY" and s.get("png")][:2]
        self.assertEqual(len(ready), 2, "the fixture sheet should cut at least two clean stickers with no stroke")
        s, p = self.req("/api/packs", {"name": "Blobs"})
        self.assertEqual(s, 200, p)
        for i in ready:
            self.assertEqual(self.req(f"/api/packs/{p['id']}/stickers", {"from_generation": {"id": self.gid, "index": i, "kind": "static"}})[0], 200)
        s, j = self.export(f"/api/v1/packs/{p['id']}/export-collection", {})
        self.assertEqual((s, j["ok"], j["count"], j["collection"]), (200, True, 2, "Blobs"), j)
        self.assertEqual(len(json.loads({n: v for n, f, _, v in form(FakeCMS.seen[-1]) if f is None}["MediaMetadata"])), 2)
        self.assertEqual(self.export(f"/api/packs/{p['id']}/export-collection", {}, self.member)[0], 403)
        self.assertEqual(self.export("/api/packs/P999/export-collection", {})[0], 404)
        self.assertEqual(self.export("/api/generations/G999/export-collection", {})[0], 404)
        self.assertEqual(self.export(f"/api/packs/{p['id']}/export-collection", {"surprise": 1})[0], 400)

    def test_a_refusal_is_an_answer_and_a_missing_setup_says_what_to_do(self):
        g = f"G{self.gid:03d}"
        FakeCMS.answer = (400, b'{"message": "MediaMetadata count does not match"}', "application/json")
        s, j = self.export(f"/api/generations/{g}/export-collection", {})
        self.assertEqual((s, j["ok"], j["status"], j["error"]), (200, False, 400, "MediaMetadata count does not match"))
        FakeCMS.answer = (400, b'{"title": "One or more validation errors occurred.", "errors": {"Description": ["The Description field is required."]}}', "application/problem+json")
        s, j = self.export(f"/api/generations/{g}/export-collection", {})
        self.assertIn("Description: The Description field is required.", j["error"])
        log = json.loads((self.c.out / "collection_exports.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertIn("errors", log["response"])                                                     # the refusal is kept to read later
        FakeCMS.answer = (502, b"<html>bad gateway</html>", "text/html")
        s, j = self.export(f"/api/generations/{g}/export-collection", {})
        self.assertEqual((j["ok"], j["status"], j["response"]), (False, 502, "<html>bad gateway</html>"))
        with patch.dict(os.environ, {"MIRSAL_COLLECTION_API_CREDENTIALS": ""}):
            self.assertEqual(self.req("/api/collection", method="GET")[1]["configured"], False)
            s, j = self.export(f"/api/generations/{g}/export-collection", {})
            self.assertEqual(s, 503)
            self.assertIn("MIRSAL_COLLECTION_API_CREDENTIALS", j["error"])
        self.assertEqual(col.credentials(), "me@nadi.ae:secret")
        self.assertEqual(col.auth_header(), "Basic " + base64.b64encode(b"me@nadi.ae:secret").decode())
        with patch.dict(os.environ, {"MIRSAL_COLLECTION_API_CREDENTIALS": "already-base64="}):
            self.assertEqual(col.auth_header(), "Basic already-base64=")
        with patch.dict(os.environ, {"MIRSAL_COLLECTION_API_CREDENTIALS": "sk-test-key-123"}):
            self.assertEqual(col.auth_header(), "Bearer sk-test-key-123")
            FakeCMS.answer = (200, b'{"id": 8, "message": "created"}', "application/json")
            s, j = self.export(f"/api/generations/{g}/export-collection", {"name": "Bearer pack"})
            self.assertEqual((s, j["ok"]), (200, True), j)
            self.assertEqual(FakeCMS.seen[-1]["auth"], "Bearer sk-test-key-123")

    def test_the_developer_key_api_answers(self):
        """docs/Api/AddCollection-API .md: 200 {Success: true, Result}; a 200 {Success: false} is a refusal; 400 explains in ErrorMessages; 401 is the key."""
        g = f"G{self.gid:03d}"
        FakeCMS.answer = (200, b'{"Success": true, "Result": {"CollectionId": 42, "Status": "Pending"}, "ErrorMessages": []}', "application/json")
        s, j = self.export(f"/api/generations/{g}/export-collection", {"name": "Approval pack", "description": "for review"})
        self.assertEqual((s, j["ok"], j["result"]), (200, True, {"CollectionId": 42, "Status": "Pending"}), j)
        FakeCMS.answer = (200, b'{"Success": false, "Result": null, "ErrorMessages": ["Collection name already exists"]}', "application/json")
        s, j = self.export(f"/api/generations/{g}/export-collection", {"name": "Approval pack", "description": "for review"})
        self.assertEqual((s, j["ok"], j["error"]), (200, False, "Collection name already exists"), "a 200 that says Success: false is a refusal")
        FakeCMS.answer = (400, b'{"Success": false, "ErrorMessages": ["Description is required", "Media is required"]}', "application/json")
        j = self.export(f"/api/generations/{g}/export-collection", {"name": "x"})[1]
        self.assertEqual((j["ok"], j["status"], j["error"]), (False, 400, "Description is required; Media is required"))
        FakeCMS.answer = (401, b"", "application/json")
        j = self.export(f"/api/generations/{g}/export-collection", {"name": "x"})[1]
        self.assertEqual((j["ok"], j["status"]), (False, 401))
        self.assertIn("developer key", j["error"])
        self.assertIn("Developer Keys page", j["error"])

    def test_the_api_limits_are_a_sentence_before_anything_is_uploaded(self):
        g = f"G{self.gid:03d}"
        FakeCMS.answer = (200, b'{"Success": true, "Result": {}}', "application/json")
        before = len(FakeCMS.seen)
        s, j = self.export(f"/api/generations/{g}/export-collection", {"name": "n" * 41})
        self.assertEqual(s, 400)
        self.assertIn("at most 40", j["error"])
        s, j = self.export(f"/api/generations/{g}/export-collection", {"name": "ok", "description": "d" * 161})
        self.assertEqual(s, 400)
        self.assertIn("at most 160", j["error"])
        self.assertEqual(len(FakeCMS.seen), before, "nothing was uploaded")
        self.assertEqual(self.export(f"/api/generations/{g}/export-collection", {"name": "n" * 40, "description": "d" * 160})[1]["ok"], True, "the limits themselves are fine")

    def test_tags_are_the_action_tokens_without_the_emoji(self):
        self.assertEqual(col.tags_of({"tags": ["laugh", "rofl", "LMAO", "🤣", "eye-roll", "laugh"]}), "laugh_rofl_lmao_eye_roll")

    def test_a_thumbnail_is_grey_for_a_webm_and_unchanged_for_a_png(self):
        """The CMS shows our MediaThumbnails PNG at `user_media/Emoji_Assets/{emoji}.png` (Haitham, 2026-10-15: it showed the
        full-colour first frame), so a `.webm`'s thumbnail is the grey silhouette, the same bytes as the Download .zip's
        `{stem}_grey.png`; a `.webp` is converted as before, a `.png` goes as it is."""
        import numpy as np
        from PIL import Image
        from mirsal.engine import ffmpeg as ff
        frames = np.zeros((3, 64, 64, 4), np.uint8)
        frames[:, 16:48, 16:48] = (255, 0, 0, 255)                     # a red square on transparency
        buf = io.BytesIO(); Image.fromarray(frames[0], "RGBA").save(buf, "WEBP", lossless=True)
        with tempfile.TemporaryDirectory() as d:
            ff.encode_webm(frames, 30, 30, Path(d) / "a.webm")
            webm = (Path(d) / "a.webm").read_bytes()
        img = Image.open(io.BytesIO(col.thumbnail("a.webp", buf.getvalue())))
        self.assertEqual((img.format, img.mode, img.size), ("PNG", "RGBA", (64, 64)))
        self.assertEqual((img.getpixel((0, 0))[3], img.getpixel((32, 32))[3] > 200), (0, True))
        grey = Image.open(io.BytesIO(col.thumbnail("a.webm", webm)))
        self.assertEqual((grey.format, grey.mode, grey.size), ("PNG", "P", (64, 64)))
        self.assertEqual(grey.getpalette()[:3], [191, 191, 191], "the #BFBFBF silhouette")
        self.assertEqual(max(grey.info["transparency"]), 153, "40% transparent, like the .zip's _grey.png")
        self.assertEqual((grey.getpixel((0, 0)), grey.getpixel((32, 32))), (0, 3), "transparent outside, solid inside")
        self.assertLess(len(col.thumbnail("a.webm", webm)), 6 * 1024)
        self.assertEqual(col.thumbnail("a.png", b"same bytes"), b"same bytes")
        with self.assertRaises(col.CollectionError):
            col.thumbnail("a.webm", b"not a video")


if __name__ == "__main__":
    unittest.main()
