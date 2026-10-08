# Mirsal Sticker Export — Internal Architecture

**Audience:** Mirsal Builder / API maintainers. **Status:** FINAL filename format decided by Haitham 2026-10-08; implement against existing schema rather than replacing it. The old `AH43`-pack-code scheme is retired: the pack identity in an export is the source generation id.

## 1. Canonical file name

Every sticker file exported in a ZIP is renamed (inside the ZIP only — source media under `out/` keeps its engine names, rule 9):

```text
{emoji}-{pack_slug}-{multi_action_tag}-{position}-{id}-{date}.{ext}
```

| # | Field | Rule |
|---|---|---|
| 1 | `emoji` | The sticker's primary emoji as a **literal Unicode glyph**, first field (e.g. `🤣`). First grapheme cluster of the saved emoji value; never an alias like `:rofl:`. |
| 2 | `pack_slug` | Pack/menu name, lowercase ASCII words separated by hyphens (e.g. `falcon`, `royal-falcon`). Identifies the pack in the menu. |
| 3 | `multi_action_tag` | Canonical bank token first, then aliases, joined with `_` (e.g. `laugh_rofl_lmao`). Multi-choice: searching `laugh` OR `lmao` finds the same sticker by its tag. |
| 4 | `position` | Source cell as `sNN`, zero-padded (`s01`–`s09`); never renumber rejected cells. Locates the sticker inside its sheet for faster review. |
| 5 | `id` | Source generation batch id (`G###`, e.g. `G112`): the pack identity for the export, mapped to the Postgres `generations` row. Never reused. |
| 6 | `date` | Generation creation date, UTC `YYYYMMDD`, frozen on first export; re-downloading does not change it. |
| `ext` | Encoder | Actual encoding: `.png` / `.webp` = static image, `.webm` = video. The media kind is read from the extension; there is no separate media field. |

Examples:

```text
🤣-falcon-laugh_rofl_lmao-s08-G112-20261008.webm
😍-falcon-love_heart_loving-s05-G112-20261008.png
👌-royal-falcon-approve_okay_yes-s06-G113-20261009.webm
```

**Each Generate run is one group.** A generation batch holds one 3×3 sheet, so the generation id already scopes the group: there is no separate `gNN` field. A pack spanning several generations has files with different ids, grouped by `pack_slug` (and by the manifest's pack record).

**Important:** the whole pack shares `pack_slug`, never one id per sticker. Static and video assets of the same logical sticker share action, emoji and cell, and differ only in extension. Reusing an action or emoji across stickers is allowed.

## 2. Tag normalization (deterministic)

`multi_action_tag` is built as: lowercase canonical token, then alias tokens, joined with single `_`. Alias tokens are normalized before joining so the separator is unambiguous: **inner underscores, hyphens and spaces are removed** (`thank_you` → `thankyou`, `eye_roll` → `eyeroll`, `open_arms` → `openarms`, `thumbs_up` → `thumbsup`, `face_palm` → `facepalm`). Empty tokens are dropped; a sticker with no alias still carries its canonical token alone.

Filenames use hyphens as field delimiters while `pack_slug` (`royal-falcon`) and actions (`eye-roll`) may contain hyphens, so a filename is **parsed right-to-left** (`date`, `G###`, `sNN` are fixed shapes) and the manifest stays authoritative — never fixed-index splitting, never alphabetical-order inference. An emoji may contain several Unicode code points (variation selectors, ZWJ sequences, skin tones): handle it as one grapheme string, never one character.

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
| Pack | Internal id (8-hex, as today), `slug`, title, owner, member source generations. No separate pack-code system. |
| Sticker (library row) | Internal id (8-hex `sid`, as today), pack FK, `source {generation, index}`, name, emoji, file. Gains an optional saved canonical `action` + alias list once chosen at export. |
| Asset (export row) | Sticker id, `source_generation`, `source_cell`, action, emoji(s), tags, media (derived from ext), revision, export date, filename, checksum. |

Suggested constraints: unique pack `slug` per owner; unique `(source_generation, source_cell, media, revision)` per asset. Multiple revisions on one date can share a display filename: keep each as a separate stored asset/export snapshot, disambiguated by `asset`/manifest row + checksum. Never reuse a retired id; ids survive renames, re-exports, restarts and restores. Sanitize everything user-supplied before it touches a path (no traversal).

## 5. Export pipeline

1. Use an approved `G###` batch / pack; existing gates, Telegram size/format validation and human approvals are unchanged.
2. Resolve the pack slug; enumerate source cells left-to-right/top-to-bottom as S1–S9. Skipped or rejected slots keep their numbers.
3. Resolve each cell's canonical action + aliases from the bank (§6). A cell with no mapping stays **unresolved** until the exporter picks from the bank (one click, saved on the sticker) — never silently defaulted.
4. Build one filename per asset from the six fields; write files into the ZIP under these names (sources untouched) with a UTF-8 `manifest.json` (schema version 1, §7).
5. Register filename, revision, hash and date in `out/` and mirror to Postgres. Re-exporting an unchanged version returns identical names and bytes.

## 6. Canonical action bank (36)

Haitham, 2026-10-08: the bank grows from 30 to 36 (rows 31–36 are new). Default emoji are starting points, **not exclusive mappings** — the saved per-sticker emoji always wins. Other emoji, including ❤️, 😢 or 😂, stay valid associations.

| # | Canonical token | Primary emoji | Aliases |
|---|---|---|---|
| 1 | `happy` | 😀 | smile, joy |
| 2 | `laugh` | 🤣 | laughing, lol, rofl, lmao |
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
      "source_generation": "G112",
      "source_cell": "S8",
      "action": "laugh",
      "emoji": "🤣",
      "emojis": ["🤣", "😂"],
      "tags": ["laugh", "rofl", "lmao", "🤣"],
      "media": "video",
      "revision": 1,
      "export_date": "20261008",
      "filename": "🤣-falcon-laugh_rofl_lmao-s08-G112-20261008.webm",
      "sha256": "<actual-file-hash>"
    }
  ]
}
```

## 8. Acceptance rules

- Emoji leads every filename as a literal glyph; pack slug, tag, `sNN`, `G###`, date follow in order.
- The whole pack shares `pack_slug`; each file's `id` is its source generation.
- `sNN`, generation and exact asset identities survive rejects, edits, and re-exports; duplicate actions are supported.
- Unmapped cells never export on a guessed action; the exporter picks from the bank.
- Unicode filenames and multi-code-point emoji round-trip through ZIP download/import byte-identical.
- Re-exporting an unchanged version returns identical names and bytes; an edited sticker becomes a new revision under a stable filename, told apart by the manifest.
- Postgres sync cannot silently replace prior asset versions.
- Compatibility holds: one engine, API-first, `out/` authoritative, human approval gates, existing Telegram validation.

