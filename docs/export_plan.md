# Mirsal sticker export plan (proposal, NOT built)

> Status (review, 2026-10-08): this file was found untracked as `mirsal/out/export-guide.md` (the runtime data dir, the wrong home for a design doc) and moved here. Nothing below is implemented: no preset keys, no public codes, no manifest version, no new tables. It is a proposal in the shape of `docs/burst_plan.md`: it waits for Haitham's go, and the conflicts listed at the end must be settled before anything is built. Do not present any of it as existing behaviour.

General export contract for all sticker packs: people, animals, mascots, and other subjects. This guide defines the naming and metadata behavior to implement.

## 1. Filename convention

Use the same format for static images and videos:

```text
{id}-{pack_slug}-{action}-s{sticker_number}-{media}-g{group}-{date}.{ext}
```

Examples (IDs are illustrative):

```text
AH43-falcon-laugh-s04-static-g01-20261008.png
AH43-falcon-laugh-s04-video-g01-20261008.webm
BK72-falcon-cry-s05-static-g01-20261008.png
CM85-falcon-scared-s07-video-g02-20261008.webm
DN96-falcon-love-s04-video-g03-20261009.webm
```

| Field | Meaning and rule |
|---|---|
| `id` | Globally unique, persistent public sticker ID, e.g. `AH43`. One logical sticker; shared by its static and video assets. |
| `pack_slug` | Readable pack name, e.g. `falcon` or `royal-falcon`. Lowercase ASCII words separated by hyphens. |
| `action` | Canonical emotion/action from the 30-name bank. |
| `sticker_number` | Original S# within its source 3×3 grid; S4 becomes `s04`. Never renumber after removal. |
| `media` | `static` or `video`. |
| `group` | Stable number of the source 3×3 group within the pack, padded to at least two digits: `g01`, `g02`, `g03`. |
| `date` | UTC date the exported asset version was registered, `YYYYMMDD`. Persist it; downloading again does not change it. |
| `ext` | Actual encoded format. Telegram-oriented exports use PNG/WEBP for static and WEBM for video. MP4 may be a separate working/app export if supported; it is not a Telegram video-sticker format. |

No spaces, braces, parentheses, emoji, duplicated pack names, random hash suffixes, or revision tokens in filenames. Do not rename an extension to pretend that a file was converted.

**The same sticker ID must retain the same action across static and video.** A laughing static sticker and its laughing animation share an ID. A crying sticker receives a different ID.

Group and sticker numbers describe origin; the public sticker ID provides identity. `g01` is not the existing generation batch identifier `G###`, and it is not a revision number.

## 2. Identity and Postgres tracing

Use separate identifiers for each level:

| Identifier | Represents |
|---|---|
| `pack_id` | Entire pack, independent of its slug. |
| `group_id` | One source 3×3 group. Store its pack-local group number, preset/version, source batch, and variation metadata. |
| `sticker_id` | One logical sticker. Its public code is filename `{id}`. |
| `asset_id` | One exact static/video file version belonging to a sticker. |

Example lookup:

```text
AH43 → laughing sticker → source group g01 / S4 → pack Falcon
     → static asset versions
     → video asset versions
```

A slug is a readable label, not an identity key. Renaming a pack must not change its pack ID or sticker IDs.

### Persistent ID rules

1. Allocate one public code when each logical sticker is registered, before export.
2. Static and video derived from that sticker reuse the code.
3. Different cells, groups, independently generated variations, and independent copies receive different sticker codes, even when they share an action.
4. Editing the existing sticker creates an asset version under the same sticker ID. Replacing it with an unrelated logical sticker creates a new sticker ID.
5. Keep codes through server restarts, renames, repeated exports, soft deletion, and restoration.
6. Never reuse deleted codes. Retain a permanent reservation/tombstone after media removal.
7. Store each sticker's code in its source metadata/result.json under `out/` and mirror it in Postgres, preserving the README's filesystem source-of-truth architecture.
8. Allocate through one coordinating service with a global database uniqueness constraint and collision retries. Persist allocation before returning it. When Postgres is unavailable, export registered stickers and defer new allocations.
9. Preserve existing internal UUIDs/primary keys; the public code can be an additional field.
10. Apply existing ownership and authentication rules. A short code is a lookup key, not an access credential.

