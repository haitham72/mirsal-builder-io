# UI/UX plan review against the current implementation (2026-10-15)

Branch `handpicked-lottie` @ `a993b4a2`. Historical audit: `170f26e`; revalidation (2026-10-14, `revalidation.md`) predates the repair batch below, the Size/Position redesign and Lottie style's Particular settings. Source only; no browser run in this pass, no app source changed.

## Verdict

The plan is **sound in direction but stale in its starting point**. About 9 of its 87 tasks are already implemented (only browser acceptance is outstanding), one is superseded, and the reaction tasks (J4/J5) describe screens that no longer exist. The **visual redesign itself (tokens, hierarchy, grouped cards, 44 px targets, consistent menus and segments) has not started**. It is still the main remaining work and should not be cut down to bug fixes. The nine original reaction/pack items in `plan.md` are all **still open**: none is implemented, and none was retired by Haitham.

## Requirement / finding → current implementation → remaining

| ref | requirement / finding | current implementation (evidence) | remaining |
|---|---|---|---|
| T-001 / F-01 | staged Keep approved size | **superseded** (f3b9ef52): `gkeepsize` and Keep approved size are gone. The batch row is `[✓] Resize · Size`, and each sticker has a one-frame editor (`vzCard`, `ACT.gresize`, `ACT.vzedit`) | rewrite `tests/js/size_preview.test.js` (it still tests `gkeepsize`, so it now fails); browser acceptance |
| T-002 / F-06 | retime dialog cancellation | implemented, in HEAD (902a917b): `dlg(...,{onDismiss})`, `dlgForget`, settle-once `retimeAsk` | browser acceptance |
| T-003, T-004 / F-05 | queue clock, Studio polling | implemented (902a917b): `data-lvt` single interval, `tickBusy`/`tickForce` | browser acceptance; T-005+ watcher migration still open |
| T-065 / F-24 | badge over Timeline | implemented (84718cd3): `.badge2{pointer-events:none}` | browser acceptance (real hit test) |
| T-086 / F-36 | phone viewer | implemented (84718cd3): ≤760 px grid, `100dvh - 24px` | phone acceptance |
| T-074 / F-30 | welcome contrast, targets | implemented (84718cd3): `--wl-ink`, 44 px dots | dark-theme acceptance |
| T-072 / F-26, F-27 | Settings navigation | implemented (84718cd3): `SET_SECTIONS` registry | acceptance (local Account, Tickets) |
| T-073 / F-28 | Help keyboard | implemented (84718cd3): `button.crow` | keyboard acceptance |
| T-012, T-033 / F-02, F-09 | size test card, size preview lifecycle | changed: the card is now the frame editor (one-frame PNG, drag, grid, scrubber), still separate from `egCard` | revise scope: share the presentation with `egCard`, keep the different endpoints |
| T-007, 018, 025, 031, 034, 035, 047, 070 / F-04, F-07–F-09, F-25 | reaction-screen tasks | the screen now has two styles. Emoji style: the preset library, `{motion}_{NN}` emoji-free exports, assignments, handpicked origin/morph. Lottie style: thumbnails, Particular groups as `<details>`, presets, morph targets, Aux, time sampling | re-scope against `docs/reaction/15-17`; no per-emoji generation, batch or menu work |
| T-024, 030, 036, 071 / F-25 | saved-set editor (particles.js) | unchanged: two `fx-adv`, inline Dup/Rename/Delete | **merge with plan items 1, 2, 4** (one implementation, both references) |
| T-056 / F-19 | semantic tokens | not started (290 literal styles, per revalidation) | first visual task |
| T-066 / F-22 | 44 px targets | not started globally; only the welcome and Help fixes have them | after T-056 |
| T-068, T-069 / F-32, F-22 | Studio grouping and primary action (J1 reference) | not started; the batch row is now simpler (Resize + Size) | do as the J1 visual reference |
| F-29 / T-077 | totals count reactions as stickers | not started | open |
| plan 1 | set card: counts on hover, ⋯ menu | not implemented (`spSetCard` shows counts and cost always; Dup/Rename/Delete inline) | open, merged with T-071 |
| plan 2 | "Manage stickers" disclosure | not implemented | open, merged with T-071 |
| plan 3 | motion presets: selected + Change | the Emoji-style library has collapsed motion rows (F-25 partial); the burst editor's chips are unchanged | open for the burst editor |
| plan 4 | one Advanced section | not implemented (two `fx-adv` in particles.js) | open, merged with T-071 |
| plan 5 | burst row without the preset name | not implemented (`pkBurst` still prints `b.preset`) | open |
| plan 6 | pack view without tabs | not implemented (`PKTAB` / `pktab` still exist) | open; Haitham's explicit request; retirement entry in `ui_baseline.json` |
| plan 7 | "Open in Studio" on Library pack cards | not on Library cards (only inside the pack view and the viewer) | open |
| plan 8 | "Open and save" on a set card | not implemented | open |
| plan 9 | erosion in the reaction Timeline | not implemented (no `erosion_px`) | open (engine + slider, rule 6) |

