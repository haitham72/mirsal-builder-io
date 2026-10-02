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
