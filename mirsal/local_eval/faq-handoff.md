# FAQ seed handoff — 2026-10-05

## Result and ownership

Created **66 repository-root FAQ files in 12 categories**, with **45 screen/looks_like headers** (68%). All are member-facing. The repository-root copies were checked against their staged copies with SHA-256. Nothing was imported into the live app or published to its real output folder.

Changed only repository-root `faq/**` and newly created artifacts under `mirsal/local_eval/`. No changes to application source, tests, docs, CLAUDE.md, README.md or `.env`; no server restart. The existing dirty `docs/measurements.md` was left alone. The parent acceptance named `d1c5e09`; the checkout already had the parent’s subsequent browser-fix commit `7db4597` when the source check finished. No existing edits were reverted.

This unifies `local_eval/faq-seed-prompt.md` with the accepted importer contract and the local-model work split. This agent authored and checked grounded answers, screen labels, exclusions, isolation and evaluation orchestration. Local **qwen/qwen3.5-9b** performed the easy question-paraphrasing task: one native local request generated ten alternate questions in 30.813 seconds. Those questions were reviewed for the same meaning. Qwen did not author these FAQ answers or approve their facts.

## Validation actually performed

- Parsed all 66 root files through the production FAQ parser; checked category/folder agreement, required text, one-line headers and paired visual metadata.
- Ran the real `python -m mirsal support import-faq --repo <repository-root faq> --json` command twice in a fresh temporary output folder: 66 created, then 66 unchanged; zero updated or skipped.
- Checked that the draft-only folder returned no member search hits.
- Used another fresh temporary output folder with `--publish` for retrieval. An unchanged draft import followed by `--publish` would not publish those existing unchanged entries, which is why the output folders were separate.
- Called the actual `mirsal.flow.support_kb.search(out, question, "member")` for 30 cases: ten direct questions, ten independently worded screenshot descriptions, ten local-Qwen paraphrases. Expected FAQ ID came first in **30/30**.
- All retrieval calls used **lexical mode**. **27/30** met the existing `enough` threshold of 0.45. Ranking success is not a guarantee that the support agent will answer: the three low-confidence cases below may still ask for clarification or offer support.
- Environment overrides were set before the imports/search: `MIRSAL_DB_WRITE=0`, `MIRSAL_OUT=<temporary folder>`, `MIRSAL_SUPPORT_REPO=` (FAQ-only corpus), and text/vision provider `none`. Asserted write-through and the Postgres branch were disabled. Temporary outputs were removed automatically.
- The first evaluation used screenshot descriptions closely following the metadata. I replaced them with independent descriptions of the visible labels and reran the evaluation after changing the query set; the final results below are from that stronger set. No application test suites or paid providers were run.

**Not verified:** Postgres vector/semantic ranking, ranking against the combined FAQ-and-docs corpus, support-agent answer generation, screenshot-to-description model accuracy, browser rendering or live notifications/Telegram pings. This is a seed/import/retrieval evaluation, not an end-to-end support acceptance test. No new browser check was attempted; the parent commit already records its browser fixes.

Evidence: [validation.json](faq/validation.json), [30 questions](faq/questions.json), [Qwen request and response](faq/qwen-question-drafts.json), [per-entry source ledger](faq/sources.json), [documentation inventory and hashes](faq/source-inventory.json). The inventory records files/headings; claims were checked against the relevant current documentation sections and code, not inferred from inventory hashes.

## Low-confidence cases for the parent model

| Query | Expected FAQ / first hit | Score | Consequence |
|---|---|---:|---|
| When attaching an image in Help a notice says A screenshot must be under 8 MB. | `troubleshooting/screenshot-large.md` / `F065` | 0.363 | Correct first result, below answer threshold |
| In the particle editor I opened a saved version. There are Save and Save as new buttons; I want to keep the original version. | `particles/save-version.md` / `F040` | 0.438 | Correct first result, below answer threshold |
| Why is the Send to Telegram option missing from my pack? | `telegram/member-send.md` / `F054` | 0.426 | Correct first result, below answer threshold |

Do not lower the production threshold just to pass this seed evaluation. The parent can evaluate longer/noisier screenshot descriptions and local vector search separately before changing retrieval behavior.

## Files and source of each

| Category | Entries |
|---|---:|
| accounts | 5 |
| ai-chat | 4 |
| ai-vision | 7 |
| animation | 5 |
| credits | 2 |
| getting-started | 4 |
| library | 6 |
| particles | 10 |
| studio | 9 |
| telegram | 4 |
| trending | 4 |
| troubleshooting | 6 |

### accounts

| FAQ file | Grounding sources |
|---|---|
| [faq/accounts/create-account.md](../../faq/accounts/create-account.md) | docs/api.md: Office accounts on the LAN<br>mirsal/mirsal/console/auth.js: gate, waiting, change, me |
| [faq/accounts/waiting-approval.md](../../faq/accounts/waiting-approval.md) | docs/api.md: Office accounts on the LAN<br>mirsal/mirsal/console/auth.js: gate, waiting, change, me |
| [faq/accounts/forgot-password.md](../../faq/accounts/forgot-password.md) | docs/api.md: Office accounts on the LAN<br>mirsal/mirsal/console/auth.js: gate, waiting, change, me |
| [faq/accounts/choose-password.md](../../faq/accounts/choose-password.md) | docs/api.md: Office accounts on the LAN<br>mirsal/mirsal/console/auth.js: gate, waiting, change, me |
| [faq/accounts/sign-out.md](../../faq/accounts/sign-out.md) | docs/api.md: Office accounts on the LAN<br>mirsal/mirsal/console/auth.js: gate, waiting, change, me |

