# HANDOFF - 2026-10-20 structural refactor

## Latest - API integration + docs convergence (2026-10-21)

Export to collection implemented on both servers (commit acca724f on redesign-ui-ux, pushed): stdlib dispatch + guards for the 4 routes, openapi rows fixed (202), StdlibCollectionTests (3 new). Docs converge here on code-audit to five files (architecture/design/api-integration/generation/rules) + backlog/waiting + inputs/; the draft docs/integration/API_DOCUMENTATION.md is superseded by docs/api-integration.md. Test: area services/collection 11/11, console/openapi 36/36; 2 console/server failures reproduce on the base (pre-existing). W29 recount 3,480; second W49 renumbered W51.

Checkout G:/Haitham/VsCode/Mirsal-Builder, branch code-audit (docs convergence to five files; implementation stays on redesign-ui-ux). Never merge
without Haitham asking.

## Latest request - super reaction (2026-10-20)

Hold the reaction, release, and the screen plays: engine/super_reaction.py (screen-shaped canvas
by aspect bucket, bottom emitters, auto/solid/gradient glow, a centre pop that floats up and
wiggles with Sway). Sources = the files in mirsal/lottie, by name. Sandbox: Create > + New >
Super reaction (#/super) and the Super Emojis tab (Reaction effects, Library > Reactions):
desktop window (plays in its chat area only) + iPhone (whole phone), both resizable, desktop as
tall as the phone. Sliders Size, Amount, Rise, Float, Sway, Spread, Glow; moving one shows ONE
still frame at Animation frame (0-100%) instead of playing.
Library (flow/super_reactions.py, out/particles/super/library.json): every file has a seeded
random look until saved; Shuffle, Save, Save as (another version of the same file), Remove
(saved version only), presets (save / load / remove). Export: JSON per screen and
superReactions.zip (each saved version, else the random look, x 8 buckets + manifest.json).
Details and open items: docs/reaction/19-19-super-reaction.md. 22 Python checks pass; browser
checked on an isolated :8797. Restart the local app to see it. Visual verdict is Haitham's.

Mirsal-redesign (other repo, branch app-ai-removal, committed LOCALLY only: its pre-push hook
allows master only): hold any emoji in the emoji panel = super-like with that exact emoji
(src/chats/superReaction.ts, canvas, no Lottie; desktop = chat area, phone = whole phone), and
the look skill now reads public/ from the repo root (the "not a picture in the app" error).

## Earlier request - natural video sequences

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

- Do not automate/restart/repoint real-data :8770. Its owner must restart the app to load new code.
- output/ and .playwright-cli/ remain local/untracked.

Explicit-path commits, branch check before each commit. No merge, deployment,
paid calls or real Telegram/collection sends.
