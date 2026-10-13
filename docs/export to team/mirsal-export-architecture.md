# Mirsal Sticker Export — Internal Architecture

**Audience:** Mirsal Builder / API maintainers. **Status:** filename format FINAL (Haitham 2026-10-08); export-to-ZIP built the same day. Expanded-bank resolution, complete-sequence validation and persisted export interpretations are built (2026-10-11). Public short codes, asset revisions and pack-generation wiring remain open; current ZIPs use `G###` and revision 1. The old `AH43`-pack-code scheme is retired.

## 1. Canonical file name

Every sticker file exported in a ZIP is renamed inside the ZIP only; source media under `out/` keeps its engine names (rule 9). The final contract is below; its public-code examples illustrate the pending allocator. Current ZIPs put the internal `G###` in the `id` field:

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

`multi_action_tag` is built as: lowercase primary token, then its alias tokens, then up to three further whole key/tag hits with their aliases (`canonical_all`, at most 4 hits), joined with single `_`. A sticker asked for as `bus emojis that is happy` with tags `bus`, `happy`, `laugh` saves `bus_happy_smile_joy_laugh_laughing_lol_rofl_lmao_lmfao`: the subject AND the moods, each with its required aliases. Split-word hits never become extras (`eye_roll` stays eye-roll alone). Alias tokens are normalized before joining so the separator is unambiguous: **inner underscores, hyphens and spaces are removed** (`thank_you` → `thankyou`, `eye_roll` → `eyeroll`, `open_arms` → `openarms`, `thumbs_up` → `thumbsup`, `face_palm` → `facepalm`). Empty tokens are dropped; a sticker with no alias still carries its canonical token alone.

Filenames use hyphens as field delimiters and no field contains one (slugs are snake_case; the `eye-roll` / `star-struck` bank tokens are stored whole and split right-to-left: `date`, code, `sNN` are fixed shapes), so a filename splits back into its six fields; the manifest still stays authoritative — never alphabetical-order inference. An emoji may contain several Unicode code points (variation selectors, ZWJ sequences, skin tones): handle it as one grapheme string, never one character.

## 3. Dashboard / receiving app mapping

| Receiving behavior | Enabled by |
|---|---|
| Tap an emoji → every same-emotion sticker across all packs | Leading `emoji` field + manifest `emojis` array + tags carrying the literal glyph |
| Search `laugh` or `lmao` → all matching stickers (multi-choice) | `multi_action_tag` tokens + manifest `tags` array (canonical + aliases + literal emoji) |
| Pack menu / category | `pack_slug` (+ manifest pack record) |
| Title | Primary token (first tag segment: the subject when the sticker names one, else the mood) |
| Faster review: find the cell in the sheet | `position` (`s08`) + `id` (`G112`) → the exact source cell |
| Traceability / versions | `id` → Postgres `generations` row; `date` + manifest `revision` + `sha256` for exact versions |

Tags travel as an **array** in the manifest/DB; the underscore-joined filename segment is a serialization for the dashboard, never the source of truth.

## 4. IDs, lineage, and persistence

The existing identifiers remain intact: `G###` = generation batch, `S#` = original source cell, `J###` = paid job; `out/` records are the source of truth and Postgres mirrors them. The export uses the records that already exist:

| Record | Responsibility |
|---|---|
| Pack | Internal id (8-hex, as today), `slug`, title, owner, member source generations (each with its public code). No separate pack-code system. |
| Generation | Internal batch id (`G###`, the address everywhere inside the app) + one public `export_code` (`0000`–`zzzz`, §10), stored on `result.json` and mirrored to Postgres. One code per generation, never reused. |
| Sticker (library row) | Internal id (8-hex `sid`, as today), pack FK, `source {generation, index}`, name, emoji, file. Optional canonical `action` is saved by the library update API; derived aliases live in export resolution snapshots. |
| Asset (export row) | Sticker id, public `export_code` + source `G###`, `source_cell`, action, emoji(s), tags, media (derived from ext), revision, export date, filename, checksum. |

Suggested constraints: unique pack `slug` per owner; unique `export_code` across generations; unique `(export_code, source_cell, media, revision)` per asset. Multiple revisions on one date can share a display filename: keep each as a separate stored asset/export snapshot, disambiguated by the manifest row + checksum. Never reuse a retired code; codes survive renames, re-exports, restarts and restores. Sanitize everything user-supplied before it touches a path (no traversal).

## 5. Export pipeline

1. Use an approved `G###` batch / pack; existing gates, Telegram size/format validation and human approvals are unchanged.
2. Resolve the pack slug; enumerate source cells left-to-right/top-to-bottom as S1–S9. Skipped or rejected slots keep their numbers.
3. Resolve each cell's canonical action + full alias set from the bank (§6). A cell with no mapping exports on a deterministic fallback tag (key/tags words) and is flagged `unresolved: true` in the manifest — the exporter's bank picker UI is still open, so nothing is silently called an action.
4. Build one filename per asset from the six fields; write files into the ZIP under these names (sources untouched) with a UTF-8 `manifest.json` (schema version 1, §7).
5. Persist the resolved associations and diagnostics in `out/export_resolutions.json`; emit filename, date, revision 1 and file checksum in the manifest. An unchanged input reuses its interpretation. Asset revision storage and its Postgres mirror remain open; ZIP-container bytes are not frozen.

## 6. Canonical action bank (36 core + 1898 extended)

Human-readable home: [docs/emoji-bank.md](../emoji-bank.md) (core table, groups, readers). Code truth: `generation/actions.py`. This section stays the export contract.

Haitham, 2026-10-08: the bank grows from 30 to 36 core moods (rows 31–36 are new). 2026-10-11: the bank grows again with the §6b extended iOS bank (generated, exhaustive): every remaining base iOS emoji as a canonical token with its primary glyph and aliases. Default emoji are starting points, **not exclusive mappings** — the saved per-sticker emoji always wins. Other emoji, including ❤️, 😢 or 😂, stay valid associations.

**Binding:** every new sticker's primary emoji MUST be a well-established public iOS emoji — i.e. a member of this bank (core §6 or extended §6b). An unlisted glyph fails validation and the cell exports `unresolved: true` until a human picks from the bank. Lookups try the core bank first, then exact extended tokens, then extended aliases (`actions.py`: three-pass order). Ambiguous extended aliases return candidates; a valid saved emoji may disambiguate them. `is_ios_emoji` validates the complete leading cluster against Unicode 15.1 fully-qualified sequences, including supported skin-tone variants.

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

## 6b. Extended iOS emoji bank (generated, exhaustive)

Source: Unicode `emoji-test.txt` 15.1, `fully-qualified` rows only (the RGI set every
iOS emoji chat app shows), minus skin-tone variants for token construction. Validation uses the separate checked-in
`generation/emoji_sequences.json`: all 3,773 fully-qualified Unicode 15.1 sequences, including actual supported tones.
**1,898 extended tokens** plus the 36 core tokens in §6: 1,934 tokens representing 1,898 distinct base glyphs (core defaults overlap the extended bank).

**Rule (binding):** every new sticker's primary emoji MUST be a well-established public
iOS emoji — i.e. a member of this bank (core §6 or extended §6b). The exporter resolves the
primary through the core bank first, then exact extended tokens, then extended aliases
(`canonical_all` in `actions.py`); an unlisted glyph fails validation and the cell exports
`unresolved: true` until a human picks from the bank. Reusing an emoji across stickers is
allowed (e.g. core `gift` and extended `wrapped-gift` both use 🎁; lookups prefer the core
token). Next-batch bookkeeping (`next_tokens`, `used_tokens`) tracks moods only
(`canonical_mood`): one teddy pack shares its subject token, but each batch draws distinct
core moods.

