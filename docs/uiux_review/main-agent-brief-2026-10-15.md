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

- Full js suite on this branch: 388 pass, 0 fail (stale suite repaired: prompt_step cpGrid stub, cell_op ?v= cache-buster, home railcreate entry, lottiestyle Particular groups; size_preview rewritten for Resize + frame editor). `node --check` clean on all touched scripts. `test_ui_inventory`: green.
- The tab loaders call only pre-existing endpoints, each covered by existing suites: `GET /api/particles` (test_particle_sets), `/api/particles/bank` (test_particles), `/api/particles/emoji-lottie` (test_emoji_lottie), `/api/particles/lottie-reactions` (test_lottie_reactions). No backend changed.
- Tabs server-verified 2026-10-15 (temp 8797, redesign code): all four tab endpoints 200 with real data (9 sets, 1898 bank, 4 Lottie files), all four JS bundles 200; shell renders, no login wall on local routes.
- Slider busy-retry built (825f4dcc: `postBusy`, 12×1s, slider/frame-editor sends survive a running cut; same fix on main cdeae419). Adjust toggle built (699a49a1).

## Still open on this branch

- Interactive browser acceptance only (both screens, both routes, dark/light, ≤760 px) — needs a human or browser agent; no browser tooling in this session.
- UI/UX redesign backlog (plan.md items 4–9, journeys) — the visual redesign work, untouched.
