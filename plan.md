# Reaction effects: what is still open


**For implementation by another LLM.** The open items of the reaction UI spec (2026-10-13). Built and removed from this plan: the rename to "reaction"
(labels only; `/api/particles`, `out/particles/`, internal names unchanged), Lottie export, the Size in / Size out envelope (scale over time), the
"Recovered" naming, the pack's own "Reactions in this pack" section, and the simplified header. Architecture: `docs/reaction.md`, `docs/effects.md`;
the look: `docs/design.md`. Find code by name, not by line number (the files moved since the spec was written).

Keep API routes, storage and internal variable names unchanged; only labels and UI move. Test on a copy of `out/` (`MIRSAL_OUT=<copy>`), in both themes and below 760 px.

## UI cleanup

1. **Set card** (`spSetCard`, `console/particles.js`): the cell / picked counts and "made for N stickers" only on hover; the cost line only when something was spent;
   Duplicate / Rename / Delete in a "⋯" menu. Keep: preview strip, name, Open, Attach / Add to pack.
2. **Sticker unlink list** (the `psunassign` rows in the open set card): hidden by default behind "Manage stickers", with "Attached to N stickers" as the summary.
3. **Motion presets**: show only the selected preset with a "Change" button (or a `<details>`) instead of every chip at once.
4. **One Advanced section** (the two `<details class=fx-adv>` in the burst editor, "reactions, spin" and "sprite resolution"): one collapsed
   `<details>` whose summary reads its values ("Advanced: 28 reactions, spin 1, 100 px").
5. **Burst rows** (`pkBurst`, `console/packs.js`): drop the preset name (the set card shows it): "burst · ready · in <pack>", keep the download.

## Pack view

6. **No tabs** (`PKTAB`, `ACT.pktab`, the `.pk-tabs` segment in `drawPack`): always the stickers grid with its selection bar first, then the reactions
   section (`pkPsHtml`), with a separator; delete `PKTAB` and `pktab`.
7. **"Open in Studio" on Library pack cards**: a button that opens the pack's stickers in the Studio (the single-sticker view already has one: `lcopenstudio`).

## Features

8. **"Open and save" on a set card**: opens the editor on that set and saves it as a new row on close or on an explicit Save.
9. **Erosion in the reaction Timeline**: `erosion_px` (default 0) on `ParticleParams` (`engine/particles.py`), applied to each sprite's alpha after keying
   and before despill (a morphological erosion; `engine/chroma.py` already has the keyer's), and a slider beside the motion controls.

Each new control is read by the backend (rule 6), and `tests/test_ui_inventory.py` must stay green (a removed action needs a `retired` entry in `tests/data/ui_baseline.json`).

## UI/UX implementation and visual redesign — remaining work (2026-10-15)

**Keep items 1–9 above until each is implemented and verified.** This section adds the broader UI/UX plan; it does not replace the reaction/pack backlog. Overlapping work is implemented once, with both references recorded. The explicit pack-layout request in item 6 is not cancelled by the audit's older question about tabs; preserve every remaining action and record any authorized retirement in the UI baseline.

### Read the current implementation before selecting tasks

Start with [review index](docs/uiux_review/README.md), [execution record](docs/uiux_review/implementation-log.md), then the relevant [journey folder](docs/uiux_review/journeys/). Use [uiux_plan.md](docs/uiux_plan.md) as a searchable task catalog, not mandatory whole-file startup reading. The earlier [revalidation](docs/uiux_review/revalidation.md) and tasks.json statuses predate the implemented repair batch and newer handpicked-Lottie work: do not treat them as today's open-bug list.

- [ ] Reconcile the selected finding/task with current source and implementation markers. Skip completed repairs; revise obsolete scopes. Update status evidence as work is accepted. Preserve the other LLM's changes; use an isolated worktree if its checkout is active, and check branch before commits.
- [ ] Complete focused browser acceptance of the implemented repair batch: staged Keep size (T-001), dialog dismissal (T-002), queue/Studio clocks (T-003/004), badge hit testing (T-065), phone viewer (T-086), welcome contrast (T-074), Settings navigation (T-072), Help keyboard controls (T-073). Source anchors and reported narrow tests exist; real-browser acceptance remains open. Reopen a repair only for a reproduced failure, not because the historical review calls it open.

### A visible redesign is required, beyond bug fixes

- [ ] Introduce/reconcile semantic tokens (T-056) for an 8px spacing grid, five type roles, readable status/colour pairs, radii, elevation, focus and motion. Use existing tokens where suitable. Then apply consistent 44px interaction targets (T-066), including phone controls; preserve per-picture decisions and honest primary/secondary hierarchy.
- [ ] Complete one representative journey (Studio, J1) as the visual reference: grouped controls, clear stage primary, progressive disclosure, consistent menus/segments and responsive sheets. Use the journey's issue → proposed-fix document and sketches. Check desktop/phone and dark/light. Show before/after hierarchy, grouping, density and readability improvements; recolouring alone is insufficient. Preserve current grid, size-mode and backend behavior.
- [ ] Extract shared presentation only where duplication is confirmed: Apply/Cancel test cards, dialogs, grouped grids, ranges/segments, feedback, download/preview lifecycle and watchers. One helper/consumer at a time, with narrow regression checks. Do not erase deliberate endpoint, unit, ownership or cancellation differences. T-058 edge synchronization and the remaining watcher migration are still candidates; the completed queue/Studio fixes do not finish that work.
- [ ] Migrate the remaining journey surfaces through the same visual system: J2 Chat; J3 Library/pack/viewer/editors; J4/J5 current reaction/Lottie/pack workflows; J6 rejection/override states; J7 Home/welcome; J8 Settings/Help/Trending; J9 export dialogs. Apply J10 theme and J11 phone acceptance to each affected journey. Keep related pending work from items 1–9 visible until its own acceptance passes.
- [ ] Preserve current preset/Unicode-manifest, emoji-free export, handpicked-Lottie and preview-cache contracts; read today's reaction sections before using old J4/J5 tasks. Old per-emoji generation/batch/menu descriptions and stale screenshots are not specifications for the new screen.
- [ ] Finish relevant documentation, count wording, inventory and reading-path corrections. Confirm dynamic/keyboard callers before retiring actions or CSS. Clear an item only after implementation, its narrow checks, required browser evidence and owning documentation are complete; record evidence in the execution record, then remove only that finished step from this next-work plan.

### Acceptance and execution boundaries

Keep shell/rail, approximately 90% of information architecture, stable JSON/routes/actions, engine authority, owner-only operations and visible reversible per-picture overrides. Use grouped cards/inset lists, consistent line icons and 150–250ms reduced-motion-aware feedback; translucent material only on bars/sheets. Product choices still unresolved in current docs remain pending; they do not block independent work or erase explicit requests above.

Use copied data/providers off and your own server, never owner port 8770. No paid calls or sends; guard Telegram mutations before opening its entry. DOM-first, focused browser evidence; no repeat full audit. One narrow test run per changed source area, zero tests for docs; no full discovery. Exact mechanical tasks: ≤2 files/150 total changed lines; bounded design/shared tasks: ≤6 files; ≤2 dependencies. Commit/push explicit owned paths only, with area docs; no merge/deployment or unrelated media changes.

### Separate proposal remains pending

[Size/Position, one-frame previews and Particular-style Lottie settings](docs/size-position-lottie-proposal.md) explicitly says **waiting for a go**, parts A–D separately. Keep it visible and unimplemented until approved; this visual-system plan does not approve its new sizing/position algorithms or retire its controls.