### ai-chat

| FAQ file | Grounding sources |
|---|---|
| [faq/ai-chat/remember-subject.md](../../faq/ai-chat/remember-subject.md) | docs/agent-and-chat.md: Spending; Memory; Questions and their answers<br>mirsal/mirsal/console/agent.js: settings popover |
| [faq/ai-chat/persistent-feedback.md](../../faq/ai-chat/persistent-feedback.md) | docs/agent-and-chat.md: Spending; Memory; Questions and their answers<br>mirsal/mirsal/console/agent.js: settings popover |
| [faq/ai-chat/which-sticker.md](../../faq/ai-chat/which-sticker.md) | docs/agent-and-chat.md: Spending; Memory; Questions and their answers<br>mirsal/mirsal/console/agent.js: settings popover |
| [faq/ai-chat/not-yet.md](../../faq/ai-chat/not-yet.md) | docs/agent-and-chat.md: Spending; Memory; Questions and their answers<br>mirsal/mirsal/console/agent.js: settings popover |

### ai-vision

| FAQ file | Grounding sources |
|---|---|
| [faq/ai-vision/review-not-approval.md](../../faq/ai-vision/review-not-approval.md) | docs/agent-and-chat.md: The vision judge; Consent; Per-frame captions; Support<br>mirsal/local_eval/results.md<br>mirsal/mirsal/console/support.js: screenshot composer |
| [faq/ai-vision/unjudged.md](../../faq/ai-vision/unjudged.md) | docs/agent-and-chat.md: The vision judge; Consent; Per-frame captions; Support<br>mirsal/local_eval/results.md<br>mirsal/mirsal/console/support.js: screenshot composer |
| [faq/ai-vision/review-time.md](../../faq/ai-vision/review-time.md) | docs/agent-and-chat.md: The vision judge; Consent; Per-frame captions; Support<br>mirsal/local_eval/results.md<br>mirsal/mirsal/console/support.js: screenshot composer |
| [faq/ai-vision/consent.md](../../faq/ai-vision/consent.md) | docs/agent-and-chat.md: The vision judge; Consent; Per-frame captions; Support<br>mirsal/local_eval/results.md<br>mirsal/mirsal/console/support.js: screenshot composer |
| [faq/ai-vision/captions.md](../../faq/ai-vision/captions.md) | docs/agent-and-chat.md: The vision judge; Consent; Per-frame captions; Support<br>mirsal/local_eval/results.md<br>mirsal/mirsal/console/support.js: screenshot composer |
| [faq/ai-vision/help-screenshot.md](../../faq/ai-vision/help-screenshot.md) | docs/agent-and-chat.md: The vision judge; Consent; Per-frame captions; Support<br>mirsal/local_eval/results.md<br>mirsal/mirsal/console/support.js: screenshot composer |
| [faq/ai-vision/useful-screenshot.md](../../faq/ai-vision/useful-screenshot.md) | docs/agent-and-chat.md: The vision judge; Consent; Per-frame captions; Support<br>mirsal/local_eval/results.md<br>mirsal/mirsal/console/support.js: screenshot composer |

### animation

| FAQ file | Grounding sources |
|---|---|
| [faq/animation/not-animated.md](../../faq/animation/not-animated.md) | docs/engine-and-studio.md: Animation; Edge; The golden path<br>mirsal/mirsal/console/generate.js: ANIMWHY, tileHtml, gate counts |
| [faq/animation/outside-slot.md](../../faq/animation/outside-slot.md) | docs/engine-and-studio.md: Animation; Edge; The golden path<br>mirsal/mirsal/console/generate.js: ANIMWHY, tileHtml, gate counts |
| [faq/animation/bad-loop.md](../../faq/animation/bad-loop.md) | docs/engine-and-studio.md: Animation; Edge; The golden path<br>mirsal/mirsal/console/generate.js: ANIMWHY, tileHtml, gate counts |
| [faq/animation/edge-changed.md](../../faq/animation/edge-changed.md) | docs/engine-and-studio.md: Animation; Edge; The golden path<br>mirsal/mirsal/console/generate.js: ANIMWHY, tileHtml, gate counts |
| [faq/animation/frame-checks.md](../../faq/animation/frame-checks.md) | docs/engine-and-studio.md: Animation; Edge; The golden path<br>mirsal/mirsal/console/generate.js: ANIMWHY, tileHtml, gate counts |

### credits

| FAQ file | Grounding sources |
|---|---|
| [faq/credits/spend-confirmation.md](../../faq/credits/spend-confirmation.md) | docs/agent-and-chat.md: Spending<br>mirsal/mirsal/console/agent.js: Ask before spending<br>mirsal/mirsal/console/auth.js: me |
| [faq/credits/request-more.md](../../faq/credits/request-more.md) | docs/agent-and-chat.md: Spending<br>mirsal/mirsal/console/agent.js: Ask before spending<br>mirsal/mirsal/console/auth.js: me |

### getting-started