## Corrections to outdated assumptions

- **Size/Position is built, not "only proposed".** A–D of `docs/size-position-lottie-proposal.md` are implemented and covered by narrow tests (`HotSpotTests`, the live slicing test, `ParticularTests`). Still open: browser acceptance, the rewritten JS test, and Haitham's confirmation of the Resize meaning. D's Pre-run, Time scale, silhouette emitter and blend modes are not built and wait for a go.
- **Reaction export contracts differ.** Emoji style exports an emoji-free preset Lottie (one external `emoji` asset, no base64). A Lottie-style composition is self-contained: it embeds every source file, and the sources keep their own assets. A redesign may share controls between them, but never the export rule.
- **Lottie style already uses progressive disclosure**: `<details>` groups with a summary of what changed, kept open per browser. Shared range/segment helpers (T-024/T-025) must cover its drop-downs (choice settings) and must not flatten the groups.
- **Revalidation's "still present"** for F-01, F-05, F-06, F-24, F-26–F-28, F-30 and F-36 is historical, because the repairs landed afterwards.

## Remaining visual-redesign gaps

Not delivered: semantic tokens (spacing, type roles, status pairs, radii, elevation, focus, motion); global 44 px targets; one Studio reference journey with a clear primary action and grouped cards; consistent menus, segments and responsive sheets across Library, Pack, Chat, Settings and the export dialogs; reduced-motion-aware feedback. Partly delivered: progressive disclosure (Lottie groups, collapsed motion rows, the frame editor) and the phone viewer. The information architecture is intact (well above the 90% target). The file and line budgets in `uiux_plan.md` (≤2 files / 150 lines) fit mechanical tasks only; the token and journey tasks need the ≤6-file bound.

## Browser acceptance (own server, copied `out/`, providers off, never port 8770)

1. Resize box and frame editor, on a video-sheet batch and on an imported 3×3 video: drag, arrows, Centre, Grid, scrubber, Apply; both themes; ≤760 px.
2. Lottie style: groups, presets, Re-roll, loop and random-still playback in lottie-web.
3. Re-import: the duplicate dialog, "Again into G###" and "As a new batch".
4. Repair batch: retime Esc and backdrop; queue clock; badge vs Timeline click; phone viewer; welcome in dark; Settings → Tickets and local Account; Help with the keyboard.

## Sequence

1. Rewrite `size_preview.test.js`; fix the two stale `test_particle_set` tests.
2. Browser acceptance 1–4 above; reopen only a reproduced failure.
3. T-056 tokens → T-066 targets.
4. J1 Studio as the visual reference (T-068/T-069).
5. Plan items 1, 2, 4 with T-071 (saved-set card), then items 5, 6 and 7, then 8 and 9.
6. The other journeys (J2, J3, J6–J9) through the same system, with J10/J11 acceptance for each; reaction tasks only after re-scoping against `reaction/15-17`.

## Decisions for Haitham

1. ~~Resize meaning~~: **approved by Haitham 2026-10-15** as built (off = one uniform scale, on = hot spot matched to the approved still; old modes stay off the screen).
2. Plan item 6 (no pack tabs) against the audit's question about tabs: the item stands unless you withdraw it.
3. Reaction wording: "Reaction effects" is used for two workflows (F-31): Home's link goes to `#/effects`, + New goes to `#/reactions`.
4. Cloud pricing copy (unchanged from `uiux_plan.md`, Questions).
