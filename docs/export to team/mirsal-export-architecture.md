# Mirsal Sticker Export — Internal Architecture

**Audience:** Mirsal Builder / API maintainers. **Status:** filename format FINAL (Haitham 2026-10-08); export-to-ZIP built the same day. The pack-generation workflow (§10) and short generation codes are DECIDED 2026-10-08, implementation open. The old `AH43`-pack-code scheme is retired.

## 1. Canonical file name

Every sticker file exported in a ZIP is renamed (inside the ZIP only — source media under `out/` keeps its engine names, rule 9):

```text
{emoji}-{pack_slug}-{multi_action_tag}-{position}-{id}-{date}.{ext}
```

| # | Field | Rule |
|---|---|---|
| 1 | `emoji` | The sticker's primary emoji as a **literal Unicode glyph**, first field (e.g. `🤣`). First grapheme cluster of the saved emoji value; never an alias like `:rofl:`. |
| 2 | `pack_slug` | Pack/menu name, lowercase snake_case ASCII (e.g. `falcon`, `royal_falcon`). Identifies the pack in the menu. `-` separates identifiers, so a slug never contains one; `_` connects words inside it. |
| 3 | `multi_action_tag` | Canonical bank token first, then aliases, joined with `_` (e.g. `laugh_rofl_lmao`). Multi-choice: searching `laugh` OR `lmao` finds the same sticker by its tag. |
| 4 | `position` | Source cell as `sNN`, zero-padded (`s01`–`s09`); never renumber rejected cells. Locates the sticker inside its sheet for faster review. |
| 5 | `id` | Source generation's public code: 4 lowercase alphanumerics `0000`–`zzzz` (e.g. `7k2q`, illustrative), allocated once per generation (§10). Never reused. The internal batch id (`G###`) stays the address inside the app; the manifest carries both. |
| 6 | `date` | Generation creation date, UTC `YYYYMMDD`, frozen on first export; re-downloading does not change it. |
| `ext` | Encoder | Actual encoding: `.png` / `.webp` = static image, `.webm` = video. The media kind is read from the extension; there is no separate media field. |

Examples:

```text
🤣-falcon-laugh_laughing_lol_rofl_lmao_lmfao-s08-7k2q-20261008.webm
😍-falcon-love_heart_loving-s05-7k2q-20261008.png
👌-royal_falcon-approve_okay_yes_thumbsup-s06-9f3a-20261009.webm
```

(`7k2q`, `9f3a` are illustrative public codes of the source generations; inside the app those batches are still addressed as `G###`.)