| FAQ file | Grounding sources |
|---|---|
| [faq/getting-started/stickers-not-emoji.md](../../faq/getting-started/stickers-not-emoji.md) | README.md: Overview and Console<br>docs/onboarding.md: The welcome modal |
| [faq/getting-started/welcome-again.md](../../faq/getting-started/welcome-again.md) | README.md: Overview and Console<br>docs/onboarding.md: The welcome modal |
| [faq/getting-started/two-ways.md](../../faq/getting-started/two-ways.md) | README.md: Overview and Console<br>docs/onboarding.md: The welcome modal |
| [faq/getting-started/batch-and-sheet.md](../../faq/getting-started/batch-and-sheet.md) | README.md: Overview and Console<br>docs/onboarding.md: The welcome modal |

### library

| FAQ file | Grounding sources |
|---|---|
| [faq/library/empty-library.md](../../faq/library/empty-library.md) | mirsal/mirsal/console/app.js: libBody, libByPackHtml<br>mirsal/mirsal/console/packs.js: pack header, delete confirmation, carousel<br>mirsal/mirsal/console/trash.js: Trash panel |
| [faq/library/my-stickers.md](../../faq/library/my-stickers.md) | mirsal/mirsal/console/app.js: libBody, libByPackHtml<br>mirsal/mirsal/console/packs.js: pack header, delete confirmation, carousel<br>mirsal/mirsal/console/trash.js: Trash panel |
| [faq/library/search-library.md](../../faq/library/search-library.md) | mirsal/mirsal/console/app.js: libBody, libByPackHtml<br>mirsal/mirsal/console/packs.js: pack header, delete confirmation, carousel<br>mirsal/mirsal/console/trash.js: Trash panel |
| [faq/library/bulk-select.md](../../faq/library/bulk-select.md) | mirsal/mirsal/console/app.js: libBody, libByPackHtml<br>mirsal/mirsal/console/packs.js: pack header, delete confirmation, carousel<br>mirsal/mirsal/console/trash.js: Trash panel |
| [faq/library/delete-pack.md](../../faq/library/delete-pack.md) | mirsal/mirsal/console/app.js: libBody, libByPackHtml<br>mirsal/mirsal/console/packs.js: pack header, delete confirmation, carousel<br>mirsal/mirsal/console/trash.js: Trash panel |
| [faq/library/download-pack.md](../../faq/library/download-pack.md) | mirsal/mirsal/console/app.js: libBody, libByPackHtml<br>mirsal/mirsal/console/packs.js: pack header, delete confirmation, carousel<br>mirsal/mirsal/console/trash.js: Trash panel |

### particles

| FAQ file | Grounding sources |
|---|---|
| [faq/particles/sprites-burst.md](../../faq/particles/sprites-burst.md) | docs/particles.md: Ownership; One scoped editor; Animated sprites and recovery; Galleries and chat |
| [faq/particles/free-source.md](../../faq/particles/free-source.md) | docs/particles.md: Ownership; One scoped editor; Animated sprites and recovery; Galleries and chat |
| [faq/particles/paid-sources.md](../../faq/particles/paid-sources.md) | docs/particles.md: Ownership; One scoped editor; Animated sprites and recovery; Galleries and chat |
| [faq/particles/save-version.md](../../faq/particles/save-version.md) | docs/particles.md: Ownership; One scoped editor; Animated sprites and recovery; Galleries and chat |
| [faq/particles/open-version.md](../../faq/particles/open-version.md) | docs/particles.md: Ownership; One scoped editor; Animated sprites and recovery; Galleries and chat |
| [faq/particles/add-more.md](../../faq/particles/add-more.md) | docs/particles.md: Ownership; One scoped editor; Animated sprites and recovery; Galleries and chat |
| [faq/particles/size-sharpness.md](../../faq/particles/size-sharpness.md) | docs/particles.md: Ownership; One scoped editor; Animated sprites and recovery; Galleries and chat |
| [faq/particles/put-in-pack.md](../../faq/particles/put-in-pack.md) | docs/particles.md: Ownership; One scoped editor; Animated sprites and recovery; Galleries and chat |
| [faq/particles/echo-preview.md](../../faq/particles/echo-preview.md) | docs/particles.md: Ownership; One scoped editor; Animated sprites and recovery; Galleries and chat |
| [faq/particles/standalone.md](../../faq/particles/standalone.md) | docs/particles.md: Ownership; One scoped editor; Animated sprites and recovery; Galleries and chat |

### studio

