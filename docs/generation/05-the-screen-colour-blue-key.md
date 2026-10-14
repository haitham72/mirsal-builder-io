# The screen colour (blue key)

<sub>Part of [generation.md](../generation.md).</sub>

The sheet prompt asks for the key in `slots.key_colour` (green; blue when the AI enhancer sees a green subject, `expander.GREEN_WORDS`). What the model **returns** wins: `run_stills` measures the outer ring
(`chroma.detect_key`, the colour with the higher key difference, `asked` when neither is clear so the sheet check still blocks it) and, when the screen is blue, writes `key_colour: "blue"` on the batch.
`pipeline.cfg_for` then makes every later step use `chroma = "blue"` (keyer, despill, the sheet check, the **video sheet**, the keying of the returned video) and `video_prompt_for` names the screen
that was really sent. It is **marked only when it is blue**: the task file gets `key_colour: "blue"` (plus `key_detected: true` when the prompt had asked for green, i.e. the model drifted), `prompts.txt` gets a
`KEY: blue` line and the batch header a "Blue key" chip; a green screen leaves no mark anywhere. A sheet with neither screen is still blocked (`background_is_key`).
