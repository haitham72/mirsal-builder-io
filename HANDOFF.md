# HANDOFF - 2026-10-20 structural refactor

Checkout G:/Haitham/VsCode/Mirsal-Builder, branch redesign-ui-ux. Never merge
without Haitham asking. The five refactors and folder redesign are complete.

## Latest request - natural video sequences

Implemented video_independent v2 for new plans: each occupied cell gets a smooth
two-action narrative with an optional third payoff. A 3x3 grid correctly labels
top-right cell 3 and mid-left cell 4; the default remains 2x2. Explicit face
gestures may use a detached hand emerging/withdrawing behind the face, with no
connecting arm/body. Images remain face-only. Exact first-frame return is added
only with Loop enabled. Saved v1/short templates and custom prompt precedence
remain unchanged. The enhancer now requests the same sequence and retains up to
600 motion characters. Details: docs/generation/20-natural-cell-video-sequences.md.
29 focused checks passed, including actual prompt delivery to a fake video CLI
for 2x2 and 3x3. No paid calls or real-data server restart. Restart the local app
before checking the new prompt in its UI.

## Completed

- e49675ed: preview cache request deduplication, retry and invalidation.
- f90ee061: Studio section/step registration replaces renderer replacement and
  HTML string insertion.
- f48df177: navigation scopes own Reactions polling and invalidate old reads.
- f7566fea: mirsal/api/ with ten routers, nine schema domains, common guards,
  OpenAPI registry and legacy stream adapter. All 92 route decorators retained.
- 2cc4556d, d3e71f78: agent lifecycle/topology and eight intent groups; all 112
  methods and three class constants retained. Old checkpoint class imports work.
- Latest UI phase: console/ui/{shell,shared,features,styles,fonts,vendor} and one
  asset manifest/resolver. Browser URLs and script order preserved; canonical
  source URLs work. Source readers/inventory follow the manifest. Vendor license
  moved with the player.

Detailed scope/evidence: docs/uiux_review/refactor-2026-10-20.md. API details:
docs/api-parts/22-native-router-layout.md. Agent details:
docs/agent-and-chat/25-agent-code-boundaries.md.

## Verification and limits

- Cache: 9 pass. Section/polling/particle editor: 63 pass.
- API contract and role/route checks pass; exact selections in the API doc.
- Agent checkpoints: 5 pass on final imports. Representative behaviors: 20/21;
  remaining locking test also fails on the saved pre-refactor implementation.
  Required focused recovery: 14 pass, zero skipped.
- UI source migration: 417 node cases passed; two old-path failures corrected,
  affected 11-case selection passed. Asset-serving/inventory: 6 pass. Two welcome
  checks pass. Shared shell retains pre-existing studio.css 9px font-scale failure.
- Playwright isolated :8797: Studio, Library, Reactions, Settings, Help and Chat
  load without page errors or failed UI assets. Draft/single composer survive
  navigation; no horizontal document overflow at 390px. Loaded artwork,
  busy/error and complete visual acceptance remain separate.

## Next

Use plan.md. Loaded-state acceptance, other watcher/edge consumers, sliders,
download/preview presenters and other caches remain separately scoped. The five
reviewed refactors, API/agent extraction and folder redesign are complete.
Owner wording/pricing/visual/merge decisions remain unapproved.

## Tools and local artifacts

- Isolated :8797 server, exec session 49126, output/refactor-browser-out; DB
  writes and providers off. Browser session refactor-check. Screenshots/scripts
  under output/playwright/refactor-*.
- Earlier :8796 (session 3670) may remain alive with older Python asset mapping.
  Restart a task-owned server before using it after the folder move.
- Do not automate/restart/repoint real-data :8770. Its owner must restart the app
  to load the new Python asset resolver.
- output/ and .playwright-cli/ remain local/untracked. Extraction scripts and
  saved original agent source are under output/.

## Unowned edits - leave untouched and unstaged

Deletions: Recovered particles L002.lottie (2).json, smiling_face.json.
Runtime writes: mirsal/out/G154-generic_test-20261015T054257/preview/anim-S1.png,
mirsal/out/higgsfield_models.json, mirsal/out/model_calls.jsonl,
mirsal/out/sessions/S020.json and subsequently observed S021.json.

Explicit-path commits, branch check before each commit. No merge, deployment,
paid calls or real Telegram/collection sends.