### Code capacity

Use uppercase `A–Z` and digits `0–9`.

| Length | Available codes |
|---|---:|
| 4 characters | 36⁴ = 1,679,616 |
| 5 characters | 36⁵ = 60,466,176 |
| 6 characters | 36⁶ = 2,176,782,336 |

Four characters cover thousands of **logical stickers**, not just packs. A full nine-sticker group consumes nine codes; a 36-sticker pack consumes 36. Random generation still needs uniqueness enforcement. Start with four characters and allow longer codes later. Excluding visually similar characters reduces capacity.

### Asset versions without filename revisions

Keep `revision`, `asset_id`, checksum, and creation time in Postgres and the export manifest. Do not include `r01` in filenames.

The simplified filename is not guaranteed to distinguish two revisions exported on the same date. Resolve exact files using manifest `asset_id` and checksum. Store each asset version under its own asset ID/path, and put each export in a separate export directory/ZIP. Never overwrite historical files just because their display filenames match.

Re-downloading an unchanged export returns the same filename, date, and bytes. A new revision on another date naturally has a different filename. Filename-only imports must flag ambiguity rather than silently choosing a same-day revision.

## 3. Thirty canonical emotion/action names

These are product labels, not official Unicode names. Store the canonical token separately from the emoji association. Emoji provide useful defaults; they cannot identify an action reliably in every case.

| # | Canonical token | Default emoji | Legacy labels / aliases |
|---|---|---|---|
| 1 | `happy` | 😀 😃 😄 🙂 | happy, happy2, smile, smiling, joy |
| 2 | `laugh` | 😂 🤣 😆 | laughing, laughter, lol, lmao |
| 3 | `cry` | 😭 😢 | crying, sobbing, tears |
| 4 | `sad` | 😔 ☹️ 🙁 | sadness, unhappy, disappointed |
| 5 | `love` | ❤️ 😍 🥰 | loving, heart, hearts, in_love |
| 6 | `angry` | 😠 😡 🤬 | anger, mad, furious, rage |
| 7 | `wink` | 😉 | winking |
| 8 | `kiss` | 😘 😚 💋 | kissing, kisses |
| 9 | `surprised` | 😮 😲 🤯 | surprise, shocked, wow |
| 10 | `scared` | 😨 😱 | afraid, fear, frightened |
| 11 | `confused` | 😕 🤨 | confusion, puzzled |
| 12 | `think` | 🤔 | thinking, pondering |
| 13 | `eye-roll` | 🙄 | eye_roll, eyeroll, rolling_eyes |
| 14 | `sleep` | 😴 💤 | sleeping, sleepy, tired |
| 15 | `cool` | 😎 | sunglasses, confident |
| 16 | `shy` | 😊 🫣 | bashful, embarrassed, blushing |
| 17 | `sick` | 🤒 🤢 🤮 | ill, unwell, nausea |
| 18 | `sneeze` | 🤧 | sneezing, achoo |
| 19 | `celebrate` | 🥳 🎉 🎊 | celebration, party, partying |
| 20 | `clap` | 👏 | clapping, applause |
| 21 | `approve` | 👍 ✅ 👌 | thumbs_up, yes, okay, ok |
| 22 | `disapprove` | 👎 ❌ | thumbs_down, no, reject |
| 23 | `thanks` | 🙏 | thank_you, thank-you, grateful |
| 24 | `hello` | 👋 | hi, wave, waving |
| 25 | `hug` | 🤗 🫂 | hugging, open_arms, embrace |
| 26 | `flex` | 💪 | flexing, strong, strength |
| 27 | `scheme` | 😏 😈 | scheming, plotting, mischievous |
| 28 | `facepalm` | 🤦 | face_palm, disbelief |
| 29 | `shrug` | 🤷 | shrugging, dunno, idk |
| 30 | `bored` | 😑 🥱 | boredom, unimpressed |

