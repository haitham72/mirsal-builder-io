"""The HTTP contract: well-formed, served, typed for TypeScript, and guarded against drift from the server's source."""
import json
import re
import threading
import unittest
from pathlib import Path

from mirsal.console import openapi

SERVER = Path(__file__).resolve().parent.parent / "mirsal" / "console" / "server.py"


def refs(node, out):
    if isinstance(node, dict):
        if "$ref" in node:
            out.add(node["$ref"])
        for v in node.values():
            refs(v, out)
    elif isinstance(node, list):
        for v in node:
            refs(v, out)


class SpecShape(unittest.TestCase):
    def setUp(self):
        self.spec = openapi.build()

    def test_it_is_openapi_31_and_every_ref_resolves(self):
        self.assertEqual(self.spec["openapi"], "3.1.0")
        found = set()
        refs(self.spec, found)
        names = set(self.spec["components"]["schemas"])
        self.assertTrue(found)
        for r in found:
            self.assertIn(r.rsplit("/", 1)[1], names, r)

    def test_operation_ids_are_unique_and_path_params_are_declared(self):
        ids = []
        for path, ops in self.spec["paths"].items():
            declared_in_path = set(re.findall(r"\{(\w+)\}", path))
            for method, op in ops.items():
                ids.append(op["operationId"])
                declared = {p["name"] for p in op.get("parameters", []) if p["in"] == "path"}
                self.assertEqual(declared, declared_in_path, f"{method} {path}")
        self.assertEqual(len(ids), len(set(ids)))

    def test_the_chat_and_events_and_assets_are_typed(self):
        p = self.spec["paths"]
        send = p["/api/chat/sessions/{id}/messages"]["post"]
        self.assertEqual(send["requestBody"]["content"]["application/json"]["schema"]["$ref"], "#/components/schemas/ChatSend")
        self.assertIn("Idempotency-Key", [x["name"] for x in send["parameters"]])
        ev = p["/api/generations/{id}/events"]["get"]
        self.assertIn("text/event-stream", ev["responses"]["200"]["content"])
        self.assertIn("Last-Event-ID", [x["name"] for x in ev["parameters"]])
        self.assertEqual(p["/api/assets/sign"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"], "#/components/schemas/AssetLink")


class DriftGuard(unittest.TestCase):
    """A route that exists in the server but not in the spec fails here, so the contract cannot silently rot."""

    def setUp(self):
        self.src = SERVER.read_text(encoding="utf-8")
        self.paths = set(openapi.build()["paths"])

    def test_every_static_api_route_of_the_server_is_described(self):
        static = {m for m in re.findall(r'path == "(/api/[^"]+)"', self.src)}
        missing = sorted(p for p in static if p not in self.paths)
        self.assertEqual(missing, [], "routes in server.py missing from console/openapi.py")

    def test_every_generation_verb_of_the_server_is_described(self):
        verbs = set(re.findall(r'if parts\[3\] == "([a-z_]+)"', self.src))
        wanted = {f"/api/generations/{{id}}/{v}" for v in verbs}
        missing = sorted(w for w in wanted if w not in self.paths)
        self.assertEqual(missing, [])

    def test_every_route_family_the_server_serves_has_a_description(self):
        for prefix in re.findall(r'path\.startswith\("(/api/[a-z]+)', self.src):
            self.assertTrue(any(p.startswith(prefix) for p in self.paths), prefix)


class TypeScript(unittest.TestCase):
    def test_types_are_generated_from_the_schemas(self):
        ts = openapi.typescript()
        for name in ("Session", "Message", "Step", "Sticker", "ChatSend", "Event", "AssetLink", "Health"):
            self.assertIn(f"export interface {name}", ts)
        self.assertEqual(ts.count("{"), ts.count("}"))
        self.assertIn('kind: "task" | "step" | "note" | "final";', ts)
        self.assertIn("status?:", ts)                                    # optional where not required


class Served(unittest.TestCase):
    def test_the_server_serves_the_same_document(self):
        import http.client
        import shutil
        import tempfile
        from mirsal.console.server import serve
        tmp = Path(tempfile.mkdtemp())
        (tmp / "in").mkdir()
        srv, c = serve(tmp / "out", tmp / "in", 0, block=False)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            h = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=10)
            h.request("GET", "/api/openapi.json")
            r = h.getresponse()
            body = json.loads(r.read())
            self.assertEqual(r.status, 200)
            self.assertEqual(set(body["paths"]), set(openapi.build()["paths"]))
        finally:
            srv.shutdown()
            c.release_writer()
            srv.server_close()
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
