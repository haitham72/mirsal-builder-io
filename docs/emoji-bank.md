# The emoji bank: every reaction the app can make

One canonical bank of emoji, shared by reactions, export tags and the sticker planner. A bank member is always a well-established public iOS emoji; the saved per-sticker emoji always wins over the default.

**Code truth:** `mirsal/mirsal/generation/actions.py` — `ACTION_BANK` (36 core), `EXTENDED_BANK` (1,898, generated from Unicode `emoji-test.txt` 15.1 fully-qualified rows minus skin-tone variants), `generation_bank()` (one token per base glyph, core moods first), `token_for_emoji()`, `next_tokens()`, `FACE_SENTENCES` / `BODY_SENTENCES` (the fixed per-token image + motion sentences). Validation uses `generation/emoji_sequences.json` (3,773 fully-qualified Unicode 15.1 sequences, tones included). The export contract lives in [export to team/mirsal-export-architecture.md](export%20to%20team/mirsal-export-architecture.md) §6 (core table) and §6b (extended table).

**Binding:** every new sticker's primary emoji must be a bank member. Lookups try the core bank first, then exact extended tokens, then extended aliases (`canonical_for` three-pass order). Default emoji are starting points, not exclusive mappings.

## Core 36 (stable, human-curated)

| # | Token | Emoji | Aliases |
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

Suggested preset grids: `core-v1` = happy, laugh, love / cry, sad, angry / surprised, scared, thanks; `social-v1` = hello, hug, kiss / wink, shy, celebrate / clap, approve, disapprove; `reactions-v1` = think, confused, eye-roll / facepalm, shrug, bored / cool, flex, scheme; `daily-v1` = sleep, sick, sneeze / dance, plead, salute / cheers, gift, star-struck.

## Extended 1,898 (generated, by Unicode group)

Not listed here row by row (it would rot): the full table is §6b of the export architecture, generated from the same source as the code. Groups, in bank order: Smileys & Emotion · People & Body · Animals & Nature · Food & Drink · Travel & Places · Activities · Objects · Symbols · Flags.

## Who reads the bank

- **Reaction effects** (`#/reactions`, `console/reactions.js`): search, two rows of small emojis, pick ONE → its fixed motion flies as the literal glyph (`engine/particles.render_emoji`, the system's colour emoji font) → Size in / Size out / Hue / preset → **Create reaction** → its card with **Download Lottie** (`POST /api/particles/emoji-preview`, `POST` / `GET /api/particles/emoji-lottie`; a token name or the glyph itself, resolved by `token_for_emoji`). No set, no pack ([reaction.md](reaction.md) §13).
- **Library > Reactions > Create** (`GET /api/particles/bank`): multi-select up to 9 → one stand-alone set per emoji ([reaction.md](reaction.md) §12).
- **Per-emoji motion** (`engine/emoji_motion.py`, `GET /api/particles/emoji-motions`): every token owns one fixed animation ([reaction.md](reaction.md) §8).
- **Planner** (`generation/tasks.py`, `generation/prompter.py`): predefined batches draw `next_tokens()` in bank order; named grids keep their cells.
- **Exporter**: filename tags and unresolved-cell picker ([export to team/mirsal-export-architecture.md](export%20to%20team/mirsal-export-architecture.md) §6–§6b, §10).