### Normalization and ambiguity

- Normalize existing textual labels: trim, lowercase, and treat spaces, hyphens, and underscores as equivalent for alias lookup.
- Preserve the original label and original emoji sequence in metadata.
- Treat numeric suffixes such as `happy2` as legacy instance labels only when their base is a recognized alias. Preserve distinction through S#.
- For emoji lookup, support equivalent text/emoji presentation selectors and supported gender/skin-tone variants without altering the stored original emoji.
- Prefer a saved canonical action, then an unambiguous text alias, then an unambiguous emoji mapping.
- If text and emoji conflict, show the proposed result for review. Do not silently overwrite an existing association.
- `🙏` can mean thanks or prayer; `👋` can mean hello or goodbye; `😭` can express intense laughter. Context or a saved explicit selection takes priority.
- Unknown actions remain unresolved until the exporter offers a choice from the 30 labels. Do not default everything to `happy`.
- Keep finer descriptions, such as “victory pose” or “sarcastic laugh,” in titles/tags. The canonical filename vocabulary stays small.


## 4. Saved 3×3 presets and pack expansion

Select a saved nine-slot preset before generation. Its ordered actions determine prompt slots, emoji defaults, and exported names. Character changes do not change the preset.

Telegram associates stickers with emojis; these 30 English labels and 3×3 layouts are Mirsal presets. Telegram's Bot API accepts 1–20 emoji associations per sticker. Source: [Telegram InputSticker](https://core.telegram.org/bots/api#inputsticker).

### Fixed cell order

Read every source grid left-to-right, top-to-bottom:

| Column 1 | Column 2 | Column 3 |
|---|---|---|
| S1 · top-left | S2 · top-centre | S3 · top-right |
| S4 · middle-left | S5 · centre | S6 · middle-right |
| S7 · bottom-left | S8 · bottom-centre | S9 · bottom-right |

These are source S# values. If S3 fails or is excluded, S4 stays S4. Do not compress numbering to eight cells. A video sheet rebuilt from approved cells must retain an explicit rebuilt-position → original-S# mapping.

### Presaved layouts

Save each preset under an immutable key/version. Each entry below is its fixed row-major order; emoji defaults come from the 30-name table.

| Preset key | First row · S1–S3 | Second row · S4–S6 | Third row · S7–S9 |
|---|---|---|---|
| `core-v1` | happy · laugh · love | cry · sad · angry | surprised · scared · thanks |
| `social-v1` | hello · hug · kiss | wink · shy · celebrate | clap · approve · disapprove |
| `reactions-v1` | think · confused · eye-roll | facepalm · shrug · bored | cool · flex · scheme |
| `daily-v1` | sleep · sick · sneeze | happy · laugh · thanks | hello · love · approve |

The first three grids cover 27 different actions. `daily-v1` adds the remaining three and repeats six useful actions: **four full grids = 36 stickers covering all 30 names**. If the requested pack must have exactly 30 stickers, generate the fourth grid but export only S1–S3 from it; preserve S4–S9 as unselected source cells.

These are suggested defaults to save, not a claim that every Telegram pack uses the same emotions. Allow named custom presets built from the same bank. For example, a “polite replies” preset can select nine existing tokens without changing their canonical names.


### Multiple groups in one pack

| Group | Saved preset | Source cells | Sticker IDs |
|---|---|---|---|
| `g01` | core-v1 | S1–S9 | Nine different public codes |
| `g02` | social-v1 | S1–S9 | Nine additional public codes |
| `g03` | reactions-v1 | S1–S9 | Nine additional public codes |
| `g04` | daily-v1 | S1–S9, or only S1–S3 for a 30-sticker pack | One code per registered logical sticker |

Each group has its own `group_id` and saved source batch/variation link. Group numbers remain stable within a pack, even after deletion or reordering. A newly generated grid variation gets a new group and new sticker IDs; reanimating existing stickers keeps their group and sticker IDs.