| FAQ file | Grounding sources |
|---|---|
| [faq/studio/drop-sticker.md](../../faq/studio/drop-sticker.md) | docs/engine-and-studio.md: The golden path; Use it anyway; Editing a created sticker<br>mirsal/mirsal/console/generate.js: cellVerb, tileHtml, grmText<br>mirsal/mirsal/console/live.js: remHtml |
| [faq/studio/use-anyway.md](../../faq/studio/use-anyway.md) | docs/engine-and-studio.md: The golden path; Use it anyway; Editing a created sticker<br>mirsal/mirsal/console/generate.js: cellVerb, tileHtml, grmText<br>mirsal/mirsal/console/live.js: remHtml |
| [faq/studio/take-back.md](../../faq/studio/take-back.md) | docs/engine-and-studio.md: The golden path; Use it anyway; Editing a created sticker<br>mirsal/mirsal/console/generate.js: cellVerb, tileHtml, grmText<br>mirsal/mirsal/console/live.js: remHtml |
| [faq/studio/bulk-allow.md](../../faq/studio/bulk-allow.md) | docs/engine-and-studio.md: The golden path; Use it anyway; Editing a created sticker<br>mirsal/mirsal/console/generate.js: cellVerb, tileHtml, grmText<br>mirsal/mirsal/console/live.js: remHtml |
| [faq/studio/hard-limit.md](../../faq/studio/hard-limit.md) | docs/engine-and-studio.md: The golden path; Use it anyway; Editing a created sticker<br>mirsal/mirsal/console/generate.js: cellVerb, tileHtml, grmText<br>mirsal/mirsal/console/live.js: remHtml |
| [faq/studio/remove-batch.md](../../faq/studio/remove-batch.md) | docs/engine-and-studio.md: The golden path; Use it anyway; Editing a created sticker<br>mirsal/mirsal/console/generate.js: cellVerb, tileHtml, grmText<br>mirsal/mirsal/console/live.js: remHtml |
| [faq/studio/restore-batch.md](../../faq/studio/restore-batch.md) | docs/engine-and-studio.md: The golden path; Use it anyway; Editing a created sticker<br>mirsal/mirsal/console/generate.js: cellVerb, tileHtml, grmText<br>mirsal/mirsal/console/live.js: remHtml |
| [faq/studio/edit-copy.md](../../faq/studio/edit-copy.md) | docs/engine-and-studio.md: The golden path; Use it anyway; Editing a created sticker<br>mirsal/mirsal/console/generate.js: cellVerb, tileHtml, grmText<br>mirsal/mirsal/console/live.js: remHtml |
| [faq/studio/fixed-sheet.md](../../faq/studio/fixed-sheet.md) | docs/engine-and-studio.md: The golden path; Use it anyway; Editing a created sticker<br>mirsal/mirsal/console/generate.js: cellVerb, tileHtml, grmText<br>mirsal/mirsal/console/live.js: remHtml |

### telegram

| FAQ file | Grounding sources |
|---|---|
| [faq/telegram/video-limits.md](../../faq/telegram/video-limits.md) | docs/engine-and-studio.md: Telegram limits<br>mirsal/mirsal/engine/config.py: EngineConfig<br>mirsal/mirsal/engine/verify.py: no_audio<br>mirsal/mirsal/console/packs.js: owner send control, sticker details |
| [faq/telegram/static-limits.md](../../faq/telegram/static-limits.md) | docs/engine-and-studio.md: Telegram limits<br>mirsal/mirsal/engine/config.py: EngineConfig<br>mirsal/mirsal/engine/verify.py: no_audio<br>mirsal/mirsal/console/packs.js: owner send control, sticker details |
| [faq/telegram/emoji-tag.md](../../faq/telegram/emoji-tag.md) | docs/engine-and-studio.md: Telegram limits<br>mirsal/mirsal/engine/config.py: EngineConfig<br>mirsal/mirsal/engine/verify.py: no_audio<br>mirsal/mirsal/console/packs.js: owner send control, sticker details |
| [faq/telegram/member-send.md](../../faq/telegram/member-send.md) | docs/engine-and-studio.md: Telegram limits<br>mirsal/mirsal/engine/config.py: EngineConfig<br>mirsal/mirsal/engine/verify.py: no_audio<br>mirsal/mirsal/console/packs.js: owner send control, sticker details |

### trending

| FAQ file | Grounding sources |
|---|---|
| [faq/trending/copy-public.md](../../faq/trending/copy-public.md) | mirsal/mirsal/console/trending.js: list, detail, ORDERS<br>docs/api.md: Trending |
| [faq/trending/no-public.md](../../faq/trending/no-public.md) | mirsal/mirsal/console/trending.js: list, detail, ORDERS<br>docs/api.md: Trending |
| [faq/trending/sort-public.md](../../faq/trending/sort-public.md) | mirsal/mirsal/console/trending.js: list, detail, ORDERS<br>docs/api.md: Trending |
| [faq/trending/comment.md](../../faq/trending/comment.md) | mirsal/mirsal/console/trending.js: list, detail, ORDERS<br>docs/api.md: Trending |

### troubleshooting

| FAQ file | Grounding sources |
|---|---|
| [faq/troubleshooting/no-answer.md](../../faq/troubleshooting/no-answer.md) | mirsal/mirsal/console/support.js: next, fresh, noteRow, suOpen, suFile<br>docs/api.md: Help & Support |
| [faq/troubleshooting/answer-wrong.md](../../faq/troubleshooting/answer-wrong.md) | mirsal/mirsal/console/support.js: next, fresh, noteRow, suOpen, suFile<br>docs/api.md: Help & Support |
| [faq/troubleshooting/waiting-support.md](../../faq/troubleshooting/waiting-support.md) | mirsal/mirsal/console/support.js: next, fresh, noteRow, suOpen, suFile<br>docs/api.md: Help & Support |
| [faq/troubleshooting/notification.md](../../faq/troubleshooting/notification.md) | mirsal/mirsal/console/support.js: next, fresh, noteRow, suOpen, suFile<br>docs/api.md: Help & Support |
| [faq/troubleshooting/reopen.md](../../faq/troubleshooting/reopen.md) | mirsal/mirsal/console/support.js: next, fresh, noteRow, suOpen, suFile<br>docs/api.md: Help & Support |
| [faq/troubleshooting/screenshot-large.md](../../faq/troubleshooting/screenshot-large.md) | mirsal/mirsal/console/support.js: next, fresh, noteRow, suOpen, suFile<br>docs/api.md: Help & Support |

