# Main-agent brief for the redesign branch (2026-10-15)

What `main` finished, what this branch already has, and Haitham's locked decisions — so the redesign continues without re-asking or redoing.

## Branch map

```
origin/main @ 53f5a7f5 (stable, merged, handpicked-lottie deleted)
 │  5ad67e2d  no-dup removal + grey everywhere (imports part NOT for this branch)
 │  9194bfc5  tile sliders Size/X/Y + 47817ab6 docs (already integrated here as WIP)
 │  2743bd7f  bridge → d78d6605 3-tabs → 15da937d Library tabs → 09d62c8c docs
 │  53f5a7f5  HANDOFF merge note
 │
 └── origin/redesign-ui-ux @ 0b242630 (this checkout: G:/Haitham/VsCode/Mirsal-Builder-redesign)
      ├── already had: grey .zip thumbnails (a439eec4), slider integration WIP + tile_sliders.test.js
      ├── ported + pushed: 42a93282 reaction tabs, 0b242630 plan/handoff finalization
      └── still open: WIP commit, slider-timeout + tabs browser acceptance (below)
```

## Locked decisions (Haitham — do not relitigate)

1. **Imports: this branch keeps the duplicate-choice dialogs** (`again`, "Again into / As a new batch", explicit recovery). Main removed the whole check; that removal must never land here — a future merge keeps this branch's dialogs.
2. **Tile sliders collapse behind a toggle.** Tiles stay compact; an Adjust control (`ACT.vslopen`, aria-expanded) reveals Size/X/Y. Built 699a49a1, covered in tile_sliders.test.js.
3. **Two homes stay, with this logic.** `#/reactions` is the MAKE side (presets, editor, bank wall, Lottie files, batch create); Library › Reactions is the OWN side (finished sets, attach/detach, bank build states, made list). The shared tabs (`rx.tab`) flip perspective without losing place — the Packs tab on `#/reactions` answers "what have I made" read-only; management lives in the Library.
4. **Frame editor stays.** Sliders for quick edits; the floating card keeps grid/scrubber/Centre. No merge, no retirement.
5. **Verification order: main agent first.** Node + contract checks are done here (below); interactive browser acceptance stays open for a human or browser agent on the 8796 server (deliberately stopped; restart via `%TEMP%/mirsal-redesign-local-test/serve.ps1`).

## Verification done here (no browser available to this session)

- `tests/js/rxlib_bridge.test.js` (6) + neighbours (`reactions`, `particles`, `tile_sliders`): 61/61 green. `node --check` clean on all touched scripts. `test_ui_inventory`: green.
- The tab loaders call only pre-existing endpoints, each covered by existing suites: `GET /api/particles` (test_particle_sets), `/api/particles/bank` (test_particles), `/api/particles/emoji-lottie` (test_emoji_lottie), `/api/particles/lottie-reactions` (test_lottie_reactions). No backend changed.
- Full js suite on this branch: 10 failures, every one also failing on main (cell_op, home, lottiestyle:17, prompt_step ×7) — the port introduced none. Stale suite repair is this branch's lane, per Haitham.

## Still open on this branch (other agent's lane)

- Commit the slider WIP (explicit paths + `tile_sliders.test.js`), then the writer-lock slider-timeout acceptance.
- Tabs browser acceptance (both screens, both routes, dark/light, ≤760 px).
- Tile-slider toggle (decision 2) and any Packs/Library dedup the redesign wants — proposals only, no instruction to remove either home.
- Delete the dead `.worktrees/redesign-ui-ux` folder in the main repo once its holding terminal closes (unregistered already, files partly removed, one empty dir left).
