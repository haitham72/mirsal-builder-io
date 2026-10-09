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

    def test_a_batch_is_sent_as_the_zip_holds_it_media_paired_with_metadata_by_index(self):
        g = f"G{self.gid:03d}"
        s, j = self.req(f"/api/generations/{g}/export-collection", {"name": "Blob pack", "description": "made in Mirsal"})
        self.assertEqual((s, j["ok"], j["collection"], j["response"]["id"]), (200, True, "Blob pack", 7), j)
        sent = FakeCMS.seen[-1]
        self.assertEqual(sent["path"], col.ENDPOINT)
        self.assertEqual(sent["auth"], "Basic " + base64.b64encode(b"me@nadi.ae:secret").decode())     # "user:password" is encoded for you
        parts = form(sent)
        fields = {n: v for n, f, _, v in parts if f is None}
        media = [(f, t, v) for n, f, t, v in parts if n == "Media"]
        meta = json.loads(fields["MediaMetadata"].decode())
        self.assertEqual((fields["CollectionName"].decode(), fields["Description"].decode()), ("Blob pack", "made in Mirsal"))
        self.assertEqual(len(media), len(meta))
        self.assertEqual(j["count"], len(media))
        zdata, _ = batches.export_zip(self.c.out, self.gid)                 # the same stickers, the same order, the same bytes as Download .zip
        with zipfile.ZipFile(io.BytesIO(zdata)) as z:
            man = json.loads(z.read("manifest.json"))
            self.assertEqual([f for f, _, _ in media], [a["filename"] for a in man["assets"]])
            self.assertEqual([v for _, _, v in media], [z.read(a["filename"]) for a in man["assets"]])
            self.assertEqual([m["emoji_utf"] for m in meta], [a["emoji"] for a in man["assets"]])
        self.assertTrue(all(t == "image/png" for _, t, _ in media))
        for m in meta:
            self.assertRegex(m["tags"], r"^[a-z0-9]+(_[a-z0-9]+)*$")
        log = [json.loads(x) for x in (self.c.out / "collection_exports.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual((log[-1]["what"], log[-1]["ok"], log[-1]["count"]), (g, True, len(media)))
        self.assertNotIn("secret", json.dumps(log))                                                       # never the credentials

    def test_a_pack_is_sent_and_only_the_owner_may(self):
        s, p = self.req("/api/packs", {"name": "Blobs"})
        self.assertEqual(s, 200, p)
        for i in (1, 2):
            self.assertEqual(self.req(f"/api/packs/{p['id']}/stickers", {"from_generation": {"id": self.gid, "index": i, "kind": "static"}})[0], 200)
        s, j = self.req(f"/api/v1/packs/{p['id']}/export-collection", {})
        self.assertEqual((s, j["ok"], j["count"], j["collection"]), (200, True, 2, "Blobs"), j)
        self.assertEqual(len(json.loads({n: v for n, f, _, v in form(FakeCMS.seen[-1]) if f is None}["MediaMetadata"])), 2)
        self.assertEqual(self.req(f"/api/packs/{p['id']}/export-collection", {}, self.member)[0], 403)
        self.assertEqual(self.req("/api/packs/P999/export-collection", {})[0], 404)
        self.assertEqual(self.req("/api/generations/G999/export-collection", {})[0], 404)
        self.assertEqual(self.req(f"/api/packs/{p['id']}/export-collection", {"surprise": 1})[0], 400)

    def test_a_refusal_is_an_answer_and_a_missing_setup_says_what_to_do(self):
        g = f"G{self.gid:03d}"
        FakeCMS.answer = (400, b'{"message": "MediaMetadata count does not match"}', "application/json")
        s, j = self.req(f"/api/generations/{g}/export-collection", {})
        self.assertEqual((s, j["ok"], j["status"], j["error"]), (200, False, 400, "MediaMetadata count does not match"))
        FakeCMS.answer = (502, b"<html>bad gateway</html>", "text/html")
        s, j = self.req(f"/api/generations/{g}/export-collection", {})
        self.assertEqual((j["ok"], j["status"], j["response"]), (False, 502, "<html>bad gateway</html>"))
        with patch.dict(os.environ, {"MIRSAL_COLLECTION_API_CREDENTIALS": ""}):
            self.assertEqual(self.req("/api/collection", method="GET")[1]["configured"], False)
            s, j = self.req(f"/api/generations/{g}/export-collection", {})
            self.assertEqual(s, 503)
            self.assertIn("MIRSAL_COLLECTION_API_CREDENTIALS", j["error"])
        self.assertEqual(col.credentials(), base64.b64encode(b"me@nadi.ae:secret").decode())
        with patch.dict(os.environ, {"MIRSAL_COLLECTION_API_CREDENTIALS": "already-base64="}):
            self.assertEqual(col.credentials(), "already-base64=")

    def test_tags_are_the_action_tokens_without_the_emoji(self):
        self.assertEqual(col.tags_of({"tags": ["laugh", "rofl", "LMAO", "🤣", "eye-roll", "laugh"]}), "laugh_rofl_lmao_eye_roll")


if __name__ == "__main__":
    unittest.main()
