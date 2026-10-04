# Entire sticker → particles flow

Revised design, 2026-10-04, incorporating Haitham’s correction: simplify the entire screen and preserve the full animated-sprite pipeline. This document describes the target; it does not mark unfinished code as complete.

## One editor

Open **Particles** from a sticker. Its thumbnail and name establish the target automatically. A batch entry selects that batch’s stickers only; pack entry selects that pack’s stickers. Library entry asks for the target first. A batch outside the library offers **Approve as a pack** and returns directly to the editor. Keep Back available.

Every saved pass is one row under the sticker (v1, v2...). Entering Particles always starts a **new version**; a saved row is reopened only with its **Open**. Inside an open set, **Add more** appends cells. Add more always exposes all creation choices, regardless of the existing set’s original source. No automatic reopening of an unrelated old effect run.

## Choose sprites

Two top-level cards, retaining the ownership rework’s decision:

| Card | Choices and primary action |
| --- | --- |
| **Sprites from the sticker** · free | Select sticker/sheet slices or library artwork; **Use selected · free** |
| **AI image sprites** | particle prompt; **2×2** / **3×3**; actual price; **Generate** |
| **Kling animated · from scratch** | particle prompt; **2×2** / **3×3**; actual price; **Generate** |

All three cards are equal and visible for every new version; both AI choices also stay in Add more. Default to 2×2; show a short relevant warning for the measured 3×3 issue. Keep provider options, key colour and other technical settings under **Advanced**. Quote first, paid click second; unavailable quote gets **Retry price** and starts nothing.

## The animated path, clarified by Haitham

**Prompt → Kling 2×2 or 3×3 animated sheet → slice → animated sprites in the particle simulator → render → add to the same pack.**

1. Generate a text-only animated sheet from the particle prompt, with the existing nothing-to-nothing Kling pipeline. Show its actual quote before starting.
2. Track the job and show progress. Reloading resumes the same job; it does not pay again. A failed paid job needs a new quote/click before retry.
3. Key and slice the sheet into animated sprite clips. Keep the clips, transparency, timing, job, cost and provenance. Show looping video tiles for selection.
4. Feed each selected clip’s frame sequence into the simulator. Each particle plays its own sprite animation as it moves, spins, scales and fades. A peak PNG is only a poster/fallback, never the sole simulation input for a valid animated clip.
5. Preview the composed animation, tune motion, render the final Telegram-compatible WebM and **Add to pack**. The selected sticker’s parent pack is the default destination. Adding affirms the set there.

Image sprites enter the same simulator as still frames. Existing animated stickers retain animation when reused or recovered. Sets may contain both still and animated sprites. The original clip-add route remains available as a secondary compatibility action; it does not replace this simulator pipeline.

## Compact simulator

One selectable sprite strip, one preview, presets, and **Energy / Float / Swirl / Size**. Put count, spin, sprite resolution and technical controls under **Advanced**. Then **Save** makes the draft the next row, or on a saved row replaces its motion and sizing; **Save as new** saves the same sprites with the edited motion as another row and leaves the first unchanged; **Assign to stickers → Test in chat** tests the branch as the Echo reply/reaction on that sticker. **Render → Add to pack → In pack ✓** remains the export path.

Save imported/generated cells in their scoped set through the engine. Remove the extra naming/“Use as particle set” modal from the normal flow; rename is secondary. No permanent explanations about ownership, saving, the ledger or what Telegram plays. Visible text is limited to labels, actual prices, progress/status and warnings attached to the affected media. Warn with **Use it anyway**; only Telegram technical failures remain final, with a reason and next action.

## Recovery from a mistaken sticker pack

Inside a sticker: **Use as particle pack → This sticker / All N stickers → Parent pack and target stickers → Use selected · free**. Open the same simulator afterward. Default source selection is the clicked sticker; selecting all is explicit.

Copy still/animated media into the target set; retain source IDs, original files and the source pack. Parent stickers own the particles; the source artwork does not acquire ownership merely by supplying media. Append to their common current set by default, with **New set** secondary. Recovery never spends or deletes originals.

## Ownership and persistence

Particles live in library stickers, never in a pack. Selected sticker groups may share a set; packs display their stickers’ union. Reuse copies a link, free. Add more appends cells without changing existing bytes or replacing the set. Delete stays soft and Restore stays reachable; parent-pack purge detaches links and retains the set visibly.

One flow context holds target sticker IDs, source choice, target set and explicitly continued job. Async replies carry an entry token so old reads cannot overwrite a newer target or New set. Provider completion/import is idempotent. A sticker with a set cannot show “never created”. Source kind, job and credits remain accessible as compact metadata.

## Build and acceptance

Engine plus additive JSON contract first, screen second. Preserve old effects/assign routes as documented aliases for one release. Finish animated-frame loading, deterministic simulation and preview/render support before advertising animated sprites. Do not stop at retaining clips beside static posters.

Acceptance first follows already-created sheets/clips copied to scratch out. Trace stored effect/job/generation paths, diagnose why a run is stuck, and use free recut/import/recovery through the actual simulator, Render and Add. Do not launch fresh generation for acceptance. Keep synthetic temporal checks to prove deterministic frame playback.

Required cases (each is checked **once**, in one browser walk-through at the end, plus a unit test only where new engine code was written; a case already shown passing is not re-checked — `docs/testing.md`, the test budget):

- Follow a stored Kling prompt/job/clip through key/slice, animated sprite selection, temporal simulator preview, Render and Add in scratch Chromium. Separately verify quote/go gating with fakes; spend nothing.
- Demonstrate animation changing over time inside individual flying particles; include a mixed still/animated set and confirm static behavior remains deterministic.
- Reopen an image-origin or recovered set and generate animated sprites into that same set; reverse the source choice as well.
- Repeat Add more without overwriting existing cells; resume a job without duplicate billing/import.
- Save edited motion/size, branch without changing the original, assign the branch to another sticker, then send it to Echo and verify that sticker’s current set plays on reply/reaction. Replay must re-read assignment; unassigned stickers never use unrelated particles.
- Scope approval/recovery to the chosen targets, reject stale replies, preserve original recovery media and show affirmation after Add.
- Exercise warnings/override, technical failure reason, soft delete/restore and parent purge retention.

Use fakes, temporary libraries and scratch Chromium on a spare port; do not re-run passed suites between cases. Never use real out or paid providers in tests, or the retired slow/full-discover gates. A fixture injected directly into a Render panel is not evidence that the complete video pipeline works. FastAPI follows particles as previously authorized; it is separate from this flow.
