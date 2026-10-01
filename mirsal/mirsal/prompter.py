"""Stub of the AI prompter agent (Phase 1 = deterministic, plain JSON, no LLM/pydantic/langgraph).
Expands one user task into one prompt per grid cell (3x3 default, 2x2, 1x1). Phase 3 swaps this for a real agent with the SAME JSON shape."""
from __future__ import annotations

import re

GUIDELINES = {
    "sheet": "{rows}x{cols} sticker sheet, {n} separate characters, equal cells, wide gaps between characters, no character touches its cell edge",
    "style": "flat vector sticker illustration, bold clean shapes, vibrant colors, friendly proportions",
    "background": "flat pure green (#00FF00) background, no shadows, no floor, no gradients",
    "consistency": "same character design, proportions and colors in all {n} cells",
    "motion": "each character moves in place, no interaction between cells, static camera, seamless loop",
}

# (key suffix, phrase, emoji) x 9 per context. Row-major cell order.
ACTIONS = {
    "school": [
        ("with_a_book", "holding a book", "📚"), ("raising_hand", "raising a hand", "✋"),
        ("with_a_backpack", "wearing a backpack", "🎒"), ("writing", "writing in a notebook", "📝"),
        ("with_a_pencil", "holding a big pencil", "✏️"), ("thinking", "thinking with a hand on chin", "🤔"),
        ("with_a_star", "holding a gold star", "⭐"), ("sleeping_at_desk", "sleeping at a desk", "😴"),
        ("waving_goodbye", "waving goodbye", "👋"),
    ],
    "birthday": [
        ("with_a_cake", "holding a birthday cake", "🎂"), ("with_a_balloon", "holding a balloon", "🎈"),
        ("with_a_gift", "holding a gift box", "🎁"), ("party_hat", "wearing a party hat", "🥳"),
        ("blowing_a_horn", "blowing a party horn", "🎉"), ("making_a_wish", "making a wish with closed eyes", "🌟"),
        ("laughing", "laughing", "😂"), ("with_confetti", "surrounded by confetti", "🎊"), ("waving", "waving hello", "👋"),
    ],
    "default": [
        ("waving", "waving hello", "👋"), ("laughing", "laughing out loud", "😂"), ("with_a_heart", "holding a heart", "❤️"),
        ("thumbs_up", "giving a thumbs up", "👍"), ("thinking", "thinking with a hand on chin", "🤔"),
        ("crying", "crying", "😢"), ("angry", "angry with crossed arms", "😡"),
        ("sleeping", "sleeping", "😴"), ("celebrating", "celebrating with arms up", "🎉"),
    ],
}
VERBS = {"create", "make", "generate", "draw", "design", "build", "give", "me"}
STOP = {"a", "an", "the", "of", "and", "to", "my", "some"}
COLORS = {"yellow", "red", "blue", "green", "pink", "purple", "orange", "brown", "black", "white", "gray", "grey",
          "golden", "cute", "little", "big", "small", "happy"}
SPLIT = re.compile(r"\b(for|in|at|during|with|on)\b")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


GRIDS = {(3, 3), (2, 2), (1, 1)}     # user's choice: 3x3 (default) or 2x2; 1x1 = regenerate one sticker


def expand(task: str, grid: tuple = (3, 3)) -> dict:
    rows, cols = grid
    words = re.findall(r"[a-z0-9]+", task.lower())
    body = " ".join(w for w in words if w not in VERBS or words.index(w) > 2)
    parts = SPLIT.split(body, maxsplit=1)
    subject = parts[0].strip() or "sticker"
    context = parts[2].strip() if len(parts) > 2 else ""
    subject_slug = slug(" ".join(w for w in subject.split() if w not in COLORS | STOP)) or "sticker"
    ctx_words = [w for w in context.split() if w not in STOP]
    ctx_slug = slug(" ".join(ctx_words))
    kind = next((w for w in ctx_words + words if w in ACTIONS), "default")
    task_slug = subject_slug + (f"_{ctx_slug}" if ctx_slug else "")
    stickers = []
    for i, (suffix, phrase, emoji) in enumerate(ACTIONS[kind][: rows * cols], 1):
        stickers.append({
            "index": i, "id": f"prompt{i:02d}",
            "prompt": f"{subject} {phrase}",
            "key": f"{subject_slug}_{suffix}",     # searchable action name; also the file name tail
            "emoji": emoji,
        })
    g = {k: v.format(rows=rows, cols=cols, n=rows * cols) for k, v in GUIDELINES.items()}
    poses = "; ".join(f"{s['index']}. {s['prompt']}" for s in stickers)
    return {
        "task": body, "task_slug": task_slug, "subject": subject, "context": context, "kind": kind, "grid": [rows, cols],
        "guidelines": g,
        "sheet_prompt": f"{g['sheet']}: {poses}. {g['style']}. {g['consistency']}. {g['background']}.",
        "video_prompt": f"Animate the sheet: {g['motion']}. {g['background']}.",
        "stickers": stickers,
    }


def validate_plan(plan: dict) -> dict:
    """A hand-written prompts file (next to a sheet) replaces the stub. Same shape as expand(); raises ValueError.
    `grid` [rows, cols] is optional: 9 stickers = 3x3, 4 = 2x2, 1 = 1x1."""
    st = plan.get("stickers")
    if not isinstance(st, list) or not st:
        raise ValueError("stickers must be a non-empty list")
    n = len(st)
    grid = tuple(plan.get("grid") or {9: (3, 3), 4: (2, 2), 1: (1, 1)}.get(n, (0, 0)))
    if grid not in GRIDS or grid[0] * grid[1] != n:
        raise ValueError(f"{n} stickers do not fill a supported grid (3x3, 2x2, 1x1)")
    plan["grid"] = list(grid)
    if sorted(s.get("index") for s in st) != list(range(1, n + 1)):
        raise ValueError(f"stickers must have index 1..{n} exactly once")
    for s in st:
        for k in ("prompt", "key", "emoji"):
            if not s.get(k):
                raise ValueError(f"sticker {s.get('index')} is missing '{k}'")
        s["key"] = slug(s["key"])
    plan["stickers"] = sorted(st, key=lambda s: s["index"])
    plan["task_slug"] = slug(plan.get("task_slug") or plan.get("task") or "task")
    plan.setdefault("task", plan["task_slug"])
    plan.setdefault("sheet_prompt", ""); plan.setdefault("video_prompt", "")
    return plan