**Worked example** — a user asks for `bus emojis that is happy`. The bus sticker saves with
the subject AND the moods (`bus emoji | happy | laugh` plus each token's required aliases):

```text
🚌-city-bus_happy_smile_joy_laugh_laughing_lol_rofl_lmao_lmfao-s03-<code>-<date>.webm
```

Searching `bus`, `happy` or `lmao` all find it (filename tag + manifest `tags` array).

**Worked example** — `school bus-statue-cherry` (three object stickers):

| Sticker words | Canonical token | Primary emoji | Aliases |
|---|---|---|---|
| school | `school` | 🏫 | school |
| bus | `bus` | 🚌 | bus |
| statue-of-liberty | `statue-of-liberty` | 🗽 | statue, liberty |
| cherries | `cherries` | 🍒 | cherries, cherry |
| cherry-blossom | `cherry-blossom` | 🌸 | cherry, blossom |

Filenames then lead with the literal glyph, e.g.
`🚌-city-school-bus_bus-stop-s03-<code>-<date>.webm`,
`🗽-city-liberty_statue_liberty-s04-<code>-<date>.png`,
`🍒-orchard-cherry_cherries-s05-<code>-<date>.webp`.

| Canonical token | Primary emoji | Aliases | Unicode name | Group |
|---|---|---|---|---|
| `grinning-face` | 😀 | grinning | grinning face | Smileys & Emotion |
| `grinning-face-with-big-eyes` | 😃 | grinning, big, eyes, eye | grinning face with big eyes | Smileys & Emotion |
| `grinning-face-with-smiling-eyes` | 😄 | grinning, smiling, eyes, eye | grinning face with smiling eyes | Smileys & Emotion |
| `beaming-face-with-smiling-eyes` | 😁 | beaming, smiling, eyes, eye | beaming face with smiling eyes | Smileys & Emotion |
| `grinning-squinting-face` | 😆 | grinning, squinting | grinning squinting face | Smileys & Emotion |
| `grinning-face-with-sweat` | 😅 | grinning, sweat | grinning face with sweat | Smileys & Emotion |
| `rolling-on-the-floor-laughing` | 🤣 | rolling, floor, laughing | rolling on the floor laughing | Smileys & Emotion |
| `face-with-tears-of-joy` | 😂 | tears, tear, joy | face with tears of joy | Smileys & Emotion |
| `slightly-smiling-face` | 🙂 | slightly, smiling | slightly smiling face | Smileys & Emotion |
| `upside-down-face` | 🙃 | upside, down | upside-down face | Smileys & Emotion |
| `melting-face` | 🫠 | melting | melting face | Smileys & Emotion |
| `winking-face` | 😉 | winking | winking face | Smileys & Emotion |
| `smiling-face-with-smiling-eyes` | 😊 | smiling, eyes, eye | smiling face with smiling eyes | Smileys & Emotion |
| `smiling-face-with-halo` | 😇 | smiling, halo | smiling face with halo | Smileys & Emotion |
| `smiling-face-with-hearts` | 🥰 | smiling, hearts, heart | smiling face with hearts | Smileys & Emotion |
| `smiling-face-with-heart-eyes` | 😍 | smiling, heart, eyes, eye | smiling face with heart-eyes | Smileys & Emotion |
| `star-struck-1f929` | 🤩 | star, struck | star-struck | Smileys & Emotion |
| `face-blowing-a-kiss` | 😘 | blowing, kiss | face blowing a kiss | Smileys & Emotion |
| `kissing-face` | 😗 | kissing | kissing face | Smileys & Emotion |
| `smiling-face` | ☺️ | smiling | smiling face | Smileys & Emotion |
| `kissing-face-with-closed-eyes` | 😚 | kissing, closed, eyes, eye | kissing face with closed eyes | Smileys & Emotion |
| `kissing-face-with-smiling-eyes` | 😙 | kissing, smiling, eyes, eye | kissing face with smiling eyes | Smileys & Emotion |
| `smiling-face-with-tear` | 🥲 | smiling, tear | smiling face with tear | Smileys & Emotion |
| `face-savoring-food` | 😋 | savoring, food | face savoring food | Smileys & Emotion |
| `face-with-tongue` | 😛 | tongue | face with tongue | Smileys & Emotion |
| `winking-face-with-tongue` | 😜 | winking, tongue | winking face with tongue | Smileys & Emotion |
| `zany-face` | 🤪 | zany | zany face | Smileys & Emotion |
| `squinting-face-with-tongue` | 😝 | squinting, tongue | squinting face with tongue | Smileys & Emotion |
| `money-mouth-face` | 🤑 | money, mouth | money-mouth face | Smileys & Emotion |
| `smiling-face-with-open-hands` | 🤗 | smiling, open, hands, hand | smiling face with open hands | Smileys & Emotion |
| `face-with-hand-over-mouth` | 🤭 | hand, over, mouth | face with hand over mouth | Smileys & Emotion |
| `face-with-open-eyes-and-hand-over-mouth` | 🫢 | open, eyes, eye, hand, over, mouth | face with open eyes and hand over mouth | Smileys & Emotion |
| `face-with-peeking-eye` | 🫣 | peeking, eye | face with peeking eye | Smileys & Emotion |
| `shushing-face` | 🤫 | shushing | shushing face | Smileys & Emotion |
| `thinking-face` | 🤔 | thinking | thinking face | Smileys & Emotion |
| `saluting-face` | 🫡 | saluting | saluting face | Smileys & Emotion |
| `zipper-mouth-face` | 🤐 | zipper, mouth | zipper-mouth face | Smileys & Emotion |
| `face-with-raised-eyebrow` | 🤨 | raised, eyebrow | face with raised eyebrow | Smileys & Emotion |
| `neutral-face` | 😐 | neutral | neutral face | Smileys & Emotion |
| `expressionless-face` | 😑 | expressionless | expressionless face | Smileys & Emotion |
| `face-without-mouth` | 😶 | without, mouth | face without mouth | Smileys & Emotion |
| `dotted-line-face` | 🫥 | dotted, line | dotted line face | Smileys & Emotion |
| `face-in-clouds` | 😶‍🌫️ | clouds, cloud | face in clouds | Smileys & Emotion |
| `smirking-face` | 😏 | smirking | smirking face | Smileys & Emotion |
| `unamused-face` | 😒 | unamused | unamused face | Smileys & Emotion |
| `face-with-rolling-eyes` | 🙄 | rolling, eyes, eye | face with rolling eyes | Smileys & Emotion |
| `grimacing-face` | 😬 | grimacing | grimacing face | Smileys & Emotion |
| `face-exhaling` | 😮‍💨 | exhaling | face exhaling | Smileys & Emotion |
| `lying-face` | 🤥 | lying | lying face | Smileys & Emotion |
| `shaking-face` | 🫨 | shaking | shaking face | Smileys & Emotion |
| `head-shaking-horizontally` | 🙂‍↔️ | head, shaking, horizontally | head shaking horizontally | Smileys & Emotion |
| `head-shaking-vertically` | 🙂‍↕️ | head, shaking, vertically | head shaking vertically | Smileys & Emotion |
| `relieved-face` | 😌 | relieved | relieved face | Smileys & Emotion |
| `pensive-face` | 😔 | pensive | pensive face | Smileys & Emotion |
| `sleepy-face` | 😪 | sleepy | sleepy face | Smileys & Emotion |
| `drooling-face` | 🤤 | drooling | drooling face | Smileys & Emotion |
| `sleeping-face` | 😴 | sleeping | sleeping face | Smileys & Emotion |
| `face-with-medical-mask` | 😷 | medical, mask | face with medical mask | Smileys & Emotion |
| `face-with-thermometer` | 🤒 | thermometer | face with thermometer | Smileys & Emotion |
| `face-with-head-bandage` | 🤕 | head, bandage | face with head-bandage | Smileys & Emotion |
| `nauseated-face` | 🤢 | nauseated | nauseated face | Smileys & Emotion |
| `face-vomiting` | 🤮 | vomiting | face vomiting | Smileys & Emotion |
| `sneezing-face` | 🤧 | sneezing | sneezing face | Smileys & Emotion |
| `hot-face` | 🥵 | hot | hot face | Smileys & Emotion |
| `cold-face` | 🥶 | cold | cold face | Smileys & Emotion |
| `woozy-face` | 🥴 | woozy | woozy face | Smileys & Emotion |
| `face-with-crossed-out-eyes` | 😵 | crossed, out, eyes, eye | face with crossed-out eyes | Smileys & Emotion |
| `face-with-spiral-eyes` | 😵‍💫 | spiral, eyes, eye | face with spiral eyes | Smileys & Emotion |
| `exploding-head` | 🤯 | exploding, head | exploding head | Smileys & Emotion |
| `cowboy-hat-face` | 🤠 | cowboy, hat | cowboy hat face | Smileys & Emotion |
| `partying-face` | 🥳 | partying | partying face | Smileys & Emotion |
| `disguised-face` | 🥸 | disguised | disguised face | Smileys & Emotion |
| `smiling-face-with-sunglasses` | 😎 | smiling, sunglasses, sunglass | smiling face with sunglasses | Smileys & Emotion |
| `nerd-face` | 🤓 | nerd | nerd face | Smileys & Emotion |
| `face-with-monocle` | 🧐 | monocle | face with monocle | Smileys & Emotion |
| `confused-face` | 😕 | confused | confused face | Smileys & Emotion |
| `face-with-diagonal-mouth` | 🫤 | diagonal, mouth | face with diagonal mouth | Smileys & Emotion |
| `worried-face` | 😟 | worried | worried face | Smileys & Emotion |
| `slightly-frowning-face` | 🙁 | slightly, frowning | slightly frowning face | Smileys & Emotion |
| `frowning-face` | ☹️ | frowning | frowning face | Smileys & Emotion |
| `face-with-open-mouth` | 😮 | open, mouth | face with open mouth | Smileys & Emotion |
| `hushed-face` | 😯 | hushed | hushed face | Smileys & Emotion |
| `astonished-face` | 😲 | astonished | astonished face | Smileys & Emotion |
| `flushed-face` | 😳 | flushed | flushed face | Smileys & Emotion |
| `pleading-face` | 🥺 | pleading | pleading face | Smileys & Emotion |
| `face-holding-back-tears` | 🥹 | holding, back, tears, tear | face holding back tears | Smileys & Emotion |
| `frowning-face-with-open-mouth` | 😦 | frowning, open, mouth | frowning face with open mouth | Smileys & Emotion |
| `anguished-face` | 😧 | anguished | anguished face | Smileys & Emotion |
| `fearful-face` | 😨 | fearful | fearful face | Smileys & Emotion |
| `anxious-face-with-sweat` | 😰 | anxious, sweat | anxious face with sweat | Smileys & Emotion |
| `sad-but-relieved-face` | 😥 | sad, but, relieved | sad but relieved face | Smileys & Emotion |
| `crying-face` | 😢 | crying | crying face | Smileys & Emotion |
| `loudly-crying-face` | 😭 | loudly, crying | loudly crying face | Smileys & Emotion |
| `face-screaming-in-fear` | 😱 | screaming, fear | face screaming in fear | Smileys & Emotion |
| `confounded-face` | 😖 | confounded | confounded face | Smileys & Emotion |
| `persevering-face` | 😣 | persevering | persevering face | Smileys & Emotion |
| `disappointed-face` | 😞 | disappointed | disappointed face | Smileys & Emotion |
| `downcast-face-with-sweat` | 😓 | downcast, sweat | downcast face with sweat | Smileys & Emotion |
| `weary-face` | 😩 | weary | weary face | Smileys & Emotion |
| `tired-face` | 😫 | tired | tired face | Smileys & Emotion |
| `yawning-face` | 🥱 | yawning | yawning face | Smileys & Emotion |
| `face-with-steam-from-nose` | 😤 | steam, nose | face with steam from nose | Smileys & Emotion |
| `enraged-face` | 😡 | enraged | enraged face | Smileys & Emotion |
| `angry-face` | 😠 | angry | angry face | Smileys & Emotion |
| `face-with-symbols-on-mouth` | 🤬 | symbols, symbol, mouth | face with symbols on mouth | Smileys & Emotion |
| `smiling-face-with-horns` | 😈 | smiling, horns, horn | smiling face with horns | Smileys & Emotion |
| `angry-face-with-horns` | 👿 | angry, horns, horn | angry face with horns | Smileys & Emotion |
| `skull` | 💀 | skull | skull | Smileys & Emotion |
| `skull-and-crossbones` | ☠️ | skull, crossbones, crossbone | skull and crossbones | Smileys & Emotion |
| `pile-of-poo` | 💩 | pile, poo | pile of poo | Smileys & Emotion |
| `clown-face` | 🤡 | clown | clown face | Smileys & Emotion |
| `ogre` | 👹 | ogre | ogre | Smileys & Emotion |
| `goblin` | 👺 | goblin | goblin | Smileys & Emotion |
| `ghost` | 👻 | ghost | ghost | Smileys & Emotion |
| `alien` | 👽 | alien | alien | Smileys & Emotion |
| `alien-monster` | 👾 | alien, monster | alien monster | Smileys & Emotion |
| `robot` | 🤖 | robot | robot | Smileys & Emotion |
| `grinning-cat` | 😺 | grinning, cat | grinning cat | Smileys & Emotion |
| `grinning-cat-with-smiling-eyes` | 😸 | grinning, cat, smiling, eyes, eye | grinning cat with smiling eyes | Smileys & Emotion |
| `cat-with-tears-of-joy` | 😹 | cat, tears, tear, joy | cat with tears of joy | Smileys & Emotion |
| `smiling-cat-with-heart-eyes` | 😻 | smiling, cat, heart, eyes, eye | smiling cat with heart-eyes | Smileys & Emotion |
| `cat-with-wry-smile` | 😼 | cat, wry, smile | cat with wry smile | Smileys & Emotion |
| `kissing-cat` | 😽 | kissing, cat | kissing cat | Smileys & Emotion |
| `weary-cat` | 🙀 | weary, cat | weary cat | Smileys & Emotion |
| `crying-cat` | 😿 | crying, cat | crying cat | Smileys & Emotion |
| `pouting-cat` | 😾 | pouting, cat | pouting cat | Smileys & Emotion |
| `see-no-evil-monkey` | 🙈 | see, no, evil, monkey | see-no-evil monkey | Smileys & Emotion |
| `hear-no-evil-monkey` | 🙉 | hear, no, evil, monkey | hear-no-evil monkey | Smileys & Emotion |
| `speak-no-evil-monkey` | 🙊 | speak, no, evil, monkey | speak-no-evil monkey | Smileys & Emotion |
| `love-letter` | 💌 | love, letter | love letter | Smileys & Emotion |
| `heart-with-arrow` | 💘 | heart, arrow | heart with arrow | Smileys & Emotion |
| `heart-with-ribbon` | 💝 | heart, ribbon | heart with ribbon | Smileys & Emotion |
| `sparkling-heart` | 💖 | sparkling, heart | sparkling heart | Smileys & Emotion |
| `growing-heart` | 💗 | growing, heart | growing heart | Smileys & Emotion |
| `beating-heart` | 💓 | beating, heart | beating heart | Smileys & Emotion |
| `revolving-hearts` | 💞 | revolving, hearts, heart | revolving hearts | Smileys & Emotion |
| `two-hearts` | 💕 | hearts, heart | two hearts | Smileys & Emotion |
| `heart-decoration` | 💟 | heart, decoration | heart decoration | Smileys & Emotion |
| `heart-exclamation` | ❣️ | heart, exclamation | heart exclamation | Smileys & Emotion |
| `broken-heart` | 💔 | broken, heart | broken heart | Smileys & Emotion |
| `heart-on-fire` | ❤️‍🔥 | heart, fire | heart on fire | Smileys & Emotion |
| `mending-heart` | ❤️‍🩹 | mending, heart | mending heart | Smileys & Emotion |
| `red-heart` | ❤️ | red, heart | red heart | Smileys & Emotion |
| `pink-heart` | 🩷 | pink, heart | pink heart | Smileys & Emotion |
| `orange-heart` | 🧡 | orange, heart | orange heart | Smileys & Emotion |
| `yellow-heart` | 💛 | yellow, heart | yellow heart | Smileys & Emotion |
| `green-heart` | 💚 | green, heart | green heart | Smileys & Emotion |
| `blue-heart` | 💙 | blue, heart | blue heart | Smileys & Emotion |
| `light-blue-heart` | 🩵 | light, blue, heart | light blue heart | Smileys & Emotion |
| `purple-heart` | 💜 | purple, heart | purple heart | Smileys & Emotion |
| `brown-heart` | 🤎 | brown, heart | brown heart | Smileys & Emotion |
| `black-heart` | 🖤 | black, heart | black heart | Smileys & Emotion |
| `grey-heart` | 🩶 | grey, heart | grey heart | Smileys & Emotion |
| `white-heart` | 🤍 | white, heart | white heart | Smileys & Emotion |
| `kiss-mark` | 💋 | kiss, mark | kiss mark | Smileys & Emotion |
| `hundred-points` | 💯 | points, point | hundred points | Smileys & Emotion |
| `anger-symbol` | 💢 | anger | anger symbol | Smileys & Emotion |
| `collision` | 💥 | collision | collision | Smileys & Emotion |
| `dizzy` | 💫 | dizzy | dizzy | Smileys & Emotion |
| `sweat-droplets` | 💦 | sweat, droplets, droplet | sweat droplets | Smileys & Emotion |
| `dashing-away` | 💨 | dashing, away | dashing away | Smileys & Emotion |
| `hole` | 🕳️ | hole | hole | Smileys & Emotion |
| `speech-balloon` | 💬 | speech, balloon | speech balloon | Smileys & Emotion |
| `eye-in-speech-bubble` | 👁️‍🗨️ | eye, speech, bubble | eye in speech bubble | Smileys & Emotion |
| `left-speech-bubble` | 🗨️ | left, speech, bubble | left speech bubble | Smileys & Emotion |
| `right-anger-bubble` | 🗯️ | right, anger, bubble | right anger bubble | Smileys & Emotion |
| `thought-balloon` | 💭 | thought, balloon | thought balloon | Smileys & Emotion |
| `zzz` | 💤 | zzz | ZZZ | Smileys & Emotion |
| `waving-hand` | 👋 | waving, hand | waving hand | People & Body |
| `raised-back-of-hand` | 🤚 | raised, back, hand | raised back of hand | People & Body |
| `hand-with-fingers-splayed` | 🖐️ | hand, fingers, finger, splayed | hand with fingers splayed | People & Body |
| `raised-hand` | ✋ | raised, hand | raised hand | People & Body |
| `vulcan-salute` | 🖖 | vulcan, salute | vulcan salute | People & Body |
| `rightwards-hand` | 🫱 | rightwards, rightward, hand | rightwards hand | People & Body |
| `leftwards-hand` | 🫲 | leftwards, leftward, hand | leftwards hand | People & Body |
| `palm-down-hand` | 🫳 | palm, down, hand | palm down hand | People & Body |
| `palm-up-hand` | 🫴 | palm, up, hand | palm up hand | People & Body |
| `leftwards-pushing-hand` | 🫷 | leftwards, leftward, pushing, hand | leftwards pushing hand | People & Body |
| `rightwards-pushing-hand` | 🫸 | rightwards, rightward, pushing, hand | rightwards pushing hand | People & Body |
| `ok-hand` | 👌 | ok, hand | OK hand | People & Body |
| `pinched-fingers` | 🤌 | pinched, fingers, finger | pinched fingers | People & Body |
| `pinching-hand` | 🤏 | pinching, hand | pinching hand | People & Body |
| `victory-hand` | ✌️ | victory, hand | victory hand | People & Body |
| `crossed-fingers` | 🤞 | crossed, fingers, finger | crossed fingers | People & Body |
| `hand-with-index-finger-and-thumb-crossed` | 🫰 | hand, index, finger, thumb, crossed | hand with index finger and thumb crossed | People & Body |
| `love-you-gesture` | 🤟 | love, you, gesture | love-you gesture | People & Body |
| `sign-of-the-horns` | 🤘 | horns, horn | sign of the horns | People & Body |
| `call-me-hand` | 🤙 | call, me, hand | call me hand | People & Body |
| `backhand-index-pointing-left` | 👈 | backhand, index, pointing, left | backhand index pointing left | People & Body |
| `backhand-index-pointing-right` | 👉 | backhand, index, pointing, right | backhand index pointing right | People & Body |
| `backhand-index-pointing-up` | 👆 | backhand, index, pointing, up | backhand index pointing up | People & Body |
| `middle-finger` | 🖕 | middle, finger | middle finger | People & Body |
| `backhand-index-pointing-down` | 👇 | backhand, index, pointing, down | backhand index pointing down | People & Body |
| `index-pointing-up` | ☝️ | index, pointing, up | index pointing up | People & Body |
| `index-pointing-at-the-viewer` | 🫵 | index, pointing, at, viewer | index pointing at the viewer | People & Body |
| `thumbs-up` | 👍 | thumbs, thumb, up | thumbs up | People & Body |
| `thumbs-down` | 👎 | thumbs, thumb, down | thumbs down | People & Body |
| `raised-fist` | ✊ | raised, fist | raised fist | People & Body |
| `oncoming-fist` | 👊 | oncoming, fist | oncoming fist | People & Body |
| `left-facing-fist` | 🤛 | left, facing, fist | left-facing fist | People & Body |
| `right-facing-fist` | 🤜 | right, facing, fist | right-facing fist | People & Body |
| `clapping-hands` | 👏 | clapping, hands, hand | clapping hands | People & Body |
| `raising-hands` | 🙌 | raising, hands, hand | raising hands | People & Body |
| `heart-hands` | 🫶 | heart, hands, hand | heart hands | People & Body |
| `open-hands` | 👐 | open, hands, hand | open hands | People & Body |
| `palms-up-together` | 🤲 | palms, palm, up, together | palms up together | People & Body |
| `handshake` | 🤝 | handshake | handshake | People & Body |
| `folded-hands` | 🙏 | folded, hands, hand | folded hands | People & Body |
| `writing-hand` | ✍️ | writing, hand | writing hand | People & Body |
| `nail-polish` | 💅 | nail, polish | nail polish | People & Body |
| `selfie` | 🤳 | selfie | selfie | People & Body |
| `flexed-biceps` | 💪 | flexed, biceps, bicep | flexed biceps | People & Body |
| `mechanical-arm` | 🦾 | mechanical, arm | mechanical arm | People & Body |
| `mechanical-leg` | 🦿 | mechanical, leg | mechanical leg | People & Body |
| `leg` | 🦵 | leg | leg | People & Body |
| `foot` | 🦶 | foot | foot | People & Body |
| `ear` | 👂 | ear | ear | People & Body |
| `ear-with-hearing-aid` | 🦻 | ear, hearing, aid | ear with hearing aid | People & Body |
| `nose` | 👃 | nose | nose | People & Body |
| `brain` | 🧠 | brain | brain | People & Body |
| `anatomical-heart` | 🫀 | anatomical, heart | anatomical heart | People & Body |
| `lungs` | 🫁 | lungs, lung | lungs | People & Body |
| `tooth` | 🦷 | tooth | tooth | People & Body |
| `bone` | 🦴 | bone | bone | People & Body |
| `eyes` | 👀 | eyes, eye | eyes | People & Body |
| `eye` | 👁️ | eye | eye | People & Body |
| `tongue` | 👅 | tongue | tongue | People & Body |
| `mouth` | 👄 | mouth | mouth | People & Body |
| `biting-lip` | 🫦 | biting, lip | biting lip | People & Body |
| `baby` | 👶 | baby | baby | People & Body |
| `child` | 🧒 | child | child | People & Body |
| `boy` | 👦 | boy | boy | People & Body |
| `girl` | 👧 | girl | girl | People & Body |
| `person` | 🧑 | person | person | People & Body |
| `person-blond-hair` | 👱 | person, blond, hair | person: blond hair | People & Body |
| `man` | 👨 | man | man | People & Body |
| `person-beard` | 🧔 | person, beard | person: beard | People & Body |
| `man-beard` | 🧔‍♂️ | man, beard | man: beard | People & Body |
| `woman-beard` | 🧔‍♀️ | woman, beard | woman: beard | People & Body |
| `man-red-hair` | 👨‍🦰 | man, red, hair | man: red hair | People & Body |
| `man-curly-hair` | 👨‍🦱 | man, curly, hair | man: curly hair | People & Body |
| `man-white-hair` | 👨‍🦳 | man, white, hair | man: white hair | People & Body |
| `man-bald` | 👨‍🦲 | man, bald | man: bald | People & Body |
| `woman` | 👩 | woman | woman | People & Body |
| `woman-red-hair` | 👩‍🦰 | woman, red, hair | woman: red hair | People & Body |
| `person-red-hair` | 🧑‍🦰 | person, red, hair | person: red hair | People & Body |
| `woman-curly-hair` | 👩‍🦱 | woman, curly, hair | woman: curly hair | People & Body |
| `person-curly-hair` | 🧑‍🦱 | person, curly, hair | person: curly hair | People & Body |
| `woman-white-hair` | 👩‍🦳 | woman, white, hair | woman: white hair | People & Body |
| `person-white-hair` | 🧑‍🦳 | person, white, hair | person: white hair | People & Body |
| `woman-bald` | 👩‍🦲 | woman, bald | woman: bald | People & Body |
| `person-bald` | 🧑‍🦲 | person, bald | person: bald | People & Body |
| `woman-blond-hair` | 👱‍♀️ | woman, blond, hair | woman: blond hair | People & Body |
| `man-blond-hair` | 👱‍♂️ | man, blond, hair | man: blond hair | People & Body |
| `older-person` | 🧓 | older, person | older person | People & Body |
| `old-man` | 👴 | old, man | old man | People & Body |
| `old-woman` | 👵 | old, woman | old woman | People & Body |
| `person-frowning` | 🙍 | person, frowning | person frowning | People & Body |
| `man-frowning` | 🙍‍♂️ | man, frowning | man frowning | People & Body |
| `woman-frowning` | 🙍‍♀️ | woman, frowning | woman frowning | People & Body |
| `person-pouting` | 🙎 | person, pouting | person pouting | People & Body |
| `man-pouting` | 🙎‍♂️ | man, pouting | man pouting | People & Body |
| `woman-pouting` | 🙎‍♀️ | woman, pouting | woman pouting | People & Body |
| `person-gesturing-no` | 🙅 | person, gesturing, no | person gesturing NO | People & Body |
| `man-gesturing-no` | 🙅‍♂️ | man, gesturing, no | man gesturing NO | People & Body |
| `woman-gesturing-no` | 🙅‍♀️ | woman, gesturing, no | woman gesturing NO | People & Body |
| `person-gesturing-ok` | 🙆 | person, gesturing, ok | person gesturing OK | People & Body |
| `man-gesturing-ok` | 🙆‍♂️ | man, gesturing, ok | man gesturing OK | People & Body |
| `woman-gesturing-ok` | 🙆‍♀️ | woman, gesturing, ok | woman gesturing OK | People & Body |
| `person-tipping-hand` | 💁 | person, tipping, hand | person tipping hand | People & Body |
| `man-tipping-hand` | 💁‍♂️ | man, tipping, hand | man tipping hand | People & Body |
| `woman-tipping-hand` | 💁‍♀️ | woman, tipping, hand | woman tipping hand | People & Body |
| `person-raising-hand` | 🙋 | person, raising, hand | person raising hand | People & Body |
| `man-raising-hand` | 🙋‍♂️ | man, raising, hand | man raising hand | People & Body |
| `woman-raising-hand` | 🙋‍♀️ | woman, raising, hand | woman raising hand | People & Body |
| `deaf-person` | 🧏 | deaf, person | deaf person | People & Body |
| `deaf-man` | 🧏‍♂️ | deaf, man | deaf man | People & Body |
| `deaf-woman` | 🧏‍♀️ | deaf, woman | deaf woman | People & Body |
| `person-bowing` | 🙇 | person, bowing | person bowing | People & Body |
| `man-bowing` | 🙇‍♂️ | man, bowing | man bowing | People & Body |
| `woman-bowing` | 🙇‍♀️ | woman, bowing | woman bowing | People & Body |
| `person-facepalming` | 🤦 | person, facepalming | person facepalming | People & Body |
| `man-facepalming` | 🤦‍♂️ | man, facepalming | man facepalming | People & Body |
| `woman-facepalming` | 🤦‍♀️ | woman, facepalming | woman facepalming | People & Body |
| `person-shrugging` | 🤷 | person, shrugging | person shrugging | People & Body |
| `man-shrugging` | 🤷‍♂️ | man, shrugging | man shrugging | People & Body |
| `woman-shrugging` | 🤷‍♀️ | woman, shrugging | woman shrugging | People & Body |
| `health-worker` | 🧑‍⚕️ | health, worker | health worker | People & Body |
| `man-health-worker` | 👨‍⚕️ | man, health, worker | man health worker | People & Body |
| `woman-health-worker` | 👩‍⚕️ | woman, health, worker | woman health worker | People & Body |
| `student` | 🧑‍🎓 | student | student | People & Body |
| `man-student` | 👨‍🎓 | man, student | man student | People & Body |
| `woman-student` | 👩‍🎓 | woman, student | woman student | People & Body |
| `teacher` | 🧑‍🏫 | teacher | teacher | People & Body |
| `man-teacher` | 👨‍🏫 | man, teacher | man teacher | People & Body |
| `woman-teacher` | 👩‍🏫 | woman, teacher | woman teacher | People & Body |
| `judge` | 🧑‍⚖️ | judge | judge | People & Body |
| `man-judge` | 👨‍⚖️ | man, judge | man judge | People & Body |
| `woman-judge` | 👩‍⚖️ | woman, judge | woman judge | People & Body |
| `farmer` | 🧑‍🌾 | farmer | farmer | People & Body |
| `man-farmer` | 👨‍🌾 | man, farmer | man farmer | People & Body |
| `woman-farmer` | 👩‍🌾 | woman, farmer | woman farmer | People & Body |
| `cook` | 🧑‍🍳 | cook | cook | People & Body |
| `man-cook` | 👨‍🍳 | man, cook | man cook | People & Body |
| `woman-cook` | 👩‍🍳 | woman, cook | woman cook | People & Body |
| `mechanic` | 🧑‍🔧 | mechanic | mechanic | People & Body |
| `man-mechanic` | 👨‍🔧 | man, mechanic | man mechanic | People & Body |
| `woman-mechanic` | 👩‍🔧 | woman, mechanic | woman mechanic | People & Body |
| `factory-worker` | 🧑‍🏭 | factory, worker | factory worker | People & Body |
| `man-factory-worker` | 👨‍🏭 | man, factory, worker | man factory worker | People & Body |
| `woman-factory-worker` | 👩‍🏭 | woman, factory, worker | woman factory worker | People & Body |
| `office-worker` | 🧑‍💼 | office, worker | office worker | People & Body |
| `man-office-worker` | 👨‍💼 | man, office, worker | man office worker | People & Body |
| `woman-office-worker` | 👩‍💼 | woman, office, worker | woman office worker | People & Body |
| `scientist` | 🧑‍🔬 | scientist | scientist | People & Body |
| `man-scientist` | 👨‍🔬 | man, scientist | man scientist | People & Body |
| `woman-scientist` | 👩‍🔬 | woman, scientist | woman scientist | People & Body |
| `technologist` | 🧑‍💻 | technologist | technologist | People & Body |
| `man-technologist` | 👨‍💻 | man, technologist | man technologist | People & Body |
| `woman-technologist` | 👩‍💻 | woman, technologist | woman technologist | People & Body |
| `singer` | 🧑‍🎤 | singer | singer | People & Body |
| `man-singer` | 👨‍🎤 | man, singer | man singer | People & Body |
| `woman-singer` | 👩‍🎤 | woman, singer | woman singer | People & Body |
| `artist` | 🧑‍🎨 | artist | artist | People & Body |
| `man-artist` | 👨‍🎨 | man, artist | man artist | People & Body |
| `woman-artist` | 👩‍🎨 | woman, artist | woman artist | People & Body |
| `pilot` | 🧑‍✈️ | pilot | pilot | People & Body |
| `man-pilot` | 👨‍✈️ | man, pilot | man pilot | People & Body |
| `woman-pilot` | 👩‍✈️ | woman, pilot | woman pilot | People & Body |
| `astronaut` | 🧑‍🚀 | astronaut | astronaut | People & Body |
| `man-astronaut` | 👨‍🚀 | man, astronaut | man astronaut | People & Body |
| `woman-astronaut` | 👩‍🚀 | woman, astronaut | woman astronaut | People & Body |
| `firefighter` | 🧑‍🚒 | firefighter | firefighter | People & Body |
| `man-firefighter` | 👨‍🚒 | man, firefighter | man firefighter | People & Body |
| `woman-firefighter` | 👩‍🚒 | woman, firefighter | woman firefighter | People & Body |
| `police-officer` | 👮 | police, officer | police officer | People & Body |
| `man-police-officer` | 👮‍♂️ | man, police, officer | man police officer | People & Body |
| `woman-police-officer` | 👮‍♀️ | woman, police, officer | woman police officer | People & Body |
| `detective` | 🕵️ | detective | detective | People & Body |
| `man-detective` | 🕵️‍♂️ | man, detective | man detective | People & Body |
| `woman-detective` | 🕵️‍♀️ | woman, detective | woman detective | People & Body |
| `guard` | 💂 | guard | guard | People & Body |
| `man-guard` | 💂‍♂️ | man, guard | man guard | People & Body |
| `woman-guard` | 💂‍♀️ | woman, guard | woman guard | People & Body |
| `ninja` | 🥷 | ninja | ninja | People & Body |
| `construction-worker` | 👷 | construction, worker | construction worker | People & Body |
| `man-construction-worker` | 👷‍♂️ | man, construction, worker | man construction worker | People & Body |
| `woman-construction-worker` | 👷‍♀️ | woman, construction, worker | woman construction worker | People & Body |
| `person-with-crown` | 🫅 | person, crown | person with crown | People & Body |
| `prince` | 🤴 | prince | prince | People & Body |
| `princess` | 👸 | princess | princess | People & Body |
| `person-wearing-turban` | 👳 | person, wearing, turban | person wearing turban | People & Body |
| `man-wearing-turban` | 👳‍♂️ | man, wearing, turban | man wearing turban | People & Body |
| `woman-wearing-turban` | 👳‍♀️ | woman, wearing, turban | woman wearing turban | People & Body |
| `person-with-skullcap` | 👲 | person, skullcap | person with skullcap | People & Body |
| `woman-with-headscarf` | 🧕 | woman, headscarf | woman with headscarf | People & Body |
| `person-in-tuxedo` | 🤵 | person, tuxedo | person in tuxedo | People & Body |
| `man-in-tuxedo` | 🤵‍♂️ | man, tuxedo | man in tuxedo | People & Body |
| `woman-in-tuxedo` | 🤵‍♀️ | woman, tuxedo | woman in tuxedo | People & Body |
| `person-with-veil` | 👰 | person, veil | person with veil | People & Body |
| `man-with-veil` | 👰‍♂️ | man, veil | man with veil | People & Body |
| `woman-with-veil` | 👰‍♀️ | woman, veil | woman with veil | People & Body |
| `pregnant-woman` | 🤰 | pregnant, woman | pregnant woman | People & Body |
| `pregnant-man` | 🫃 | pregnant, man | pregnant man | People & Body |
| `pregnant-person` | 🫄 | pregnant, person | pregnant person | People & Body |
| `breast-feeding` | 🤱 | breast, feeding | breast-feeding | People & Body |
| `woman-feeding-baby` | 👩‍🍼 | woman, feeding, baby | woman feeding baby | People & Body |
| `man-feeding-baby` | 👨‍🍼 | man, feeding, baby | man feeding baby | People & Body |
| `person-feeding-baby` | 🧑‍🍼 | person, feeding, baby | person feeding baby | People & Body |
| `baby-angel` | 👼 | baby, angel | baby angel | People & Body |
| `santa-claus` | 🎅 | santa, claus | Santa Claus | People & Body |
| `mrs-claus` | 🤶 | mrs, claus | Mrs. Claus | People & Body |
| `mx-claus` | 🧑‍🎄 | mx, claus | mx claus | People & Body |
| `superhero` | 🦸 | superhero | superhero | People & Body |
| `man-superhero` | 🦸‍♂️ | man, superhero | man superhero | People & Body |
| `woman-superhero` | 🦸‍♀️ | woman, superhero | woman superhero | People & Body |
| `supervillain` | 🦹 | supervillain | supervillain | People & Body |
| `man-supervillain` | 🦹‍♂️ | man, supervillain | man supervillain | People & Body |
| `woman-supervillain` | 🦹‍♀️ | woman, supervillain | woman supervillain | People & Body |
| `mage` | 🧙 | mage | mage | People & Body |
| `man-mage` | 🧙‍♂️ | man, mage | man mage | People & Body |
| `woman-mage` | 🧙‍♀️ | woman, mage | woman mage | People & Body |
| `fairy` | 🧚 | fairy | fairy | People & Body |
| `man-fairy` | 🧚‍♂️ | man, fairy | man fairy | People & Body |
| `woman-fairy` | 🧚‍♀️ | woman, fairy | woman fairy | People & Body |
| `vampire` | 🧛 | vampire | vampire | People & Body |
| `man-vampire` | 🧛‍♂️ | man, vampire | man vampire | People & Body |
| `woman-vampire` | 🧛‍♀️ | woman, vampire | woman vampire | People & Body |
| `merperson` | 🧜 | merperson | merperson | People & Body |
| `merman` | 🧜‍♂️ | merman | merman | People & Body |
| `mermaid` | 🧜‍♀️ | mermaid | mermaid | People & Body |
| `elf` | 🧝 | elf | elf | People & Body |
| `man-elf` | 🧝‍♂️ | man, elf | man elf | People & Body |
| `woman-elf` | 🧝‍♀️ | woman, elf | woman elf | People & Body |
| `genie` | 🧞 | genie | genie | People & Body |
| `man-genie` | 🧞‍♂️ | man, genie | man genie | People & Body |
| `woman-genie` | 🧞‍♀️ | woman, genie | woman genie | People & Body |
| `zombie` | 🧟 | zombie | zombie | People & Body |
| `man-zombie` | 🧟‍♂️ | man, zombie | man zombie | People & Body |
| `woman-zombie` | 🧟‍♀️ | woman, zombie | woman zombie | People & Body |
| `troll` | 🧌 | troll | troll | People & Body |
| `person-getting-massage` | 💆 | person, getting, massage | person getting massage | People & Body |
| `man-getting-massage` | 💆‍♂️ | man, getting, massage | man getting massage | People & Body |
| `woman-getting-massage` | 💆‍♀️ | woman, getting, massage | woman getting massage | People & Body |
| `person-getting-haircut` | 💇 | person, getting, haircut | person getting haircut | People & Body |
| `man-getting-haircut` | 💇‍♂️ | man, getting, haircut | man getting haircut | People & Body |
| `woman-getting-haircut` | 💇‍♀️ | woman, getting, haircut | woman getting haircut | People & Body |
| `person-walking` | 🚶 | person, walking | person walking | People & Body |
| `man-walking` | 🚶‍♂️ | man, walking | man walking | People & Body |
| `woman-walking` | 🚶‍♀️ | woman, walking | woman walking | People & Body |
| `person-walking-facing-right` | 🚶‍➡️ | person, walking, facing, right | person walking facing right | People & Body |
| `woman-walking-facing-right` | 🚶‍♀️‍➡️ | woman, walking, facing, right | woman walking facing right | People & Body |
| `man-walking-facing-right` | 🚶‍♂️‍➡️ | man, walking, facing, right | man walking facing right | People & Body |
| `person-standing` | 🧍 | person, standing | person standing | People & Body |
| `man-standing` | 🧍‍♂️ | man, standing | man standing | People & Body |
| `woman-standing` | 🧍‍♀️ | woman, standing | woman standing | People & Body |
| `person-kneeling` | 🧎 | person, kneeling | person kneeling | People & Body |
| `man-kneeling` | 🧎‍♂️ | man, kneeling | man kneeling | People & Body |
| `woman-kneeling` | 🧎‍♀️ | woman, kneeling | woman kneeling | People & Body |
| `person-kneeling-facing-right` | 🧎‍➡️ | person, kneeling, facing, right | person kneeling facing right | People & Body |
| `woman-kneeling-facing-right` | 🧎‍♀️‍➡️ | woman, kneeling, facing, right | woman kneeling facing right | People & Body |
| `man-kneeling-facing-right` | 🧎‍♂️‍➡️ | man, kneeling, facing, right | man kneeling facing right | People & Body |
| `person-with-white-cane` | 🧑‍🦯 | person, white, cane | person with white cane | People & Body |
| `person-with-white-cane-facing-right` | 🧑‍🦯‍➡️ | person, white, cane, facing, right | person with white cane facing right | People & Body |
| `man-with-white-cane` | 👨‍🦯 | man, white, cane | man with white cane | People & Body |
| `man-with-white-cane-facing-right` | 👨‍🦯‍➡️ | man, white, cane, facing, right | man with white cane facing right | People & Body |
| `woman-with-white-cane` | 👩‍🦯 | woman, white, cane | woman with white cane | People & Body |
| `woman-with-white-cane-facing-right` | 👩‍🦯‍➡️ | woman, white, cane, facing, right | woman with white cane facing right | People & Body |
| `person-in-motorized-wheelchair` | 🧑‍🦼 | person, motorized, wheelchair | person in motorized wheelchair | People & Body |
| `person-in-motorized-wheelchair-facing-right` | 🧑‍🦼‍➡️ | person, motorized, wheelchair, facing, right | person in motorized wheelchair facing right | People & Body |
| `man-in-motorized-wheelchair` | 👨‍🦼 | man, motorized, wheelchair | man in motorized wheelchair | People & Body |
| `man-in-motorized-wheelchair-facing-right` | 👨‍🦼‍➡️ | man, motorized, wheelchair, facing, right | man in motorized wheelchair facing right | People & Body |
| `woman-in-motorized-wheelchair` | 👩‍🦼 | woman, motorized, wheelchair | woman in motorized wheelchair | People & Body |
| `woman-in-motorized-wheelchair-facing-right` | 👩‍🦼‍➡️ | woman, motorized, wheelchair, facing, right | woman in motorized wheelchair facing right | People & Body |
| `person-in-manual-wheelchair` | 🧑‍🦽 | person, manual, wheelchair | person in manual wheelchair | People & Body |
| `person-in-manual-wheelchair-facing-right` | 🧑‍🦽‍➡️ | person, manual, wheelchair, facing, right | person in manual wheelchair facing right | People & Body |
| `man-in-manual-wheelchair` | 👨‍🦽 | man, manual, wheelchair | man in manual wheelchair | People & Body |
| `man-in-manual-wheelchair-facing-right` | 👨‍🦽‍➡️ | man, manual, wheelchair, facing, right | man in manual wheelchair facing right | People & Body |
| `woman-in-manual-wheelchair` | 👩‍🦽 | woman, manual, wheelchair | woman in manual wheelchair | People & Body |
| `woman-in-manual-wheelchair-facing-right` | 👩‍🦽‍➡️ | woman, manual, wheelchair, facing, right | woman in manual wheelchair facing right | People & Body |
| `person-running` | 🏃 | person, running | person running | People & Body |
| `man-running` | 🏃‍♂️ | man, running | man running | People & Body |
| `woman-running` | 🏃‍♀️ | woman, running | woman running | People & Body |
| `person-running-facing-right` | 🏃‍➡️ | person, running, facing, right | person running facing right | People & Body |
| `woman-running-facing-right` | 🏃‍♀️‍➡️ | woman, running, facing, right | woman running facing right | People & Body |
| `man-running-facing-right` | 🏃‍♂️‍➡️ | man, running, facing, right | man running facing right | People & Body |
| `woman-dancing` | 💃 | woman, dancing | woman dancing | People & Body |
| `man-dancing` | 🕺 | man, dancing | man dancing | People & Body |
| `person-in-suit-levitating` | 🕴️ | person, suit, levitating | person in suit levitating | People & Body |
| `people-with-bunny-ears` | 👯 | people, bunny, ears, ear | people with bunny ears | People & Body |
| `men-with-bunny-ears` | 👯‍♂️ | men, bunny, ears, ear | men with bunny ears | People & Body |
| `women-with-bunny-ears` | 👯‍♀️ | women, bunny, ears, ear | women with bunny ears | People & Body |
| `person-in-steamy-room` | 🧖 | person, steamy, room | person in steamy room | People & Body |
| `man-in-steamy-room` | 🧖‍♂️ | man, steamy, room | man in steamy room | People & Body |
| `woman-in-steamy-room` | 🧖‍♀️ | woman, steamy, room | woman in steamy room | People & Body |
| `person-climbing` | 🧗 | person, climbing | person climbing | People & Body |
| `man-climbing` | 🧗‍♂️ | man, climbing | man climbing | People & Body |
| `woman-climbing` | 🧗‍♀️ | woman, climbing | woman climbing | People & Body |
| `person-fencing` | 🤺 | person, fencing | person fencing | People & Body |
| `horse-racing` | 🏇 | horse, racing | horse racing | People & Body |
| `skier` | ⛷️ | skier | skier | People & Body |
| `snowboarder` | 🏂 | snowboarder | snowboarder | People & Body |
| `person-golfing` | 🏌️ | person, golfing | person golfing | People & Body |
| `man-golfing` | 🏌️‍♂️ | man, golfing | man golfing | People & Body |
| `woman-golfing` | 🏌️‍♀️ | woman, golfing | woman golfing | People & Body |
| `person-surfing` | 🏄 | person, surfing | person surfing | People & Body |
| `man-surfing` | 🏄‍♂️ | man, surfing | man surfing | People & Body |
| `woman-surfing` | 🏄‍♀️ | woman, surfing | woman surfing | People & Body |
| `person-rowing-boat` | 🚣 | person, rowing, boat | person rowing boat | People & Body |
| `man-rowing-boat` | 🚣‍♂️ | man, rowing, boat | man rowing boat | People & Body |
| `woman-rowing-boat` | 🚣‍♀️ | woman, rowing, boat | woman rowing boat | People & Body |
| `person-swimming` | 🏊 | person, swimming | person swimming | People & Body |
| `man-swimming` | 🏊‍♂️ | man, swimming | man swimming | People & Body |
| `woman-swimming` | 🏊‍♀️ | woman, swimming | woman swimming | People & Body |
| `person-bouncing-ball` | ⛹️ | person, bouncing, ball | person bouncing ball | People & Body |
| `man-bouncing-ball` | ⛹️‍♂️ | man, bouncing, ball | man bouncing ball | People & Body |
| `woman-bouncing-ball` | ⛹️‍♀️ | woman, bouncing, ball | woman bouncing ball | People & Body |
| `person-lifting-weights` | 🏋️ | person, lifting, weights, weight | person lifting weights | People & Body |
| `man-lifting-weights` | 🏋️‍♂️ | man, lifting, weights, weight | man lifting weights | People & Body |
| `woman-lifting-weights` | 🏋️‍♀️ | woman, lifting, weights, weight | woman lifting weights | People & Body |
| `person-biking` | 🚴 | person, biking | person biking | People & Body |
| `man-biking` | 🚴‍♂️ | man, biking | man biking | People & Body |
| `woman-biking` | 🚴‍♀️ | woman, biking | woman biking | People & Body |
| `person-mountain-biking` | 🚵 | person, mountain, biking | person mountain biking | People & Body |
| `man-mountain-biking` | 🚵‍♂️ | man, mountain, biking | man mountain biking | People & Body |
| `woman-mountain-biking` | 🚵‍♀️ | woman, mountain, biking | woman mountain biking | People & Body |
| `person-cartwheeling` | 🤸 | person, cartwheeling | person cartwheeling | People & Body |
| `man-cartwheeling` | 🤸‍♂️ | man, cartwheeling | man cartwheeling | People & Body |
| `woman-cartwheeling` | 🤸‍♀️ | woman, cartwheeling | woman cartwheeling | People & Body |
| `people-wrestling` | 🤼 | people, wrestling | people wrestling | People & Body |
| `men-wrestling` | 🤼‍♂️ | men, wrestling | men wrestling | People & Body |
| `women-wrestling` | 🤼‍♀️ | women, wrestling | women wrestling | People & Body |
| `person-playing-water-polo` | 🤽 | person, playing, water, polo | person playing water polo | People & Body |
| `man-playing-water-polo` | 🤽‍♂️ | man, playing, water, polo | man playing water polo | People & Body |
| `woman-playing-water-polo` | 🤽‍♀️ | woman, playing, water, polo | woman playing water polo | People & Body |
| `person-playing-handball` | 🤾 | person, playing, handball | person playing handball | People & Body |
| `man-playing-handball` | 🤾‍♂️ | man, playing, handball | man playing handball | People & Body |
| `woman-playing-handball` | 🤾‍♀️ | woman, playing, handball | woman playing handball | People & Body |
| `person-juggling` | 🤹 | person, juggling | person juggling | People & Body |
| `man-juggling` | 🤹‍♂️ | man, juggling | man juggling | People & Body |
| `woman-juggling` | 🤹‍♀️ | woman, juggling | woman juggling | People & Body |
| `person-in-lotus-position` | 🧘 | person, lotus, position | person in lotus position | People & Body |
| `man-in-lotus-position` | 🧘‍♂️ | man, lotus, position | man in lotus position | People & Body |
| `woman-in-lotus-position` | 🧘‍♀️ | woman, lotus, position | woman in lotus position | People & Body |
| `person-taking-bath` | 🛀 | person, taking, bath | person taking bath | People & Body |
| `person-in-bed` | 🛌 | person, bed | person in bed | People & Body |
| `people-holding-hands` | 🧑‍🤝‍🧑 | people, holding, hands, hand | people holding hands | People & Body |
| `women-holding-hands` | 👭 | women, holding, hands, hand | women holding hands | People & Body |
| `woman-and-man-holding-hands` | 👫 | woman, man, holding, hands, hand | woman and man holding hands | People & Body |
| `men-holding-hands` | 👬 | men, holding, hands, hand | men holding hands | People & Body |
| `kiss-1f48f` | 💏 | kiss | kiss | People & Body |
| `kiss-woman-man` | 👩‍❤️‍💋‍👨 | kiss, woman, man | kiss: woman, man | People & Body |
| `kiss-man-man` | 👨‍❤️‍💋‍👨 | kiss, man | kiss: man, man | People & Body |
| `kiss-woman-woman` | 👩‍❤️‍💋‍👩 | kiss, woman | kiss: woman, woman | People & Body |
| `couple-with-heart` | 💑 | couple, heart | couple with heart | People & Body |
| `couple-with-heart-woman-man` | 👩‍❤️‍👨 | couple, heart, woman, man | couple with heart: woman, man | People & Body |
| `couple-with-heart-man-man` | 👨‍❤️‍👨 | couple, heart, man | couple with heart: man, man | People & Body |
| `couple-with-heart-woman-woman` | 👩‍❤️‍👩 | couple, heart, woman | couple with heart: woman, woman | People & Body |
| `family-man-woman-boy` | 👨‍👩‍👦 | family, man, woman, boy | family: man, woman, boy | People & Body |
| `family-man-woman-girl` | 👨‍👩‍👧 | family, man, woman, girl | family: man, woman, girl | People & Body |
| `family-man-woman-girl-boy` | 👨‍👩‍👧‍👦 | family, man, woman, girl, boy | family: man, woman, girl, boy | People & Body |
| `family-man-woman-boy-boy` | 👨‍👩‍👦‍👦 | family, man, woman, boy | family: man, woman, boy, boy | People & Body |
| `family-man-woman-girl-girl` | 👨‍👩‍👧‍👧 | family, man, woman, girl | family: man, woman, girl, girl | People & Body |
| `family-man-man-boy` | 👨‍👨‍👦 | family, man, boy | family: man, man, boy | People & Body |
| `family-man-man-girl` | 👨‍👨‍👧 | family, man, girl | family: man, man, girl | People & Body |
| `family-man-man-girl-boy` | 👨‍👨‍👧‍👦 | family, man, girl, boy | family: man, man, girl, boy | People & Body |
| `family-man-man-boy-boy` | 👨‍👨‍👦‍👦 | family, man, boy | family: man, man, boy, boy | People & Body |
| `family-man-man-girl-girl` | 👨‍👨‍👧‍👧 | family, man, girl | family: man, man, girl, girl | People & Body |
| `family-woman-woman-boy` | 👩‍👩‍👦 | family, woman, boy | family: woman, woman, boy | People & Body |
| `family-woman-woman-girl` | 👩‍👩‍👧 | family, woman, girl | family: woman, woman, girl | People & Body |
| `family-woman-woman-girl-boy` | 👩‍👩‍👧‍👦 | family, woman, girl, boy | family: woman, woman, girl, boy | People & Body |
| `family-woman-woman-boy-boy` | 👩‍👩‍👦‍👦 | family, woman, boy | family: woman, woman, boy, boy | People & Body |
| `family-woman-woman-girl-girl` | 👩‍👩‍👧‍👧 | family, woman, girl | family: woman, woman, girl, girl | People & Body |
| `family-man-boy` | 👨‍👦 | family, man, boy | family: man, boy | People & Body |
| `family-man-boy-boy` | 👨‍👦‍👦 | family, man, boy | family: man, boy, boy | People & Body |
| `family-man-girl` | 👨‍👧 | family, man, girl | family: man, girl | People & Body |
| `family-man-girl-boy` | 👨‍👧‍👦 | family, man, girl, boy | family: man, girl, boy | People & Body |
| `family-man-girl-girl` | 👨‍👧‍👧 | family, man, girl | family: man, girl, girl | People & Body |
| `family-woman-boy` | 👩‍👦 | family, woman, boy | family: woman, boy | People & Body |
| `family-woman-boy-boy` | 👩‍👦‍👦 | family, woman, boy | family: woman, boy, boy | People & Body |
| `family-woman-girl` | 👩‍👧 | family, woman, girl | family: woman, girl | People & Body |
| `family-woman-girl-boy` | 👩‍👧‍👦 | family, woman, girl, boy | family: woman, girl, boy | People & Body |
| `family-woman-girl-girl` | 👩‍👧‍👧 | family, woman, girl | family: woman, girl, girl | People & Body |
| `speaking-head` | 🗣️ | speaking, head | speaking head | People & Body |
| `bust-in-silhouette` | 👤 | bust, silhouette | bust in silhouette | People & Body |
| `busts-in-silhouette` | 👥 | busts, bust, silhouette | busts in silhouette | People & Body |
| `people-hugging` | 🫂 | people, hugging | people hugging | People & Body |
| `family` | 👪 | family | family | People & Body |
| `family-adult-adult-child` | 🧑‍🧑‍🧒 | family, adult, child | family: adult, adult, child | People & Body |
| `family-adult-adult-child-child` | 🧑‍🧑‍🧒‍🧒 | family, adult, child | family: adult, adult, child, child | People & Body |
| `family-adult-child` | 🧑‍🧒 | family, adult, child | family: adult, child | People & Body |
| `family-adult-child-child` | 🧑‍🧒‍🧒 | family, adult, child | family: adult, child, child | People & Body |
| `footprints` | 👣 | footprints, footprint | footprints | People & Body |
| `monkey-face` | 🐵 | monkey | monkey face | Animals & Nature |
| `monkey` | 🐒 | monkey | monkey | Animals & Nature |
| `gorilla` | 🦍 | gorilla | gorilla | Animals & Nature |
| `orangutan` | 🦧 | orangutan | orangutan | Animals & Nature |
| `dog-face` | 🐶 | dog | dog face | Animals & Nature |
| `dog` | 🐕 | dog | dog | Animals & Nature |
| `guide-dog` | 🦮 | guide, dog | guide dog | Animals & Nature |
| `service-dog` | 🐕‍🦺 | service, dog | service dog | Animals & Nature |
| `poodle` | 🐩 | poodle | poodle | Animals & Nature |
| `wolf` | 🐺 | wolf | wolf | Animals & Nature |
| `fox` | 🦊 | fox | fox | Animals & Nature |
| `raccoon` | 🦝 | raccoon | raccoon | Animals & Nature |
| `cat-face` | 🐱 | cat | cat face | Animals & Nature |
| `cat` | 🐈 | cat | cat | Animals & Nature |
| `black-cat` | 🐈‍⬛ | black, cat | black cat | Animals & Nature |
| `lion` | 🦁 | lion | lion | Animals & Nature |
| `tiger-face` | 🐯 | tiger | tiger face | Animals & Nature |
| `tiger` | 🐅 | tiger | tiger | Animals & Nature |
| `leopard` | 🐆 | leopard | leopard | Animals & Nature |
| `horse-face` | 🐴 | horse | horse face | Animals & Nature |
| `moose` | 🫎 | moose | moose | Animals & Nature |
| `donkey` | 🫏 | donkey | donkey | Animals & Nature |
| `horse` | 🐎 | horse | horse | Animals & Nature |
| `unicorn` | 🦄 | unicorn | unicorn | Animals & Nature |
| `zebra` | 🦓 | zebra | zebra | Animals & Nature |
| `deer` | 🦌 | deer | deer | Animals & Nature |
| `bison` | 🦬 | bison | bison | Animals & Nature |
| `cow-face` | 🐮 | cow | cow face | Animals & Nature |
| `ox` | 🐂 | ox | ox | Animals & Nature |
| `water-buffalo` | 🐃 | water, buffalo | water buffalo | Animals & Nature |
| `cow` | 🐄 | cow | cow | Animals & Nature |
| `pig-face` | 🐷 | pig | pig face | Animals & Nature |
| `pig` | 🐖 | pig | pig | Animals & Nature |
| `boar` | 🐗 | boar | boar | Animals & Nature |
| `pig-nose` | 🐽 | pig, nose | pig nose | Animals & Nature |
| `ram` | 🐏 | ram | ram | Animals & Nature |
| `ewe` | 🐑 | ewe | ewe | Animals & Nature |
| `goat` | 🐐 | goat | goat | Animals & Nature |
| `camel` | 🐪 | camel | camel | Animals & Nature |
| `two-hump-camel` | 🐫 | hump, camel | two-hump camel | Animals & Nature |
| `llama` | 🦙 | llama | llama | Animals & Nature |
| `giraffe` | 🦒 | giraffe | giraffe | Animals & Nature |
| `elephant` | 🐘 | elephant | elephant | Animals & Nature |
| `mammoth` | 🦣 | mammoth | mammoth | Animals & Nature |
| `rhinoceros` | 🦏 | rhinoceros | rhinoceros | Animals & Nature |
| `hippopotamus` | 🦛 | hippopotamus | hippopotamus | Animals & Nature |
| `mouse-face` | 🐭 | mouse | mouse face | Animals & Nature |
| `mouse` | 🐁 | mouse | mouse | Animals & Nature |
| `rat` | 🐀 | rat | rat | Animals & Nature |
| `hamster` | 🐹 | hamster | hamster | Animals & Nature |
| `rabbit-face` | 🐰 | rabbit | rabbit face | Animals & Nature |
| `rabbit` | 🐇 | rabbit | rabbit | Animals & Nature |
| `chipmunk` | 🐿️ | chipmunk | chipmunk | Animals & Nature |
| `beaver` | 🦫 | beaver | beaver | Animals & Nature |
| `hedgehog` | 🦔 | hedgehog | hedgehog | Animals & Nature |
| `bat` | 🦇 | bat | bat | Animals & Nature |
| `bear` | 🐻 | bear | bear | Animals & Nature |
| `polar-bear` | 🐻‍❄️ | polar, bear | polar bear | Animals & Nature |
| `koala` | 🐨 | koala | koala | Animals & Nature |
| `panda` | 🐼 | panda | panda | Animals & Nature |
| `sloth` | 🦥 | sloth | sloth | Animals & Nature |
| `otter` | 🦦 | otter | otter | Animals & Nature |
| `skunk` | 🦨 | skunk | skunk | Animals & Nature |
| `kangaroo` | 🦘 | kangaroo | kangaroo | Animals & Nature |
| `badger` | 🦡 | badger | badger | Animals & Nature |
| `paw-prints` | 🐾 | paw, prints, print | paw prints | Animals & Nature |
| `turkey` | 🦃 | turkey | turkey | Animals & Nature |
| `chicken` | 🐔 | chicken | chicken | Animals & Nature |
| `rooster` | 🐓 | rooster | rooster | Animals & Nature |
| `hatching-chick` | 🐣 | hatching, chick | hatching chick | Animals & Nature |
| `baby-chick` | 🐤 | baby, chick | baby chick | Animals & Nature |
| `front-facing-baby-chick` | 🐥 | front, facing, baby, chick | front-facing baby chick | Animals & Nature |
| `bird` | 🐦 | bird | bird | Animals & Nature |
| `penguin` | 🐧 | penguin | penguin | Animals & Nature |
| `dove` | 🕊️ | dove | dove | Animals & Nature |
| `eagle` | 🦅 | eagle | eagle | Animals & Nature |
| `duck` | 🦆 | duck | duck | Animals & Nature |
| `swan` | 🦢 | swan | swan | Animals & Nature |
| `owl` | 🦉 | owl | owl | Animals & Nature |
| `dodo` | 🦤 | dodo | dodo | Animals & Nature |
| `feather` | 🪶 | feather | feather | Animals & Nature |
| `flamingo` | 🦩 | flamingo | flamingo | Animals & Nature |
| `peacock` | 🦚 | peacock | peacock | Animals & Nature |
| `parrot` | 🦜 | parrot | parrot | Animals & Nature |
| `wing` | 🪽 | wing | wing | Animals & Nature |
| `black-bird` | 🐦‍⬛ | black, bird | black bird | Animals & Nature |
| `goose` | 🪿 | goose | goose | Animals & Nature |
| `phoenix` | 🐦‍🔥 | phoenix | phoenix | Animals & Nature |
| `frog` | 🐸 | frog | frog | Animals & Nature |
| `crocodile` | 🐊 | crocodile | crocodile | Animals & Nature |
| `turtle` | 🐢 | turtle | turtle | Animals & Nature |
| `lizard` | 🦎 | lizard | lizard | Animals & Nature |
| `snake` | 🐍 | snake | snake | Animals & Nature |
| `dragon-face` | 🐲 | dragon | dragon face | Animals & Nature |
| `dragon` | 🐉 | dragon | dragon | Animals & Nature |
| `sauropod` | 🦕 | sauropod | sauropod | Animals & Nature |
| `t-rex` | 🦖 | rex | T-Rex | Animals & Nature |
| `spouting-whale` | 🐳 | spouting, whale | spouting whale | Animals & Nature |
| `whale` | 🐋 | whale | whale | Animals & Nature |
| `dolphin` | 🐬 | dolphin | dolphin | Animals & Nature |
| `seal` | 🦭 | seal | seal | Animals & Nature |
| `fish` | 🐟 | fish | fish | Animals & Nature |
| `tropical-fish` | 🐠 | tropical, fish | tropical fish | Animals & Nature |
| `blowfish` | 🐡 | blowfish | blowfish | Animals & Nature |
| `shark` | 🦈 | shark | shark | Animals & Nature |
| `octopus` | 🐙 | octopus | octopus | Animals & Nature |
| `spiral-shell` | 🐚 | spiral, shell | spiral shell | Animals & Nature |
| `coral` | 🪸 | coral | coral | Animals & Nature |
| `jellyfish` | 🪼 | jellyfish | jellyfish | Animals & Nature |
| `snail` | 🐌 | snail | snail | Animals & Nature |
| `butterfly` | 🦋 | butterfly | butterfly | Animals & Nature |
| `bug` | 🐛 | bug | bug | Animals & Nature |
| `ant` | 🐜 | ant | ant | Animals & Nature |
| `honeybee` | 🐝 | honeybee | honeybee | Animals & Nature |
| `beetle` | 🪲 | beetle | beetle | Animals & Nature |
| `lady-beetle` | 🐞 | lady, beetle | lady beetle | Animals & Nature |
| `cricket` | 🦗 | cricket | cricket | Animals & Nature |
| `cockroach` | 🪳 | cockroach | cockroach | Animals & Nature |
| `spider` | 🕷️ | spider | spider | Animals & Nature |
| `spider-web` | 🕸️ | spider, web | spider web | Animals & Nature |
| `scorpion` | 🦂 | scorpion | scorpion | Animals & Nature |
| `mosquito` | 🦟 | mosquito | mosquito | Animals & Nature |
| `fly` | 🪰 | fly | fly | Animals & Nature |
| `worm` | 🪱 | worm | worm | Animals & Nature |
| `microbe` | 🦠 | microbe | microbe | Animals & Nature |
| `bouquet` | 💐 | bouquet | bouquet | Animals & Nature |
| `cherry-blossom` | 🌸 | cherry, blossom | cherry blossom | Animals & Nature |
| `white-flower` | 💮 | white, flower | white flower | Animals & Nature |
| `lotus` | 🪷 | lotus | lotus | Animals & Nature |
| `rosette` | 🏵️ | rosette | rosette | Animals & Nature |
| `rose` | 🌹 | rose | rose | Animals & Nature |
| `wilted-flower` | 🥀 | wilted, flower | wilted flower | Animals & Nature |
| `hibiscus` | 🌺 | hibiscus | hibiscus | Animals & Nature |
| `sunflower` | 🌻 | sunflower | sunflower | Animals & Nature |
| `blossom` | 🌼 | blossom | blossom | Animals & Nature |
| `tulip` | 🌷 | tulip | tulip | Animals & Nature |
| `hyacinth` | 🪻 | hyacinth | hyacinth | Animals & Nature |
| `seedling` | 🌱 | seedling | seedling | Animals & Nature |
| `potted-plant` | 🪴 | potted, plant | potted plant | Animals & Nature |
| `evergreen-tree` | 🌲 | evergreen, tree | evergreen tree | Animals & Nature |
| `deciduous-tree` | 🌳 | deciduous, tree | deciduous tree | Animals & Nature |
| `palm-tree` | 🌴 | palm, tree | palm tree | Animals & Nature |
| `cactus` | 🌵 | cactus | cactus | Animals & Nature |
| `sheaf-of-rice` | 🌾 | sheaf, rice | sheaf of rice | Animals & Nature |
| `herb` | 🌿 | herb | herb | Animals & Nature |
| `shamrock` | ☘️ | shamrock | shamrock | Animals & Nature |
| `four-leaf-clover` | 🍀 | leaf, clover | four leaf clover | Animals & Nature |
| `maple-leaf` | 🍁 | maple, leaf | maple leaf | Animals & Nature |
| `fallen-leaf` | 🍂 | fallen, leaf | fallen leaf | Animals & Nature |
| `leaf-fluttering-in-wind` | 🍃 | leaf, fluttering, wind | leaf fluttering in wind | Animals & Nature |
| `empty-nest` | 🪹 | empty, nest | empty nest | Animals & Nature |
| `nest-with-eggs` | 🪺 | nest, eggs, egg | nest with eggs | Animals & Nature |
| `mushroom` | 🍄 | mushroom | mushroom | Animals & Nature |
| `grapes` | 🍇 | grapes, grape | grapes | Food & Drink |
| `melon` | 🍈 | melon | melon | Food & Drink |
| `watermelon` | 🍉 | watermelon | watermelon | Food & Drink |
| `tangerine` | 🍊 | tangerine | tangerine | Food & Drink |
| `lemon` | 🍋 | lemon | lemon | Food & Drink |
| `lime` | 🍋‍🟩 | lime | lime | Food & Drink |
| `banana` | 🍌 | banana | banana | Food & Drink |
| `pineapple` | 🍍 | pineapple | pineapple | Food & Drink |
| `mango` | 🥭 | mango | mango | Food & Drink |
| `red-apple` | 🍎 | red, apple | red apple | Food & Drink |
| `green-apple` | 🍏 | green, apple | green apple | Food & Drink |
| `pear` | 🍐 | pear | pear | Food & Drink |
| `peach` | 🍑 | peach | peach | Food & Drink |
| `cherries` | 🍒 | cherries, cherry | cherries | Food & Drink |
| `strawberry` | 🍓 | strawberry | strawberry | Food & Drink |
| `blueberries` | 🫐 | blueberries, blueberry | blueberries | Food & Drink |
| `kiwi-fruit` | 🥝 | kiwi, fruit | kiwi fruit | Food & Drink |
| `tomato` | 🍅 | tomato | tomato | Food & Drink |
| `olive` | 🫒 | olive | olive | Food & Drink |
| `coconut` | 🥥 | coconut | coconut | Food & Drink |
| `avocado` | 🥑 | avocado | avocado | Food & Drink |
| `eggplant` | 🍆 | eggplant | eggplant | Food & Drink |
| `potato` | 🥔 | potato | potato | Food & Drink |
| `carrot` | 🥕 | carrot | carrot | Food & Drink |
| `ear-of-corn` | 🌽 | ear, corn | ear of corn | Food & Drink |
| `hot-pepper` | 🌶️ | hot, pepper | hot pepper | Food & Drink |
| `bell-pepper` | 🫑 | bell, pepper | bell pepper | Food & Drink |
| `cucumber` | 🥒 | cucumber | cucumber | Food & Drink |
| `leafy-green` | 🥬 | leafy, green | leafy green | Food & Drink |
| `broccoli` | 🥦 | broccoli | broccoli | Food & Drink |
| `garlic` | 🧄 | garlic | garlic | Food & Drink |
| `onion` | 🧅 | onion | onion | Food & Drink |
| `peanuts` | 🥜 | peanuts, peanut | peanuts | Food & Drink |
| `beans` | 🫘 | beans, bean | beans | Food & Drink |
| `chestnut` | 🌰 | chestnut | chestnut | Food & Drink |
| `ginger-root` | 🫚 | ginger, root | ginger root | Food & Drink |
| `pea-pod` | 🫛 | pea, pod | pea pod | Food & Drink |
| `brown-mushroom` | 🍄‍🟫 | brown, mushroom | brown mushroom | Food & Drink |
| `bread` | 🍞 | bread | bread | Food & Drink |
| `croissant` | 🥐 | croissant | croissant | Food & Drink |
| `baguette-bread` | 🥖 | baguette, bread | baguette bread | Food & Drink |
| `flatbread` | 🫓 | flatbread | flatbread | Food & Drink |
| `pretzel` | 🥨 | pretzel | pretzel | Food & Drink |
| `bagel` | 🥯 | bagel | bagel | Food & Drink |
| `pancakes` | 🥞 | pancakes, pancake | pancakes | Food & Drink |
| `waffle` | 🧇 | waffle | waffle | Food & Drink |
| `cheese-wedge` | 🧀 | cheese, wedge | cheese wedge | Food & Drink |
| `meat-on-bone` | 🍖 | meat, bone | meat on bone | Food & Drink |
| `poultry-leg` | 🍗 | poultry, leg | poultry leg | Food & Drink |
| `cut-of-meat` | 🥩 | cut, meat | cut of meat | Food & Drink |
| `bacon` | 🥓 | bacon | bacon | Food & Drink |
| `hamburger` | 🍔 | hamburger | hamburger | Food & Drink |
| `french-fries` | 🍟 | french, fries, fry | french fries | Food & Drink |
| `pizza` | 🍕 | pizza | pizza | Food & Drink |
| `hot-dog` | 🌭 | hot, dog | hot dog | Food & Drink |
| `sandwich` | 🥪 | sandwich | sandwich | Food & Drink |
| `taco` | 🌮 | taco | taco | Food & Drink |
| `burrito` | 🌯 | burrito | burrito | Food & Drink |
| `tamale` | 🫔 | tamale | tamale | Food & Drink |
| `stuffed-flatbread` | 🥙 | stuffed, flatbread | stuffed flatbread | Food & Drink |
| `falafel` | 🧆 | falafel | falafel | Food & Drink |
| `egg` | 🥚 | egg | egg | Food & Drink |
| `cooking` | 🍳 | cooking | cooking | Food & Drink |
| `shallow-pan-of-food` | 🥘 | shallow, pan, food | shallow pan of food | Food & Drink |
| `pot-of-food` | 🍲 | pot, food | pot of food | Food & Drink |
| `fondue` | 🫕 | fondue | fondue | Food & Drink |
| `bowl-with-spoon` | 🥣 | bowl, spoon | bowl with spoon | Food & Drink |
| `green-salad` | 🥗 | green, salad | green salad | Food & Drink |
| `popcorn` | 🍿 | popcorn | popcorn | Food & Drink |
| `butter` | 🧈 | butter | butter | Food & Drink |
| `salt` | 🧂 | salt | salt | Food & Drink |
| `canned-food` | 🥫 | canned, food | canned food | Food & Drink |
| `bento-box` | 🍱 | bento, box | bento box | Food & Drink |
| `rice-cracker` | 🍘 | rice, cracker | rice cracker | Food & Drink |
| `rice-ball` | 🍙 | rice, ball | rice ball | Food & Drink |
| `cooked-rice` | 🍚 | cooked, rice | cooked rice | Food & Drink |
| `curry-rice` | 🍛 | curry, rice | curry rice | Food & Drink |
| `steaming-bowl` | 🍜 | steaming, bowl | steaming bowl | Food & Drink |
| `spaghetti` | 🍝 | spaghetti | spaghetti | Food & Drink |
| `roasted-sweet-potato` | 🍠 | roasted, sweet, potato | roasted sweet potato | Food & Drink |
| `oden` | 🍢 | oden | oden | Food & Drink |
| `sushi` | 🍣 | sushi | sushi | Food & Drink |
| `fried-shrimp` | 🍤 | fried, shrimp | fried shrimp | Food & Drink |
| `fish-cake-with-swirl` | 🍥 | fish, cake, swirl | fish cake with swirl | Food & Drink |
| `moon-cake` | 🥮 | moon, cake | moon cake | Food & Drink |
| `dango` | 🍡 | dango | dango | Food & Drink |
| `dumpling` | 🥟 | dumpling | dumpling | Food & Drink |
| `fortune-cookie` | 🥠 | fortune, cookie | fortune cookie | Food & Drink |
| `takeout-box` | 🥡 | takeout, box | takeout box | Food & Drink |
| `crab` | 🦀 | crab | crab | Food & Drink |
| `lobster` | 🦞 | lobster | lobster | Food & Drink |
| `shrimp` | 🦐 | shrimp | shrimp | Food & Drink |
| `squid` | 🦑 | squid | squid | Food & Drink |
| `oyster` | 🦪 | oyster | oyster | Food & Drink |
| `soft-ice-cream` | 🍦 | soft, ice, cream | soft ice cream | Food & Drink |
| `shaved-ice` | 🍧 | shaved, ice | shaved ice | Food & Drink |
| `ice-cream` | 🍨 | ice, cream | ice cream | Food & Drink |
| `doughnut` | 🍩 | doughnut | doughnut | Food & Drink |
| `cookie` | 🍪 | cookie | cookie | Food & Drink |
| `birthday-cake` | 🎂 | birthday, cake | birthday cake | Food & Drink |
| `shortcake` | 🍰 | shortcake | shortcake | Food & Drink |
| `cupcake` | 🧁 | cupcake | cupcake | Food & Drink |
| `pie` | 🥧 | pie | pie | Food & Drink |
| `chocolate-bar` | 🍫 | chocolate, bar | chocolate bar | Food & Drink |
| `candy` | 🍬 | candy | candy | Food & Drink |
| `lollipop` | 🍭 | lollipop | lollipop | Food & Drink |
| `custard` | 🍮 | custard | custard | Food & Drink |
| `honey-pot` | 🍯 | honey, pot | honey pot | Food & Drink |
| `baby-bottle` | 🍼 | baby, bottle | baby bottle | Food & Drink |
| `glass-of-milk` | 🥛 | glass, milk | glass of milk | Food & Drink |
| `hot-beverage` | ☕ | hot, beverage | hot beverage | Food & Drink |
| `teapot` | 🫖 | teapot | teapot | Food & Drink |
| `teacup-without-handle` | 🍵 | teacup, without, handle | teacup without handle | Food & Drink |
| `sake` | 🍶 | sake | sake | Food & Drink |
| `bottle-with-popping-cork` | 🍾 | bottle, popping, cork | bottle with popping cork | Food & Drink |
| `wine-glass` | 🍷 | wine, glass | wine glass | Food & Drink |
| `cocktail-glass` | 🍸 | cocktail, glass | cocktail glass | Food & Drink |
| `tropical-drink` | 🍹 | tropical, drink | tropical drink | Food & Drink |
| `beer-mug` | 🍺 | beer, mug | beer mug | Food & Drink |
| `clinking-beer-mugs` | 🍻 | clinking, beer, mugs, mug | clinking beer mugs | Food & Drink |
| `clinking-glasses` | 🥂 | clinking, glasses, glass | clinking glasses | Food & Drink |
| `tumbler-glass` | 🥃 | tumbler, glass | tumbler glass | Food & Drink |
| `pouring-liquid` | 🫗 | pouring, liquid | pouring liquid | Food & Drink |
| `cup-with-straw` | 🥤 | cup, straw | cup with straw | Food & Drink |
| `bubble-tea` | 🧋 | bubble, tea | bubble tea | Food & Drink |
| `beverage-box` | 🧃 | beverage, box | beverage box | Food & Drink |
| `mate` | 🧉 | mate | mate | Food & Drink |
| `ice` | 🧊 | ice | ice | Food & Drink |
| `chopsticks` | 🥢 | chopsticks, chopstick | chopsticks | Food & Drink |
| `fork-and-knife-with-plate` | 🍽️ | fork, knife, plate | fork and knife with plate | Food & Drink |
| `fork-and-knife` | 🍴 | fork, knife | fork and knife | Food & Drink |
| `spoon` | 🥄 | spoon | spoon | Food & Drink |
| `kitchen-knife` | 🔪 | kitchen, knife | kitchen knife | Food & Drink |
| `jar` | 🫙 | jar | jar | Food & Drink |
| `amphora` | 🏺 | amphora | amphora | Food & Drink |
| `globe-showing-europe-africa` | 🌍 | globe, showing, europe, africa | globe showing Europe-Africa | Travel & Places |
| `globe-showing-americas` | 🌎 | globe, showing, americas, america | globe showing Americas | Travel & Places |
| `globe-showing-asia-australia` | 🌏 | globe, showing, asia, australia | globe showing Asia-Australia | Travel & Places |
| `globe-with-meridians` | 🌐 | globe, meridians, meridian | globe with meridians | Travel & Places |
| `world-map` | 🗺️ | world, map | world map | Travel & Places |
| `map-of-japan` | 🗾 | map, japan | map of Japan | Travel & Places |
| `compass` | 🧭 | compass | compass | Travel & Places |
| `snow-capped-mountain` | 🏔️ | snow, capped, mountain | snow-capped mountain | Travel & Places |
| `mountain` | ⛰️ | mountain | mountain | Travel & Places |
| `volcano` | 🌋 | volcano | volcano | Travel & Places |
| `mount-fuji` | 🗻 | mount, fuji | mount fuji | Travel & Places |
| `camping` | 🏕️ | camping | camping | Travel & Places |
| `beach-with-umbrella` | 🏖️ | beach, umbrella | beach with umbrella | Travel & Places |
| `desert` | 🏜️ | desert | desert | Travel & Places |
| `desert-island` | 🏝️ | desert, island | desert island | Travel & Places |
| `national-park` | 🏞️ | national, park | national park | Travel & Places |
| `stadium` | 🏟️ | stadium | stadium | Travel & Places |
| `classical-building` | 🏛️ | classical, building | classical building | Travel & Places |
| `building-construction` | 🏗️ | building, construction | building construction | Travel & Places |
| `brick` | 🧱 | brick | brick | Travel & Places |
| `rock` | 🪨 | rock | rock | Travel & Places |
| `wood` | 🪵 | wood | wood | Travel & Places |
| `hut` | 🛖 | hut | hut | Travel & Places |
| `houses` | 🏘️ | houses, house | houses | Travel & Places |
| `derelict-house` | 🏚️ | derelict, house | derelict house | Travel & Places |
| `house` | 🏠 | house | house | Travel & Places |
| `house-with-garden` | 🏡 | house, garden | house with garden | Travel & Places |
| `office-building` | 🏢 | office, building | office building | Travel & Places |
| `japanese-post-office` | 🏣 | japanese, post, office | Japanese post office | Travel & Places |
| `post-office` | 🏤 | post, office | post office | Travel & Places |
| `hospital` | 🏥 | hospital | hospital | Travel & Places |
| `bank` | 🏦 | bank | bank | Travel & Places |
| `hotel` | 🏨 | hotel | hotel | Travel & Places |
| `love-hotel` | 🏩 | love, hotel | love hotel | Travel & Places |
| `convenience-store` | 🏪 | convenience, store | convenience store | Travel & Places |
| `school` | 🏫 | school | school | Travel & Places |
| `department-store` | 🏬 | department, store | department store | Travel & Places |
| `factory` | 🏭 | factory | factory | Travel & Places |
| `japanese-castle` | 🏯 | japanese, castle | Japanese castle | Travel & Places |
| `castle` | 🏰 | castle | castle | Travel & Places |
| `wedding` | 💒 | wedding | wedding | Travel & Places |
| `tokyo-tower` | 🗼 | tokyo, tower | Tokyo tower | Travel & Places |
| `statue-of-liberty` | 🗽 | statue, liberty | Statue of Liberty | Travel & Places |
| `church` | ⛪ | church | church | Travel & Places |
| `mosque` | 🕌 | mosque | mosque | Travel & Places |
| `hindu-temple` | 🛕 | hindu, temple | hindu temple | Travel & Places |
| `synagogue` | 🕍 | synagogue | synagogue | Travel & Places |
| `shinto-shrine` | ⛩️ | shinto, shrine | shinto shrine | Travel & Places |
| `kaaba` | 🕋 | kaaba | kaaba | Travel & Places |
| `fountain` | ⛲ | fountain | fountain | Travel & Places |
| `tent` | ⛺ | tent | tent | Travel & Places |
| `foggy` | 🌁 | foggy | foggy | Travel & Places |
| `night-with-stars` | 🌃 | night, stars, star | night with stars | Travel & Places |
| `cityscape` | 🏙️ | cityscape | cityscape | Travel & Places |
| `sunrise-over-mountains` | 🌄 | sunrise, over, mountains, mountain | sunrise over mountains | Travel & Places |
| `sunrise` | 🌅 | sunrise | sunrise | Travel & Places |
| `cityscape-at-dusk` | 🌆 | cityscape, at, dusk | cityscape at dusk | Travel & Places |
| `sunset` | 🌇 | sunset | sunset | Travel & Places |
| `bridge-at-night` | 🌉 | bridge, at, night | bridge at night | Travel & Places |
| `hot-springs` | ♨️ | hot, springs, spring | hot springs | Travel & Places |
| `carousel-horse` | 🎠 | carousel, horse | carousel horse | Travel & Places |
| `playground-slide` | 🛝 | playground, slide | playground slide | Travel & Places |
| `ferris-wheel` | 🎡 | ferris, wheel | ferris wheel | Travel & Places |
| `roller-coaster` | 🎢 | roller, coaster | roller coaster | Travel & Places |
| `barber-pole` | 💈 | barber, pole | barber pole | Travel & Places |
| `circus-tent` | 🎪 | circus, tent | circus tent | Travel & Places |
| `locomotive` | 🚂 | locomotive | locomotive | Travel & Places |
| `railway-car` | 🚃 | railway, car | railway car | Travel & Places |
| `high-speed-train` | 🚄 | high, speed, train | high-speed train | Travel & Places |
| `bullet-train` | 🚅 | bullet, train | bullet train | Travel & Places |
| `train` | 🚆 | train | train | Travel & Places |
| `metro` | 🚇 | metro | metro | Travel & Places |
| `light-rail` | 🚈 | light, rail | light rail | Travel & Places |
| `station` | 🚉 | station | station | Travel & Places |
| `tram` | 🚊 | tram | tram | Travel & Places |
| `monorail` | 🚝 | monorail | monorail | Travel & Places |
| `mountain-railway` | 🚞 | mountain, railway | mountain railway | Travel & Places |
| `tram-car` | 🚋 | tram, car | tram car | Travel & Places |
| `bus` | 🚌 | bus | bus | Travel & Places |
| `oncoming-bus` | 🚍 | oncoming, bus | oncoming bus | Travel & Places |
| `trolleybus` | 🚎 | trolleybus | trolleybus | Travel & Places |
| `minibus` | 🚐 | minibus | minibus | Travel & Places |
| `ambulance` | 🚑 | ambulance | ambulance | Travel & Places |
| `fire-engine` | 🚒 | fire, engine | fire engine | Travel & Places |
| `police-car` | 🚓 | police, car | police car | Travel & Places |
| `oncoming-police-car` | 🚔 | oncoming, police, car | oncoming police car | Travel & Places |
| `taxi` | 🚕 | taxi | taxi | Travel & Places |
| `oncoming-taxi` | 🚖 | oncoming, taxi | oncoming taxi | Travel & Places |
| `automobile` | 🚗 | automobile | automobile | Travel & Places |
| `oncoming-automobile` | 🚘 | oncoming, automobile | oncoming automobile | Travel & Places |
| `sport-utility-vehicle` | 🚙 | sport, utility, vehicle | sport utility vehicle | Travel & Places |
| `pickup-truck` | 🛻 | pickup, truck | pickup truck | Travel & Places |
| `delivery-truck` | 🚚 | delivery, truck | delivery truck | Travel & Places |
| `articulated-lorry` | 🚛 | articulated, lorry | articulated lorry | Travel & Places |
| `tractor` | 🚜 | tractor | tractor | Travel & Places |
| `racing-car` | 🏎️ | racing, car | racing car | Travel & Places |
| `motorcycle` | 🏍️ | motorcycle | motorcycle | Travel & Places |
| `motor-scooter` | 🛵 | motor, scooter | motor scooter | Travel & Places |
| `manual-wheelchair` | 🦽 | manual, wheelchair | manual wheelchair | Travel & Places |
| `motorized-wheelchair` | 🦼 | motorized, wheelchair | motorized wheelchair | Travel & Places |
| `auto-rickshaw` | 🛺 | auto, rickshaw | auto rickshaw | Travel & Places |
| `bicycle` | 🚲 | bicycle | bicycle | Travel & Places |
| `kick-scooter` | 🛴 | kick, scooter | kick scooter | Travel & Places |
| `skateboard` | 🛹 | skateboard | skateboard | Travel & Places |
| `roller-skate` | 🛼 | roller, skate | roller skate | Travel & Places |
| `bus-stop` | 🚏 | bus, stop | bus stop | Travel & Places |
| `motorway` | 🛣️ | motorway | motorway | Travel & Places |
| `railway-track` | 🛤️ | railway, track | railway track | Travel & Places |
| `oil-drum` | 🛢️ | oil, drum | oil drum | Travel & Places |
| `fuel-pump` | ⛽ | fuel, pump | fuel pump | Travel & Places |
| `wheel` | 🛞 | wheel | wheel | Travel & Places |
| `police-car-light` | 🚨 | police, car, light | police car light | Travel & Places |
| `horizontal-traffic-light` | 🚥 | horizontal, traffic, light | horizontal traffic light | Travel & Places |
| `vertical-traffic-light` | 🚦 | vertical, traffic, light | vertical traffic light | Travel & Places |
| `stop-sign` | 🛑 | stop | stop sign | Travel & Places |
| `construction` | 🚧 | construction | construction | Travel & Places |
| `anchor` | ⚓ | anchor | anchor | Travel & Places |
| `ring-buoy` | 🛟 | ring, buoy | ring buoy | Travel & Places |
| `sailboat` | ⛵ | sailboat | sailboat | Travel & Places |
| `canoe` | 🛶 | canoe | canoe | Travel & Places |
| `speedboat` | 🚤 | speedboat | speedboat | Travel & Places |
| `passenger-ship` | 🛳️ | passenger, ship | passenger ship | Travel & Places |
| `ferry` | ⛴️ | ferry | ferry | Travel & Places |
| `motor-boat` | 🛥️ | motor, boat | motor boat | Travel & Places |
| `ship` | 🚢 | ship | ship | Travel & Places |
| `airplane` | ✈️ | airplane | airplane | Travel & Places |
| `small-airplane` | 🛩️ | small, airplane | small airplane | Travel & Places |
| `airplane-departure` | 🛫 | airplane, departure | airplane departure | Travel & Places |
| `airplane-arrival` | 🛬 | airplane, arrival | airplane arrival | Travel & Places |
| `parachute` | 🪂 | parachute | parachute | Travel & Places |
| `seat` | 💺 | seat | seat | Travel & Places |
| `helicopter` | 🚁 | helicopter | helicopter | Travel & Places |
| `suspension-railway` | 🚟 | suspension, railway | suspension railway | Travel & Places |
| `mountain-cableway` | 🚠 | mountain, cableway | mountain cableway | Travel & Places |
| `aerial-tramway` | 🚡 | aerial, tramway | aerial tramway | Travel & Places |
| `satellite` | 🛰️ | satellite | satellite | Travel & Places |
| `rocket` | 🚀 | rocket | rocket | Travel & Places |
| `flying-saucer` | 🛸 | flying, saucer | flying saucer | Travel & Places |
| `bellhop-bell` | 🛎️ | bellhop, bell | bellhop bell | Travel & Places |
| `luggage` | 🧳 | luggage | luggage | Travel & Places |
| `hourglass-done` | ⌛ | hourglass, done | hourglass done | Travel & Places |
| `hourglass-not-done` | ⏳ | hourglass, not, done | hourglass not done | Travel & Places |
| `watch` | ⌚ | watch | watch | Travel & Places |
| `alarm-clock` | ⏰ | alarm, clock | alarm clock | Travel & Places |
| `stopwatch` | ⏱️ | stopwatch | stopwatch | Travel & Places |
| `timer-clock` | ⏲️ | timer, clock | timer clock | Travel & Places |
| `mantelpiece-clock` | 🕰️ | mantelpiece, clock | mantelpiece clock | Travel & Places |
| `twelve-o-clock` | 🕛 | clock | twelve o’clock | Travel & Places |
| `twelve-thirty` | 🕧 | thirty | twelve-thirty | Travel & Places |
| `one-o-clock` | 🕐 | clock | one o’clock | Travel & Places |
| `one-thirty` | 🕜 | thirty | one-thirty | Travel & Places |
| `two-o-clock` | 🕑 | clock | two o’clock | Travel & Places |
| `two-thirty` | 🕝 | thirty | two-thirty | Travel & Places |
| `three-o-clock` | 🕒 | clock | three o’clock | Travel & Places |
| `three-thirty` | 🕞 | thirty | three-thirty | Travel & Places |
| `four-o-clock` | 🕓 | clock | four o’clock | Travel & Places |
| `four-thirty` | 🕟 | thirty | four-thirty | Travel & Places |
| `five-o-clock` | 🕔 | clock | five o’clock | Travel & Places |
| `five-thirty` | 🕠 | thirty | five-thirty | Travel & Places |
| `six-o-clock` | 🕕 | clock | six o’clock | Travel & Places |
| `six-thirty` | 🕡 | thirty | six-thirty | Travel & Places |
| `seven-o-clock` | 🕖 | clock | seven o’clock | Travel & Places |
| `seven-thirty` | 🕢 | thirty | seven-thirty | Travel & Places |
| `eight-o-clock` | 🕗 | clock | eight o’clock | Travel & Places |
| `eight-thirty` | 🕣 | thirty | eight-thirty | Travel & Places |
| `nine-o-clock` | 🕘 | clock | nine o’clock | Travel & Places |
| `nine-thirty` | 🕤 | thirty | nine-thirty | Travel & Places |
| `ten-o-clock` | 🕙 | clock | ten o’clock | Travel & Places |
| `ten-thirty` | 🕥 | thirty | ten-thirty | Travel & Places |
| `eleven-o-clock` | 🕚 | clock | eleven o’clock | Travel & Places |
| `eleven-thirty` | 🕦 | thirty | eleven-thirty | Travel & Places |
| `new-moon` | 🌑 | new, moon | new moon | Travel & Places |
| `waxing-crescent-moon` | 🌒 | waxing, crescent, moon | waxing crescent moon | Travel & Places |
| `first-quarter-moon` | 🌓 | first, quarter, moon | first quarter moon | Travel & Places |
| `waxing-gibbous-moon` | 🌔 | waxing, gibbous, moon | waxing gibbous moon | Travel & Places |
| `full-moon` | 🌕 | full, moon | full moon | Travel & Places |
| `waning-gibbous-moon` | 🌖 | waning, gibbous, moon | waning gibbous moon | Travel & Places |
| `last-quarter-moon` | 🌗 | last, quarter, moon | last quarter moon | Travel & Places |
| `waning-crescent-moon` | 🌘 | waning, crescent, moon | waning crescent moon | Travel & Places |
| `crescent-moon` | 🌙 | crescent, moon | crescent moon | Travel & Places |
| `new-moon-face` | 🌚 | new, moon | new moon face | Travel & Places |
| `first-quarter-moon-face` | 🌛 | first, quarter, moon | first quarter moon face | Travel & Places |
| `last-quarter-moon-face` | 🌜 | last, quarter, moon | last quarter moon face | Travel & Places |
| `thermometer` | 🌡️ | thermometer | thermometer | Travel & Places |
| `sun` | ☀️ | sun | sun | Travel & Places |
| `full-moon-face` | 🌝 | full, moon | full moon face | Travel & Places |
| `sun-with-face` | 🌞 | sun | sun with face | Travel & Places |
| `ringed-planet` | 🪐 | ringed, planet | ringed planet | Travel & Places |
| `star` | ⭐ | star | star | Travel & Places |
| `glowing-star` | 🌟 | glowing, star | glowing star | Travel & Places |
| `shooting-star` | 🌠 | shooting, star | shooting star | Travel & Places |
| `milky-way` | 🌌 | milky, way | milky way | Travel & Places |
| `cloud` | ☁️ | cloud | cloud | Travel & Places |
| `sun-behind-cloud` | ⛅ | sun, behind, cloud | sun behind cloud | Travel & Places |
| `cloud-with-lightning-and-rain` | ⛈️ | cloud, lightning, rain | cloud with lightning and rain | Travel & Places |
| `sun-behind-small-cloud` | 🌤️ | sun, behind, small, cloud | sun behind small cloud | Travel & Places |
| `sun-behind-large-cloud` | 🌥️ | sun, behind, large, cloud | sun behind large cloud | Travel & Places |
| `sun-behind-rain-cloud` | 🌦️ | sun, behind, rain, cloud | sun behind rain cloud | Travel & Places |
| `cloud-with-rain` | 🌧️ | cloud, rain | cloud with rain | Travel & Places |
| `cloud-with-snow` | 🌨️ | cloud, snow | cloud with snow | Travel & Places |
| `cloud-with-lightning` | 🌩️ | cloud, lightning | cloud with lightning | Travel & Places |
| `tornado` | 🌪️ | tornado | tornado | Travel & Places |
| `fog` | 🌫️ | fog | fog | Travel & Places |
| `wind-face` | 🌬️ | wind | wind face | Travel & Places |
| `cyclone` | 🌀 | cyclone | cyclone | Travel & Places |
| `rainbow` | 🌈 | rainbow | rainbow | Travel & Places |
| `closed-umbrella` | 🌂 | closed, umbrella | closed umbrella | Travel & Places |
| `umbrella` | ☂️ | umbrella | umbrella | Travel & Places |
| `umbrella-with-rain-drops` | ☔ | umbrella, rain, drops, drop | umbrella with rain drops | Travel & Places |
| `umbrella-on-ground` | ⛱️ | umbrella, ground | umbrella on ground | Travel & Places |
| `high-voltage` | ⚡ | high, voltage | high voltage | Travel & Places |
| `snowflake` | ❄️ | snowflake | snowflake | Travel & Places |
| `snowman` | ☃️ | snowman | snowman | Travel & Places |
| `snowman-without-snow` | ⛄ | snowman, without, snow | snowman without snow | Travel & Places |
| `comet` | ☄️ | comet | comet | Travel & Places |
| `fire` | 🔥 | fire | fire | Travel & Places |
| `droplet` | 💧 | droplet | droplet | Travel & Places |
| `water-wave` | 🌊 | water, wave | water wave | Travel & Places |
| `jack-o-lantern` | 🎃 | jack, lantern | jack-o-lantern | Activities |
| `christmas-tree` | 🎄 | christmas, christma, tree | Christmas tree | Activities |
| `fireworks` | 🎆 | fireworks, firework | fireworks | Activities |
| `sparkler` | 🎇 | sparkler | sparkler | Activities |
| `firecracker` | 🧨 | firecracker | firecracker | Activities |
| `sparkles` | ✨ | sparkles, sparkle | sparkles | Activities |
| `balloon` | 🎈 | balloon | balloon | Activities |
| `party-popper` | 🎉 | party, popper | party popper | Activities |
| `confetti-ball` | 🎊 | confetti, ball | confetti ball | Activities |
| `tanabata-tree` | 🎋 | tanabata, tree | tanabata tree | Activities |
| `pine-decoration` | 🎍 | pine, decoration | pine decoration | Activities |
| `japanese-dolls` | 🎎 | japanese, dolls, doll | Japanese dolls | Activities |
| `carp-streamer` | 🎏 | carp, streamer | carp streamer | Activities |
| `wind-chime` | 🎐 | wind, chime | wind chime | Activities |
| `moon-viewing-ceremony` | 🎑 | moon, viewing, ceremony | moon viewing ceremony | Activities |
| `red-envelope` | 🧧 | red, envelope | red envelope | Activities |
| `ribbon` | 🎀 | ribbon | ribbon | Activities |
| `wrapped-gift` | 🎁 | wrapped, gift | wrapped gift | Activities |
| `reminder-ribbon` | 🎗️ | reminder, ribbon | reminder ribbon | Activities |
| `admission-tickets` | 🎟️ | admission, tickets, ticket | admission tickets | Activities |
| `ticket` | 🎫 | ticket | ticket | Activities |
| `military-medal` | 🎖️ | military, medal | military medal | Activities |
| `trophy` | 🏆 | trophy | trophy | Activities |
| `sports-medal` | 🏅 | sports, sport, medal | sports medal | Activities |
| `1st-place-medal` | 🥇 | 1st, place, medal | 1st place medal | Activities |
| `2nd-place-medal` | 🥈 | 2nd, place, medal | 2nd place medal | Activities |
| `3rd-place-medal` | 🥉 | 3rd, place, medal | 3rd place medal | Activities |
| `soccer-ball` | ⚽ | soccer, ball | soccer ball | Activities |
| `baseball` | ⚾ | baseball | baseball | Activities |
| `softball` | 🥎 | softball | softball | Activities |
| `basketball` | 🏀 | basketball | basketball | Activities |
| `volleyball` | 🏐 | volleyball | volleyball | Activities |
| `american-football` | 🏈 | american, football | american football | Activities |
| `rugby-football` | 🏉 | rugby, football | rugby football | Activities |
| `tennis` | 🎾 | tennis | tennis | Activities |
| `flying-disc` | 🥏 | flying, disc | flying disc | Activities |
| `bowling` | 🎳 | bowling | bowling | Activities |
| `cricket-game` | 🏏 | cricket, game | cricket game | Activities |
| `field-hockey` | 🏑 | field, hockey | field hockey | Activities |
| `ice-hockey` | 🏒 | ice, hockey | ice hockey | Activities |
| `lacrosse` | 🥍 | lacrosse | lacrosse | Activities |
| `ping-pong` | 🏓 | ping, pong | ping pong | Activities |
| `badminton` | 🏸 | badminton | badminton | Activities |
| `boxing-glove` | 🥊 | boxing, glove | boxing glove | Activities |
| `martial-arts-uniform` | 🥋 | martial, arts, art, uniform | martial arts uniform | Activities |
| `goal-net` | 🥅 | goal, net | goal net | Activities |
| `flag-in-hole` | ⛳ | hole | flag in hole | Activities |
| `ice-skate` | ⛸️ | ice, skate | ice skate | Activities |
| `fishing-pole` | 🎣 | fishing, pole | fishing pole | Activities |
| `diving-mask` | 🤿 | diving, mask | diving mask | Activities |
| `running-shirt` | 🎽 | running, shirt | running shirt | Activities |
| `skis` | 🎿 | skis | skis | Activities |
| `sled` | 🛷 | sled | sled | Activities |
| `curling-stone` | 🥌 | curling, stone | curling stone | Activities |
| `bullseye` | 🎯 | bullseye | bullseye | Activities |
| `yo-yo` | 🪀 | yo | yo-yo | Activities |
| `kite` | 🪁 | kite | kite | Activities |
| `water-pistol` | 🔫 | water, pistol | water pistol | Activities |
| `pool-8-ball` | 🎱 | pool, ball | pool 8 ball | Activities |
| `crystal-ball` | 🔮 | crystal, ball | crystal ball | Activities |
| `magic-wand` | 🪄 | magic, wand | magic wand | Activities |
| `video-game` | 🎮 | video, game | video game | Activities |
| `joystick` | 🕹️ | joystick | joystick | Activities |
| `slot-machine` | 🎰 | slot, machine | slot machine | Activities |
| `game-die` | 🎲 | game, die | game die | Activities |
| `puzzle-piece` | 🧩 | puzzle, piece | puzzle piece | Activities |
| `teddy-bear` | 🧸 | teddy, bear | teddy bear | Activities |
| `pi-ata` | 🪅 | pi, ata | piñata | Activities |
| `mirror-ball` | 🪩 | mirror, ball | mirror ball | Activities |
| `nesting-dolls` | 🪆 | nesting, dolls, doll | nesting dolls | Activities |
| `spade-suit` | ♠️ | spade, suit | spade suit | Activities |
| `heart-suit` | ♥️ | heart, suit | heart suit | Activities |
| `diamond-suit` | ♦️ | diamond, suit | diamond suit | Activities |
| `club-suit` | ♣️ | club, suit | club suit | Activities |
| `chess-pawn` | ♟️ | chess, pawn | chess pawn | Activities |
| `joker` | 🃏 | joker | joker | Activities |
| `mahjong-red-dragon` | 🀄 | mahjong, red, dragon | mahjong red dragon | Activities |
| `flower-playing-cards` | 🎴 | flower, playing, cards, card | flower playing cards | Activities |
| `performing-arts` | 🎭 | performing, arts, art | performing arts | Activities |
| `framed-picture` | 🖼️ | framed, picture | framed picture | Activities |
| `artist-palette` | 🎨 | artist, palette | artist palette | Activities |
| `thread` | 🧵 | thread | thread | Activities |
| `sewing-needle` | 🪡 | sewing, needle | sewing needle | Activities |
| `yarn` | 🧶 | yarn | yarn | Activities |
| `knot` | 🪢 | knot | knot | Activities |
| `glasses` | 👓 | glasses, glass | glasses | Objects |
| `sunglasses` | 🕶️ | sunglasses, sunglass | sunglasses | Objects |
| `goggles` | 🥽 | goggles, goggle | goggles | Objects |
| `lab-coat` | 🥼 | lab, coat | lab coat | Objects |
| `safety-vest` | 🦺 | safety, vest | safety vest | Objects |
| `necktie` | 👔 | necktie | necktie | Objects |
| `t-shirt` | 👕 | shirt | t-shirt | Objects |
| `jeans` | 👖 | jeans, jean | jeans | Objects |
| `scarf` | 🧣 | scarf | scarf | Objects |
| `gloves` | 🧤 | gloves, glove | gloves | Objects |
| `coat` | 🧥 | coat | coat | Objects |
| `socks` | 🧦 | socks, sock | socks | Objects |
| `dress` | 👗 | dress | dress | Objects |
| `kimono` | 👘 | kimono | kimono | Objects |
| `sari` | 🥻 | sari | sari | Objects |
| `one-piece-swimsuit` | 🩱 | piece, swimsuit | one-piece swimsuit | Objects |
| `briefs` | 🩲 | briefs, brief | briefs | Objects |
| `shorts` | 🩳 | shorts, short | shorts | Objects |
| `bikini` | 👙 | bikini | bikini | Objects |
| `woman-s-clothes` | 👚 | woman, clothes, clothe | woman’s clothes | Objects |
| `folding-hand-fan` | 🪭 | folding, hand, fan | folding hand fan | Objects |
| `purse` | 👛 | purse | purse | Objects |
| `handbag` | 👜 | handbag | handbag | Objects |
| `clutch-bag` | 👝 | clutch, bag | clutch bag | Objects |
| `shopping-bags` | 🛍️ | shopping, bags, bag | shopping bags | Objects |
| `backpack` | 🎒 | backpack | backpack | Objects |
| `thong-sandal` | 🩴 | thong, sandal | thong sandal | Objects |
| `man-s-shoe` | 👞 | man, shoe | man’s shoe | Objects |
| `running-shoe` | 👟 | running, shoe | running shoe | Objects |
| `hiking-boot` | 🥾 | hiking, boot | hiking boot | Objects |
| `flat-shoe` | 🥿 | flat, shoe | flat shoe | Objects |
| `high-heeled-shoe` | 👠 | high, heeled, shoe | high-heeled shoe | Objects |
| `woman-s-sandal` | 👡 | woman, sandal | woman’s sandal | Objects |
| `ballet-shoes` | 🩰 | ballet, shoes, shoe | ballet shoes | Objects |
| `woman-s-boot` | 👢 | woman, boot | woman’s boot | Objects |
| `hair-pick` | 🪮 | hair, pick | hair pick | Objects |
| `crown` | 👑 | crown | crown | Objects |
| `woman-s-hat` | 👒 | woman, hat | woman’s hat | Objects |
| `top-hat` | 🎩 | top, hat | top hat | Objects |
| `graduation-cap` | 🎓 | graduation, cap | graduation cap | Objects |
| `billed-cap` | 🧢 | billed, cap | billed cap | Objects |
| `military-helmet` | 🪖 | military, helmet | military helmet | Objects |
| `rescue-worker-s-helmet` | ⛑️ | rescue, worker, helmet | rescue worker’s helmet | Objects |
| `prayer-beads` | 📿 | prayer, beads, bead | prayer beads | Objects |
| `lipstick` | 💄 | lipstick | lipstick | Objects |
| `ring` | 💍 | ring | ring | Objects |
| `gem-stone` | 💎 | gem, stone | gem stone | Objects |
| `muted-speaker` | 🔇 | muted, speaker | muted speaker | Objects |
| `speaker-low-volume` | 🔈 | speaker, low, volume | speaker low volume | Objects |
| `speaker-medium-volume` | 🔉 | speaker, medium, volume | speaker medium volume | Objects |
| `speaker-high-volume` | 🔊 | speaker, high, volume | speaker high volume | Objects |
| `loudspeaker` | 📢 | loudspeaker | loudspeaker | Objects |
| `megaphone` | 📣 | megaphone | megaphone | Objects |
| `postal-horn` | 📯 | postal, horn | postal horn | Objects |
| `bell` | 🔔 | bell | bell | Objects |
| `bell-with-slash` | 🔕 | bell, slash | bell with slash | Objects |
| `musical-score` | 🎼 | musical, score | musical score | Objects |
| `musical-note` | 🎵 | musical, note | musical note | Objects |
| `musical-notes` | 🎶 | musical, notes, note | musical notes | Objects |
| `studio-microphone` | 🎙️ | studio, microphone | studio microphone | Objects |
| `level-slider` | 🎚️ | level, slider | level slider | Objects |
| `control-knobs` | 🎛️ | control, knobs, knob | control knobs | Objects |
| `microphone` | 🎤 | microphone | microphone | Objects |
| `headphone` | 🎧 | headphone | headphone | Objects |
| `radio` | 📻 | radio | radio | Objects |
| `saxophone` | 🎷 | saxophone | saxophone | Objects |
| `accordion` | 🪗 | accordion | accordion | Objects |
| `guitar` | 🎸 | guitar | guitar | Objects |
| `musical-keyboard` | 🎹 | musical, keyboard | musical keyboard | Objects |
| `trumpet` | 🎺 | trumpet | trumpet | Objects |
| `violin` | 🎻 | violin | violin | Objects |
| `banjo` | 🪕 | banjo | banjo | Objects |
| `drum` | 🥁 | drum | drum | Objects |
| `long-drum` | 🪘 | long, drum | long drum | Objects |
| `maracas` | 🪇 | maracas, maraca | maracas | Objects |
| `flute` | 🪈 | flute | flute | Objects |
| `mobile-phone` | 📱 | mobile, phone | mobile phone | Objects |
| `mobile-phone-with-arrow` | 📲 | mobile, phone, arrow | mobile phone with arrow | Objects |
| `telephone` | ☎️ | telephone | telephone | Objects |
| `telephone-receiver` | 📞 | telephone, receiver | telephone receiver | Objects |
| `pager` | 📟 | pager | pager | Objects |
| `fax-machine` | 📠 | fax, machine | fax machine | Objects |
| `battery` | 🔋 | battery | battery | Objects |
| `low-battery` | 🪫 | low, battery | low battery | Objects |
| `electric-plug` | 🔌 | electric, plug | electric plug | Objects |
| `laptop` | 💻 | laptop | laptop | Objects |
| `desktop-computer` | 🖥️ | desktop, computer | desktop computer | Objects |
| `printer` | 🖨️ | printer | printer | Objects |
| `keyboard` | ⌨️ | keyboard | keyboard | Objects |
| `computer-mouse` | 🖱️ | computer, mouse | computer mouse | Objects |
| `trackball` | 🖲️ | trackball | trackball | Objects |
| `computer-disk` | 💽 | computer, disk | computer disk | Objects |
| `floppy-disk` | 💾 | floppy, disk | floppy disk | Objects |
| `optical-disk` | 💿 | optical, disk | optical disk | Objects |
| `dvd` | 📀 | dvd | dvd | Objects |
| `abacus` | 🧮 | abacus | abacus | Objects |
| `movie-camera` | 🎥 | movie, camera | movie camera | Objects |
| `film-frames` | 🎞️ | film, frames, frame | film frames | Objects |
| `film-projector` | 📽️ | film, projector | film projector | Objects |
| `clapper-board` | 🎬 | clapper, board | clapper board | Objects |
| `television` | 📺 | television | television | Objects |
| `camera` | 📷 | camera | camera | Objects |
| `camera-with-flash` | 📸 | camera, flash | camera with flash | Objects |
| `video-camera` | 📹 | video, camera | video camera | Objects |
| `videocassette` | 📼 | videocassette | videocassette | Objects |
| `magnifying-glass-tilted-left` | 🔍 | magnifying, glass, tilted, left | magnifying glass tilted left | Objects |
| `magnifying-glass-tilted-right` | 🔎 | magnifying, glass, tilted, right | magnifying glass tilted right | Objects |
| `candle` | 🕯️ | candle | candle | Objects |
| `light-bulb` | 💡 | light, bulb | light bulb | Objects |
| `flashlight` | 🔦 | flashlight | flashlight | Objects |
| `red-paper-lantern` | 🏮 | red, paper, lantern | red paper lantern | Objects |
| `diya-lamp` | 🪔 | diya, lamp | diya lamp | Objects |
| `notebook-with-decorative-cover` | 📔 | notebook, decorative, cover | notebook with decorative cover | Objects |
| `closed-book` | 📕 | closed, book | closed book | Objects |
| `open-book` | 📖 | open, book | open book | Objects |
| `green-book` | 📗 | green, book | green book | Objects |
| `blue-book` | 📘 | blue, book | blue book | Objects |
| `orange-book` | 📙 | orange, book | orange book | Objects |
| `books` | 📚 | books, book | books | Objects |
| `notebook` | 📓 | notebook | notebook | Objects |
| `ledger` | 📒 | ledger | ledger | Objects |
| `page-with-curl` | 📃 | page, curl | page with curl | Objects |
| `scroll` | 📜 | scroll | scroll | Objects |
| `page-facing-up` | 📄 | page, facing, up | page facing up | Objects |
| `newspaper` | 📰 | newspaper | newspaper | Objects |
| `rolled-up-newspaper` | 🗞️ | rolled, up, newspaper | rolled-up newspaper | Objects |
| `bookmark-tabs` | 📑 | bookmark, tabs, tab | bookmark tabs | Objects |
| `bookmark` | 🔖 | bookmark | bookmark | Objects |
| `label` | 🏷️ | label | label | Objects |
| `money-bag` | 💰 | money, bag | money bag | Objects |
| `coin` | 🪙 | coin | coin | Objects |
| `yen-banknote` | 💴 | yen, banknote | yen banknote | Objects |
| `dollar-banknote` | 💵 | dollar, banknote | dollar banknote | Objects |
| `euro-banknote` | 💶 | euro, banknote | euro banknote | Objects |
| `pound-banknote` | 💷 | pound, banknote | pound banknote | Objects |
| `money-with-wings` | 💸 | money, wings, wing | money with wings | Objects |
| `credit-card` | 💳 | credit, card | credit card | Objects |
| `receipt` | 🧾 | receipt | receipt | Objects |
| `chart-increasing-with-yen` | 💹 | chart, increasing, yen | chart increasing with yen | Objects |
| `envelope` | ✉️ | envelope | envelope | Objects |
| `e-mail` | 📧 | mail | e-mail | Objects |
| `incoming-envelope` | 📨 | incoming, envelope | incoming envelope | Objects |
| `envelope-with-arrow` | 📩 | envelope, arrow | envelope with arrow | Objects |
| `outbox-tray` | 📤 | outbox, tray | outbox tray | Objects |
| `inbox-tray` | 📥 | inbox, tray | inbox tray | Objects |
| `package` | 📦 | package | package | Objects |
| `closed-mailbox-with-raised-flag` | 📫 | closed, mailbox, raised | closed mailbox with raised flag | Objects |
| `closed-mailbox-with-lowered-flag` | 📪 | closed, mailbox, lowered | closed mailbox with lowered flag | Objects |
| `open-mailbox-with-raised-flag` | 📬 | open, mailbox, raised | open mailbox with raised flag | Objects |
| `open-mailbox-with-lowered-flag` | 📭 | open, mailbox, lowered | open mailbox with lowered flag | Objects |
| `postbox` | 📮 | postbox | postbox | Objects |
| `ballot-box-with-ballot` | 🗳️ | ballot, box | ballot box with ballot | Objects |
| `pencil` | ✏️ | pencil | pencil | Objects |
| `black-nib` | ✒️ | black, nib | black nib | Objects |
| `fountain-pen` | 🖋️ | fountain, pen | fountain pen | Objects |
| `pen` | 🖊️ | pen | pen | Objects |
| `paintbrush` | 🖌️ | paintbrush | paintbrush | Objects |
| `crayon` | 🖍️ | crayon | crayon | Objects |
| `memo` | 📝 | memo | memo | Objects |
| `briefcase` | 💼 | briefcase | briefcase | Objects |
| `file-folder` | 📁 | file, folder | file folder | Objects |
| `open-file-folder` | 📂 | open, file, folder | open file folder | Objects |
| `card-index-dividers` | 🗂️ | card, index, dividers, divider | card index dividers | Objects |
| `calendar` | 📅 | calendar | calendar | Objects |
| `tear-off-calendar` | 📆 | tear, off, calendar | tear-off calendar | Objects |
| `spiral-notepad` | 🗒️ | spiral, notepad | spiral notepad | Objects |
| `spiral-calendar` | 🗓️ | spiral, calendar | spiral calendar | Objects |
| `card-index` | 📇 | card, index | card index | Objects |
| `chart-increasing` | 📈 | chart, increasing | chart increasing | Objects |
| `chart-decreasing` | 📉 | chart, decreasing | chart decreasing | Objects |
| `bar-chart` | 📊 | bar, chart | bar chart | Objects |
| `clipboard` | 📋 | clipboard | clipboard | Objects |
| `pushpin` | 📌 | pushpin | pushpin | Objects |
| `round-pushpin` | 📍 | round, pushpin | round pushpin | Objects |
| `paperclip` | 📎 | paperclip | paperclip | Objects |
| `linked-paperclips` | 🖇️ | linked, paperclips, paperclip | linked paperclips | Objects |
| `straight-ruler` | 📏 | straight, ruler | straight ruler | Objects |
| `triangular-ruler` | 📐 | triangular, ruler | triangular ruler | Objects |
| `scissors` | ✂️ | scissors, scissor | scissors | Objects |
| `card-file-box` | 🗃️ | card, file, box | card file box | Objects |
| `file-cabinet` | 🗄️ | file, cabinet | file cabinet | Objects |
| `wastebasket` | 🗑️ | wastebasket | wastebasket | Objects |
| `locked` | 🔒 | locked | locked | Objects |
| `unlocked` | 🔓 | unlocked | unlocked | Objects |
| `locked-with-pen` | 🔏 | locked, pen | locked with pen | Objects |
| `locked-with-key` | 🔐 | locked, key | locked with key | Objects |
| `key` | 🔑 | key | key | Objects |
| `old-key` | 🗝️ | old, key | old key | Objects |
| `hammer` | 🔨 | hammer | hammer | Objects |
| `axe` | 🪓 | axe | axe | Objects |
| `pick` | ⛏️ | pick | pick | Objects |
| `hammer-and-pick` | ⚒️ | hammer, pick | hammer and pick | Objects |
| `hammer-and-wrench` | 🛠️ | hammer, wrench | hammer and wrench | Objects |
| `dagger` | 🗡️ | dagger | dagger | Objects |
| `crossed-swords` | ⚔️ | crossed, swords, sword | crossed swords | Objects |
| `bomb` | 💣 | bomb | bomb | Objects |
| `boomerang` | 🪃 | boomerang | boomerang | Objects |
| `bow-and-arrow` | 🏹 | bow, arrow | bow and arrow | Objects |
| `shield` | 🛡️ | shield | shield | Objects |
| `carpentry-saw` | 🪚 | carpentry, saw | carpentry saw | Objects |
| `wrench` | 🔧 | wrench | wrench | Objects |
| `screwdriver` | 🪛 | screwdriver | screwdriver | Objects |
| `nut-and-bolt` | 🔩 | nut, bolt | nut and bolt | Objects |
| `gear` | ⚙️ | gear | gear | Objects |
| `clamp` | 🗜️ | clamp | clamp | Objects |
| `balance-scale` | ⚖️ | balance, scale | balance scale | Objects |
| `white-cane` | 🦯 | white, cane | white cane | Objects |
| `link` | 🔗 | link | link | Objects |
| `broken-chain` | ⛓️‍💥 | broken, chain | broken chain | Objects |
| `chains` | ⛓️ | chains, chain | chains | Objects |
| `hook` | 🪝 | hook | hook | Objects |
| `toolbox` | 🧰 | toolbox | toolbox | Objects |
| `magnet` | 🧲 | magnet | magnet | Objects |
| `ladder` | 🪜 | ladder | ladder | Objects |
| `alembic` | ⚗️ | alembic | alembic | Objects |
| `test-tube` | 🧪 | test, tube | test tube | Objects |
| `petri-dish` | 🧫 | petri, dish | petri dish | Objects |
| `dna` | 🧬 | dna | dna | Objects |
| `microscope` | 🔬 | microscope | microscope | Objects |
| `telescope` | 🔭 | telescope | telescope | Objects |
| `satellite-antenna` | 📡 | satellite, antenna | satellite antenna | Objects |
| `syringe` | 💉 | syringe | syringe | Objects |
| `drop-of-blood` | 🩸 | drop, blood | drop of blood | Objects |
| `pill` | 💊 | pill | pill | Objects |
| `adhesive-bandage` | 🩹 | adhesive, bandage | adhesive bandage | Objects |
| `crutch` | 🩼 | crutch | crutch | Objects |
| `stethoscope` | 🩺 | stethoscope | stethoscope | Objects |
| `x-ray` | 🩻 | ray | x-ray | Objects |
| `door` | 🚪 | door | door | Objects |
| `elevator` | 🛗 | elevator | elevator | Objects |
| `mirror` | 🪞 | mirror | mirror | Objects |
| `window` | 🪟 | window | window | Objects |
| `bed` | 🛏️ | bed | bed | Objects |
| `couch-and-lamp` | 🛋️ | couch, lamp | couch and lamp | Objects |
| `chair` | 🪑 | chair | chair | Objects |
| `toilet` | 🚽 | toilet | toilet | Objects |
| `plunger` | 🪠 | plunger | plunger | Objects |
| `shower` | 🚿 | shower | shower | Objects |
| `bathtub` | 🛁 | bathtub | bathtub | Objects |
| `mouse-trap` | 🪤 | mouse, trap | mouse trap | Objects |
| `razor` | 🪒 | razor | razor | Objects |
| `lotion-bottle` | 🧴 | lotion, bottle | lotion bottle | Objects |
| `safety-pin` | 🧷 | safety, pin | safety pin | Objects |
| `broom` | 🧹 | broom | broom | Objects |
| `basket` | 🧺 | basket | basket | Objects |
| `roll-of-paper` | 🧻 | roll, paper | roll of paper | Objects |
| `bucket` | 🪣 | bucket | bucket | Objects |
| `soap` | 🧼 | soap | soap | Objects |
| `bubbles` | 🫧 | bubbles, bubble | bubbles | Objects |
| `toothbrush` | 🪥 | toothbrush | toothbrush | Objects |
| `sponge` | 🧽 | sponge | sponge | Objects |
| `fire-extinguisher` | 🧯 | fire, extinguisher | fire extinguisher | Objects |
| `shopping-cart` | 🛒 | shopping, cart | shopping cart | Objects |
| `cigarette` | 🚬 | cigarette | cigarette | Objects |
| `coffin` | ⚰️ | coffin | coffin | Objects |
| `headstone` | 🪦 | headstone | headstone | Objects |
| `funeral-urn` | ⚱️ | funeral, urn | funeral urn | Objects |
| `nazar-amulet` | 🧿 | nazar, amulet | nazar amulet | Objects |
| `hamsa` | 🪬 | hamsa | hamsa | Objects |
| `moai` | 🗿 | moai | moai | Objects |
| `placard` | 🪧 | placard | placard | Objects |
| `identification-card` | 🪪 | identification, card | identification card | Objects |
| `atm-sign` | 🏧 | atm | ATM sign | Symbols |
| `litter-in-bin-sign` | 🚮 | litter, bin | litter in bin sign | Symbols |
| `potable-water` | 🚰 | potable, water | potable water | Symbols |
| `wheelchair-symbol` | ♿ | wheelchair | wheelchair symbol | Symbols |
| `men-s-room` | 🚹 | men, room | men’s room | Symbols |
| `women-s-room` | 🚺 | women, room | women’s room | Symbols |
| `restroom` | 🚻 | restroom | restroom | Symbols |
| `baby-symbol` | 🚼 | baby | baby symbol | Symbols |
| `water-closet` | 🚾 | water, closet | water closet | Symbols |
| `passport-control` | 🛂 | passport, control | passport control | Symbols |
| `customs` | 🛃 | customs, custom | customs | Symbols |
| `baggage-claim` | 🛄 | baggage, claim | baggage claim | Symbols |
| `left-luggage` | 🛅 | left, luggage | left luggage | Symbols |
| `warning` | ⚠️ | warning | warning | Symbols |
| `children-crossing` | 🚸 | children, crossing | children crossing | Symbols |
| `no-entry` | ⛔ | no, entry | no entry | Symbols |
| `prohibited` | 🚫 | prohibited | prohibited | Symbols |
| `no-bicycles` | 🚳 | no, bicycles, bicycle | no bicycles | Symbols |
| `no-smoking` | 🚭 | no, smoking | no smoking | Symbols |
| `no-littering` | 🚯 | no, littering | no littering | Symbols |
| `non-potable-water` | 🚱 | non, potable, water | non-potable water | Symbols |
| `no-pedestrians` | 🚷 | no, pedestrians, pedestrian | no pedestrians | Symbols |
| `no-mobile-phones` | 📵 | no, mobile, phones, phone | no mobile phones | Symbols |
| `no-one-under-eighteen` | 🔞 | no, under, eighteen | no one under eighteen | Symbols |
| `radioactive` | ☢️ | radioactive | radioactive | Symbols |
| `biohazard` | ☣️ | biohazard | biohazard | Symbols |
| `up-arrow` | ⬆️ | up, arrow | up arrow | Symbols |
| `up-right-arrow` | ↗️ | up, right, arrow | up-right arrow | Symbols |
| `right-arrow` | ➡️ | right, arrow | right arrow | Symbols |
| `down-right-arrow` | ↘️ | down, right, arrow | down-right arrow | Symbols |
| `down-arrow` | ⬇️ | down, arrow | down arrow | Symbols |
| `down-left-arrow` | ↙️ | down, left, arrow | down-left arrow | Symbols |
| `left-arrow` | ⬅️ | left, arrow | left arrow | Symbols |
| `up-left-arrow` | ↖️ | up, left, arrow | up-left arrow | Symbols |
| `up-down-arrow` | ↕️ | up, down, arrow | up-down arrow | Symbols |
| `left-right-arrow` | ↔️ | left, right, arrow | left-right arrow | Symbols |
| `right-arrow-curving-left` | ↩️ | right, arrow, curving, left | right arrow curving left | Symbols |
| `left-arrow-curving-right` | ↪️ | left, arrow, curving, right | left arrow curving right | Symbols |
| `right-arrow-curving-up` | ⤴️ | right, arrow, curving, up | right arrow curving up | Symbols |
| `right-arrow-curving-down` | ⤵️ | right, arrow, curving, down | right arrow curving down | Symbols |
| `clockwise-vertical-arrows` | 🔃 | clockwise, vertical, arrows, arrow | clockwise vertical arrows | Symbols |
| `counterclockwise-arrows-button` | 🔄 | counterclockwise, arrows, arrow, button | counterclockwise arrows button | Symbols |
| `back-arrow` | 🔙 | back, arrow | BACK arrow | Symbols |
| `end-arrow` | 🔚 | end, arrow | END arrow | Symbols |
| `on-arrow` | 🔛 | arrow | ON! arrow | Symbols |
| `soon-arrow` | 🔜 | soon, arrow | SOON arrow | Symbols |
| `top-arrow` | 🔝 | top, arrow | TOP arrow | Symbols |
| `place-of-worship` | 🛐 | place, worship | place of worship | Symbols |
| `atom-symbol` | ⚛️ | atom | atom symbol | Symbols |
| `om` | 🕉️ | om | om | Symbols |
| `star-of-david` | ✡️ | star, david | star of David | Symbols |
| `wheel-of-dharma` | ☸️ | wheel, dharma | wheel of dharma | Symbols |
| `yin-yang` | ☯️ | yin, yang | yin yang | Symbols |
| `latin-cross` | ✝️ | latin, cross | latin cross | Symbols |
| `orthodox-cross` | ☦️ | orthodox, cross | orthodox cross | Symbols |
| `star-and-crescent` | ☪️ | star, crescent | star and crescent | Symbols |
| `peace-symbol` | ☮️ | peace | peace symbol | Symbols |
| `menorah` | 🕎 | menorah | menorah | Symbols |
| `dotted-six-pointed-star` | 🔯 | dotted, pointed, star | dotted six-pointed star | Symbols |
| `khanda` | 🪯 | khanda | khanda | Symbols |
| `aries` | ♈ | aries, ary | Aries | Symbols |
| `taurus` | ♉ | taurus | Taurus | Symbols |
| `gemini` | ♊ | gemini | Gemini | Symbols |
| `cancer` | ♋ | cancer | Cancer | Symbols |
| `leo` | ♌ | leo | Leo | Symbols |
| `virgo` | ♍ | virgo | Virgo | Symbols |
| `libra` | ♎ | libra | Libra | Symbols |
| `scorpio` | ♏ | scorpio | Scorpio | Symbols |
| `sagittarius` | ♐ | sagittarius | Sagittarius | Symbols |
| `capricorn` | ♑ | capricorn | Capricorn | Symbols |
| `aquarius` | ♒ | aquarius | Aquarius | Symbols |
| `pisces` | ♓ | pisces, pisce | Pisces | Symbols |
| `ophiuchus` | ⛎ | ophiuchus | Ophiuchus | Symbols |
| `shuffle-tracks-button` | 🔀 | shuffle, tracks, track, button | shuffle tracks button | Symbols |
| `repeat-button` | 🔁 | repeat, button | repeat button | Symbols |
| `repeat-single-button` | 🔂 | repeat, single, button | repeat single button | Symbols |
| `play-button` | ▶️ | play, button | play button | Symbols |
| `fast-forward-button` | ⏩ | fast, forward, button | fast-forward button | Symbols |
| `next-track-button` | ⏭️ | next, track, button | next track button | Symbols |
| `play-or-pause-button` | ⏯️ | play, pause, button | play or pause button | Symbols |
| `reverse-button` | ◀️ | reverse, button | reverse button | Symbols |
| `fast-reverse-button` | ⏪ | fast, reverse, button | fast reverse button | Symbols |
| `last-track-button` | ⏮️ | last, track, button | last track button | Symbols |
| `upwards-button` | 🔼 | upwards, upward, button | upwards button | Symbols |
| `fast-up-button` | ⏫ | fast, up, button | fast up button | Symbols |
| `downwards-button` | 🔽 | downwards, downward, button | downwards button | Symbols |
| `fast-down-button` | ⏬ | fast, down, button | fast down button | Symbols |
| `pause-button` | ⏸️ | pause, button | pause button | Symbols |
| `stop-button` | ⏹️ | stop, button | stop button | Symbols |
| `record-button` | ⏺️ | record, button | record button | Symbols |
| `eject-button` | ⏏️ | eject, button | eject button | Symbols |
| `cinema` | 🎦 | cinema | cinema | Symbols |
| `dim-button` | 🔅 | dim, button | dim button | Symbols |
| `bright-button` | 🔆 | bright, button | bright button | Symbols |
| `antenna-bars` | 📶 | antenna, bars, bar | antenna bars | Symbols |
| `wireless` | 🛜 | wireless | wireless | Symbols |
| `vibration-mode` | 📳 | vibration, mode | vibration mode | Symbols |
| `mobile-phone-off` | 📴 | mobile, phone, off | mobile phone off | Symbols |
| `female-sign` | ♀️ | female | female sign | Symbols |
| `male-sign` | ♂️ | male | male sign | Symbols |
| `transgender-symbol` | ⚧️ | transgender | transgender symbol | Symbols |
| `multiply` | ✖️ | multiply | multiply | Symbols |
| `plus` | ➕ | plus | plus | Symbols |
| `minus` | ➖ | minus | minus | Symbols |
| `divide` | ➗ | divide | divide | Symbols |
| `heavy-equals-sign` | 🟰 | heavy, equals, equal | heavy equals sign | Symbols |
| `infinity` | ♾️ | infinity | infinity | Symbols |
| `double-exclamation-mark` | ‼️ | double, exclamation, mark | double exclamation mark | Symbols |
| `exclamation-question-mark` | ⁉️ | exclamation, question, mark | exclamation question mark | Symbols |
| `red-question-mark` | ❓ | red, question, mark | red question mark | Symbols |
| `white-question-mark` | ❔ | white, question, mark | white question mark | Symbols |
| `white-exclamation-mark` | ❕ | white, exclamation, mark | white exclamation mark | Symbols |
| `red-exclamation-mark` | ❗ | red, exclamation, mark | red exclamation mark | Symbols |
| `wavy-dash` | 〰️ | wavy, dash | wavy dash | Symbols |
| `currency-exchange` | 💱 | currency, exchange | currency exchange | Symbols |
| `heavy-dollar-sign` | 💲 | heavy, dollar | heavy dollar sign | Symbols |
| `medical-symbol` | ⚕️ | medical | medical symbol | Symbols |
| `recycling-symbol` | ♻️ | recycling | recycling symbol | Symbols |
| `fleur-de-lis` | ⚜️ | fleur, de, lis | fleur-de-lis | Symbols |
| `trident-emblem` | 🔱 | trident, emblem | trident emblem | Symbols |
| `name-badge` | 📛 | name, badge | name badge | Symbols |
| `japanese-symbol-for-beginner` | 🔰 | japanese, beginner | Japanese symbol for beginner | Symbols |
| `hollow-red-circle` | ⭕ | hollow, red, circle | hollow red circle | Symbols |
| `check-mark-button` | ✅ | check, mark, button | check mark button | Symbols |
| `check-box-with-check` | ☑️ | check, box | check box with check | Symbols |
| `check-mark` | ✔️ | check, mark | check mark | Symbols |
| `cross-mark` | ❌ | cross, mark | cross mark | Symbols |
| `cross-mark-button` | ❎ | cross, mark, button | cross mark button | Symbols |
| `curly-loop` | ➰ | curly, loop | curly loop | Symbols |
| `double-curly-loop` | ➿ | double, curly, loop | double curly loop | Symbols |
| `part-alternation-mark` | 〽️ | part, alternation, mark | part alternation mark | Symbols |
| `eight-spoked-asterisk` | ✳️ | spoked, asterisk | eight-spoked asterisk | Symbols |
| `eight-pointed-star` | ✴️ | pointed, star | eight-pointed star | Symbols |
| `sparkle` | ❇️ | sparkle | sparkle | Symbols |
| `copyright` | ©️ | copyright | copyright | Symbols |
| `registered` | ®️ | registered | registered | Symbols |
| `trade-mark` | ™️ | trade, mark | trade mark | Symbols |
| `keycap-hash` | #️⃣ | keycap, hash | keycap: # | Symbols |
| `keycap-asterisk` | *️⃣ | keycap, asterisk | keycap: * | Symbols |
| `keycap-0` | 0️⃣ | keycap | keycap: 0 | Symbols |
| `keycap-1` | 1️⃣ | keycap | keycap: 1 | Symbols |
| `keycap-2` | 2️⃣ | keycap | keycap: 2 | Symbols |
| `keycap-3` | 3️⃣ | keycap | keycap: 3 | Symbols |
| `keycap-4` | 4️⃣ | keycap | keycap: 4 | Symbols |
| `keycap-5` | 5️⃣ | keycap | keycap: 5 | Symbols |
| `keycap-6` | 6️⃣ | keycap | keycap: 6 | Symbols |
| `keycap-7` | 7️⃣ | keycap | keycap: 7 | Symbols |
| `keycap-8` | 8️⃣ | keycap | keycap: 8 | Symbols |
| `keycap-9` | 9️⃣ | keycap | keycap: 9 | Symbols |
| `keycap-10` | 🔟 | 10 | keycap: 10 | Symbols |
| `input-latin-uppercase` | 🔠 | input, latin, uppercase | input latin uppercase | Symbols |
| `input-latin-lowercase` | 🔡 | input, latin, lowercase | input latin lowercase | Symbols |
| `input-numbers` | 🔢 | input, numbers, number | input numbers | Symbols |
| `input-symbols` | 🔣 | input, symbols, symbol | input symbols | Symbols |
| `input-latin-letters` | 🔤 | input, latin, letters, letter | input latin letters | Symbols |
| `a-button-blood-type` | 🅰️ | button, blood, type | A button (blood type) | Symbols |
| `ab-button-blood-type` | 🆎 | ab, button, blood, type | AB button (blood type) | Symbols |
| `b-button-blood-type` | 🅱️ | button, blood, type | B button (blood type) | Symbols |
| `cl-button` | 🆑 | cl, button | CL button | Symbols |
| `cool-button` | 🆒 | cool, button | COOL button | Symbols |
| `free-button` | 🆓 | free, button | FREE button | Symbols |
| `information` | ℹ️ | information | information | Symbols |
| `id-button` | 🆔 | id, button | ID button | Symbols |
| `circled-m` | Ⓜ️ | circled | circled M | Symbols |
| `new-button` | 🆕 | new, button | NEW button | Symbols |
| `ng-button` | 🆖 | ng, button | NG button | Symbols |
| `o-button-blood-type` | 🅾️ | button, blood, type | O button (blood type) | Symbols |
| `ok-button` | 🆗 | ok, button | OK button | Symbols |
| `p-button` | 🅿️ | button | P button | Symbols |
| `sos-button` | 🆘 | sos, button | SOS button | Symbols |
| `up-button` | 🆙 | up, button | UP! button | Symbols |
| `vs-button` | 🆚 | vs, button | VS button | Symbols |
| `japanese-here-button` | 🈁 | japanese, here, button | Japanese “here” button | Symbols |
| `japanese-service-charge-button` | 🈂️ | japanese, service, charge, button | Japanese “service charge” button | Symbols |
| `japanese-monthly-amount-button` | 🈷️ | japanese, monthly, amount, button | Japanese “monthly amount” button | Symbols |
| `japanese-not-free-of-charge-button` | 🈶 | japanese, not, free, charge, button | Japanese “not free of charge” button | Symbols |
| `japanese-reserved-button` | 🈯 | japanese, reserved, button | Japanese “reserved” button | Symbols |
| `japanese-bargain-button` | 🉐 | japanese, bargain, button | Japanese “bargain” button | Symbols |
| `japanese-discount-button` | 🈹 | japanese, discount, button | Japanese “discount” button | Symbols |
| `japanese-free-of-charge-button` | 🈚 | japanese, free, charge, button | Japanese “free of charge” button | Symbols |
| `japanese-prohibited-button` | 🈲 | japanese, prohibited, button | Japanese “prohibited” button | Symbols |
| `japanese-acceptable-button` | 🉑 | japanese, acceptable, button | Japanese “acceptable” button | Symbols |
| `japanese-application-button` | 🈸 | japanese, application, button | Japanese “application” button | Symbols |
| `japanese-passing-grade-button` | 🈴 | japanese, passing, grade, button | Japanese “passing grade” button | Symbols |
| `japanese-vacancy-button` | 🈳 | japanese, vacancy, button | Japanese “vacancy” button | Symbols |
| `japanese-congratulations-button` | ㊗️ | japanese, congratulations, congratulation, button | Japanese “congratulations” button | Symbols |
| `japanese-secret-button` | ㊙️ | japanese, secret, button | Japanese “secret” button | Symbols |
| `japanese-open-for-business-button` | 🈺 | japanese, open, business, button | Japanese “open for business” button | Symbols |
| `japanese-no-vacancy-button` | 🈵 | japanese, no, vacancy, button | Japanese “no vacancy” button | Symbols |
| `red-circle` | 🔴 | red, circle | red circle | Symbols |
| `orange-circle` | 🟠 | orange, circle | orange circle | Symbols |
| `yellow-circle` | 🟡 | yellow, circle | yellow circle | Symbols |
| `green-circle` | 🟢 | green, circle | green circle | Symbols |
| `blue-circle` | 🔵 | blue, circle | blue circle | Symbols |
| `purple-circle` | 🟣 | purple, circle | purple circle | Symbols |
| `brown-circle` | 🟤 | brown, circle | brown circle | Symbols |
| `black-circle` | ⚫ | black, circle | black circle | Symbols |
| `white-circle` | ⚪ | white, circle | white circle | Symbols |
| `red-square` | 🟥 | red, square | red square | Symbols |
| `orange-square` | 🟧 | orange, square | orange square | Symbols |
| `yellow-square` | 🟨 | yellow, square | yellow square | Symbols |
| `green-square` | 🟩 | green, square | green square | Symbols |
| `blue-square` | 🟦 | blue, square | blue square | Symbols |
| `purple-square` | 🟪 | purple, square | purple square | Symbols |
| `brown-square` | 🟫 | brown, square | brown square | Symbols |
| `black-large-square` | ⬛ | black, large, square | black large square | Symbols |
| `white-large-square` | ⬜ | white, large, square | white large square | Symbols |
| `black-medium-square` | ◼️ | black, medium, square | black medium square | Symbols |
| `white-medium-square` | ◻️ | white, medium, square | white medium square | Symbols |
| `black-medium-small-square` | ◾ | black, medium, small, square | black medium-small square | Symbols |
| `white-medium-small-square` | ◽ | white, medium, small, square | white medium-small square | Symbols |
| `black-small-square` | ▪️ | black, small, square | black small square | Symbols |
| `white-small-square` | ▫️ | white, small, square | white small square | Symbols |
| `large-orange-diamond` | 🔶 | large, orange, diamond | large orange diamond | Symbols |
| `large-blue-diamond` | 🔷 | large, blue, diamond | large blue diamond | Symbols |
| `small-orange-diamond` | 🔸 | small, orange, diamond | small orange diamond | Symbols |
| `small-blue-diamond` | 🔹 | small, blue, diamond | small blue diamond | Symbols |
| `red-triangle-pointed-up` | 🔺 | red, triangle, pointed, up | red triangle pointed up | Symbols |
| `red-triangle-pointed-down` | 🔻 | red, triangle, pointed, down | red triangle pointed down | Symbols |
| `diamond-with-a-dot` | 💠 | diamond, dot | diamond with a dot | Symbols |
| `radio-button` | 🔘 | radio, button | radio button | Symbols |
| `white-square-button` | 🔳 | white, square, button | white square button | Symbols |
| `black-square-button` | 🔲 | black, square, button | black square button | Symbols |
| `chequered-flag` | 🏁 | chequered | chequered flag | Flags |
| `triangular-flag` | 🚩 | triangular | triangular flag | Flags |
| `crossed-flags` | 🎌 | crossed, flags, flag | crossed flags | Flags |
| `black-flag` | 🏴 | black | black flag | Flags |
| `white-flag` | 🏳️ | white | white flag | Flags |
| `rainbow-flag` | 🏳️‍🌈 | rainbow | rainbow flag | Flags |
| `transgender-flag` | 🏳️‍⚧️ | transgender | transgender flag | Flags |
| `pirate-flag` | 🏴‍☠️ | pirate | pirate flag | Flags |
| `flag-ascension-island` | 🇦🇨 | ascension, island | flag: Ascension Island | Flags |
| `flag-andorra` | 🇦🇩 | andorra | flag: Andorra | Flags |
| `flag-united-arab-emirates` | 🇦🇪 | united, arab, emirates, emirate | flag: United Arab Emirates | Flags |
| `flag-afghanistan` | 🇦🇫 | afghanistan | flag: Afghanistan | Flags |
| `flag-antigua-barbuda` | 🇦🇬 | antigua, barbuda | flag: Antigua & Barbuda | Flags |
| `flag-anguilla` | 🇦🇮 | anguilla | flag: Anguilla | Flags |
| `flag-albania` | 🇦🇱 | albania | flag: Albania | Flags |
| `flag-armenia` | 🇦🇲 | armenia | flag: Armenia | Flags |
| `flag-angola` | 🇦🇴 | angola | flag: Angola | Flags |
| `flag-antarctica` | 🇦🇶 | antarctica | flag: Antarctica | Flags |
| `flag-argentina` | 🇦🇷 | argentina | flag: Argentina | Flags |
| `flag-american-samoa` | 🇦🇸 | american, samoa | flag: American Samoa | Flags |
| `flag-austria` | 🇦🇹 | austria | flag: Austria | Flags |
| `flag-australia` | 🇦🇺 | australia | flag: Australia | Flags |
| `flag-aruba` | 🇦🇼 | aruba | flag: Aruba | Flags |
| `flag-land-islands` | 🇦🇽 | land, islands, island | flag: Åland Islands | Flags |
| `flag-azerbaijan` | 🇦🇿 | azerbaijan | flag: Azerbaijan | Flags |
| `flag-bosnia-herzegovina` | 🇧🇦 | bosnia, herzegovina | flag: Bosnia & Herzegovina | Flags |
| `flag-barbados` | 🇧🇧 | barbados | flag: Barbados | Flags |
| `flag-bangladesh` | 🇧🇩 | bangladesh | flag: Bangladesh | Flags |
| `flag-belgium` | 🇧🇪 | belgium | flag: Belgium | Flags |
| `flag-burkina-faso` | 🇧🇫 | burkina, faso | flag: Burkina Faso | Flags |
| `flag-bulgaria` | 🇧🇬 | bulgaria | flag: Bulgaria | Flags |
| `flag-bahrain` | 🇧🇭 | bahrain | flag: Bahrain | Flags |
| `flag-burundi` | 🇧🇮 | burundi | flag: Burundi | Flags |
| `flag-benin` | 🇧🇯 | benin | flag: Benin | Flags |
| `flag-st-barth-lemy` | 🇧🇱 | st, barth, lemy | flag: St. Barthélemy | Flags |
| `flag-bermuda` | 🇧🇲 | bermuda | flag: Bermuda | Flags |
| `flag-brunei` | 🇧🇳 | brunei | flag: Brunei | Flags |
| `flag-bolivia` | 🇧🇴 | bolivia | flag: Bolivia | Flags |
| `flag-caribbean-netherlands` | 🇧🇶 | caribbean, netherlands, netherland | flag: Caribbean Netherlands | Flags |
| `flag-brazil` | 🇧🇷 | brazil | flag: Brazil | Flags |
| `flag-bahamas` | 🇧🇸 | bahamas, bahama | flag: Bahamas | Flags |
| `flag-bhutan` | 🇧🇹 | bhutan | flag: Bhutan | Flags |
| `flag-bouvet-island` | 🇧🇻 | bouvet, island | flag: Bouvet Island | Flags |
| `flag-botswana` | 🇧🇼 | botswana | flag: Botswana | Flags |
| `flag-belarus` | 🇧🇾 | belarus | flag: Belarus | Flags |
| `flag-belize` | 🇧🇿 | belize | flag: Belize | Flags |
| `flag-canada` | 🇨🇦 | canada | flag: Canada | Flags |
| `flag-cocos-keeling-islands` | 🇨🇨 | cocos, keeling, islands, island | flag: Cocos (Keeling) Islands | Flags |
| `flag-congo-kinshasa` | 🇨🇩 | congo, kinshasa | flag: Congo - Kinshasa | Flags |
| `flag-central-african-republic` | 🇨🇫 | central, african, republic | flag: Central African Republic | Flags |
| `flag-congo-brazzaville` | 🇨🇬 | congo, brazzaville | flag: Congo - Brazzaville | Flags |
| `flag-switzerland` | 🇨🇭 | switzerland | flag: Switzerland | Flags |
| `flag-c-te-d-ivoire` | 🇨🇮 | te, ivoire | flag: Côte d’Ivoire | Flags |
| `flag-cook-islands` | 🇨🇰 | cook, islands, island | flag: Cook Islands | Flags |
| `flag-chile` | 🇨🇱 | chile | flag: Chile | Flags |
| `flag-cameroon` | 🇨🇲 | cameroon | flag: Cameroon | Flags |
| `flag-china` | 🇨🇳 | china | flag: China | Flags |
| `flag-colombia` | 🇨🇴 | colombia | flag: Colombia | Flags |
| `flag-clipperton-island` | 🇨🇵 | clipperton, island | flag: Clipperton Island | Flags |
| `flag-costa-rica` | 🇨🇷 | costa, rica | flag: Costa Rica | Flags |
| `flag-cuba` | 🇨🇺 | cuba | flag: Cuba | Flags |
| `flag-cape-verde` | 🇨🇻 | cape, verde | flag: Cape Verde | Flags |
| `flag-cura-ao` | 🇨🇼 | cura, ao | flag: Curaçao | Flags |
| `flag-christmas-island` | 🇨🇽 | christmas, christma, island | flag: Christmas Island | Flags |
| `flag-cyprus` | 🇨🇾 | cyprus | flag: Cyprus | Flags |
| `flag-czechia` | 🇨🇿 | czechia | flag: Czechia | Flags |
| `flag-germany` | 🇩🇪 | germany | flag: Germany | Flags |
| `flag-diego-garcia` | 🇩🇬 | diego, garcia | flag: Diego Garcia | Flags |
| `flag-djibouti` | 🇩🇯 | djibouti | flag: Djibouti | Flags |
| `flag-denmark` | 🇩🇰 | denmark | flag: Denmark | Flags |
| `flag-dominica` | 🇩🇲 | dominica | flag: Dominica | Flags |
| `flag-dominican-republic` | 🇩🇴 | dominican, republic | flag: Dominican Republic | Flags |
| `flag-algeria` | 🇩🇿 | algeria | flag: Algeria | Flags |
| `flag-ceuta-melilla` | 🇪🇦 | ceuta, melilla | flag: Ceuta & Melilla | Flags |
| `flag-ecuador` | 🇪🇨 | ecuador | flag: Ecuador | Flags |
| `flag-estonia` | 🇪🇪 | estonia | flag: Estonia | Flags |
| `flag-egypt` | 🇪🇬 | egypt | flag: Egypt | Flags |
| `flag-western-sahara` | 🇪🇭 | western, sahara | flag: Western Sahara | Flags |
| `flag-eritrea` | 🇪🇷 | eritrea | flag: Eritrea | Flags |
| `flag-spain` | 🇪🇸 | spain | flag: Spain | Flags |
| `flag-ethiopia` | 🇪🇹 | ethiopia | flag: Ethiopia | Flags |
| `flag-european-union` | 🇪🇺 | european, union | flag: European Union | Flags |
| `flag-finland` | 🇫🇮 | finland | flag: Finland | Flags |
| `flag-fiji` | 🇫🇯 | fiji | flag: Fiji | Flags |
| `flag-falkland-islands` | 🇫🇰 | falkland, islands, island | flag: Falkland Islands | Flags |
| `flag-micronesia` | 🇫🇲 | micronesia | flag: Micronesia | Flags |
| `flag-faroe-islands` | 🇫🇴 | faroe, islands, island | flag: Faroe Islands | Flags |
| `flag-france` | 🇫🇷 | france | flag: France | Flags |
| `flag-gabon` | 🇬🇦 | gabon | flag: Gabon | Flags |
| `flag-united-kingdom` | 🇬🇧 | united, kingdom | flag: United Kingdom | Flags |
| `flag-grenada` | 🇬🇩 | grenada | flag: Grenada | Flags |
| `flag-georgia` | 🇬🇪 | georgia | flag: Georgia | Flags |
| `flag-french-guiana` | 🇬🇫 | french, guiana | flag: French Guiana | Flags |
| `flag-guernsey` | 🇬🇬 | guernsey | flag: Guernsey | Flags |
| `flag-ghana` | 🇬🇭 | ghana | flag: Ghana | Flags |
| `flag-gibraltar` | 🇬🇮 | gibraltar | flag: Gibraltar | Flags |
| `flag-greenland` | 🇬🇱 | greenland | flag: Greenland | Flags |
| `flag-gambia` | 🇬🇲 | gambia | flag: Gambia | Flags |
| `flag-guinea` | 🇬🇳 | guinea | flag: Guinea | Flags |
| `flag-guadeloupe` | 🇬🇵 | guadeloupe | flag: Guadeloupe | Flags |
| `flag-equatorial-guinea` | 🇬🇶 | equatorial, guinea | flag: Equatorial Guinea | Flags |
| `flag-greece` | 🇬🇷 | greece | flag: Greece | Flags |
| `flag-south-georgia-south-sandwich-islands` | 🇬🇸 | south, georgia, sandwich, islands, island | flag: South Georgia & South Sandwich Islands | Flags |
| `flag-guatemala` | 🇬🇹 | guatemala | flag: Guatemala | Flags |
| `flag-guam` | 🇬🇺 | guam | flag: Guam | Flags |
| `flag-guinea-bissau` | 🇬🇼 | guinea, bissau | flag: Guinea-Bissau | Flags |
| `flag-guyana` | 🇬🇾 | guyana | flag: Guyana | Flags |
| `flag-hong-kong-sar-china` | 🇭🇰 | hong, kong, sar, china | flag: Hong Kong SAR China | Flags |
| `flag-heard-mcdonald-islands` | 🇭🇲 | heard, mcdonald, islands, island | flag: Heard & McDonald Islands | Flags |
| `flag-honduras` | 🇭🇳 | honduras, hondura | flag: Honduras | Flags |
| `flag-croatia` | 🇭🇷 | croatia | flag: Croatia | Flags |
| `flag-haiti` | 🇭🇹 | haiti | flag: Haiti | Flags |
| `flag-hungary` | 🇭🇺 | hungary | flag: Hungary | Flags |
| `flag-canary-islands` | 🇮🇨 | canary, islands, island | flag: Canary Islands | Flags |
| `flag-indonesia` | 🇮🇩 | indonesia | flag: Indonesia | Flags |
| `flag-ireland` | 🇮🇪 | ireland | flag: Ireland | Flags |
| `flag-israel` | 🇮🇱 | israel | flag: Israel | Flags |
| `flag-isle-of-man` | 🇮🇲 | isle, man | flag: Isle of Man | Flags |
| `flag-india` | 🇮🇳 | india | flag: India | Flags |
| `flag-british-indian-ocean-territory` | 🇮🇴 | british, indian, ocean, territory | flag: British Indian Ocean Territory | Flags |
| `flag-iraq` | 🇮🇶 | iraq | flag: Iraq | Flags |
| `flag-iran` | 🇮🇷 | iran | flag: Iran | Flags |
| `flag-iceland` | 🇮🇸 | iceland | flag: Iceland | Flags |
| `flag-italy` | 🇮🇹 | italy | flag: Italy | Flags |
| `flag-jersey` | 🇯🇪 | jersey | flag: Jersey | Flags |
| `flag-jamaica` | 🇯🇲 | jamaica | flag: Jamaica | Flags |
| `flag-jordan` | 🇯🇴 | jordan | flag: Jordan | Flags |
| `flag-japan` | 🇯🇵 | japan | flag: Japan | Flags |
| `flag-kenya` | 🇰🇪 | kenya | flag: Kenya | Flags |
| `flag-kyrgyzstan` | 🇰🇬 | kyrgyzstan | flag: Kyrgyzstan | Flags |
| `flag-cambodia` | 🇰🇭 | cambodia | flag: Cambodia | Flags |
| `flag-kiribati` | 🇰🇮 | kiribati | flag: Kiribati | Flags |
| `flag-comoros` | 🇰🇲 | comoros | flag: Comoros | Flags |
| `flag-st-kitts-nevis` | 🇰🇳 | st, kitts, kitt, nevis | flag: St. Kitts & Nevis | Flags |
| `flag-north-korea` | 🇰🇵 | north, korea | flag: North Korea | Flags |
| `flag-south-korea` | 🇰🇷 | south, korea | flag: South Korea | Flags |
| `flag-kuwait` | 🇰🇼 | kuwait | flag: Kuwait | Flags |
| `flag-cayman-islands` | 🇰🇾 | cayman, islands, island | flag: Cayman Islands | Flags |
| `flag-kazakhstan` | 🇰🇿 | kazakhstan | flag: Kazakhstan | Flags |
| `flag-laos` | 🇱🇦 | laos | flag: Laos | Flags |
| `flag-lebanon` | 🇱🇧 | lebanon | flag: Lebanon | Flags |
| `flag-st-lucia` | 🇱🇨 | st, lucia | flag: St. Lucia | Flags |
| `flag-liechtenstein` | 🇱🇮 | liechtenstein | flag: Liechtenstein | Flags |
| `flag-sri-lanka` | 🇱🇰 | sri, lanka | flag: Sri Lanka | Flags |
| `flag-liberia` | 🇱🇷 | liberia | flag: Liberia | Flags |
| `flag-lesotho` | 🇱🇸 | lesotho | flag: Lesotho | Flags |
| `flag-lithuania` | 🇱🇹 | lithuania | flag: Lithuania | Flags |
| `flag-luxembourg` | 🇱🇺 | luxembourg | flag: Luxembourg | Flags |
| `flag-latvia` | 🇱🇻 | latvia | flag: Latvia | Flags |
| `flag-libya` | 🇱🇾 | libya | flag: Libya | Flags |
| `flag-morocco` | 🇲🇦 | morocco | flag: Morocco | Flags |
| `flag-monaco` | 🇲🇨 | monaco | flag: Monaco | Flags |
| `flag-moldova` | 🇲🇩 | moldova | flag: Moldova | Flags |
| `flag-montenegro` | 🇲🇪 | montenegro | flag: Montenegro | Flags |
| `flag-st-martin` | 🇲🇫 | st, martin | flag: St. Martin | Flags |
| `flag-madagascar` | 🇲🇬 | madagascar | flag: Madagascar | Flags |
| `flag-marshall-islands` | 🇲🇭 | marshall, islands, island | flag: Marshall Islands | Flags |
| `flag-north-macedonia` | 🇲🇰 | north, macedonia | flag: North Macedonia | Flags |
| `flag-mali` | 🇲🇱 | mali | flag: Mali | Flags |
| `flag-myanmar-burma` | 🇲🇲 | myanmar, burma | flag: Myanmar (Burma) | Flags |
| `flag-mongolia` | 🇲🇳 | mongolia | flag: Mongolia | Flags |
| `flag-macao-sar-china` | 🇲🇴 | macao, sar, china | flag: Macao SAR China | Flags |
| `flag-northern-mariana-islands` | 🇲🇵 | northern, mariana, islands, island | flag: Northern Mariana Islands | Flags |
| `flag-martinique` | 🇲🇶 | martinique | flag: Martinique | Flags |
| `flag-mauritania` | 🇲🇷 | mauritania | flag: Mauritania | Flags |
| `flag-montserrat` | 🇲🇸 | montserrat | flag: Montserrat | Flags |
| `flag-malta` | 🇲🇹 | malta | flag: Malta | Flags |
| `flag-mauritius` | 🇲🇺 | mauritius | flag: Mauritius | Flags |
| `flag-maldives` | 🇲🇻 | maldives, maldive | flag: Maldives | Flags |
| `flag-malawi` | 🇲🇼 | malawi | flag: Malawi | Flags |
| `flag-mexico` | 🇲🇽 | mexico | flag: Mexico | Flags |
| `flag-malaysia` | 🇲🇾 | malaysia | flag: Malaysia | Flags |
| `flag-mozambique` | 🇲🇿 | mozambique | flag: Mozambique | Flags |
| `flag-namibia` | 🇳🇦 | namibia | flag: Namibia | Flags |
| `flag-new-caledonia` | 🇳🇨 | new, caledonia | flag: New Caledonia | Flags |
| `flag-niger` | 🇳🇪 | niger | flag: Niger | Flags |
| `flag-norfolk-island` | 🇳🇫 | norfolk, island | flag: Norfolk Island | Flags |
| `flag-nigeria` | 🇳🇬 | nigeria | flag: Nigeria | Flags |
| `flag-nicaragua` | 🇳🇮 | nicaragua | flag: Nicaragua | Flags |
| `flag-netherlands` | 🇳🇱 | netherlands, netherland | flag: Netherlands | Flags |
| `flag-norway` | 🇳🇴 | norway | flag: Norway | Flags |
| `flag-nepal` | 🇳🇵 | nepal | flag: Nepal | Flags |
| `flag-nauru` | 🇳🇷 | nauru | flag: Nauru | Flags |
| `flag-niue` | 🇳🇺 | niue | flag: Niue | Flags |
| `flag-new-zealand` | 🇳🇿 | new, zealand | flag: New Zealand | Flags |
| `flag-oman` | 🇴🇲 | oman | flag: Oman | Flags |
| `flag-panama` | 🇵🇦 | panama | flag: Panama | Flags |
| `flag-peru` | 🇵🇪 | peru | flag: Peru | Flags |
| `flag-french-polynesia` | 🇵🇫 | french, polynesia | flag: French Polynesia | Flags |
| `flag-papua-new-guinea` | 🇵🇬 | papua, new, guinea | flag: Papua New Guinea | Flags |
| `flag-philippines` | 🇵🇭 | philippines, philippine | flag: Philippines | Flags |
| `flag-pakistan` | 🇵🇰 | pakistan | flag: Pakistan | Flags |
| `flag-poland` | 🇵🇱 | poland | flag: Poland | Flags |
| `flag-st-pierre-miquelon` | 🇵🇲 | st, pierre, miquelon | flag: St. Pierre & Miquelon | Flags |
| `flag-pitcairn-islands` | 🇵🇳 | pitcairn, islands, island | flag: Pitcairn Islands | Flags |
| `flag-puerto-rico` | 🇵🇷 | puerto, rico | flag: Puerto Rico | Flags |
| `flag-palestinian-territories` | 🇵🇸 | palestinian, territories, territory | flag: Palestinian Territories | Flags |
| `flag-portugal` | 🇵🇹 | portugal | flag: Portugal | Flags |
| `flag-palau` | 🇵🇼 | palau | flag: Palau | Flags |
| `flag-paraguay` | 🇵🇾 | paraguay | flag: Paraguay | Flags |
| `flag-qatar` | 🇶🇦 | qatar | flag: Qatar | Flags |
| `flag-r-union` | 🇷🇪 | union | flag: Réunion | Flags |
| `flag-romania` | 🇷🇴 | romania | flag: Romania | Flags |
| `flag-serbia` | 🇷🇸 | serbia | flag: Serbia | Flags |
| `flag-russia` | 🇷🇺 | russia | flag: Russia | Flags |
| `flag-rwanda` | 🇷🇼 | rwanda | flag: Rwanda | Flags |
| `flag-saudi-arabia` | 🇸🇦 | saudi, arabia | flag: Saudi Arabia | Flags |
| `flag-solomon-islands` | 🇸🇧 | solomon, islands, island | flag: Solomon Islands | Flags |
| `flag-seychelles` | 🇸🇨 | seychelles, seychelle | flag: Seychelles | Flags |
| `flag-sudan` | 🇸🇩 | sudan | flag: Sudan | Flags |
| `flag-sweden` | 🇸🇪 | sweden | flag: Sweden | Flags |
| `flag-singapore` | 🇸🇬 | singapore | flag: Singapore | Flags |
| `flag-st-helena` | 🇸🇭 | st, helena | flag: St. Helena | Flags |
| `flag-slovenia` | 🇸🇮 | slovenia | flag: Slovenia | Flags |
| `flag-svalbard-jan-mayen` | 🇸🇯 | svalbard, jan, mayen | flag: Svalbard & Jan Mayen | Flags |
| `flag-slovakia` | 🇸🇰 | slovakia | flag: Slovakia | Flags |
| `flag-sierra-leone` | 🇸🇱 | sierra, leone | flag: Sierra Leone | Flags |
| `flag-san-marino` | 🇸🇲 | san, marino | flag: San Marino | Flags |
| `flag-senegal` | 🇸🇳 | senegal | flag: Senegal | Flags |
| `flag-somalia` | 🇸🇴 | somalia | flag: Somalia | Flags |
| `flag-suriname` | 🇸🇷 | suriname | flag: Suriname | Flags |
| `flag-south-sudan` | 🇸🇸 | south, sudan | flag: South Sudan | Flags |
| `flag-s-o-tom-pr-ncipe` | 🇸🇹 | tom, pr, ncipe | flag: São Tomé & Príncipe | Flags |
| `flag-el-salvador` | 🇸🇻 | el, salvador | flag: El Salvador | Flags |
| `flag-sint-maarten` | 🇸🇽 | sint, maarten | flag: Sint Maarten | Flags |
| `flag-syria` | 🇸🇾 | syria | flag: Syria | Flags |
| `flag-eswatini` | 🇸🇿 | eswatini | flag: Eswatini | Flags |
| `flag-tristan-da-cunha` | 🇹🇦 | tristan, da, cunha | flag: Tristan da Cunha | Flags |
| `flag-turks-caicos-islands` | 🇹🇨 | turks, turk, caicos, islands, island | flag: Turks & Caicos Islands | Flags |
| `flag-chad` | 🇹🇩 | chad | flag: Chad | Flags |
| `flag-french-southern-territories` | 🇹🇫 | french, southern, territories, territory | flag: French Southern Territories | Flags |
| `flag-togo` | 🇹🇬 | togo | flag: Togo | Flags |
| `flag-thailand` | 🇹🇭 | thailand | flag: Thailand | Flags |
| `flag-tajikistan` | 🇹🇯 | tajikistan | flag: Tajikistan | Flags |
| `flag-tokelau` | 🇹🇰 | tokelau | flag: Tokelau | Flags |
| `flag-timor-leste` | 🇹🇱 | timor, leste | flag: Timor-Leste | Flags |
| `flag-turkmenistan` | 🇹🇲 | turkmenistan | flag: Turkmenistan | Flags |
| `flag-tunisia` | 🇹🇳 | tunisia | flag: Tunisia | Flags |
| `flag-tonga` | 🇹🇴 | tonga | flag: Tonga | Flags |
| `flag-t-rkiye` | 🇹🇷 | rkiye | flag: Türkiye | Flags |
| `flag-trinidad-tobago` | 🇹🇹 | trinidad, tobago | flag: Trinidad & Tobago | Flags |
| `flag-tuvalu` | 🇹🇻 | tuvalu | flag: Tuvalu | Flags |
| `flag-taiwan` | 🇹🇼 | taiwan | flag: Taiwan | Flags |
| `flag-tanzania` | 🇹🇿 | tanzania | flag: Tanzania | Flags |
| `flag-ukraine` | 🇺🇦 | ukraine | flag: Ukraine | Flags |
| `flag-uganda` | 🇺🇬 | uganda | flag: Uganda | Flags |
| `flag-u-s-outlying-islands` | 🇺🇲 | outlying, islands, island | flag: U.S. Outlying Islands | Flags |
| `flag-united-nations` | 🇺🇳 | united, nations, nation | flag: United Nations | Flags |
| `flag-united-states` | 🇺🇸 | united, states, state | flag: United States | Flags |
| `flag-uruguay` | 🇺🇾 | uruguay | flag: Uruguay | Flags |
| `flag-uzbekistan` | 🇺🇿 | uzbekistan | flag: Uzbekistan | Flags |
| `flag-vatican-city` | 🇻🇦 | vatican, city | flag: Vatican City | Flags |
| `flag-st-vincent-grenadines` | 🇻🇨 | st, vincent, grenadines, grenadine | flag: St. Vincent & Grenadines | Flags |
| `flag-venezuela` | 🇻🇪 | venezuela | flag: Venezuela | Flags |
| `flag-british-virgin-islands` | 🇻🇬 | british, virgin, islands, island | flag: British Virgin Islands | Flags |
| `flag-u-s-virgin-islands` | 🇻🇮 | virgin, islands, island | flag: U.S. Virgin Islands | Flags |
| `flag-vietnam` | 🇻🇳 | vietnam | flag: Vietnam | Flags |
| `flag-vanuatu` | 🇻🇺 | vanuatu | flag: Vanuatu | Flags |
| `flag-wallis-futuna` | 🇼🇫 | wallis, futuna | flag: Wallis & Futuna | Flags |
| `flag-samoa` | 🇼🇸 | samoa | flag: Samoa | Flags |
| `flag-kosovo` | 🇽🇰 | kosovo | flag: Kosovo | Flags |
| `flag-yemen` | 🇾🇪 | yemen | flag: Yemen | Flags |
| `flag-mayotte` | 🇾🇹 | mayotte | flag: Mayotte | Flags |
| `flag-south-africa` | 🇿🇦 | south, africa | flag: South Africa | Flags |
| `flag-zambia` | 🇿🇲 | zambia | flag: Zambia | Flags |
| `flag-zimbabwe` | 🇿🇼 | zimbabwe | flag: Zimbabwe | Flags |
| `flag-england` | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 | england | flag: England | Flags |
| `flag-scotland` | 🏴󠁧󠁢󠁳󠁣󠁴󠁿 | scotland | flag: Scotland | Flags |
| `flag-wales` | 🏴󠁧󠁢󠁷󠁬󠁳󠁿 | wales, wale | flag: Wales | Flags |

### Resolution and persistence (built 2026-10-11)

`generation/actions.resolve(key, tags, emoji=..., action=..., limit=4)` returns `{hits, candidates, reason}`. A saved canonical `action` wins. Whole keys and all whole tags are matched before split-word fallback; core mappings retain precedence, then exact extended tokens, then extended aliases. An ambiguous alias is never assigned by row order: `cherry` without a saved distinguishing glyph returns `cherries` and `cherry-blossom` as candidates. A saved 🍒 selects `cherries`; 🌸 selects `cherry-blossom`. Extra hits use whole fields only and the total is capped at four. `canonical_mood` and the next-batch queue still use only the 36 core moods.

`generation/emoji.py` extracts complete sequences: regional-indicator flags, subdivision tag flags, variation selectors, keycaps, tones and ZWJ sequences. Exact membership in the checked-in Unicode 15.1 allow-list validates the extracted primary. It does not accept malformed sequences because their prefix happens to be valid. Valid saved emoji remain authoritative; missing emoji uses the resolved token's default. An invalid saved primary exports with safe 🙂 and `unresolved: true`, `resolution_reason: "invalid_emoji"`; original metadata stays intact. Unknown mappings use deterministic fallback tags and `resolution_reason: "unmapped"`; ambiguity uses `"ambiguous_alias"` and its candidate tokens. These diagnostics do not add a generation/review gate.

Both batch and library ZIPs call `media/export_resolutions.describe`. `out/export_resolutions.json` is a schema-v1 ledger of resolution snapshots keyed by SHA-256 of source identity plus input metadata (`emoji`, `key`, `tags`, explicit `action`, fallback exclusions). A source identity is `G###/S#`; imported library stickers use `library/<sid>`. A process lock and `.export-resolutions.lock` serialize atomic writes. Each snapshot stores action, emoji associations, tags, diagnostics and `bank_version`; unchanged inputs reuse it after restart or bank changes. A metadata edit makes another snapshot; restoring the metadata reuses the earlier one. Pack slug, cell, date and filename are contextual. Source media stays untouched. This ledger is file-authoritative and is not yet mirrored to Postgres.

The existing library update API accepts optional `action`: `POST /api/packs/{id}/stickers/{sid}` with `{ "action": "cherries" }` records a canonical token, and `{ "action": "" }` clears it. Unknown tokens return 400 without saving the edit. This supports reversible selections; the Studio picker screen and a dedicated generation-cell selection endpoint remain open.

Manifest v1 adds `bank_version` on each asset, plus `resolution_reason` and `candidates` when unresolved. Consumers should use these arrays rather than infer action associations from filenames. Short public generation codes and asset revision storage are separate open work; current ZIPs still use `G###` and revision 1.

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
  ],
  "grey": [
    {"sticker_id": "<library-sid>", "emoji": "🤣", "original": "🤣-falcon-laugh_laughing_lol_rofl_lmao_lmfao-s08-7k2q-20261008.webm",
     "filename": "🤣-falcon-laugh_laughing_lol_rofl_lmao_lmfao-s08-7k2q-20261008_grey.png", "kb": 2.7}
  ]
}
```

**Grey stand-ins (Haitham, 2026-10-12).** Every animation in a Download .zip (pack or batch) has a PNG right beside it, under its own name plus
`_grey.png` (`🤣-falcon-laugh-s08-7k2q-20261008.webm` -> `🤣-falcon-laugh-s08-7k2q-20261008_grey.png`): the sticker's still (the image sheet's
cell, same `S#`; the video's first frame when the still is gone) as a flat silhouette in one colour, 75% white and 25% black (`#BFBFBF`), the
still's alpha kept as the shape, the whole silhouette 40% transparent (a solid pixel's alpha is 153). It is a palette PNG with 4 alpha levels
(transparent, two edge steps, solid), about 2-4 KB at 512 px. They are listed under `grey` (`original` names the file it stands for), never
`assets`, so Export to collection sends only the stickers (`media/grey.py`).

