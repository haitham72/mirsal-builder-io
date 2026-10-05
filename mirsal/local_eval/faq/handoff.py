"""Render the factual handoff from the saved evaluation and source ledger."""
import collections
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
entries=json.loads((HERE/'sources.json').read_text(encoding='utf-8'))
r=json.loads((HERE/'validation.json').read_text(encoding='utf-8'))
q=json.loads((HERE/'qwen-question-drafts.json').read_text(encoding='utf-8'))
counts=collections.Counter(e['category'] for e in entries)
lines=['# FAQ seed handoff — 2026-10-05','',
 '## Result and ownership','',
 'Created **66 repository-root FAQ files in 12 categories**, with **45 screen/looks_like headers** (68%). All are member-facing. The repository-root copies were checked against their staged copies with SHA-256. Nothing was imported into the live app or published to its real output folder.',
 '',
 'Changed only repository-root `faq/**` and newly created artifacts under `mirsal/local_eval/`. No changes to application source, tests, docs, CLAUDE.md, README.md or `.env`; no server restart. The existing dirty `docs/measurements.md` was left alone. The parent acceptance named `d1c5e09`; the checkout already had the parent’s subsequent browser-fix commit `7db4597` when the source check finished. No existing edits were reverted.',
 '',
 'This unifies `local_eval/faq-seed-prompt.md` with the accepted importer contract and the local-model work split. This agent authored and checked grounded answers, screen labels, exclusions, isolation and evaluation orchestration. Local **qwen/qwen3.5-9b** performed the easy question-paraphrasing task: one native local request generated ten alternate questions in '+str(q['seconds'])+' seconds. Those questions were reviewed for the same meaning. Qwen did not author these FAQ answers or approve their facts.',
 '',
 '## Validation actually performed','',
 '- Parsed all 66 root files through the production FAQ parser; checked category/folder agreement, required text, one-line headers and paired visual metadata.',
 '- Ran the real `python -m mirsal support import-faq --repo <repository-root faq> --json` command twice in a fresh temporary output folder: 66 created, then 66 unchanged; zero updated or skipped.',
 '- Checked that the draft-only folder returned no member search hits.',
 '- Used another fresh temporary output folder with `--publish` for retrieval. An unchanged draft import followed by `--publish` would not publish those existing unchanged entries, which is why the output folders were separate.',
 '- Called the actual `mirsal.flow.support_kb.search(out, question, "member")` for 30 cases: ten direct questions, ten independently worded screenshot descriptions, ten local-Qwen paraphrases. Expected FAQ ID came first in **30/30**.',
 '- All retrieval calls used **lexical mode**. **27/30** met the existing `enough` threshold of 0.45. Ranking success is not a guarantee that the support agent will answer: the three low-confidence cases below may still ask for clarification or offer support.',
 '- Environment overrides were set before the imports/search: `MIRSAL_DB_WRITE=0`, `MIRSAL_OUT=<temporary folder>`, `MIRSAL_SUPPORT_REPO=` (FAQ-only corpus), and text/vision provider `none`. Asserted write-through and the Postgres branch were disabled. Temporary outputs were removed automatically.',
 '- The first evaluation used screenshot descriptions closely following the metadata. I replaced them with independent descriptions of the visible labels and reran the evaluation after changing the query set; the final results below are from that stronger set. No application test suites or paid providers were run.',
 '',
 '**Not verified:** Postgres vector/semantic ranking, ranking against the combined FAQ-and-docs corpus, support-agent answer generation, screenshot-to-description model accuracy, browser rendering or live notifications/Telegram pings. This is a seed/import/retrieval evaluation, not an end-to-end support acceptance test. No new browser check was attempted; the parent commit already records its browser fixes.',
 '',
 'Evidence: [validation.json](faq/validation.json), [30 questions](faq/questions.json), [Qwen request and response](faq/qwen-question-drafts.json), [per-entry source ledger](faq/sources.json), [documentation inventory and hashes](faq/source-inventory.json). The inventory records files/headings; claims were checked against the relevant current documentation sections and code, not inferred from inventory hashes.',
 '',
 '## Low-confidence cases for the parent model','',
 '| Query | Expected FAQ / first hit | Score | Consequence |','|---|---|---:|---|']
for t in r['retrieval']:
    if not t['enough']:
        lines.append(f"| {t['query']} | `{t['expected_path']}` / `{t['first_id']}` | {t['hits'][0]['score']} | Correct first result, below answer threshold |")
lines += ['',
 'Do not lower the production threshold just to pass this seed evaluation. The parent can evaluate longer/noisier screenshot descriptions and local vector search separately before changing retrieval behavior.',
 '',
 '## Files and source of each','',
 '| Category | Entries |','|---|---:|',*[f'| {cat} | {n} |' for cat,n in sorted(counts.items())]]