The AI-vision entries give the earlier 30-sticker run as one measurement: roughly ten seconds per sticker; five unsupported reason answers became unjudged. They do not claim human-labelled accuracy or a future performance guarantee. Generated-media vision consent is distinct from Help’s local-only screenshot reading.

## Questions intentionally skipped

| Question / topic | Reason |
|---|---|
| How do I import my own sheet or pick from Higgsfield history? | These controls are owner-only (`console/imports.js`); no `imports/` entries were created. |
| How do I send a pack to Telegram or configure its bot? | Sending is owner-only (`console/packs.js`); setup is staff-only. Kept file-limit facts and the member-visible reason for the missing send button. |
| How do I manage users, grant credits, process tickets or publish an FAQ? | Admin/owner procedures; outside the member knowledge base. |
| How do I use Google sign-in or public deployment? | Paused; not current supported behavior. |
| How do I launch burst creation lanes? | `docs/burst_plan.md` is a proposal, not built. Existing particle bursts are covered separately. |
| How do I permanently purge deleted particle sets? | Described as unbuilt in `docs/particles.md`. |
| Why does my animation go grey at the end? | No single verified general cause; avoid inventing a diagnosis. Help can receive the user’s screenshot and details. |
| How long will every generation take, or exactly how many credits will it cost? | Depends on the selected model/job and live quote; do not turn measurements into promises. |
| How do I repair a specific stuck job, lost file or unavailable local server? | No verified member-level general repair instructions; excluded developer recovery steps and speculative fixes. |

## Full import output

IDs below are from disposable temporary outputs. They are not promised IDs for the eventual real import.

```json
{
  "first": {
    "created": [
      "F001",
      "F002",
      "F003",
      "F004",
      "F005",
      "F006",
      "F007",
      "F008",
      "F009",
      "F010",
      "F011",
      "F012",
      "F013",
      "F014",
      "F015",
      "F016",
      "F017",
      "F018",
      "F019",
      "F020",
      "F021",
      "F022",
      "F023",
      "F024",
      "F025",
      "F026",
      "F027",
      "F028",
      "F029",
      "F030",
      "F031",
      "F032",
      "F033",
      "F034",
      "F035",
      "F036",
      "F037",
      "F038",
      "F039",
      "F040",
      "F041",
      "F042",
      "F043",
      "F044",
      "F045",
      "F046",
      "F047",
      "F048",
      "F049",
      "F050",
      "F051",
      "F052",
      "F053",
      "F054",
      "F055",
      "F056",
      "F057",
      "F058",
      "F059",
      "F060",
      "F061",
      "F062",
      "F063",
      "F064",
      "F065",
      "F066"
    ],
    "updated": [],
    "unchanged": 0,
    "skipped": [],
    "published": false
  },
  "second": {
    "created": [],
    "updated": [],
    "unchanged": 66,
    "skipped": [],
    "published": false
  },
  "temporary_publish": {
    "created": [
      "F001",
      "F002",
      "F003",
      "F004",
      "F005",
      "F006",
      "F007",
      "F008",
      "F009",
      "F010",
      "F011",
      "F012",
      "F013",
      "F014",
      "F015",
      "F016",
      "F017",
      "F018",
      "F019",
      "F020",
      "F021",
      "F022",
      "F023",
      "F024",
      "F025",
      "F026",
      "F027",
      "F028",
      "F029",
      "F030",
      "F031",
      "F032",
      "F033",
      "F034",
      "F035",
      "F036",
      "F037",
      "F038",
      "F039",
      "F040",
      "F041",
      "F042",
      "F043",
      "F044",
      "F045",
      "F046",
      "F047",
      "F048",
      "F049",
      "F050",
      "F051",
      "F052",
      "F053",
      "F054",
      "F055",
      "F056",
      "F057",
      "F058",
      "F059",
      "F060",
      "F061",
      "F062",
      "F063",
      "F064",
      "F065",
      "F066"
    ],
    "updated": [],
    "unchanged": 0,
    "skipped": [],
    "published": true
  }
}
```

Draft search returned no hits:

```json
{
  "mode": "lexical",
  "hits": [],
  "enough": false,
  "code_used": false
}
```

## Retrieval results