**Each Generate run is one group.** A generation batch holds one 3×3 sheet, so its public code already scopes the group: there is no separate `gNN` field. A pack spanning several generations has files with different codes, grouped by `pack_slug` (and by the manifest's pack record).

**Important:** the whole pack shares `pack_slug`, never one id per sticker. Static and video assets of the same logical sticker share action, emoji and cell, and differ only in extension. Reusing an action or emoji across stickers is allowed.

## 2. Tag normalization (deterministic)

`multi_action_tag` is built as: lowercase canonical token, then alias tokens, joined with single `_`. Alias tokens are normalized before joining so the separator is unambiguous: **inner underscores, hyphens and spaces are removed** (`thank_you` → `thankyou`, `eye_roll` → `eyeroll`, `open_arms` → `openarms`, `thumbs_up` → `thumbsup`, `face_palm` → `facepalm`). Empty tokens are dropped; a sticker with no alias still carries its canonical token alone.

Filenames use hyphens as field delimiters and no field contains one (slugs are snake_case; the `eye-roll` / `star-struck` bank tokens are stored whole and split right-to-left: `date`, code, `sNN` are fixed shapes), so a filename splits back into its six fields; the manifest still stays authoritative — never alphabetical-order inference. An emoji may contain several Unicode code points (variation selectors, ZWJ sequences, skin tones): handle it as one grapheme string, never one character.

## 3. Dashboard / receiving app mapping

| Receiving behavior | Enabled by |
|---|---|
| Tap an emoji → every same-emotion sticker across all packs | Leading `emoji` field + manifest `emojis` array + tags carrying the literal glyph |
| Search `laugh` or `lmao` → all matching stickers (multi-choice) | `multi_action_tag` tokens + manifest `tags` array (canonical + aliases + literal emoji) |
| Pack menu / category | `pack_slug` (+ manifest pack record) |
| Title | Canonical action token (first tag segment) |
| Faster review: find the cell in the sheet | `position` (`s08`) + `id` (`G112`) → the exact source cell |
| Traceability / versions | `id` → Postgres `generations` row; `date` + manifest `revision` + `sha256` for exact versions |

Tags travel as an **array** in the manifest/DB; the underscore-joined filename segment is a serialization for the dashboard, never the source of truth.

## 4. IDs, lineage, and persistence

The existing identifiers remain intact: `G###` = generation batch, `S#` = original source cell, `J###` = paid job; `out/` records are the source of truth and Postgres mirrors them. The export uses the records that already exist:

| Record | Responsibility |
|---|---|
| Pack | Internal id (8-hex, as today), `slug`, title, owner, member source generations (each with its public code). No separate pack-code system. |
| Generation | Internal batch id (`G###`, the address everywhere inside the app) + one public `export_code` (`0000`–`zzzz`, §10), stored on `result.json` and mirrored to Postgres. One code per generation, never reused. |
| Sticker (library row) | Internal id (8-hex `sid`, as today), pack FK, `source {generation, index}`, name, emoji, file. Gains an optional saved canonical `action` + alias list once chosen at export. |
| Asset (export row) | Sticker id, public `export_code` + source `G###`, `source_cell`, action, emoji(s), tags, media (derived from ext), revision, export date, filename, checksum. |

Suggested constraints: unique pack `slug` per owner; unique `export_code` across generations; unique `(export_code, source_cell, media, revision)` per asset. Multiple revisions on one date can share a display filename: keep each as a separate stored asset/export snapshot, disambiguated by the manifest row + checksum. Never reuse a retired code; codes survive renames, re-exports, restarts and restores. Sanitize everything user-supplied before it touches a path (no traversal).

## 5. Export pipeline

1. Use an approved `G###` batch / pack; existing gates, Telegram size/format validation and human approvals are unchanged.
2. Resolve the pack slug; enumerate source cells left-to-right/top-to-bottom as S1–S9. Skipped or rejected slots keep their numbers.
3. Resolve each cell's canonical action + full alias set from the bank (§6). A cell with no mapping exports on a deterministic fallback tag (key/tags words) and is flagged `unresolved: true` in the manifest — the exporter's bank picker UI is still open, so nothing is silently called an action.
4. Build one filename per asset from the six fields; write files into the ZIP under these names (sources untouched) with a UTF-8 `manifest.json` (schema version 1, §7).
5. Register filename, revision, hash and date in `out/` and mirror to Postgres. Re-exporting an unchanged version returns identical names and bytes.

## 6. Canonical action bank (36)

Haitham, 2026-10-08: the bank grows from 30 to 36 (rows 31–36 are new). Default emoji are starting points, **not exclusive mappings** — the saved per-sticker emoji always wins. Other emoji, including ❤️, 😢 or 😂, stay valid associations.

| # | Canonical token | Primary emoji | Aliases |
|---|---|---|---|
| 1 | `happy` | 😀 | smile, joy |
| 2 | `laugh` | 🤣 | laughing, lol, rofl, lmao, lmfao |
| 3 | `cry` | 😭 | crying, sobbing, tears |
| 4 | `sad` | 😔 | unhappy, disappointed |
| 5 | `love` | 😍 | heart, loving |
| 6 | `angry` | 😠 | mad, furious, rage |
| 7 | `wink` | 😉 | winking |
| 8 | `kiss` | 😘 | kissing |
| 9 | `surprised` | 😮 | shocked, wow |
| 10 | `scared` | 😱 | frightened, fear |
| 11 | `confused` | 😕 | puzzled |
| 12 | `think` | 🤔 | thinking |
| 13 | `eye-roll` | 🙄 | eyeroll |
| 14 | `sleep` | 😴 | sleepy |
| 15 | `cool` | 😎 | sunglasses |
| 16 | `shy` | 😊 | bashful, blushing |
| 17 | `sick` | 🤒 | ill |
| 18 | `sneeze` | 🤧 | sneezing |
| 19 | `celebrate` | 🥳 | party |
| 20 | `clap` | 👏 | applause |
| 21 | `approve` | 👍 | okay, yes, thumbsup |
| 22 | `disapprove` | 👎 | reject, no |
| 23 | `thanks` | 🙏 | thankyou |
| 24 | `hello` | 👋 | wave, hi |
| 25 | `hug` | 🤗 | openarms |
| 26 | `flex` | 💪 | flexing |
| 27 | `scheme` | 😏 | scheming |
| 28 | `facepalm` | 🤦 | facepalm |
| 29 | `shrug` | 🤷 | dunno |
| 30 | `bored` | 😑 | unimpressed |
| 31 | `dance` | 🕺 | dancing |
| 32 | `plead` | 🥺 | begging, please |
| 33 | `salute` | 🫡 | saluting, respect |
| 34 | `cheers` | 🍻 | toast |
| 35 | `gift` | 🎁 | present, surprise |
| 36 | `star-struck` | 🤩 | starstruck, amazed |

Suggested preset grids (Mirsal presets, not a Telegram vocabulary): `core-v1` = happy, laugh, love / cry, sad, angry / surprised, scared, thanks; `social-v1` = hello, hug, kiss / wink, shy, celebrate / clap, approve, disapprove; `reactions-v1` = think, confused, eye-roll / facepalm, shrug, bored / cool, flex, scheme; `daily-v1` = sleep, sick, sneeze / dance, plead, salute / cheers, gift, star-struck. Four grids × 9 = 36 slots covering all 36 actions with no repeats. A legacy label like `happy2` normalizes to `happy` while the original label is preserved; conflicting mappings keep the original and ask, never silently remap.

## 7. Manifest (schema version 1)

```json
{
  "schema_version": 1,
  "pack": {"id": "<internal-hex>", "slug": "falcon", "title": "Falcon", "generations": ["G112"]},
  "assets": [
    {
      "sticker_id": "<library-sid>",
      "export_code": "7k2q",
      "source_generation": "G112",
      "source_cell": "S8",
      "action": "laugh",
      "emoji": "🤣",
      "emojis": ["🤣", "😂"],
      "tags": ["laugh", "laughing", "lol", "rofl", "lmao", "lmfao", "🤣"],
      "media": "video",
      "revision": 1,
      "export_date": "20261008",
      "filename": "🤣-falcon-laugh_laughing_lol_rofl_lmao_lmfao-s08-7k2q-20261008.webm",
      "sha256": "<actual-file-hash>"
    }
  ]
}
```

## 8. Acceptance rules

- Emoji leads every filename as a literal glyph; pack slug, tag, `sNN`, public code, date follow in order.
- The whole pack shares `pack_slug`; each file's code is its source generation's public code (one code per generation, §10).
- `sNN`, generation and exact asset identities survive rejects, edits, and re-exports; duplicate actions are supported.
- Unmapped cells export on a deterministic fallback tag and carry `unresolved: true`; the exporter bank picker UI is still open.
- Unicode filenames and multi-code-point emoji round-trip through ZIP download/import byte-identical.
- Re-exporting an unchanged version returns identical names and bytes; an edited sticker becomes a new revision under a stable filename, told apart by the manifest.
- Postgres sync cannot silently replace prior asset versions.
- Compatibility holds: one engine, API-first, `out/` authoritative, human approval gates, existing Telegram validation.

## 9. Implementation plan (Mirsal Builder)

Engine functions + JSON contract first, screens second (rule 11); stdlib-first, `pathlib` only (rule 8).

**Built 2026-10-08 (export-to-zip scope):** steps 1, 2, 4 (date/slug; sticker `action` persistence not needed — the tag resolves at export time), 5, 7 (`generation/actions.py`, `media/export_names.py` with `describe`, both `export_zip`s renamed-in-ZIP + manifest v1, `tests/test_export_names.py`). Unmapped cells take the deterministic key/tags fallback with `unresolved: true` in the manifest.

Still open:

1. **Exporter bank picker UI** — the Studio export dialog offers the bank per `unresolved` cell (one recorded human pick, reversible); until then the fallback stands.
2. **Validation** — existing Telegram checks unchanged; plus filename checks (NFC, no separators, sane length).
3. **Out of scope** — in-app tag/emoji search UI (the tap-emoji and multi-choice search are receiving-app behaviors; the manifest `tags`/`emojis` arrays enable them; pool search stays semantic); pack-merge vs generation-scoped ids; the Telegram upload path (files as-is).

## 10. Pack generation workflow (DECIDED 2026-10-08, implementation open)

How `"generate sticker pack for {subject}"`, `generate more`, regenerate-as-versions, and the public generation codes work. Nothing below is built yet; it reuses the golden path (request → plan → sheet → stills → video → animations → pack) unchanged.

### 10.1 Request claims the next preset grid (always 3×3)

`"generate sticker pack for falcon"` (chat or Studio) is a pack intent: a new pack record (`slug: falcon`, title) plus a claim queue — the four preset grids in order (`core-v1`, `social-v1`, `reactions-v1`, `daily-v1`), 36 actions total. The first request claims the first **unclaimed** grid: the pack record gains `groups[] += {preset_key, status: CLAIMED, generation: null}`, and the sheet job is built from the preset's nine stored actions (prompts, emoji defaults, tags) — never guessed labels.

**Built 2026-10-08 (preset engine, no claim queue yet):** `actions.PRESETS` + `FACE_SENTENCES` + `preset_cells`, and `expand(..., preset=)` — an explicit grid name wins (preset words stripped from the subject, preset implies face), otherwise a face-mode 3×3 takes `core-v1`, so `generic emojis` now claims happy → thanks in bank order with bank emoji. Cell keys are `{subject}_{token}`, tags carry token + aliases. What is still open is the pack-record claim ledger itself: every emoji request still takes `core-v1` (nothing remembers the pack's claimed grids yet), and `generate more` does not advance the queue.

Neither the auto expander nor the AI enhancer chooses 2×2 vs 3×3 here: a preset grid is nine slots by definition, so preset packs are always 3×3. The expander fills the deterministic plan, the enhancer only improves wording. 2×2 stays for the freeform flows only.

Claim state lives in the pack record (`library.json`, file-primary, under the library lock): an unclaimed grid is a preset with no group entry. The claim is written synchronously **before** any paid call, so two simultaneous `generate more` clicks serialize: the second sees the first's `CLAIMED` entry and takes the next grid. When the sheet returns, the batch is cut and reviewed exactly as today, and the group entry becomes `{status: READY, generation: G###, export_code}`.

### 10.2 `generate more` claims the next grid in the same pack

`"generate more"` (chat) or Create more (Studio) on an open pack claims the next unclaimed preset for **that pack**: a new group, a new generation, same `pack_slug`. When all four grids are claimed the pack is complete (36 stickers): the app says so in words and offers the next step (a custom 9-pick from the bank, or a new pack) — never a silent repeat, never a dead end.

### 10.3 Regenerate stays in the same batch as versions

Regenerating a preset-pack sticker does **not** open a new batch (today's 1×1 regen does). The new take is appended as a version of the same sticker in the same batch: `sticker.versions[] += {revision, files, report, ts, by, reason}`. S#, bank action, emoji and generation code never change; each version is reviewed on its own (approve → becomes current, reversible); old versions are kept for undo and audit, never deleted. Export always ships the latest approved version; the manifest `revision` tells versions apart under a stable filename. Freeform (non-preset) batches keep today's new-batch regen until unified.

### 10.4 Public generation codes (`0000`–`zzzz`)

Each generation gets one public code: 4 lowercase alphanumerics (`36^4 = 1,679,616` values), compared case-insensitively, no exclusions. `G###` stays the internal address everywhere (rule 9: folders, API, URLs, asset keys, chat, Postgres) — the code is the **public** face used in export filenames, the manifest, and a new Postgres mirror column. The mapping lives in `result.json` (`export_code`) plus a file registry `out/export_codes.json` (`{code: "G###"}`) written under the writer lock, so allocation works offline; the Postgres `UNIQUE` is the backstop (needs a numbered migration). Allocation is random-pick + registry-check + retry, at preset-claim time; existing batches get their codes lazily at first export (persisted the same way). `G###` is never shown in an export again.

### 10.5 One code per generation, not one per pack (recommendation: multiple ids)

Haitham's question — should the id be one per pack or several per pack? **Several: one code per generation.** The stated goal is tracing generation versions, and a single pack-wide id erases exactly that: which generation (which sheet, which paid job, which spend) made which sticker, and which version of a regenerated sticker is which. Per-generation codes keep the lineage (`7k2q` = the second sheet of Falcon, v3 of its S4 is still `7k2q` + revision 3); the pack identity is already carried by `pack_slug` plus the manifest pack record, so nothing is lost. A single pack id would push version tracing into side channels and break the money trail (tasks/jobs link by generation). Cost of per-generation codes: one allocation per claim — negligible.

### 10.6 Build order (when it gets a go)

1. Claim ledger on the pack record (`groups[]`) + preset-queue resolver (chat intent + Studio entry); all-claimed answer with next-step choices. (Preset engine already built: §10.1.)
2. Preset prompt builder (nine stored actions → sheet/video prompts through the existing templates).
3. In-batch `versions[]` (+ `normalise` default, write-through, Studio version switcher, export uses latest approved).
4. Code allocator (registry + retry, claim-time allocation, lazy backfill at export, `export_names` id field becomes the code, manifest carries both ids).
5. Postgres mirror column + numbered migration; chat-side references stay `G###`.
6. Custom 9-pick presets from the bank (after the fixed four prove out).
