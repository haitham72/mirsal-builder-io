# The Prompt tab writes the prompts (2026-10-02)

<sub>Part of [generation.md](../generation.md).</sub>

The Studio's Prompt tab (a batch's own, and the same tab inside an Earlier-batches card) is editable: what is typed is what is SENT. Server side: `POST /api/live/sheet {prompt, from_generation?, sheet_prompt?}` starts a NEW sheet from that
batch's own plan (same cells, same tags) with the person's text in place of the template's sheet prompt (`prompter.apply_custom` / `clean_custom`, at most 6000 characters, empty or non-text is a 400; the text lives in the new task's `plan.custom` and on the
batch as `custom_prompts: ["sheet_prompt"]`, and survives a rebuild of the plan); `POST /api/live/video {generation, video_prompt?}` sends the person's video prompt as written, plus Haitham's expressive line once when it is not in it (`prompter.with_expressive`), and keeps what was sent on the video sheet (`video_prompt_sent`, `video_prompt_custom`).
Both are recorded on the job (`request.custom_prompt`) and stay under the Idempotency-Key. A member can only start from a batch they own (404 otherwise). Client side (`generate.js`): drafts live per batch and kind (`PD`), so a refresh while a batch works never loses what was
typed (and the poll does not re-render while a box has the focus); the buttons say "with my prompt" only when the text really differs from the template's, show the live price, and are off without Higgsfield; "Generate video" needs a kept sticker and a sheet that has no returned video
(the engine does not animate a sliced sheet twice); Reset puts the template back. The templates themselves are never edited (`_v4`, never edit one that was used).