| # | Kind | Query | Expected ID | First ID | Score | Enough | Pass |
|---:|---|---|---|---|---:|---|---|
| 1 | question | Why does my account say Waiting for approval? | F005 | F005 | 1.0 | True | True |
| 2 | question | How do I reset a forgotten password? | F003 | F003 | 1.0 | True | True |
| 3 | question | Why am I asked to choose my own password? | F001 | F001 | 1.0 | True | True |
| 4 | question | What does Use it anyway do on a blocked sticker? | F052 | F052 | 1.0 | True | True |
| 5 | question | Will removing a batch remove stickers already in my packs? | F049 | F049 | 1.0 | True | True |
| 6 | question | How do I restore a removed batch? | F050 | F050 | 1.0 | True | True |
| 7 | question | Why must I animate again after changing the edge? | F018 | F018 | 1.0 | True | True |
| 8 | question | Why does an animation show Bad loop? | F017 | F017 | 1.0 | True | True |
| 9 | question | Why does my Library say Nothing here yet? | F031 | F031 | 1.0 | True | True |
| 10 | question | Where can I see all my stickers grouped by pack? | F032 | F032 | 1.0 | True | True |
| 11 | screenshot-description | In Help, below the reply there is a Send to support button and the message Nothing in the help answers this yet. | F062 | F062 | 0.608 | True | True |
| 12 | screenshot-description | A Help answer ends with Did this solve it? I can choose Yes, solved or No, send to support. | F061 | F061 | 0.85 | True | True |
| 13 | screenshot-description | My Help conversation has a Waiting for support label. It says a person will answer here and I get a notification. | F066 | F066 | 0.812 | True | True |
| 14 | screenshot-description | The left column of Help has Notifications with a Support answered item. Where is the reply? | F063 | F063 | 0.593 | True | True |
| 15 | screenshot-description | This Help conversation is marked Resolved. At the bottom I see Not fixed after all? and a Reopen button. | F064 | F064 | 0.78 | True | True |
| 16 | screenshot-description | When attaching an image in Help a notice says A screenshot must be under 8 MB. | F065 | F065 | 0.363 | False | True |
| 17 | screenshot-description | In the particle editor I opened a saved version. There are Save and Save as new buttons; I want to keep the original version. | F040 | F040 | 0.438 | False | True |
| 18 | screenshot-description | I see particle version rows labelled v1 and v2 with Open buttons. How do I edit an old version? | F037 | F037 | 0.747 | True | True |
| 19 | screenshot-description | The particle simulator has Energy, Float, Swirl and Size sliders. Which one makes the particles bigger? | F041 | F041 | 0.597 | True | True |
| 20 | screenshot-description | A public pack in Library Trending has a Use in my workflow button. Does it copy the pack? | F058 | F058 | 0.907 | True | True |
| 21 | local-qwen-paraphrase | Can I create stickers or custom emoji with Mirsal? | F025 | F025 | 0.857 | True | True |
| 22 | local-qwen-paraphrase | What distinguishes a batch from a sheet? | F024 | F024 | 0.62 | True | True |
| 23 | local-qwen-paraphrase | Are there specific limits for animated Telegram stickers? | F056 | F056 | 0.744 | True | True |
| 24 | local-qwen-paraphrase | Why is the Send to Telegram option missing from my pack? | F054 | F054 | 0.426 | False | True |
| 25 | local-qwen-paraphrase | How do I ensure a preference persists beyond the next generation? | F007 | F007 | 0.663 | True | True |
| 26 | local-qwen-paraphrase | What should I do when the AI asks me to specify a sticker? | F009 | F009 | 0.578 | True | True |
| 27 | local-qwen-paraphrase | Does the AI automatically approve stickers during pre-review? | F013 | F013 | 0.658 | True | True |
| 28 | local-qwen-paraphrase | Why might the AI leave a sticker unjudged? | F015 | F015 | 0.72 | True | True |
| 29 | local-qwen-paraphrase | How much time does the local AI pre-review process take? | F014 | F014 | 0.695 | True | True |
| 30 | local-qwen-paraphrase | Does adding more particles replace my existing sprites? | F034 | F034 | 0.824 | True | True |

## Parent-model integration handoff

The seed files are ready for the existing draft-review workflow. Importing into the real app, publishing entries, changing `.env` and restarting the server were intentionally left outside this work. The accepted real import must omit `--publish`; an authorized reviewer then uses Help > FAQ review. Do not substitute the temporary IDs above for real entry IDs.

The 30-case set is ready to register as the support evaluation in `docs/backlog.md`; this agent did not edit that file because the accepted ownership boundary forbids it. Three confidence misses and untested vector/full-corpus behavior remain evidence for the parent, not claims of completed app acceptance.

The accepted browser configuration remains a parent integration prerequisite if not already configured: `MIRSAL_SUPPORT_REPO` points at the repository root, and `VISION_MODEL` / `MIRSAL_SUPPORT_MODEL` select `qwen/qwen3.5-9b`. No settings values were read from or written to `.env` here.

## Reproduce the isolated evaluation

From `mirsal/`, run `.\.venv\Scripts\python.exe local_eval\faq\evaluate.py validate`. It uses repository-root `faq/`, creates and removes its own temporary output folders, disables database writes, performs imports and reads the saved query set. Running `prepare` is optional and makes a new local-Qwen question-generation call; it is not needed to reproduce the recorded evaluation.

Helper files: `faq/build.py` (rebuild staged files and source ledger), `faq/install.ps1` (copy only reviewed, identical staged root files; refuses conflicting existing entries), `faq/evaluate.py` (question preparation/validation), `faq/handoff.py` (this report). Staged copies are retained under `faq/seed/` for review. Root FAQ files are the importer input. No commit or push was made by this FAQ task.

## Completed main-to-sol task — support case chains (2026-10-05)

Added **21 FAQs**, bringing repository-root `faq/` to **87 entries**. Existing FAQs, including the main agent’s corrected account closings, were preserved. Added **26 chains / 62 turns**, with **six on-topic no-answer turns**, in [cases.json](faq/cases.json). Nine local-Qwen paraphrases were reviewed and applied; one was rejected because it changed touching a boundary to extending past it. Expected outcomes were authored by this agent, not Qwen.

