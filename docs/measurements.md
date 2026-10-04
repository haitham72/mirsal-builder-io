# Measurements

Recorded numbers, never opinions. `python -m mirsal measure-cells --record` appends a block to this file; the other sections were written by
hand from a real run. Dates are absolute.

## Video cells that leave their slot (`measure-cells`, 2026-10-02, 36 cells in 4 video sheets of the real G00x batches)

```
slot_fill  gap  sheets  cells  flagged  share   cross_slot  inside_slot  inside_frame  subject_px(mean/min)
0.74       26%       2     18        1   5.6%           1            0             0  257.2/160
0.80       20%       1      9        8  88.9%           8            7             0  427.1/390
0.84       16%       1      9        4  44.4%           1            3             0  439.2/408
```

A wider gap between stickers on the video sheet flags fewer cells: 0.74 (the default) is the best measured, but it is 2 sheets and some of
those clips were made with the cheaper Kling `std` model. **Open:** re-run with `pro` at 0.74 to reach "nothing flagged" and choose the default.

## Pool search (3B), first real run (2026-10-02, 45 approved stickers of G001-G005, local embeddings)

Embeddings: `text-embedding-nomic-embed-text-v1.5` on LM Studio (768-d, hardcoded), documents as `search_document: ...`, queries as
`search_query: ...`. Thresholds are **provisional** (`SUBJECT_MIN` 0.50, `ACTION_MIN` 0.40; `MIRSAL_POOL_SUBJECT_MIN` / `MIRSAL_POOL_ACTION_MIN`
override them) until Haitham's eval set (`docs/inputs/search_queries.md`, not written) exists.

| query | result | cosine subject / action |
|---|---|---|
| batman | G002 batman lego stickers (a pack; 2 shown by the default diversity cap) | 0.746 / - |
| batman throwing | G002/S2 `throwing_batarang`, G002/S7 `gliding_in_air` | 0.746 / 0.597, 0.402 |
| angel reading a newspaper | G001/S6, S7 | 0.966 / - |
| old man sleeping | G004/S8 `old_man_pixar_style_sleepy` | 0.610 / 0.695 |
| barbie love | G005/S5, S9 | 0.788 / - |
| mouse with a gold chain | G003/S2 `mouse_shy`, S1 `mouse_proud` | 0.556 / - |
| **falcon dancing** | nothing (no falcon in the pool) | below the gate |
| **penguin skiing** | nothing | below the gate |
| **tedy bear** (typo; no teddy in the pool) | nothing | below the gate |
| a hero fighting | nothing ("hero" is not "Batman" at this gate) | below the gate |

A related query scores 0.55-0.97 on the subject, an unrelated one 0.20-0.35. Latency is the query embedding (1.3-2.2 s the first time, a Redis
hit after); the SQL is single-digit ms on 45 rows.

**The first real search found a bug, fixed:** the lexical scorer returned the old man's stickers for "batman" (trigram overlap of "man", rank
0.22). Word coverage now compares whole words (`_close`), so "batman" is not "man" and typos ("tedy bok") still match (`tests/test_pool.py`).

**Open:** precision@5 >= 0.8 needs Haitham's labelled queries; the gap flow shows "Found N, generate M more?" without a price.

## Vision judge (S6), first live runs (2026-10-02, G002 Batman Lego, 9 stickers, a COPY of out/)

| model | approved | rejected | unjudged | per sticker |
|---|---|---|---|---|
| `mistralai/ministral-3-3b:2` | 7 | S2 (batarang), S7 (gliding) | 0 | about 3 s |
| `qwen3.5-4b:2` with `reasoning_effort: "none"` | 7 | S5 (victory pose) | S7 (invalid JSON twice) | about 4 s |

The two small models disagree on which stickers are bad, and nobody has checked either against a person: **the judge is uncalibrated until
Haitham labels 30 stickers** (target: agreement >= 80%, otherwise point the same code at OpenAI). Thinking models spend the token budget on hidden
reasoning when it is left on (300 tokens gave an empty answer): the client sends `reasoning_effort: "none"` (0 reasoning tokens, a 2 s answer).

## Photo cutout (3C), test photo `ref/upload.jpeg` (2026-10-02)

`python -m mirsal photo ref/upload.jpeg` -> `out/photo/photo-upload.png`: method `chroma_green`, foreground 0.289 of the canvas (91 598 px),
512x512, 193 KB PNG, all checks ok. Edge quality on a real photo is Haitham's judgement (not looked at by the builder, by rule).

## Sharpness (the reworked `sharpness` check, 2026-10-02)

**Why it was rebuilt.** The old metric compared the decoded clip to its own encoder input, so softness that happened *before* the encode (a 320 px source cell upscaled to 512, the cheaper Kling `std`
model) read 1.00 on every clip. A down-up "retention" metric was tried and rejected (flat at 0.97-1.0 and not monotonic in blur). The check now also compares the animation's mean edge energy to its
**own approved still's** (`detail_vs_still`) and says how soft that is in pixels of blur (`soft_sigma`: the Gaussian radius that takes the still down to that level); it fails (WARN) on the worse of the
encode loss (`sharp_kept` < 0.8) and the detail ratio (`detail_vs_still` < 0.75). `python -m mirsal measure-sharpness` measures every stored animation.

On the 31 real animations of this PC the metric separates the batch the owner called soft from the rest: G002 (Kling `std`, 320 px cells) reads a mean of 0.65 (lowest 0.58, about 1.3 px of blur), all 8 flagged; G001 (mean 0.91, lowest 0.89),
G003 (mean 1.00, lowest 0.97) and G005 (mean 1.17, lowest 1.02: the animation is sharper than its still) pass. The threshold 0.75 sits in the gap between the two groups: **provisional until Haitham confirms by eye** that the flagged
cells are the ones he sees as soft (the measurement itself used no media viewing).

## measure-sharpness 2026-10-02 05:12

```
31 animations, 8 softer than 0.75x of their still's edge detail
generation  cells  mean_detail  min_detail  mean_blur_px  flagged
G001            5         0.91        0.89           0.7        0
G002            8         0.65        0.58           1.3        8
G003            9         1.00        0.97           0.1        0
G005            9         1.17        1.02           0.0        0
```

## Particle effects: Kling text-only clips (2026-10-02)

Two clips for the strawberry burst (`docs/effects.md` §3 has the method and the table), judged by `alpha / background coverage per cell and frame`, never by eye: 2x2 (J037) 4 of 4 cells empty at the start, burst from
0.33 s, edge crossing <= 0.24 %, 1 of 4 empty at the end (0.7 % covered on the others), engine output 4 READY stickers of 199-237 KB; 3x3 (J038) 9 of 9 empty at the start, edge crossing 10-26 %, 0 of 9 empty at the
end. Particle simulator: 90 frames x 30 particles in 0.53 s at 512 px, 0.15 s at 256 px; the five presets encode to 201-245 KB WebM (crf 38-46).
