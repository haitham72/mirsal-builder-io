# A sheet Python blocked, in words (`flow/explain.py`, 2026-10-02)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

A sheet that fails a BLOCK check of the sheet stage (`grid_detected`, `background_is_key`, `sheet_size`, `sheet_decodes`) leaves a batch with nine FAILED stickers and the same reason. It was downloaded and paid for, but it looked as if "the task was never retrieved"
(the falcon sheet G094: `found 3x2, plan says 3x3`; the characters touched across the first column gap, 90% background instead of 97%). `pipeline.state()` and the chat's `tools.generation()` now carry `problem` = `{check, value, limit, title, why, fix, received: {job, cost}, retry,
retry_estimate}` (None for a healthy batch). The Studio's batch shows it instead of "This sheet cannot be used", the chat's generation card shows it with a button "Try the sheet again · about 2 credits"
(`{type: "retry_sheet", generation}` on `POST /api/chat/sessions/{id}/messages`; the price is on the button, so the click is the go-ahead; the Studio's button goes through Generate, which shows the live price). The block itself is untouched: nothing is cut, nothing is forced, the blocked batch stays in History.
No threshold was changed.
