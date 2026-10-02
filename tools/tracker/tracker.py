"""Generation tracker. Run: python tracker.py  ->  http://127.0.0.1:8765
Scans Images_gen/ and videos_gen/ live on every request (names + sizes only; never opens media).
Human fields (status, chosen takes, set path, notes) persist in tracker.json beside this file."""
import json, os, re, sys, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = next((os.path.join(os.path.dirname(os.path.dirname(HERE)), d) for d in ('inputs', 'Phase_01')
                 if os.path.isdir(os.path.join(os.path.dirname(os.path.dirname(HERE)), d, 'Images_gen'))),
                os.path.join(os.path.dirname(os.path.dirname(HERE)), 'inputs'))  # the watch folders (inputs/, or Phase_01/ in an older checkout)
DB = os.path.join(HERE, "tracker.json")
LOCK = threading.Lock()
STATUSES = ["generated", "prepared", "1A_validated", "reviewed", "1B_done", "rejected"]
FIELDS = {"status", "chosen_img", "chosen_vid", "set_path", "notes"}
DIR_RE = re.compile(r"^(img|vid)-(\d{3})-(.+)$")
FILE_RE = re.compile(r"\((\d+)\)\.([A-Za-z0-9]+)$")

def scan():
    items = {}
    for kind, root in (("img", "Images_gen"), ("vid", "videos_gen")):
        base = os.path.join(ROOT, root)
        if not os.path.isdir(base):
            continue
        for d in sorted(os.listdir(base)):
            m = DIR_RE.match(d)
            full = os.path.join(base, d)
            if not m or m.group(1) != kind or not os.path.isdir(full):
                continue
            key = f"{m.group(2)}-{m.group(3)}"
            it = items.setdefault(key, {"id": m.group(2), "subject": m.group(3), "key": key, "img": [], "vid": []})
            for f in sorted(os.listdir(full)):
                fm = FILE_RE.search(f)
                if fm:
                    it[kind].append({"take": int(fm.group(1)), "ext": fm.group(2).lower(),
                                     "kb": round(os.path.getsize(os.path.join(full, f)) / 1024)})
            it[kind].sort(key=lambda x: x["take"])
    return items

def load():
    try:
        with open(DB, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save(db):
    fd, tmp = tempfile.mkstemp(dir=HERE, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DB)

def state():
    db, items = load(), scan()
    rows = []
    for key in sorted(items):
        it = items[key]
        it.update({"status": "generated", "chosen_img": None, "chosen_vid": None, "set_path": "", "notes": ""})
        it.update(db.get(key, {}))
        rows.append(it)
    return {"statuses": STATUSES, "rows": rows}

PAGE = """<!doctype html><meta charset=utf-8><title>Generation tracker</title>
<style>body{font:14px system-ui;margin:20px;background:#111;color:#eee}table{border-collapse:collapse;width:100%}
th,td{padding:6px 8px;border-bottom:1px solid #333;text-align:left;vertical-align:top}th{color:#9ab}
input,select{background:#1c1c1c;color:#eee;border:1px solid #444;padding:3px;font:inherit}small{color:#888}
.ok{color:#6c6}</style><h3>Generation tracker <small id=meta></small></h3>
<table><thead><tr><th>ID<th>Subject<th>Image takes<th>Video takes<th>Chosen img<th>Chosen vid<th>Status<th>Set path<th>Notes</thead><tbody id=b></tbody></table>
<script>
const sel=(o,v,k,f)=>`<select data-k="${k}" data-f="${f}"><option value="">-</option>${o.map(x=>`<option ${String(x)===String(v)?'selected':''}>${x}</option>`).join('')}</select>`;
async function post(k,f,v){await fetch('/api/update',{method:'POST',body:JSON.stringify({key:k,field:f,value:v})});document.getElementById('meta').textContent='saved '+new Date().toLocaleTimeString()}
async function load(){
 if(document.activeElement&&document.activeElement.closest('tbody'))return;
 const s=await (await fetch('/api/state')).json();
 document.getElementById('b').innerHTML=s.rows.map(r=>`<tr><td>${r.id}<td>${r.subject}
 <td>${r.img.map(t=>t.take+' <small>'+t.kb+'KB</small>').join(', ')||'<small>none</small>'}
 <td>${r.vid.map(t=>t.take+' <small>'+t.kb+'KB</small>').join(', ')||'<small>none</small>'}
 <td>${sel(r.img.map(t=>t.take),r.chosen_img,r.key,'chosen_img')}<td>${sel(r.vid.map(t=>t.take),r.chosen_vid,r.key,'chosen_vid')}
 <td>${sel(s.statuses,r.status,r.key,'status')}
 <td><input data-k="${r.key}" data-f="set_path" value="${r.set_path}" placeholder="mirsal/sets/${r.subject}/01">
 <td><input data-k="${r.key}" data-f="notes" value="${r.notes}">`).join('');
}
document.addEventListener('change',e=>{const d=e.target.dataset;if(d.k)post(d.k,d.f,e.target.value||null).then(load)});
load();setInterval(load,4000);
</script>"""

class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code); self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path == "/api/state":
            with LOCK: self._send(200, json.dumps(state()))
        elif self.path == "/":
            self._send(200, PAGE, "text/html")
        else:
            self._send(404, "{}")
    def do_POST(self):
        if self.path != "/api/update":
            return self._send(404, "{}")
        try:
            p = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            key, field, value = p["key"], p["field"], p["value"]
            if field not in FIELDS or key not in scan():
                raise ValueError("bad field or key")
            if field == "status" and value not in STATUSES:
                raise ValueError("bad status")
            if field.startswith("chosen_") and value is not None:
                value = int(value)
        except Exception as e:
            return self._send(400, json.dumps({"error": str(e)}))
        with LOCK:
            db = load(); db.setdefault(key, {})[field] = value; save(db)
        self._send(200, "{}")
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"Tracker on http://127.0.0.1:{port}  (root: {ROOT})")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