S4 can exist in every group. Each occurrence is a different sticker with its own public code. Pack-wide display order is separate from source S# and group number.

### Preset persistence

- Save preset key/version, a snapshot of all nine ordered actions, emojis, source S#, group number, and allocated sticker IDs before export.
- Updating a preset creates a new version. Old groups retain their saved snapshots.
- Build image and motion prompts from stored actions; never guess labels again during export.
- An animation preserves the source sticker's action. Record reviewed label corrections as metadata revisions.
- When rebuilding a video sheet from approved stickers, save its position → original sticker-ID/S# mapping.
- Store pack membership/order by sticker ID. Never renumber original cells to fill rejected slots.

## 5. Export manifest and exact file lookup

Include `manifest.json` in pack ZIPs. Keep pack/group identity separate from sticker and asset identity.

Illustrative structure (replace example asset IDs/checksums with actual values):

```json
{
  "schema_version": 2,
  "export_id": "export-example-001",
  "pack": {
    "pack_id": "pack-example-001",
    "slug": "falcon",
    "title": "Falcon"
  },
  "groups": [
    {
      "group_id": "group-example-001",
      "group_number": 1,
      "preset_key": "custom-nine",
      "preset_version": 1,
      "source_batch_id": "G###",
      "variation_number": 4
    }
  ],
  "assets": [
    {
      "sticker_id": "AH43",
      "asset_id": "asset-example-001",
      "group_id": "group-example-001",
      "group_number": 1,
      "sticker_number": 4,
      "action": "laugh",
      "media": "video",
      "revision": 2,
      "export_date": "20261008",
      "filename": "AH43-falcon-laugh-s04-video-g01-20261008.webm",
      "mime_type": "video/webm",
      "sha256": "<actual-sha256>",
      "title": "Laughing Falcon",
      "emojis": ["😂", "🤣"],
      "tags": ["falcon", "laugh", "funny"],
      "original_action": "laughing"
    }
  ],
  "sticker_order": ["AH43"]
}
```

The manifest's `sticker_id` is the public filename code; retain the internal sticker primary key separately if different.

Postgres must preserve these relationships:

| Record | Required information |
|---|---|
| Pack | Internal ID, slug, title, owner, ordered membership |
| Group | Internal ID, pack ID, stable group number, preset snapshot/version, source batch, variation |
| Sticker | Internal ID, unique public code, source group/S#, canonical action, emojis, title/tags |
| Asset | Unique asset ID, sticker ID, media, revision, date, filename, MIME type, checksum, storage path |

Use uniqueness constraints for public sticker code, group number within a pack, source S# within a group, and `(sticker_id, media, revision)`. Keep this compatible with existing tables rather than replacing the storage design.

API lookup by `AH43` returns the sticker and its related assets. Lookup by `asset_id` returns the exact file version. Use existing API route conventions. When filenames lack a manifest, use sticker ID plus media/date/checksum to match registered assets; ambiguous matches require review.

## 6. Dashboard and legacy imports

Prefill “Assign to emoji,” “Title,” and “Add Tags” from saved metadata.

| Dashboard field | Example |
|---|---|
| Assign to emoji | 😂; also 🤣 if multiple associations are supported |
| Title | Laughing Falcon |
| Add Tags | falcon, laugh, funny |
| Source lookup | AH43 → Falcon → g01 → S4 → video asset |

Import flow:

1. Read the manifest when available.
2. Resolve sticker and asset IDs through the authenticated API.
3. Validate group, S#, action, media, date, and file checksum.
4. Prefill editable emoji/title/tags.
5. Treat an identical asset ID/checksum as a duplicate.
6. Flag missing, conflicting, or ambiguous identities for review.

For legacy names, resolve existing source records before assigning persistent sticker codes. Never infer cell order from filenames sorted alphabetically. Normalize aliases such as `laughing → laugh`, `eye_roll → eye-roll`, `flexing → flex`, `open_arms → hug`, `sneezing → sneeze`, and `thank_you → thanks`. Map “scream” contextually to `scared` or `surprised`, retaining “scream” as a tag.

