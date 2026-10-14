# Not built

<sub>Part of [generation.md](../generation.md).</sub>

The vision judge is built (`mirsal/vision/`, see [`agent-and-chat.md`](../agent-and-chat.md)) but **uncalibrated** until Haitham labels 30 stickers; `python -m mirsal measure-cells` is built and its first
numbers are in [`measurements.md`](../measurements.md) (the target "nothing flagged" needs a re-run with Kling `pro`); the sheet-vs-single and outline decisions, the 20-prompt AI lab rating, and the
leftovers of the original planner design that wait for Haitham's word (UAE content rules, English + Arabic Telegram keywords, 4x4 sheets) are listed in `docs/backlog.md` (live generation).
`out/jobs/*.json` and `out/model_calls.jsonl` are mirrored into Postgres (write-through and `db import`).
