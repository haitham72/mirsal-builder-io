# HANDOFF - session save point, 2026-10-20

Checkout `G:/Haitham/VsCode/Mirsal-Builder`, branch `redesign-ui-ux`.
Last pushed commit **9baa54e9** (dark-rework close-out docs + Postgres profile
sync docs), pushed to `origin/redesign-ui-ux`. Previous save point's close-out
is done: `current-status.md` and the J01/J07/J10 journey headers now say they
describe the pre-dark-rework audit and link `dark-rework-2026-10-19.md`; the
untracked `output/playwright/` scratch was moved out of the repo (not deleted,
not committed). Main stays `0167761b`.

This session separately confirmed the chat's Postgres profile sync
(`docs/agent-and-chat/24-durable-turns-and-profiles-2026-10-16.md`,
`out/profile/<user>.json` -> `user_profiles` via `store/sync.sync_profile`):
`mirsal-db` had exited and was restarted (`docker start mirsal-db`); a name
saved before that restart never reached Postgres (sync is best-effort, skipped
silently when unreachable) and a name saved after the restart did
(`user_profiles` row for `user_id='local'`). No code changed for this; only
the two docs above were updated to say so.

plan.md is next steps only; nothing here needs more docs work before Haitham's
review.

## Latest user decisions

- Dark mode should learn from https://higgsfield.ai/ai/video but KEEP Mirsal's
  original cyan-blue accent. The intermediate soft-blue draft was replaced.
- **New request always open**, including reopened batches. Do not fold it to
  reduce density. Options/Prompt engine may retain internal disclosures.
- Missing sticker/video options were found by Haitham: **Stickers / Sheet / Both**.
  No removed-controls regression was invented/fixed; keep those choices.
- **Plan** Studio creation settings on the left, artwork/workspace right like
  Higgsfield. Proposal is written in `docs/design/15-studio-creation-sidebar-plan.md`.
  Sidebar implementation has NOT started; plan review is pending.

## Implemented in the working tree

1. `mirsal/mirsal/console/theme.css`: neutral charcoal depth and original cyan
   actions, separate Chat canvas/user messages/composer/menus, quiet neutral
   greeting, dark aurora/dots/pointer glow disabled, shared primary hover fixed.
   Light palette and media/diagnostic colors are preserved.
2. `console/composer.js`: New request is a named SECTION, not collapsible details.
   `console/studio.css`: removes outer closed-state styling, retains nested options.
3. New tests `mirsal/tests/js/theme_palette.test.js` (3) and
   `mirsal/tests/js/composer_visibility.test.js` (1).
4. Documentation/evidence: dark-mode.md; design foundations/per-screen docs;
   current status/backlog; J01/J07/J10 status/checklists; audit UX-02 follow-up;
   implementation log; `docs/uiux_review/dark-rework-2026-10-19.md` and `.json`;
   **10 cited screenshots** in `docs/uiux_review/dark-rework-shots/`.
5. Layout proposal and its design.md index entry are documentation only.

## Verified - do not rerun for docs

- Four narrow Node regressions pass after real failing assertions. Final cyan
  palette 3/3 passed after the accent revision; composer 1/1 pass remains valid.
  Command: `node --test mirsal/tests/js/theme_palette.test.js mirsal/tests/js/composer_visibility.test.js`.
- Playwright: **36 core states** (9 states x desktop/phone x light/dark), plus
  **24 actual view-switch cases** (Stills/Animation x Stickers/Sheet/Both x four
  width/theme states). Nine individual items and nine frame/Adjust controls in
  Stickers/Both; none in Sheet by design; Size/X/Y reachable.
- No app page errors, failed responses or mutation POSTs. Primary hover:
  **13.24:1 dark / 5.17:1 light** on both widths. Dark ambient animation: none.
  Sampled light colors unchanged; tiny shadow interpolation is not a palette change.
- Eighteen light states were retained after their pass because later edits were
  dark-scoped; affected dark states were rechecked. Final screenshots explicitly
  isolate open/closed menus. Harness errors about nested summaries or toggling an
  already-open Adjust panel were corrected; they were not product regressions.
- Source hashes in the dated JSON match the current three production files.
  Changed Markdown links resolved; git diff --check passed at the last check.
- Broader inherited results only: agent 322 / 4 failures / 9 errors; old Node
  390/390, wrapper 18/18. Full suites were NOT rerun or claimed freshly green.

## Remaining close-out details

All done this session: docs clarified and linked (see above), scratch archived
outside the repo, explicit paths committed as `9baa54e9` and pushed. Nothing
left to close out before Haitham's review.

- User's initial phone-editor/Save question was answered: the populated image/
  animation editors and Save form clip at phone width; this is still UX-01, NOT
  fixed by the dark theme or the future sidebar plan.
- Do not implement the proposed sidebar merely because its plan is written.

## Running tools / paths

- The prior session's task server (**http://127.0.0.1:8798/**) is no longer
  running; its Playwright sessions are gone too. Nothing to stop/repoint.
- **User real-data app http://127.0.0.1:8770/** is the only server now up; it
  is live and was restarted by Haitham this session. Never stop/repoint/automate it.
- `mirsal-db` (Postgres, port 5434) was found stopped and was started with
  `docker start mirsal-db`; it is up. If it exits again, Postgres writes
  (profiles/tasks/tickets) silently stop until `serve` is also restarted
  (`store/db.available()` caches the first failure per process) — see
  `docs/dev-notes.md` and `docs/agent-and-chat/24-durable-turns-and-profiles-2026-10-16.md`.
- Reference measured ~318px creation panel, near-neutral page/form/control
  backgrounds. The proposal uses a 352px preferred / 320-384px bounded Mirsal
  panel, rehomes batch history to avoid an extra permanent column and preserves
  every per-item tool, free/priced step and import/review/export contract.

## Unowned edits - leave untouched and unstaged

- Deletions: `Recovered particles L002.lottie (2).json`, `smiling_face.json`.
- Runtime writes from the live real-data server (never stage these):
  `mirsal/out/G154-generic_test-20261015T054257/preview/anim-S1.png`,
  `mirsal/out/higgsfield_models.json`, `mirsal/out/model_calls.jsonl`,
  `mirsal/out/sessions/S020.json` (new, from this session's "my name is" checks).
- Never stage runtime data, secrets, artwork or unrelated changes. The new UI
  screenshots are documentation evidence. Verify branch before every commit.
  No merge, deployment, paid call, Telegram or collection send is authorized.