The main agent’s instruction records that the original 66 FAQs were committed and imported into the real app as drafts. It also supplied [semantic-check.json](faq/semantic-check.json): 30/30 original questions first and confident with local nomic embeddings; two unrelated queries were nevertheless vector-confident. Those are the main agent’s measurements, not a new Postgres validation by this task. The earlier handoff sections above are historical snapshots. This task neither changed nor reran that semantic evidence.

### Checks completed

- All 87 files passed the production seed parser and category/visual-metadata checks.
- Case IDs are unique; all cited seed paths exist; request/need/activity values match the requested contract; six no-answer turns are present.
- Six synthetic fixture sets were materialized in temporary output and read by the production activity function. Required job/batch sources were found; the other member’s J005 was not exposed.
- Fresh temporary draft import: **87 created**, zero skipped/updated. Second import: **87 unchanged**, zero created/updated/skipped. Draft search returned no hits.
- Separate fresh temporary publication for retrieval only: **21/21 new FAQ questions ranked their expected entry first**. The original 30-query set also remained **30/30 first** against the expanded FAQ corpus.
- All these checks used `MIRSAL_DB_WRITE=0`, temporary `MIRSAL_OUT`, FAQ-only corpus, and text/vision provider `none`. No real app import, publication, provider generation, Telegram message, code/test/doc edit or server restart occurred.

Evidence: [chain-validation.json](faq/chain-validation.json), [chain-sources.json](faq/chain-sources.json), [chain-paraphrases.json](faq/chain-paraphrases.json).

**Not executed here:** the 26 conversations end to end through the support model; private-message UI/actions; feature/access escalation; notification/watch transitions; real screenshot recognition; vector ranking of the new corpus. The instruction explicitly assigns draft import and scratch-server end-to-end execution to the main agent. Static case validity and activity-fixture checks do not establish that the model satisfies the expected outcomes.

### Fixture contract for the main agent

`fixture.user` is the synthetic member (u1). Write each `fixture.jobs` object to the scratch output’s jobs/<id>.json and each `fixture.batches` object to <generation_id>/result.json, with an empty slices/ folder, as in SupportCaseTests. Each case gets a fresh isolated output and conversation; never materialize these fixtures into real out/. Jobs retain numeric creation/claim/completion timestamps matching the test shapes. Rebase timestamps together if testing much later so elapsed time remains useful.

Cases with activity fixtures cover a running, failed, timed-out and completed job, a 2-of-9 batch, and another member’s private job. The running-job case supplies a CLAIMED job and asks about watching it; it does not simulate the later DONE transition. A watch-transition extension should change that scratch job to DONE, invoke the existing watch check, and verify one update/resolution, using SupportCaseTests. Private reply cases cite the user instructions; they do not contain tokens or simulate admin replies. Stub Telegram pings in the scratch runner.

`no_answer: true` means do not invent capabilities, explanations or disclose another member’s records. It can include an honest statement that the sources do not establish the requested feature; it is not a requirement to emit an empty response. Follow-up turns must use the same conversation: checking each turn independently would miss the point of these chains.

### New root FAQ files and grounding

