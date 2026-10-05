"""Isolated, local-only 30-sticker evaluation; never changes live reviews."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mirsal.vision.judge import SYSTEM, _flatten, parse_judgement

HERE = Path(__file__).resolve().parent
ENDPOINT = "http://localhost:1234/api/v1/chat"
MODEL = "qwen/qwen3.5-9b"


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare(count=30):
    dataset = HERE / "dataset.json"
    if dataset.exists():
        raise SystemExit("dataset.json already exists; keep its labels and source snapshot.")
    groups = []
    for path in sorted((ROOT / "out").glob("G*/result.json")):
        try:
            res = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if res.get("kind") == "particles":
            continue
        rows = []
        for sticker in res.get("stickers", []):
            media = path.parent / (sticker.get("png") or "missing")
            if sticker.get("status") != "READY" or not media.is_file():
                continue
            digest = hashlib.sha256(media.read_bytes()).hexdigest()
            rows.append({"id": f"{res['generation_id']}/S{sticker['index']}", "image": str(media.resolve()),
                         "sha256": digest, "subject": res.get("task") or res.get("subject") or path.parent.name,
                         "name": sticker.get("title") or sticker.get("key") or "unknown",
                         "action": sticker.get("concept") or sticker.get("key") or "unspecified",
                         "emoji": sticker.get("emoji"), "saved_review": (sticker.get("review") or {}).get("still"),
                         "human_decision": None, "human_reason": ""})
        if rows:
            groups.append(deque(rows))
    selected, seen = [], set()
    while groups and len(selected) < count:
        remaining = []
        for group in groups:
            row = group.popleft()
            if row["sha256"] not in seen and len(selected) < count:
                selected.append(row)
                seen.add(row["sha256"])
            if group:
                remaining.append(group)
        groups = remaining
    if len(selected) != count:
        raise SystemExit(f"Only {len(selected)} unique READY sticker images found; requested {count}.")
    write(dataset, {"purpose": "Local vision-judge evaluation; independent human labels optional and initially empty",
                    "selection": "deterministic round-robin across batches; unique image hashes; not a representative random sample",
                    "model": MODEL, "endpoint": ENDPOINT, "cases": selected})
    print(f"Prepared {len(selected)} unique sticker cases in {dataset}")


def chat(system, value, timeout):
    body = {"model": MODEL, "system_prompt": system, "input": value, "temperature": 0,
            "reasoning": "off", "max_output_tokens": 700, "store": False}
    request = urllib.request.Request(ENDPOINT, json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
    # Disable proxies and redirects: every request must stay on the specified local service.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=timeout) as response:
        result = json.load(response)
    text = "\n".join(item["content"] for item in result.get("output", [])
                     if item.get("type") == "message" and isinstance(item.get("content"), str))
    if not text.strip():
        raise ValueError("Local model returned no final message")
    return text, result


def summarise(dataset, rows):
    cases = {case["id"]: case for case in dataset["cases"]}
    rows = [row for row in rows if row["id"] in cases]
    labels = {key: case["human_decision"] for key, case in cases.items() if case.get("human_decision") in ("APPROVE", "REJECT")}
    compared = [row for row in rows if row["id"] in labels]
    matches = sum(row["decision"] == labels[row["id"]] for row in compared)
    counts = Counter(row["decision"] for row in rows)
    summary = {"model": MODEL, "endpoint": ENDPOINT, "prepared": len(cases), "completed": len(rows),
               "decisions": dict(counts), "valid_json": sum(row["decision"] != "UNJUDGED" for row in rows),
               "human_labelled_cases": len(labels), "labelled_cases_run": len(compared),
               "human_agreement": matches / len(compared) if compared else None,
               "quality_calibrated": bool(len(labels) >= 30 and len(compared) >= 30 and matches / len(compared) >= .8),
               "median_seconds": round(statistics.median(row["seconds"] for row in rows), 3) if rows else None}
    write(HERE / "summary.json", summary)
    lines = ["# Local Qwen vision evaluation", "", f"Model: `{MODEL}`. Endpoint: `{ENDPOINT}`.", "",
             f"Completed: {len(rows)}/{len(cases)}. Decisions: {dict(counts)}.",
             f"Valid parsed verdicts: {summary['valid_json']}/{len(rows)}. Median seconds: {summary['median_seconds']}.", "",
             "Human agreement: " + (f"{matches}/{len(compared)} ({100 * matches / len(compared):.1f}%)" if compared else "not measured; independent labels are empty."),
             "Saved approval states are context only and are not used as an independent accuracy target.",
             "This run uses the production review prompt/parser with one image per case; pack-reference consistency and animation frames are not evaluated.", "",
             "| Case | Verdict | Seconds | Reasons / error |", "|---|---|---:|---|"]
    for row in rows:
        detail = row.get("error") or ", ".join(row.get("judgement", {}).get("reasons", [])) or "—"
        lines.append(f"| {row['id']} | {row['decision']} | {row['seconds']:.2f} | {detail.replace('|', '/').replace(chr(10), ' ')} |")
    (HERE / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def run(limit, timeout, max_seconds):
    dataset = json.loads((HERE / "dataset.json").read_text(encoding="utf-8"))
    signature = hashlib.sha256((SYSTEM + MODEL + ENDPOINT + "reasoning=off;single-image").encode()).hexdigest()
    log = HERE / "results.jsonl"
    previous = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    case_hashes = {case["id"]: case["sha256"] for case in dataset["cases"]}
    rows = {row["id"]: row for row in previous if row.get("signature") == signature and row.get("sha256") == case_hashes.get(row["id"])}
    started, failures = time.monotonic(), 0
    try:
        for case in dataset["cases"][:limit]:
            if case["id"] in rows:
                continue
            remaining = max_seconds - (time.monotonic() - started)
            if remaining <= 1:
                print("Time budget reached; rerun to resume remaining cases.", flush=True)
                break
            t0 = time.monotonic()
            row = {"id": case["id"], "sha256": case["sha256"], "signature": signature, "decision": "UNJUDGED"}
            try:
                data = Path(case["image"]).read_bytes()
                if hashlib.sha256(data).hexdigest() != case["sha256"]:
                    raise ValueError("Source changed after dataset preparation; not evaluated")
                prompt = (f"Intended sticker: {case['name']}\nAction / feeling: {case['action']}\n"
                          f"Telegram emoji tag: {case.get('emoji')}\nSubject of the pack: {case['subject']}\n"
                          "No reference sticker supplied; character_match and style_match must be null.")
                image = "data:image/png;base64," + base64.b64encode(_flatten(data)).decode()
                text, raw = chat(SYSTEM, [{"type": "text", "content": prompt}, {"type": "image", "data_url": image}], min(timeout, remaining))
                judgement = parse_judgement(text, MODEL).to_dict()
                row.update(decision=judgement["decision"], judgement=judgement, answer=text, stats=raw.get("stats"), model_instance_id=raw.get("model_instance_id"))
                failures = 0
            except (OSError, ValueError, urllib.error.URLError) as error:
                row["error"] = str(error)
                failures += 1
            row["seconds"] = round(time.monotonic() - t0, 3)
            rows[case["id"]] = row
            with log.open("a", encoding="utf-8") as file:
                file.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"{len(rows)}/{len(dataset['cases'])} {case['id']}: {row['decision']} ({row['seconds']}s)", flush=True)
            if failures >= 3:
                print("Stopped after three consecutive failures; see results.md.", flush=True)
                break
    finally:
        summary = summarise(dataset, list(rows.values()))
        print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run", "smoke", "summary"))
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--timeout", type=float, default=45)
    parser.add_argument("--max-seconds", type=float, default=240)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "smoke":
        text, response = chat("You answer only in rhymes.", "What is your favorite color?", args.timeout)
        write(HERE / "smoke.json", {"answer": text, "response": response})
        print(text)
    elif args.command == "summary":
        dataset = json.loads((HERE / "dataset.json").read_text(encoding="utf-8"))
        rows = [json.loads(line) for line in (HERE / "results.jsonl").read_text(encoding="utf-8").splitlines()]
        print(json.dumps(summarise(dataset, list({r["id"]: r for r in rows}.values())), indent=2))
    else:
        if args.limit < 1 or args.timeout <= 0 or args.max_seconds <= 0:
            parser.error("limit and time budgets must be positive")
        run(args.limit, args.timeout, args.max_seconds)
