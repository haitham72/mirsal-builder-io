# Mirsal Sticker Export — Internal Architecture

**Audience:** Mirsal Builder / API maintainers. **Status:** proposed export contract; implement against existing schema rather than replacing it.

## 1. Ownership boundary

The integration handoff needs only these four filename components:

```text
{pack_id}-{pack_slug}-{action}-{emoji}
```

Mirsal Builder owns and appends the remaining asset-origin metadata:

```text
-s{sticker_number}-{media}-g{group}-{date}.{ext}
```

Canonical file name:

```text
{pack_id}-{pack_slug}-{action}-{emoji}-s{sticker_number}-{media}-g{group}-{date}.{ext}
```

Examples:

```text
AH43-falcon-laugh-🤣-s04-static-g01-20261008.png
AH43-falcon-laugh-🤣-s04-video-g01-20261008.webm
AH43-falcon-love-😍-s05-static-g01-20261008.png
AH43-falcon-approve-👌-s06-video-g02-20261008.webm
```

**Important:** `pack_id` is the same across an entire pack. It is **not** a unique sticker ID. Static and video assets of the same logical sticker are linked through internal `sticker_id` and `asset_id` records, plus the source group/cell. Reusing an action or emoji is allowed. In an existing production schema, `AH43` can be a stable external pack code mapped to the internal pack primary key, rather than replacing the primary key.

## 2. Field contracts

| Field | Owner | Rule |
|---|---|---|
| `pack_id` | Mirsal DB | Persistent pack lookup code, e.g. `AH43`; unique across packs, never reused. |
| `pack_slug` | Pack metadata | Lowercase readable pack/category key, e.g. `falcon`, `royal-falcon`; resolves to pack/category in receiving application. |
| `action` | Canonical action bank | Short normalized token (`laugh`, `love`, `approve`, etc.); used as the dashboard title. |
| `emoji` | Sticker metadata | One primary **literal Unicode emoji sequence** (🤣, 😒, 😍, 👌, 😘); used for emoji assignment, interaction and search. |
| `sNN` | Mirsal engine | Source grid cell S1–S9 padded to `s01`–`s09`; never renumber rejected cells. |
| `media` | Exporter | `static` or `video`. |
| `gNN` | Mirsal engine | Pack-local 3×3 group number, e.g. `g01`, `g02`; distinct from existing run `G###`. |
| `date` | Exporter | Registered export version date as `YYYYMMDD` in UTC, stable on re-download. |
| `ext` | Encoder | Actual encoding: `.png` or `.webp` for static, `.webm` for Telegram video sticker. |

The literal emoji component should remain in UTF-8 filenames and ZIP entries. Never replace it with an alias such as `:rofl:`. An emoji may contain more than one Unicode code point (including variation selectors or ZWJ sequences), so parse/store it as a string, not a single character. Filenames use hyphens as field delimiters: validate any slug/action strings containing hyphens through the saved export manifest, rather than assuming a simple fixed-index split.

## 3. Dashboard / receiving app mapping

| Receiving field | Source | Example |
|---|---|---|
| Pack lookup / internal DB | `pack_id` | `AH43` |
| Pack/category for **Assign to emoji** workflow | `pack_slug` | `falcon` |
| **Assign to emoji** selected value | `emoji` | 🤣 |
| **Title** | `action` | `laugh` |
| **Tags** | canonical action + aliases + literal emoji, joined with `_` | `laugh_happy_joy_🤣` |

`pack_slug` identifies the pack/category **used by** the emoji-assignment flow; it is not itself the Unicode emoji. The explicit emoji field drives actual emoji assignment. Tags can be serialized with `_` for the receiving dashboard, but store tag tokens as an array in the DB; do not make underscore-joined text the source of truth. Normalize aliases that themselves contain underscores before joining.

## 4. IDs, lineage, and persistence

The README's existing identifiers remain intact: `G###` = generation batch, `S#` = original source cell, `J###` = paid job; existing `out/` records are the source of truth and Postgres mirrors them. The export code introduces or maps the following logical records:

| Record | Responsibility |
|---|---|
| Pack | Internal UUID/PK, unique persistent `pack_id`, slug, title, owner. |
| Group | Source `G###`, group ordinal (`g01`...), preset/version, variation, pack FK. |
| Sticker | Internal stable `sticker_id`, pack/group FK, source `S#`, action, primary emoji, additional emojis, tags. |
| Asset | Stable `asset_id`, sticker FK, `media`, revision, extension, filename, checksum, stored path, creation/export timestamps. |

Suggested constraints: unique `pack_id`; unique `(pack_id, group_number)`; unique `(group_id, source_sticker_number)`; unique `(sticker_id, media, revision)`. An entire pack shares `pack_id`, so **do not** use `pack_id` alone to look up an individual asset. Resolve by registered `asset_id` or a manifest-backed exact identity. Multiple revisions on the same date can have identical display filenames: preserve each as a separate stored asset and ZIP/export snapshot, and use asset IDs/checksums to disambiguate.

