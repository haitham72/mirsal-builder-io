# Sheet-level problems are cut anyway (2026-10-02)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

Haitham: "Python blocking the imported images is stupid, it does not let me bypass it." Before, any BLOCK of the sheet stage returned from `run_stills` before a single sticker file existed (two touching characters cost eight good stickers: G094 and G098 had `grid_detected` BLOCK, 9 of 9 `sheet_blocked`, 0 files). Now (`flow/pipeline.py`):

- `SHEET_FATAL = {sheet_decodes}`: a file that does not open is the only hard stop.
- `SHEET_PROCEED = {grid_detected, sheet_size}`: the sheet is cut with the grid that was planned; the problem is stored on the batch (`sheet_issues`), as a `WARN` line in every sticker's history (`stage sheet`, detail `cut_anyway`) and in its metrics (`sheet_issue`); every cell is judged on its own still checks (a cell that straddles a boundary fails `blank_cell` / `inside_cell` / `single_subject` / `duplicate_cell` as usual) and a human decides at G2. No check was loosened: the verifier's verdict on the sheet is unchanged and shown; what changed is that it no longer discards the cells.
- `background_is_key` (no key screen) still stops, because every cell would come out wrong, but never as a dead end: `POST /api/generations/{id}/recut` (`pipeline.recut`, free, from the stored sheet, refused once a sticker has a human decision or a video sheet exists) cuts it anyway. The Studio's sheet-problem panel and the chat's problem card show **Cut it anyway** next to *Try the sheet again* (`flow/explain.py` carries `cut_anyway`). Old blocked batches (G094, G098) can be cut with it.
- Test: `tests/test_golden.py::test_a_layout_problem_cuts_the_sheet_anyway_and_a_stopped_sheet_has_one_free_click`.