## 8. Acceptance rules

- Emoji leads every filename as a literal glyph; pack slug, tag, `sNN`, public code, date follow in order.
- The whole pack shares `pack_slug`; each file's code is its source generation's public code (one code per generation, §10).
- `sNN`, generation and exact asset identities survive rejects, edits, and re-exports; duplicate actions are supported.
- Unmapped cells export on a deterministic fallback tag and carry `unresolved: true`; the exporter bank picker UI is still open.
- Every primary emoji is a bank member (core §6 or extended §6b: a well-established public iOS emoji, `is_ios_emoji`); subject+mood stickers carry the primary plus whole-tag extras, at most 4 hits (`canonical_all`).
- Unicode filenames and multi-code-point emoji round-trip through ZIP download/import byte-identical.
- Re-exporting an unchanged version returns identical names and bytes; an edited sticker becomes a new revision under a stable filename, told apart by the manifest.
- Postgres sync cannot silently replace prior asset versions.
- Compatibility holds: one engine, API-first, `out/` authoritative, human approval gates, existing Telegram validation.

## 9. Implementation plan (Mirsal Builder)

Engine functions + JSON contract first, screens second (rule 11); stdlib-first, `pathlib` only (rule 8).

The batch and library ZIP exporters share indexed resolution, exact emoji validation and the persisted interpretation ledger (§6b). The library API stores optional canonical choices. Unresolved cells retain deterministic fallback names and diagnostic manifest fields. These built contracts are described above; the remaining implementation is below.

