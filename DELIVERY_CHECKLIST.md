# App and API delivery acceptance checklist

**Goal:** user entry -> default 2x2 image sheet -> video sheet using the new guidance prompt and Higgsfield Kling 4.0 -> approved pack -> delivery to the final API -> confirmed success.

This is the single checklist for app review and final API delivery. These are acceptance targets, not claims that the features are implemented or tested. Check a parent topic only when its applicable child checks pass. Final Lottie asset checks stay deferred until the files are supplied.

## Review setup and evidence

- Review existing history/library at **http://127.0.0.1:8770/**. Use a disposable copy for changes; ports 8797/8798 are test copies. Automation must use a test copy.
- Repeat layout checks on desktop and at phone width, in **Light and Dark**.
- Stop at a shown price. Paid generation and external sends require approval for the specific run.
- Record each result as **Pass / Issue / Not checked / Deferred**; check a box only for Pass. An unchecked item is not accepted.
- Record **build/commit + environment + screen/API route + action + expected/actual + theme/width + pack/batch/job/export IDs + screenshot or sanitized request/response evidence**, as applicable. Omit credentials.
- Record wording, pricing and visual verdicts explicitly. Review Telegram delivery separately when requested; the final delivery gate here is the collection API.

References: [final API contract](docs/API/API_DOCUMENTATION.md), [Mirsal API integration](docs/api-integration.md), [generation](docs/generation.md), [known defects and engineering limits](docs/backlog.md), [owner decisions](docs/waiting-for-haitham.md). Past audits live in git history.