A four-character base-36 uppercase pack code has `36^4 = 1,679,616` possible values; sufficient for thousands of packs, but allocation still needs a uniqueness constraint and collision handling. Never reuse retired codes. IDs survive renames, re-exports, restarts and restore operations. Do not place arbitrary user-supplied filename data directly into paths; sanitize and prevent traversal.

## 5. Export pipeline and 3×3 groups

1. Use an approved `G###` batch / pack; preserve existing gate, validation, Telegram size/format and human-approval rules.
2. Resolve the persistent pack code and saved preset, then enumerate source cells left-to-right/top-to-bottom as S1–S9. Skipped or rejected slots retain their original numbers.
3. Generate one metadata record per logical sticker (source group/cell), with canonical action, primary emoji, alias tags and any secondary emoji associations.
4. Export static/video assets independently; same sticker's still + animation share their `sticker_id`, action and primary emoji. The `media` component differentiates filenames.
5. Register exact asset IDs, revisions, hashes and filenames in `out/` and mirror to Postgres. Re-exporting an unchanged version preserves filename and bytes.
6. Package a UTF-8 `manifest.json` with the files. Never infer group or cell ordering from alphabetically sorted filenames.

Suggested preset groups: `core-v1` = happy, laugh, love / cry, sad, angry / surprised, scared, thanks; `social-v1` = hello, hug, kiss / wink, shy, celebrate / clap, approve, disapprove; `reactions-v1` = think, confused, eye-roll / facepalm, shrug, bored / cool, flex, scheme; `daily-v1` = sleep, sick, sneeze / happy, laugh, thanks / hello, love, approve. These are **Mirsal presets**, not an official Telegram vocabulary. Support multiple grids under one pack (`g01`, `g02`...).

## 6. Canonical action bank (30)

| Action | Primary emoji | Typical aliases |
|---|---|---|
| happy | 😀 | smile, joy |
| laugh | 🤣 | laughing, lol |
| cry | 😭 | crying, sobbing |
| sad | 😔 | unhappy, disappointed |
| love | 😍 | heart, loving |
| angry | 😡 | mad, furious |
| wink | 😉 | winking |
| kiss | 😘 | kissing |
| surprised | 😮 | shocked, wow |
| scared | 😱 | frightened, fear |
| confused | 😕 | puzzled |
| think | 🤔 | thinking |
| eye-roll | 🙄 | eye_roll, eyeroll |
| sleep | 😴 | sleepy |
| cool | 😎 | sunglasses |
| shy | 😊 | bashful |
| sick | 🤒 | ill |
| sneeze | 🤧 | sneezing |
| celebrate | 🥳 | party |
| clap | 👏 | applause |
| approve | 👌 | okay, yes, thumbs_up |
| disapprove | 👎 | reject, no |
| thanks | 🙏 | thank_you |
| hello | 👋 | wave, hi |
| hug | 🤗 | open_arms |
| flex | 💪 | flexing |
| scheme | 😏 | scheming |
| facepalm | 🤦 | face_palm |
| shrug | 🤷 | dunno |
| bored | 😒 | unimpressed |

Default emoji are suggested starting points, **not exclusive mappings**. Save the actual selected emoji per sticker. Other emoji, including ❤️, 😢 or 😂, are valid associations even if not shown above. A legacy label like `happy2` may normalize to `happy` while preserving its original source name. If aliases conflict, keep the original and request confirmation; do not silently remap.

## 7. Minimal manifest example

```json
{
  "pack_id": "AH43",
  "pack_slug": "falcon",
  "group": "g01",
  "source_batch": "G123",
  "assets": [
    {
      "sticker_id": "internal-sticker-id",
      "asset_id": "internal-asset-id",
      "source_cell": "S4",
      "action": "laugh",
      "emoji": "🤣",
      "emojis": ["🤣", "😂"],
      "tags": ["laugh", "happy", "joy", "🤣"],
      "media": "video",
      "revision": 1,
      "filename": "AH43-falcon-laugh-🤣-s04-video-g01-20261008.webm",
      "sha256": "<actual-file-hash>"
    }
  ]
}
```

## 8. Acceptance rules

- Pack code remains identical across every sticker in the pack, static/video forms and different 3×3 groups.
- Actual emoji appears in filename, DB emoji metadata, dashboard assignment and searchable tags.
- Filename first four components are the receiving-team contract; suffix is generated by Mirsal only.
- `S#`, group and exact asset identities survive rejects, edits, and re-exports; duplicate actions are supported.
- Unicode filenames and multi-code-point emoji round-trip correctly through ZIP download/import.
- Postgres sync cannot silently replace prior asset versions.
- Maintain compatibility with README architecture: one engine, API-first, `out/` authoritative, human approval gates, existing Telegram validation.