Still open:

1. **Exporter bank picker UI** — the Studio export dialog offers the bank per `unresolved` cell (one recorded human pick, reversible); until then the fallback stands.
2. **Validation** — existing Telegram checks unchanged; plus filename checks (NFC, no separators, sane length).
3. **Out of scope** — in-app tag/emoji search UI (the tap-emoji and multi-choice search are receiving-app behaviors; the manifest `tags`/`emojis` arrays enable them; pool search stays semantic); pack-merge vs generation-scoped ids; the Telegram upload path (files as-is).

## 10. Pack generation workflow (DECIDED 2026-10-08, implementation open)

How `"generate sticker pack for {subject}"`, `generate more`, regenerate-as-versions, and the public generation codes work. Presets and the claim-ledger core are built; chat/Studio wiring, public codes and asset versions remain open. The workflow reuses the golden path (request → plan → sheet → stills → video → animations → pack) unchanged.

### 10.1 Request claims the next preset grid (always 3×3)

`"generate sticker pack for falcon"` (chat or Studio) is a pack intent: a new pack session (`pack-falcon`) plus a claim queue — the four preset grids in order (`core-v1`, `social-v1`, `reactions-v1`, `daily-v1`), 36 actions total. The first request claims the first **unclaimed** grid, and the sheet job is built from the preset's nine stored actions (prompts, emoji defaults, tags) — never guessed labels. Storage, ids and states are §10.7 (session file + claim rows, not the pack record).

