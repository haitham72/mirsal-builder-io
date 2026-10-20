# Studio: left creation panel — proposed plan

Requested by Haitham, 2026-10-19. **Built 2026-10-20 (steps 1-4 below; see "Implemented"); awaiting Haitham's visual review.**
Creation settings belong on the left; artwork and the active batch belong in the
main workspace. **New request stays open.** Retain Mirsal's cyan-blue accent.

## Reference and direction

Inspected the public [Higgsfield Video page](https://higgsfield.ai/ai/video)
without logging in or generating. At 1440px its creation form measured about
318px wide, with a separate workspace to the right. Page/form/control backgrounds
were approximately `#0f1113`, `#131517`, `#1c1e20`. These observations inform the
proposal; their lime brand, model defaults and billing behavior are not Mirsal's.

Use neutral charcoal depth, quiet borders, readable white/gray text and cyan
for the active view, focus and primary action. Avoid tinting the entire Chat or
Studio background cyan. Keep actual sticker, preview and issue colors unchanged.
Dark mode uses its own intentional palette; Light retains its current palette.

## Desktop layout

```text
┌──────────┬──────────────────────────────────────────────────────────┐
│ App rail │ Create: Chat | Studio                     Theme / Account│
│          ├───────────────────┬──────────────────────────────────────┤
│ Home     │ New request       │ Project / Batch / Version   Batches  │
│ Create   │ (always visible)  ├──────────────────────────────────────┤
│ Library  │                   │ Prompt → Stills → Motion → Pack      │
│ Help     │ References        │ View: Stickers | Sheet | Both        │
│          │ Prompt            │                                      │
│          │ Image/video model │ Active sheet / individual items      │
│          │ Style             │                                      │
│          │ Grid / options    │ Per-item decisions and adjustments   │
│          │ Prompt engine     │                                      │
│          │                   │                                      │
│          │ Existing creation │ Existing stage action / progress     │
│          │ action + price    │                                      │
└──────────┴───────────────────┴──────────────────────────────────────┘
```

- Keep the existing 96px desktop app rail. Replace Studio's permanent second
  column with a creation panel: **352px preferred, 320–384px bounded**. Do not
  add another always-open project/history column beside it.
- Keep Chat/Studio navigation and global theme controls in the shared shell.
  The main workspace gets the remaining width; independently scroll the left
  settings and right artwork regions.
- Keep the prompt/creation action accessible at the bottom of the left panel
  while its settings scroll. Account for price, busy/error messages and viewport
  height; no button may cover settings or artwork.
- Use the existing sticker inspector as a bounded overlay when editing.
  Do not permanently squeeze the artwork into a fourth narrow column.

## Left panel: move the existing composer, once

Order: **New request → references → prompt → model → style → options → prompt
engine → existing creation action**. Show image/video model context clearly;
use only controls that the backend already reads.

The outer New request section cannot collapse, including when reopening a batch.
Options and Prompt engine can retain their internal disclosures. Grid starts at
2×2 for new plans; explicit 3×3 and imported/existing grids remain untouched.

Reuse one composer mount and the same setting state/handlers, not a second form
with duplicate IDs. Preserve draft text, reference files, model/style selections,
AI settings, import choices and stage behavior across redraws and navigation.
Do not reinterpret typing into New request as editing the selected old batch.

Preserve the free Generate prompt step and its separate priced generation step.
Do not collapse them into a paid Generate action or invent a price. Existing
price acceptance, insufficient-credit, unavailable-provider and busy states stay.
Left creation and right review/pack actions have distinct purposes; do not
duplicate a given mutation button in both places.

## Main workspace: keep the controls discoverable

- Project/batch/version identity and a labelled **Batches** entry stay at the
  top. Open the existing project/history data in an accessible drawer/popover;
  retain grouping, version switching and previous/next navigation.
- Keep the journey and **Stickers | Sheet | Both** directly above the artwork,
  with a clear selected state. Keep the user's remembered view choice.
- In Sheet view, offer a short contextual link to Stickers for individual
  editing; never imply that the per-item controls were removed.
- Individual still/video items retain their identity, review reason and
  reversible decisions: Use it anyway / Take it back / Bring back as applicable.
  Size, Position, Reset, frame editing, text/emoji edits and existing tools stay
  reachable. Keep the frame editor's Apply/Cancel and Resize contracts.
- Existing sheet tools, prompt edits, regeneration, versioning, imports, exports
  and pack actions retain their handlers and approval boundaries.

## Narrow screens

At 1024px, try a 320px creation panel with at least roughly 600px of workspace;
verify actual control bounds. Below the point where both fit, show the workspace
full width and expose **Creation settings** as a labelled drawer/bottom sheet.
The drawer contains the same always-open New request section and preserves its
values when closed. This is a responsive container, not a collapsed composer.

At ≤760px, retain the app's existing phone navigation. Allow one major side
surface at a time (creation settings, batches, or item inspector), with clear
focus entry, Escape/Close, return to its launcher and unsaved-state preservation.
Exact breakpoints follow measured bounds, not a device-name guess.

## Bounded implementation order

1. Add the Studio shell regions and a single composer mount target; preserve
   the existing layout on other routes. Add a failing mount/state regression.
2. Move project/history presentation into the workspace entry/drawer, retaining
   current data and handlers. Verify that earlier work remains obvious/reachable.
3. Move creation fields and action into the left panel; preserve free/priced
   stages, imports and draft state. Verify busy/disabled/error cases with fakes.
4. Add phone drawer and keyboard/focus behavior. Keep per-item controls and view
   switches visible/operable; independently fix the already-audited phone editor
   layout rather than assuming the sidebar solves it.
5. Review dark/light screenshots, reconcile action/route inventories and remove
   each implemented tracker entry only with its evidence and area docs.

## Acceptance before calling the layout done

- 1440 / 1024 / 760 / 390px, both themes: correct regions, scroll, contrast,
  keyboard focus and no clipped artwork/controls.
- New and reopened batches: New request visible, drafts retained; switching
  project/batch/version or navigating away/back loses no state.
- Imported 2×2/3×3, generated video-sheet fixtures, Still/Animation and each
  Stickers/Sheet/Both view: individual tools and reversible decisions preserved.
- Free prompt / quoted paid step / offline provider / busy / error / cancel:
  no extra mutation or spend, no silently accepted price.
- Native clicks and keyboard activation, not forced clicks; copied/sanitized
  data, disabled providers, narrow fake failing→passing regressions.
- Preserve route/action inventory, engine authority, import duplicate/router
  consent, Resize and separate Emoji/Lottie export contracts.

## Implemented (2026-10-20)

- On `#/studio` the second column is the creation panel (`body.studio-split`, `--col2-w` 352px, 320px under 1180px). The one New request composer (`#cpwrap`) is moved into `#c2create` (`composer.js` `studioCol`, `cpHost`); leaving the Studio keeps the node (`cpStash` / `CPKEEP`), so draft text, references and open disclosures return unchanged. `RENDER.generate` skips the legacy prompt row when the composer exists, so `#prompt` is unique.
- The workspace starts with a top bar: **Batches** (always) and **Creation settings** (900px and narrower, opening the existing second-column drawer, whose `#c2tog` is labelled the same on the Studio). Using a setting inside the composer no longer closes that drawer; Generate does.
- Earlier batches and the open project's map (`projmap.js`) draw into the **Batches** drawer `#bdrawer` (`live.js` `histHost`, `ACT.bdopen`, `bdClose`): non-modal, focus moves to its first control, Escape or Close returns focus to the Batches button, opening a batch (`hopen`, `pmopen`) closes it, and the breadcrumb's project link opens it on the project list. Create (`#/create`) keeps the list in its column.
- Measured on a copied workspace: panel 352/320px at 1440/1024 with the workspace beside it; drawers at 760/390; no horizontal scroll.
- Completion pass (2026-10-20): the composer has a scrolling `.cp-scroll` and separate `.cp-footer`; Generate prompt, its existing price label, draft return and import actions remain reachable below the settings. `cpDrawBar` moves the one action group into the footer after each redraw.
- `tests/js/studio_panel.test.js` covers retaining the composer node and draft, drawer visibility/expanded state, focus restoration after replacing the launcher, and Studio/Create history routing. This file plus `composer_visibility.test.js`: 4 tests passed.
- Browser check on isolated port 8796 with providers disabled: 1440/1024/760/390 at 720px height, light and dark. No horizontal overflow or duplicate prompt/Generate IDs; footer stays above the viewport/mobile rail and below the settings. Native Creative/Predefined clicks worked in all eight layouts; the reported empty pill could not be reproduced with Options open. Draft survives Library and back; drawer Escape restores launcher focus. Local screenshots: `output/playwright/studio-{light,dark}-{width}.png`. This was an empty workspace check, not acceptance of loaded artwork or paid states; final visual approval remains pending.

No new framework, engine redesign, paid run, send, deployment or branch merge
belongs to this layout phase. Final visual approval remains Haitham's.
