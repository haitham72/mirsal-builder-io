"""Stage the two requested documentation updates without changing repository-root files."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
repo = here.parents[1]
summary = json.loads((here / "summary.json").read_text(encoding="utf-8"))
assert summary["completed"] == 30 and summary["valid_json"] == 25
assert summary["model"] == "qwen/qwen3.5-9b"
stage = here / "doc_updates"
stage.mkdir(exist_ok=True)
manifest = []

for name in ("waiting-for-haitham.md", "measurements.md"):
    original = (repo / "docs" / name).read_bytes()
    text = original.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    if name == "waiting-for-haitham.md":
        old = next(line for line in text.splitlines() if line.startswith("**11. "))
        new = ('**11. Compare your judgments with the prepared vision-judge results.** The local 30-sticker run with '
               '`qwen/qwen3.5-9b` is complete (2026-10-05): 24 APPROVE, 1 REJECT, 5 UNJUDGED because of unsupported reason codes; '
               '25/30 usable first-pass verdicts, median 10.437 s. Results: [local evaluation](../mirsal/local_eval/results.md), '
               'recorded in `docs/measurements.md`. **Only independent human labels remain:** review the already prepared '
               '`mirsal/local_eval/dataset.json` cases and fill `human_decision` (APPROVE/REJECT), optionally `human_reason`. '
               'Then an agent regenerates the summary locally without another model call. Existing saved approvals were not treated '
               'as fresh ground truth. The 83.3% usable-response rate is not accuracy; the provisional human-agreement target remains '
               '>= 80%. Unblocks: measuring whether the judge agrees with you; it does not block using the app or its advisory judge.')
        text = text.replace(old, new, 1)
    else:
        heading = "## Vision judge: local Qwen 9B evaluation (2026-10-05)"
        assert heading not in text, "Already recorded; do not duplicate the results."
        block = '''## Vision judge: local Qwen 9B evaluation (2026-10-05)

Actual model: `qwen/qwen3.5-9b`, served locally through LM Studio's `http://localhost:1234/api/v1/chat`. All 30 prepared cases were run. The supplied rhyme smoke request also returned a rhyming answer (`mirsal/local_eval/smoke.json`).

| Measurement | Result |
|---|---:|
| Unique READY still-sticker cases completed | 30/30 |
| APPROVE | 24 |
| REJECT | 1 (G104/S1: AMBIGUOUS_ACTION, WEAK_CONCEPT) |
| UNJUDGED | 5 |
| Usable first-pass verdicts through the production parser | 25/30 (83.3%) |
| Median end-to-end time per sticker | 10.437 s |
| Independently human-labelled cases | 0 |
| Agreement with a human | Not measured |

The five UNJUDGED cases are G004/S1, G096/S1, G097/S1, G105/S1 and G004/S2. Their responses used unsupported reason codes such as CONCEPT_MATCH and WARM_EXPRESSION. These failures were retained rather than repaired or counted as passes.

Method: deterministic round-robin sampling across existing batches, unique source-image hashes, the production review prompt and verdict parser, one still image on grey per request, temperature 0, reasoning off, 700 maximum output tokens, no stored chat and no automatic repair call. The production judge normally offers one repair round; this run measures first-pass behavior only. Source hashes are pinned. No cloud fallback, paid generation, live review changes or application configuration changes were made.

Scope: this tests local vision responses, parser compatibility and latency. It does not evaluate animation motion, reference-image consistency, pool search or chat resolution. The sample is not a balanced or representative accuracy benchmark. **83.3% is the usable-response rate, not model accuracy.** Independent labels are empty, so the judge remains uncalibrated against Haitham's judgments. Saved review states are context only and are never provided to the model as answers.

Artifacts and runner: [results](../mirsal/local_eval/results.md), [summary](../mirsal/local_eval/summary.json), [dataset](../mirsal/local_eval/dataset.json), [instructions](../mirsal/local_eval/README.md). After Haitham fills the dataset's human labels, `mirsal/.venv/Scripts/python.exe -B mirsal/local_eval/run.py summary` from the repository root recomputes agreement without any new inference. W11 tracks only that human comparison.

'''
        marker = "## Photo cutout (3C)"
        assert marker in text
        text = text.replace(marker, block.replace("\n", newline) + marker, 1)
    updated = text.encode("utf-8")
    (stage / name).write_bytes(updated)
    manifest.append({"name": name, "original": hashlib.sha256(original).hexdigest(), "updated": hashlib.sha256(updated).hexdigest()})
(stage / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("Staged measurements and W11; authoritative files not changed yet.")