**Built 2026-10-08 (preset engine, no claim queue yet):** `actions.PRESETS` + `FACE_SENTENCES` + `preset_cells`, and `expand(..., preset=)` — an explicit grid name wins (preset words stripped from the subject, preset implies face), otherwise a face-mode 3×3 takes `core-v1`, so `generic emojis` now claims happy → thanks in bank order with bank emoji. Cell keys are `{subject}_{token}`, tags carry token + aliases. The claim ledger core is built (§10.7); what is still open is the wiring: every emoji request still takes `core-v1` because no chat or Studio path calls the ledger yet, and `generate more` does not advance the queue.

Neither the auto expander nor the AI enhancer chooses 2×2 vs 3×3 here: a preset grid is nine slots by definition, so preset packs are always 3×3. The expander fills the deterministic plan, the enhancer only improves wording. 2×2 stays for the freeform flows only.

Claim state lives in the session file `out/pack_sessions/<slug>.json`, not the library pack record (§10.7): an unclaimed grid is a preset with no claim row. The claim is written synchronously **before** any paid call, so two simultaneous `generate more` clicks serialize: the second sees the first's `CLAIMED` row and takes the next grid. When the sheet returns, the batch is cut and reviewed exactly as today, and the claim becomes `DONE` with the generation linked.