Latest verification: [2026-10-23 smoke-test results](#smoke-test-results-2026-10-23). Checked boxes below apply to that smoke scope; broader scenarios remain open.

## Acceptance checklist

- [ ] **1. Network works with new users — very low priority**
  - [ ] A new user can reach the app and API from another device on the intended network.
  - [ ] Registration, account approval and sign-in work for a fresh account.
  - [ ] The approved user can start a creation request; access errors give a useful message.

- [ ] **2. User entry -> image sheet -> video sheet -> approve pack — core flow**
  - [ ] User entry
    - [ ] Submit a user request and receive a request/job ID through the API.
    - [ ] The request and its progress remain available after refresh or reconnect.
    - [ ] Chat <-> Studio and New work as expected; photo/video imports retain the intended input.
    - [ ] Explicit 3x3 and duplicate Open existing / Import again choices work while fresh requests keep the 2x2 default.
  - [ ] Default image sheet
    - [ ] A fresh request defaults to a **2x2 sheet: four stickers**.
    - [ ] The API request, saved plan and generated sheet agree on the 2x2 layout.
    - [ ] Review the sheet and approve the intended stickers; saved approvals survive refresh.
  - [ ] Video sheet and generation
    - [ ] Build the video input sheet from the approved stickers, preserving their order and IDs.
    - [ ] Use the **new guidance video prompt**; record its template/version and the exact prompt sent.
    - [ ] Default to **Kling 4.0 through Higgsfield**; verify the actual provider/model ID in the submitted job.
    - [ ] Confirm the prompt and video input sheet reach the provider together; no silent fallback to an older prompt or model.
    - [ ] The returned video is processed into the corresponding animations, with each animation mapped to its original sticker.
    - [ ] A failed generation reports its error and can resume or retry without losing approved work or duplicating a paid job.
  - [ ] Review decisions and editing
    - [ ] Prompt -> Stills -> Motion -> Pack, versions and sheet/sticker views are understandable.
    - [ ] Rejected pictures show the reason, Use it anyway and Take it back; technical limits are explained.
    - [ ] Size/position/reset, the frame editor, image tools, text/layers and animation/trim work without clipping on desktop and phone.
    - [ ] Save persists the intended edit; Cancel preserves the original.
  - [ ] Approve pack
    - [ ] Review the final animations and save the pack approval through the API.
    - [ ] The saved pack contains exactly the selected assets, emoji tags and metadata.
    - [ ] Delivery uses the approved pack version; rejected or unapproved assets are excluded.

- [ ] **3. Create default reactions — simulator emoji default**
  - [ ] A new reaction defaults to the **simulator with emoji**.
  - [ ] Create and preview a reaction with the default settings and selected emoji.
  - [ ] Save, reload and reproduce the reaction from its API data.
  - [ ] Attach the reaction to the intended pack/sticker without changing its emoji association.
  - [ ] Both reaction entry points open the same intended editor; ownership, edit and save-as-new match the saved version.
  - [ ] Export the reaction in the format accepted by the final API, with matching metadata.

- [ ] **4. Create normal reactions using Lottie files**
  - [ ] The normal-reaction flow supports a supplied Lottie JSON file.
  - [ ] Preview, save and reload the reaction while retaining its file and emoji/sticker association.
  - [ ] Invalid or missing files produce a useful error and preserve the saved work.
  - [ ] Export includes the intended JSON files and their matching metadata.
  - [ ] **Deferred: final Lottie files will be supplied later.** Once supplied:
    - [ ] Replace the temporary/sample files with the final Lottie assets.
    - [ ] Repeat preview, save/reload and final API delivery checks with those assets.

- [ ] **5. Price is implemented through to the final API**
  - [ ] Complete the [pricing fields and implementation plan](#pricing-fields-and-implementation-plan).
  - [ ] Collection price
    - [x] Set and save a pack price; reloading the pack preserves it.
    - [ ] Confirm the agreed currency, allowed values and free/omitted-price behavior.
    - [x] Invalid values return a useful validation error.
    - [x] The delivery preview and API request use the saved, approved price.
  - [ ] Final API contract: `POST /api/v1/Upload/AddCollection`
    - [x] Use Bearer authentication and `multipart/form-data` as specified in [docs/API](docs/API/API_DOCUMENTATION.md).
    - [x] Enforce a 40-character collection name and 160-character description; longer values fail before queuing.
    - [ ] Send `CollectionName`, `Description`, `ContentType`, `ContentSubType`, `Media` and `MediaMetadata`.
    - [ ] Send **`Price` as a string** and verify the receiving API stores the intended value.
    - [x] Uploaded filenames include extensions and use the correct MIME types.
    - [x] `MediaMetadata` is a JSON string; its count and order match `Media`, including each asset's `emoji_utf` and `tags`.
    - [ ] Verify accepted content type/subtype values for sticker packs, simulator reactions and Lottie reactions.
  - [ ] Generation cost
    - [ ] Show and accept the generation cost before paid provider calls.
    - [ ] Keep generation credits separate from the collection price sent to the final API.

- [ ] **6. One-click create pack -> expand packs in batches seamlessly**
  - [ ] One Create pack action starts the default flow from the user's request, carrying it through the required pricing and review steps.
  - [ ] Completion creates one pack from the approved selection and returns its pack ID.
  - [ ] Double-clicking or retrying the same operation does not create duplicate packs or assets.
  - [ ] Expand that pack with another batch without re-entering the original request.
  - [ ] Expansion preserves the subject/style and uses new actions rather than repeating existing stickers.
  - [ ] New batches retain the 2x2 default and join the same pack after approval.
  - [ ] Progress identifies each batch; partial failure allows retrying the failed batch while preserving successful batches.
  - [ ] Existing approvals, reactions, metadata and price survive expansion.
  - [ ] Deliver the expanded approved pack; verify the final API receives the complete intended asset list once.

- [ ] **7. Success from the API — final delivery gate**
  - [x] Start delivery and retain the export/job ID while it is queued or sending.
  - [ ] Show success only after the final API confirms the intended assets were delivered; compare inserted/updated counts with the sent count. `Success: true` with zero inserted/updated is insufficient; queued/processing is still pending.
  - [ ] A successful response includes the collection details; retain the returned collection ID/reference when provided.
  - [ ] Where the response uses `Success`, `Result` and `ErrorMessages`, treat `Success: false` as failure even with HTTP 200.
  - [x] Display the API success message, or a clear confirmation based on its accepted response, linked to the correct pack/export.
  - [ ] Verify the received collection's assets, metadata, reactions and price against the approved pack.
  - [ ] Authentication, validation and server errors show the API's useful error message.
  - [ ] A timeout remains pending or unconfirmed until the outcome is checked; retry does not silently duplicate a collection.
  - [x] Save a delivery record with the pack/version, export ID, timestamp, final status and sanitized API response.

- [ ] **8. App review across the supporting screens**
  - [ ] Home / welcome
    - [ ] Counts, artwork, film and wording look right; the theme switch and navigation make sense.
  - [ ] Find old work
    - [ ] Reopen a saved Chat, earlier Studio batch and Library pack; refresh and navigate away/back without losing them.
  - [ ] Chat
    - [ ] Conversation, stage/options, selection and plan/price are understandable; long history scrolls normally.
  - [ ] Library
    - [x] The two latest existing packs open, decode their animated media and download ZIPs with valid manifest hashes, on desktop and phone in both themes.
    - [ ] Search, pack/sticker preview, selection, move and download work as expected.
    - [ ] Trash/restore is understandable and preserves the intended assets and associations.
  - [ ] Reaction navigation
    - [ ] Emoji style / Lottie style / Packs tabs open correctly; previews match the selected saved version.
  - [ ] Settings / people / help
    - [ ] Options, health, accounts, Trending, support and FAQ review are clear for the intended role.
  - [ ] Every screen
    - [ ] Phone scrolling, labels, contrast, hover, keyboard Tab/Enter/Escape and menus are usable.
    - [ ] Loading, empty/error states and recovery are clear, including loaded artwork and busy states.

- [ ] **9. Super-like reactions (super reactions)**
  - [x] Load the saved `like button.json` version `V001`.
  - [x] Hold and release the reaction; it plays in the desktop chat area and on the phone screen.
  - [x] Export the saved version for all eight screen buckets; phone and desktop JSON have valid references and the intended aspect ratios.
  - [ ] Deliver the super-like assets to the final API and verify the inserted asset count.
  - [ ] Confirm the final API/client representation of a super-like: `super_like` is rejected as `ContentType`; only `emoji` and `emoji_reaction` are accepted.
  - [ ] Verify stored name, price and super-like metadata after delivery.

## Pricing fields and implementation plan

**Status: implemented for saved pack prices, pack/batch exports and chat export; verified with a local receiver and browser.** Live CMS stored-price readback and JSON reaction-collection integration remain open. New batches retain the pack's saved price. Generation credits remain a separate cost.

### Fields

| Location | Field | Type and behavior |
|---|---|---|
| Saved pack; pack create/update/read APIs | `price` | Decimal string or `null`, for example `"2"`, `"2.50"` or `"0"`. Existing packs remain unset until a person sets a price. Omitted update fields leave the saved price unchanged; explicit `null` clears it. |
| Future saved reaction/super-like collection or export draft | `price` | Deferred until those collection exports are connected. Reuse the collection-price contract without putting prices on reusable motion presets or screen-size variants. |
| Pack and batch export requests (`CollectionExport`) | `price` | Optional nullable decimal string. Omitted = inherit the saved collection price; explicit string = override for this export; explicit `null` = omit the price for this export. Batch export can supply a price even without a pack. |
| Queued export, outcome and delivery record | `price` | Snapshot the resolved price when queuing. Show the exact price sent; later edits to the source collection must not change an in-flight export. |
| Final CMS multipart request | `Price` | Send the resolved value as a string. Send `"0"` for an explicitly free collection; omit the field when the resolved price is unset. Preserve the distinction between zero and unset. |

**Contract decisions to settle:** confirm the CMS currency, maximum value and allowed decimal precision, and confirm how the receiver handles an omitted price versus `"0"`. The supplied API contract has no currency field. Currency is therefore left unspecified; add a currency payload field only if the receiving contract supports it. Normalization uses exact strings without floating-point conversion. Existing packs are not assigned a price automatically.

### Implementation order

- [x] **1. Shared validation and normalization**
  - [x] Define one validator for saved prices and export overrides; accept finite, non-negative decimal strings and normalize them without binary floating-point conversion.
  - [x] Reject malformed text, negative values, booleans, NaN/infinity and unsupported separators/exponents. Return a useful HTTP 400 before queuing or uploading. Monetary bounds await the receiving contract.
- [ ] **2. Persist the source price**
  - [x] Add `price` to pack create/update/read and library responses; save it with pack metadata.
  - [x] Preserve it after reload, rename, adding stickers/batches and trash/restore. Do not infer a price from generation spend.
  - [ ] Define the same saved field for reaction and super-like collection metadata when those collection exports are connected.
- [x] **3. Extend the API contract on both servers**
  - [x] Add `price` to `CollectionExport`, native routes, stdlib handlers, `/api/v1/` aliases and the OpenAPI inventory.
  - [x] Apply the same omitted/inherited, explicit override, zero and explicit-null behavior on pack/batch export requests; chat export uses the saved price.
- [x] **4. Add usable price inputs**
  - [x] Add a labelled price input to pack metadata editing and the export dialog; prefill the export price from the saved collection.
  - [x] Make saving the collection price and overriding it for one export clear. Show free/unset states and validation errors; retain entered values after a failed request. Currency stays unspecified until confirmed.
  - [x] Provide labelled, focusable controls and verify dialog/input/Save visibility at desktop and phone widths in both themes. Each control has a backend that reads and validates its value.
- [ ] **5. Carry the price through delivery**
  - [x] Resolve and snapshot the price before enqueueing; pass it through the worker and multipart builder as `Price`.
  - [x] Include the resolved/sent price in export state and sanitized delivery records so the outgoing value is reviewable.
  - [ ] Reuse this contract for simulator/Lottie/super-like collections once their JSON delivery issue is resolved; keep their collection names and ordered media metadata alongside the price.
- [x] **6. Verify with a fake receiving API**
  - [x] Prove persistence and exact multipart `Price` values for paid, free and unset cases on both servers and route aliases.
  - [x] Cover inheritance, one-export overrides, explicit clearing and invalid-value rejection before any upload.
  - [x] Verify that changing the saved price after queuing does not change the queued price. Use focused collection/library checks with providers disabled.
- [ ] **7. Verify actual stored pricing**
  - [ ] Use an existing pack for a live check, with its selected price shown, and compare the receiving CMS's stored name and price with the queued request.
  - [ ] Repeat for reaction and super-like collections after their asset delivery works. A success flag or inserted count without stored-price evidence does not close pricing acceptance.

Implementation areas: `runtime/pricing.py` (shared validation), `media/library.py` (saved pack metadata), `api/schemas/collection.py`, `api/routers/collection.py`, `console/server.py`, `api/openapi.py`, `services/collection.py` (request, queue and multipart), `agent/tools.py` (chat export), and `console/ui/features/library/packs.js` (price controls).

## Pricing verification: 2026-10-23

Verified the working tree using existing pack `2d6bc270` copied to a disposable output folder and a localhost CMS receiver. No image/video generation or external CMS submissions were run for this implementation.

- Collection/OpenAPI selection: **24 tests passed**; the added chat-export check passed separately. After correcting the OpenAPI price pattern, all **5 schema/type checks passed** again.
- Both API servers and `/api/v1/` aliases preserve saved prices, accept export overrides, distinguish free from unset, reject invalid values before upload and retain the queued price if the pack is repriced during preparation.
- Browser: saved `2.5000` reloaded as `2.5`; invalid `-1` stayed visible with its error and did not change storage. Export prices `3.7500`, `0` and blank reached the local receiver as `"3.75"`, `"0"` and an omitted `Price`, while the saved pack price stayed `2.5`.
- Saved free/unset display and clearing passed. Dialog, input and Save control fit inside 1440 px and 390 px viewports in both themes, with no page errors.

Evidence: [browser results](output/playwright/pricing-20261023/browser-results.json), [actual multipart fields at the local receiver](output/playwright/pricing-20261023/received.json), [dialog bounds](output/playwright/pricing-20261023/layout-results.json), [phone screenshot](output/playwright/pricing-20261023/price-dark-390.png). Actual CMS stored-price/currency confirmation and JSON collection integration remain unchecked.

## Known checks to resolve

- Existing generation docs describe Kling 3.0. This checklist explicitly targets **Kling 4.0 via Higgsfield**, as requested; implementation and provider availability still need verification.
- **Pricing is implemented and locally verified; receiving-system confirmation remains:** verify the live CMS stores the intended price and confirm currency/range/precision. Earlier direct CMS requests sent `Price: "2"`, but the stored price was not returned or verified.
- **JSON delivery is unconfirmed:** the CMS returns `Success: true` with zero inserted/updated assets for the tested simulator, Lottie-style and super-like JSON. Adding paired thumbnails did not resolve it. Mirsal's normal pack exporter rejects JSON with HTTP 409.
- **Success validation needs strengthening:** the current application checks HTTP status and the success flag, without validating the inserted/updated count. The observed response provides counts but no collection ID or stored name/price for readback.
- Final Lottie asset checks remain deferred until those files are supplied.

## Smoke-test results: 2026-10-23

Build `9ec0444f`, branch `code-audit`. Used a disposable copy on port 8807 and the configured live CMS. No image/video model generation was run; reaction JSON was exported from existing saved settings. The 14 original media files and both original pack records were verified unchanged.

These initial smoke results predate the pricing implementation; the former `price` rejection was resolved by the [pricing follow-up](#pricing-verification-2026-10-23).

| Submission | Existing assets | API result | Verdict |
|---|---|---|---|
| `test` | Latest pack `2d6bc270`, Generic Test manually; 4 animations | HTTP 200, `Success: true`, `insertedCount: 4`; app toast and notification confirmed | Pass for pack delivery |
| `test_simulated` | Latest simulator presets `burst_04`, `confetti_07` | HTTP 200, success flag, 0 inserted/updated | Delivery not confirmed |
| `test_animated_lottie` | Saved Burn calories and like button simulations | HTTP 200, success flag, 0 inserted/updated | Delivery not confirmed |
| `test_super_like` | Saved V001, phone and desktop JSON | HTTP 400: ContentType must be emoji or emoji_reaction | Rejected |
| `test_simulated_thumbs` | Simulator pair with PNG thumbnails | HTTP 200, success flag, 0 inserted/updated | Thumbnail hypothesis did not resolve delivery |
| `test_super_like_thumbs` | Super-like pair as `emoji_reaction`, super-like tags, PNG thumbnails | HTTP 200, success flag, 0 inserted/updated | Delivery not confirmed |

The `test` pack was sent through the app's export dialog and normal queue (`X1a1673c52990c13`). Reaction submissions used the documented CMS multipart contract directly because the app's pack exporter accepts only WEBM/PNG/WebP. Each reaction request included sample price `"2"`, file extensions/MIME types and ordered emoji/tag metadata. This does not establish application support for reaction delivery or persisted pricing.

Both existing packs (`2d6bc270`: 4 assets; `9ebb180c`: 10 assets, including one reaction) loaded and downloaded successfully. Manifest hashes matched; all media decoded at 512x512. Eight pack views covered Light/Dark at 1440/390 px with no document overflow. Library, Studio, Reactions, Settings, Help and Chat routes loaded with no page/HTTP errors during the completed checks. The super-like hold/release test played on both desktop and phone. Name/description limits passed; `price` was rejected with HTTP 400.

An earlier diagnostic submission `Smoke 1023 2d6bc270` also reported 4 inserted assets. The preliminary second-pack submission `Smoke 1023 9ebb180c` was rate-limited with HTTP 429 and `retryAfterSeconds: 57`; later submissions respected the cooldown. HTTP 200 and the success flag alone were not counted as a JSON delivery pass.

Evidence: [receipt summary](output/playwright/pack-smoke-20261023/receipt-summary.json), [reaction receipts](output/playwright/pack-smoke-20261023/reaction-delivery.json), [thumbnail/type retry receipts](output/playwright/pack-smoke-20261023/reaction-delivery-with-thumbnails.json), [browser summary](output/playwright/pack-smoke-20261023/browser-matrix-summary.json), [naming and super-like checks](output/playwright/pack-smoke-20261023/browser-targeted-summary.json), [pack confirmation](output/playwright/pack-smoke-20261023/test-pack-result.png), [super-like preview](output/playwright/pack-smoke-20261023/super-phone.png).

Not checked in this smoke test: new-user/LAN access, image/video generation and Kling 4.0 delivery, new pack creation/expansion, editing/trash/role combinations, final replacement Lottie assets, and CMS readback of stored names/prices or downstream client playback.