Keep old filenames as aliases and create an old-name → new-name migration map. Rename exported copies without destructively renaming source media under `out/`. Preserve unknown legacy timestamps; do not assume their timezone.

Register manually imported external files using the existing import workflow. Allocate new logical sticker identities unless they are verified versions of existing stickers.

## 7. Export checklist

- Export approved or explicitly allowed assets using existing review gates.
- Validate all nine source slots against the saved preset; rejected cells never shift other identities.
- Preserve sticker IDs across static/video derivation and editing.
- Different logical stickers have different IDs, even with identical actions.
- Group numbers describe source grids; revisions remain in metadata.
- Repeated downloads preserve names, dates, versions, and bytes.
- Register complete manifests before exposing downloads.
- Keep exact asset versions separate, including same-day versions with matching filenames.
- Retain 30 canonical labels, preset snapshots, original S#, and pack membership order.
- Continue existing Telegram media validation and the project's static/video delivery behavior.
- Codes survive renames, restore, restart, and Postgres mirror rebuild; deleted codes remain reserved.

## 8. Review against the repo (2026-10-08, blocking before any build)

What is sound: `g01` is explicitly not the batch id `G###` (no collision with rule 9); S# stability ("S4 stays S4", no compression) matches rule 10; the Telegram facts are right (1–20 emoji per sticker, WEBM/PNG/WEBP, MP4 is not a sticker format); manifest-first lookup by `asset_id` + checksum (never filename parsing) is the right call; never-reused codes match the purge-ledger philosophy (a purged number stays taken).

What must be settled first:

1. **Scope the filenames to export ZIPs.** Rule 9 fixes the internal names (`{media}-{subject}-{action}[-{pack}]-{UTC time}-{hash}.{ext}` in `out/G00N/slices/`). The ban on "random hash suffixes" and the date token contradict it unless the new names apply only inside export ZIPs/manifests. Internal `out/` names stay untouched.
2. **`schema_version: 2` is wrong.** No versioned manifest exists: batch exports write `{batch, prompt, count, stickers}` (`flow/batches.py` `export_zip`), pack exports `{pack, id, count, stickers}` (`media/library.py`). A new manifest starts at version 1 with a migration from the current unversioned shape.
3. **File store stays primary.** `docs/store-and-search.md`: the file store is the record, Postgres mirrors it, the app works without the database. §2 rule 8 ("allocate through one coordinating service with a global DB uniqueness constraint; when Postgres is unavailable, defer new allocations") inverts that and makes export depend on Postgres. Allocation must work offline (file-backed, under the writer lock) with the DB constraint as backstop only.
4. **New records need a storage decision.** `docs/engine-and-studio.md` documents that there is no packs/pack-sticker table in Postgres (a pack is `library.json`). Pack/group/sticker/asset records either extend `library.json` (file-primary) or come with numbered, re-runnable migrations. Sticker codes in `result.json` need a `pipeline.normalise` default (like `tags`/`review`), write-through in `store/sync.py`, and a Haitham-accepted storage shape first.
5. **Presets are a new prompter surface.** Prompt building is template-locked (new versions only, never edit a used one). Four preset grids + custom presets + the 30-name bank + alias normalisation overlap `generation/prompter.py`, `generation/styles.py` and per-cell tags/emoji, and "unknown actions wait for an exporter choice" is a new UI surface. None of it is specced against the existing templates.
6. **Import prefill is unbuilt.** Title exists (`pipeline.set_titles`), emoji/tags exist per sticker, but manifest-driven prefill, the legacy alias map and the old→new migration map do not; `flow/imports.py` knows jobs/generations/effects, not sticker codes.
7. **Open details:** which gate records a canonical-action correction; how group numbers survive a pack merge; whether groups share the never-reuse rule; the exact code alphabet (exclusions from the `A–Z0–9` set must be stated, with capacity recomputed).