### 10.2 `generate more` claims the next grid in the same pack

`"generate more"` (chat) or Create more (Studio) on an open pack claims the next unclaimed preset for **that pack**: a new group, a new generation, same `pack_slug`. When all four grids are claimed the pack is complete (36 stickers): the app says so in words and offers the next step (a custom 9-pick from the bank, or a new pack) — never a silent repeat, never a dead end.

### 10.3 Regenerate stays in the same batch as versions

Regenerating a preset-pack sticker does **not** open a new batch (today's 1×1 regen does). The new take is appended as a version of the same sticker in the same batch: `sticker.versions[] += {revision, files, report, ts, by, reason}`. S#, bank action, emoji and generation code never change; each version is reviewed on its own (approve → becomes current, reversible); old versions are kept for undo and audit, never deleted. Export always ships the latest approved version; the manifest `revision` tells versions apart under a stable filename. Freeform (non-preset) batches keep today's new-batch regen until unified.

### 10.4 Public generation codes (`0000`–`zzzz`)

Each generation gets one public code: 4 lowercase alphanumerics (`36^4 = 1,679,616` values), compared case-insensitively, no exclusions. `G###` stays the internal address everywhere (rule 9: folders, API, URLs, asset keys, chat, Postgres) — the code is the **public** face used in export filenames, the manifest, and a new Postgres mirror column. The mapping lives in `result.json` (`export_code`) plus a file registry `out/export_codes.json` (`{code: "G###"}`) written under the writer lock, so allocation works offline; the Postgres `UNIQUE` is the backstop (needs a numbered migration). Allocation is random-pick + registry-check + retry, at preset-claim time; existing batches get their codes lazily at first export (persisted the same way). `G###` is never shown in an export again.

### 10.5 One code per generation, not one per pack (recommendation: multiple ids)

Haitham's question — should the id be one per pack or several per pack? **Several: one code per generation.** The stated goal is tracing generation versions, and a single pack-wide id erases exactly that: which generation (which sheet, which paid job, which spend) made which sticker, and which version of a regenerated sticker is which. Per-generation codes keep the lineage (`7k2q` = the second sheet of Falcon, v3 of its S4 is still `7k2q` + revision 3); the pack identity is already carried by `pack_slug` plus the manifest pack record, so nothing is lost. A single pack id would push version tracing into side channels and break the money trail (tasks/jobs link by generation). Cost of per-generation codes: one allocation per claim — negligible.

### 10.6 Build order (when it gets a go)

1. Claim ledger core (§10.7, **built**) + preset-queue resolver (chat intent + Studio entry, open); all-claimed answer with next-step choices. (Preset engine already built: §10.1.)
2. Preset prompt builder (nine stored actions → sheet/video prompts through the existing templates) — **built**: a claim's plan is `prompter.expand(subject, grid, face=True, preset=…)`.
3. In-batch `versions[]` (+ `normalise` default, write-through, Studio version switcher, export uses latest approved).
4. Code allocator (registry + retry, claim-time allocation, lazy backfill at export, `export_names` id field becomes the code, manifest carries both ids).
5. Postgres mirror column + numbered migration; chat-side references stay `G###`.
6. Custom 9-pick presets from the bank (after the fixed four prove out).

### 10.7 Claim ledger: files, tables, state machine (core BUILT 2026-10-08; resolver and chat wiring open)

**Built (plan Phase 1):** `generation/claims.py` (`claim_next` opens the session and claims the next preset in one lock hold, `plan_claim`, `mark_requested`, `link_generation`, `current`, `find_claim`, `list_sessions`; `ClaimError` in words with an HTTP code), `migrations/012_pack_claims.sql` (the three tables, `UNIQUE (session, preset)`, no CHECK on status, no FK on `claim_generations.generation_id` so the mirror may see a claim before its generation), `store/repo.save_pack_session` / `import_pack_sessions` (the claim's `tasks` row has provider `mirsal-pack`, `name_key` = the session slug, `request` = session, preset, grid, jobs, plan; `generation_id` = the current generation once it is in the database), `store/sync.sync_pack_session` (write-through on every ledger write, real `out/` only), `db import` hookup. The lock is in-process plus `out/.claims.lock` across processes (waited for, never refused). A failed job may be requested again (`REQUESTED -> REQUESTED`, the job list grows); the same job or the same generation twice is one event. Tests: `tests/test_claims.py`. Nothing calls the ledger yet: the resolver and chat wiring are plan Phase 2.

How `"generate sticker pack for {subject}"`, `generate more` and regenerate are stored. File store leads, Postgres mirrors (store-and-search.md); nothing here changes a paid path, so no spend rules are involved.

**Entities (user words → system).** Three levels, each with a file record and a mirror row:

| Level | File (primary) | Postgres (mirror) | Id |
|---|---|---|---|
| Pack session `{pack_subject_name}` | `out/pack_sessions/<slug>.json` | `pack_sessions(slug PK, subject, title, owner, pack_id, created)` | `pack-<slug>` (e.g. `pack-falcon`) |
| Claim (one preset grid for one session) | inside the session file: `claims[]` | `claims(id PK, session FK → pack_sessions, preset, grid, status, plan jsonb, created)` | `C###` global sequence (e.g. `C008`) |
| Generation (one sheet run) | `out/G###/result.json` (as today) | `generations` (as today) + `claim_generations(claim_id, generation_id, revision, ts)` | `G###` internal, public code later |

The session also opens a row in the **`tasks` table** (kind `'sheet'`, `external_task_id = <claim id>`, `name_key = <subject>`) at claim time — no constraint change needed: a claim *is* a sheet task, and the external id is unique by construction. That is the visibility the task table gives today (`mirsal task`, the Queue) for free.

**Why not fewer tables.** `tasks.generation_id` is singular, but regenerate means N generations per claim — hence `claim_generations` (append-only lineage) instead of altering `generations`. Claims do not reuse `out/tasks/NNN.json`: that number space belongs to watch folders (`tasks.next_number` counts them), so claims live under the session file and `out/claims/` never exists as a competing namespace. Reviews stay append-only; a regenerated generation gets its own reviews, never an edit of the old ones.

**Claim state machine.** `UNCLAIMED` (a preset with no row — implicit, never stored) → `CLAIMED` (row written synchronously under the writer lock, **before** any paid call; two simultaneous `generate more` clicks serialize here: the loser reads the winner's row) → `PLANNED` (prompt + plan stored on the claim, = today's plan-card content) → `REQUESTED` (job file created) → `DONE` (generation linked, `claim_generations += (claim, G, revision)`) → re-`REQUESTED` on regenerate. A claim never goes backwards and never deletes: rejection only adds rows.

**The five flows.**

1. **New session** `"generate sticker pack for falcon"`: create `pack-falcon` (session file + row + first claim, all in one lock hold) → answer names the session, the claimed grid (`core-v1`, 3×3), and the price before anything is spent.
2. **Current claim 2×2 or 3×3**: the claim stores `grid`. Presets hold 9 actions: 3×3 takes all nine, 2×2 takes the first four (fixed slicing rule, never reordered). Grid is chosen at claim time (user's choice, default 3×3) and frozen with the prompt.
3. **Prompt per claim**: built from the preset's nine stored actions through the existing templates (face v4 for emoji packs) — no new prompt machinery. Stored on the claim file + task `request` jsonb, exactly like `tasks.reserve` stores `plan` today.
4. **Regenerate → same claim, newer id**: new job → new generation (`G###`, plus public code when §10.4 lands) → appended as the next `revision` on the same claim. Old generations stay (rejection never deletes); *current* = latest `DONE` generation, export ships its latest approved stickers. Coarse lineage lives here; sticker-level `versions[]` (§10.3) is the finer layer later — both point the same way and never conflict.
5. **Generate more → next claim**: first preset with no claim row for this session → new `C###` → flows 2–3 again under the same session. All four claimed → the pack is complete (36 stickers): answer says so in words with choices (custom 9-pick from the bank, or a new pack) — never a silent repeat, never a dead end.

**Backfill & import.** `db import` reads `out/pack_sessions/` like `import_tasks` reads `out/tasks/` (idempotent re-import). Existing batches predate claims and get none: their `claim_generations` rows arrive only if a later regenerate links them. Migration number is the next free one at build time (`012_*`); per the frozen-constraint procedure it only adds tables, never alters live ones.