| File | Sources |
|---|---|
| [faq/troubleshooting/feature-request.md](../../faq/troubleshooting/feature-request.md) | docs/agent-and-chat.md: The real cases<br>docs/api.md: Help & Support<br>mirsal/mirsal/console/support.js: next, priv |
| [faq/accounts/access-request.md](../../faq/accounts/access-request.md) | docs/agent-and-chat.md: The real cases<br>docs/api.md: Help & Support<br>mirsal/mirsal/console/support.js: next, priv |
| [faq/accounts/private-reply.md](../../faq/accounts/private-reply.md) | docs/agent-and-chat.md: The real cases<br>docs/api.md: Help & Support<br>mirsal/mirsal/console/support.js: next, priv |
| [faq/accounts/forget-private-reply.md](../../faq/accounts/forget-private-reply.md) | docs/agent-and-chat.md: The real cases<br>docs/api.md: Help & Support<br>mirsal/mirsal/console/support.js: next, priv |
| [faq/troubleshooting/job-progress.md](../../faq/troubleshooting/job-progress.md) | docs/agent-and-chat.md: Your activity as sources; Watches<br>mirsal/mirsal/flow/support.py: activity, check_watches |
| [faq/troubleshooting/job-arrival.md](../../faq/troubleshooting/job-arrival.md) | docs/agent-and-chat.md: Your activity as sources; Watches<br>mirsal/mirsal/flow/support.py: activity, check_watches |
| [faq/troubleshooting/job-timeout.md](../../faq/troubleshooting/job-timeout.md) | docs/agent-and-chat.md: Your activity as sources; Watches<br>mirsal/mirsal/flow/support.py: activity, check_watches |
| [faq/troubleshooting/job-failure.md](../../faq/troubleshooting/job-failure.md) | docs/agent-and-chat.md: Your activity as sources; Watches<br>mirsal/mirsal/flow/support.py: activity, check_watches |
| [faq/troubleshooting/own-activity.md](../../faq/troubleshooting/own-activity.md) | docs/agent-and-chat.md: Your activity as sources; Watches<br>mirsal/mirsal/flow/support.py: activity, check_watches |
| [faq/studio/accepted-count.md](../../faq/studio/accepted-count.md) | docs/agent-and-chat.md: Your activity as sources; Watches<br>mirsal/mirsal/flow/support.py: activity, check_watches<br>docs/engine-and-studio.md: Use it anyway |
| [faq/studio/zip-from-studio.md](../../faq/studio/zip-from-studio.md) | mirsal/mirsal/console/packs.js: pack header<br>mirsal/mirsal/console/generate.js: Studio controls<br>docs/api.md: pack export.zip<br>docs/agent-and-chat.md: Request kinds |
| [faq/studio/external-edit-return.md](../../faq/studio/external-edit-return.md) | docs/api.md: Import an existing sheet or video<br>docs/engine-and-studio.md: Editing a created sticker<br>mirsal/mirsal/console/imports.js: import controls<br>mirsal/mirsal/console/prepare.js: Save to sticker |
| [faq/credits/reserved-balance.md](../../faq/credits/reserved-balance.md) | docs/api.md: Credits per person<br>mirsal/mirsal/flow/jobs.py: _settle |
| [faq/credits/failed-job-refund.md](../../faq/credits/failed-job-refund.md) | docs/api.md: Credits per person<br>mirsal/mirsal/flow/jobs.py: _settle |
| [faq/credits/automatic-refill.md](../../faq/credits/automatic-refill.md) | docs/api.md: Credits per person<br>mirsal/mirsal/flow/jobs.py: _settle<br>docs/agent-and-chat.md: The real cases<br>docs/api.md: Help & Support<br>mirsal/mirsal/console/support.js: next, priv |
| [faq/imports/member-controls.md](../../faq/imports/member-controls.md) | docs/api.md: Import an existing sheet or video<br>mirsal/mirsal/console/imports.js: owner, impButtons<br>docs/agent-and-chat.md: Request kinds |
| [faq/particles/restore-set.md](../../faq/particles/restore-set.md) | docs/particles.md: Storage, migration and deletion<br>mirsal/mirsal/console/particles.js: deletion, spTrashHtml |
| [faq/particles/deleted-parent-pack.md](../../faq/particles/deleted-parent-pack.md) | docs/particles.md: Storage, migration and deletion<br>mirsal/mirsal/console/packs.js: delete confirmation |
| [faq/animation/edited-size-limit.md](../../faq/animation/edited-size-limit.md) | docs/engine-and-studio.md: Editing a created sticker<br>mirsal/mirsal/console/prepare.js: Save to sticker<br>mirsal/mirsal/engine/verify.py: TECHNICAL |
| [faq/troubleshooting/new-question.md](../../faq/troubleshooting/new-question.md) | mirsal/mirsal/console/support.js: suCol, ACT.sunew, composer |
| [faq/library/open-studio-edit.md](../../faq/library/open-studio-edit.md) | docs/engine-and-studio.md: Editing a created sticker |

### Case chains

| ID | Turns |
|---|---:|
| pack-zip-to-studio-feature | 3 |
| blocked-sticker-to-external-edit-feature | 3 |
| particle-delete-to-purge-feature | 2 |
| help-answer-to-feature-suggestion | 3 |
| member-import-to-access-request | 2 |
| credits-top-up-access-request | 2 |
| tester-token-private-reply | 3 |
| private-message-notification | 2 |
| running-video-duration-and-arrival | 2 |
| failed-job-and-refund | 2 |
| timeout-not-paid-retry | 2 |
| accepted-count-to-override | 3 |
| activity-privacy-no-leak | 2 |
| completed-job-and-batch | 2 |
| animation-edge-stale | 2 |
| particle-versions-and-echo | 3 |
| library-edit-and-pack-copies | 2 |
| pack-trash-and-particle-retention | 2 |
| trending-copy-and-comments | 3 |
| telegram-limit-and-platform-unknown | 2 |
| chat-preference-and-selection | 3 |
| balance-reservation-and-admin | 3 |
| approved-account-admin-help | 2 |
| help-screenshot-and-unjudged | 3 |
| unknown-cause-needs-screenshot | 2 |
| help-reopen-to-new-issue | 2 |

### New local files

`faq/cases.json`, `faq/chain-sources.json`, `faq/chain-paraphrases.json`, `faq/chain-validation.json`, `faq/build_chains.py`, `faq/paraphrase_chains.py`, `faq/review_paraphrases.py`, `faq/install-chains.ps1`, `faq/validate_chains.py`, `faq/finish_chains.py`, and the 21 staged copies under `faq/chains-seed/`. Changed `local_eval/faq-handoff.md` by adding this update. The original source/evaluation artifacts were preserved. Reproduction: `.\.venv\Scripts\python.exe local_eval\faq\validate_chains.py`. The older evaluate.py remains the historical 66-entry evaluator; use validate_chains.py for the expanded corpus.

No extra entry was added for planned Google sign-in or permanent particle purge; those appear only as feature-request/unknown-capability cases where appropriate. Member import documentation describes the missing owner-only controls, without teaching an owner procedure. External-edit replacement is documented as the current workflow gap described by the main agent; a future implementation must revise that FAQ and its feature-request expectation.

The task instruction `local_eval/main-to-sol.md` is removed on completion as Haitham requested. No commit or push was performed by this task.