for cat in sorted(counts):
    lines+=['',f'### {cat}','', '| FAQ file | Grounding sources |','|---|---|']
    for e in entries:
        if e['category']==cat:
            lines.append(f"| [faq/{e['path']}](../../faq/{e['path']}) | "+'<br>'.join(e['sources'])+' |')
lines += ['',
 'The AI-vision entries give the earlier 30-sticker run as one measurement: roughly ten seconds per sticker; five unsupported reason answers became unjudged. They do not claim human-labelled accuracy or a future performance guarantee. Generated-media vision consent is distinct from Help’s local-only screenshot reading.',
 '',
 '## Questions intentionally skipped','',
 '| Question / topic | Reason |','|---|---|',
 '| How do I import my own sheet or pick from Higgsfield history? | These controls are owner-only (`console/imports.js`); no `imports/` entries were created. |',
 '| How do I send a pack to Telegram or configure its bot? | Sending is owner-only (`console/packs.js`); setup is staff-only. Kept file-limit facts and the member-visible reason for the missing send button. |',
 '| How do I manage users, grant credits, process tickets or publish an FAQ? | Admin/owner procedures; outside the member knowledge base. |',
 '| How do I use Google sign-in or public deployment? | Paused; not current supported behavior. |',
 '| How do I launch burst creation lanes? | `docs/burst_plan.md` is a proposal, not built. Existing particle bursts are covered separately. |',
 '| How do I permanently purge deleted particle sets? | Described as unbuilt in `docs/particles.md`. |',
 '| Why does my animation go grey at the end? | No single verified general cause; avoid inventing a diagnosis. Help can receive the user’s screenshot and details. |',
 '| How long will every generation take, or exactly how many credits will it cost? | Depends on the selected model/job and live quote; do not turn measurements into promises. |',
 '| How do I repair a specific stuck job, lost file or unavailable local server? | No verified member-level general repair instructions; excluded developer recovery steps and speculative fixes. |',
 '',
 '## Full import output','',
 'IDs below are from disposable temporary outputs. They are not promised IDs for the eventual real import.',
 '', '```json',json.dumps(r['imports'],ensure_ascii=False,indent=2),'```',
 '', 'Draft search returned no hits:', '', '```json',json.dumps(r['draft_search'],ensure_ascii=False,indent=2),'```',
 '', '## Retrieval results','',
 '| # | Kind | Query | Expected ID | First ID | Score | Enough | Pass |',
 '|---:|---|---|---|---|---:|---|---|']
for i,t in enumerate(r['retrieval'],1):
    lines.append(f"| {i} | {t['kind']} | {t['query']} | {t['expected_id']} | {t['first_id']} | {t['hits'][0]['score']} | {t['enough']} | {t['passed']} |")
lines += ['',
 '## Parent-model integration handoff','',
 'The seed files are ready for the existing draft-review workflow. Importing into the real app, publishing entries, changing `.env` and restarting the server were intentionally left outside this work. The accepted real import must omit `--publish`; an authorized reviewer then uses Help > FAQ review. Do not substitute the temporary IDs above for real entry IDs.',
 '',
 'The 30-case set is ready to register as the support evaluation in `docs/backlog.md`; this agent did not edit that file because the accepted ownership boundary forbids it. Three confidence misses and untested vector/full-corpus behavior remain evidence for the parent, not claims of completed app acceptance.',
 '',
 'The accepted browser configuration remains a parent integration prerequisite if not already configured: `MIRSAL_SUPPORT_REPO` points at the repository root, and `VISION_MODEL` / `MIRSAL_SUPPORT_MODEL` select `qwen/qwen3.5-9b`. No settings values were read from or written to `.env` here.',
 '',
 '## Reproduce the isolated evaluation','',
 'From `mirsal/`, run `.\\.venv\\Scripts\\python.exe local_eval\\faq\\evaluate.py validate`. It uses repository-root `faq/`, creates and removes its own temporary output folders, disables database writes, performs imports and reads the saved query set. Running `prepare` is optional and makes a new local-Qwen question-generation call; it is not needed to reproduce the recorded evaluation.',
 '',
 'Helper files: `faq/build.py` (rebuild staged files and source ledger), `faq/install.ps1` (copy only reviewed, identical staged root files; refuses conflicting existing entries), `faq/evaluate.py` (question preparation/validation), `faq/handoff.py` (this report). Staged copies are retained under `faq/seed/` for review. Root FAQ files are the importer input. No commit or push was made by this FAQ task.',
 '']
(HERE.parent/'faq-handoff.md').write_text('\n'.join(lines),encoding='utf-8')
print('Wrote local_eval/faq-handoff.md')