## 9. Implementation plan (Mirsal Builder)

Engine functions + JSON contract first, screens second (rule 11); stdlib-first, `pathlib` only (rule 8).

1. **Bank module** — new `generation/actions.py`: `ACTION_BANK` (the 36 rows: token → primary emoji + aliases), `normalize_tag()` (§2 rule), `canonical_for(key, tags)` → `(token, aliases)` or `None` when unmapped. Pure; no `psycopg`/`redis`/`langgraph` import (rule 3).
2. **Filename builder** — new `media/export_names.py`: `build(emoji, slug, tags, index, gid, date)` → stem; `parse(stem)` right-to-left on the `sNN` / `G###` / date anchors, manifest-authoritative; `first_emoji()` grapheme splitter (ZWJ `U+200D`, VS16 `U+FE0F`, skin-tone modifiers kept with their base). Pure + round-trip tests.
3. **Unresolved-action flow** — batch sticker gains optional `action` (+ `pipeline.normalise` default, mirrored by `store/sync.py`); the Studio export dialog offers the bank per unmapped cell (one recorded human pick, reversible). No guessing.
4. **Persist the fields** — `date` = generation `created` (UTC `YYYYMMDD`), frozen at first export; `slug` = pack slug (add-or-derive on the library pack record); library rows already carry `source {generation, index}`.
5. **Both `export_zip`s** (`flow/batches.py`, `media/library.py`) rename inside the ZIP only (sources untouched, rule 9) and write manifest v1 (`ensure_ascii=False`); ZIP via Python `zipfile`, never a shell (PowerShell mangles non-ASCII).
6. **Validation** — existing Telegram checks unchanged; plus filename checks (NFC, no separators, sane length).
7. **Tests** (budget: narrowest) — new `tests/test_export_names.py`: build/parse round-trip, alias normalization (`thank_you` → `thankyou`), unresolved `None`, emoji splitter (skin tone, VS16, ZWJ), export-twice byte-identical. Run by name.
8. **Out of scope** — in-app tag/emoji search UI (the tap-emoji and multi-choice search are receiving-app behaviors; the manifest `tags`/`emojis` arrays enable them; pool search stays semantic); pack-merge vs generation-scoped ids; the Telegram upload path (files as-is).
