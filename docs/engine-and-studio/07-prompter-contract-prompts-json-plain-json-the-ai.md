# Prompter contract (`prompts.json`, plain JSON; the AI expansion plugs in through `generation/expander.py`)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

```json
{ "task": "teddy yellow bear for school", "task_slug": "teddy_bear_school", "subject": "teddy yellow bear",
  "context": "school", "kind": "school", "guidelines": {"sheet": "...", "style": "...", "background": "...", "consistency": "...", "motion": "..."},
  "sheet_prompt": "...", "video_prompt": "...",
  "stickers": [ {"index": 1, "id": "prompt01", "prompt": "teddy yellow bear holding a book", "key": "teddy_bear_with_a_book", "emoji": "📚"} ] }
```

**The stub does not look at the image.** Labels are assigned by cell position from `ACTIONS`; they only match a sheet if that sheet was generated from this plan's `sheet_prompt` (shown, copyable, in the console). For a sheet made any other way, put the real 9 prompts in `<sheet name>.json` (e.g. `img-001-teddy_bear (2).json`) or `<folder>/prompts.json` (same shape, `task_slug` + 9 x `{index, prompt, key, emoji}`); it replaces the stub, is validated, and the console shows `labels from: <file>`. The app only reads these files.

Nine stickers, row-major cell order. `key` is the searchable action name and the file-name tail. Colour words are dropped from slugs, kept in prompts. Action sets live in `ACTIONS` (school, birthday, default); a real planner (Phase 2) must return the same shape.
