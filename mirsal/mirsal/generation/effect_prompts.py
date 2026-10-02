"""Prompts of the particle effects: the text Kling gets for a text-only burst video, built by code from a small plan (template-locked: a model or a person fills the JSON, `lint_plan`
checks it, `video_prompt` writes the text, so the prompt can never drift or smuggle in anything else).

A burst effect is what Telegram does when you press an emoji: it starts from NOTHING, the pieces burst out of the centre, grow a little, then gravity takes them down until the
screen is empty again. So the video has no start image (nothing to start from) and every cell must begin and end empty. The screen colour is the engine's key colour: green,
unless a piece of the effect is itself green (leaves, grass, a frog): then blue, so the keyer does not eat the pieces.

`TEMPLATE_ID` / `VERSION` are stored with every effect; a new wording is a new version (`_v2`), a used one is never edited."""
from __future__ import annotations

import re

TEMPLATE_ID = "effect_video"
VERSION = 1

MAX_ELEMENTS = 9
MAX_WORDS = 5
MAX_GRID = 3
GREENISH = re.compile(r"\b(green|leaf|leaves|grass|lime|mint|clover|frog|pickle|emerald|cactus|basil|herb|moss|fern|jade|olive)\b", re.I)
FORBIDDEN = re.compile(r"\b(stickers?|text|letters?|words?|logo|watermark|hands?|fingers?|faces?|people|person)\b", re.I)

# one entry per cell, so the cells of one video are different takes of the same burst
VARIATIONS = [
    "a tight fast vortex", "a wide gentle burst", "a slow lazy swirl", "a sharp pop that rises high first",
    "a clockwise spiral", "a counter-clockwise spiral", "a heavy fall with large pieces", "a light floaty fall with small pieces", "a fountain that shoots straight up",
]


def key_colour_for(elements: list[str]) -> str:
    """The screen colour: green, unless a piece of the effect is green (then blue)."""
    return "blue" if any(GREENISH.search(e) for e in elements) else "green"


def lint_plan(plan: dict) -> dict:
    """The plan the template is filled from: {subject, elements[1..9], style?}. Returns the cleaned plan; raises ValueError with the reason (a human can fix and retry)."""
    subject = " ".join(str(plan.get("subject") or "").split())[:60]
    if not subject:
        raise ValueError("the effect needs a subject (what the emoji is)")
    els: list[str] = []
    for e in plan.get("elements") or []:
        e = " ".join(str(e).split())[:60].strip(" .,;")
        if not e or e.lower() in {x.lower() for x in els}:
            continue
        if len(e.split()) > MAX_WORDS:
            raise ValueError(f"'{e}' is too long: at most {MAX_WORDS} words per piece")
        if FORBIDDEN.search(e):
            raise ValueError(f"'{e}' cannot be a piece of a burst (no text, logos, hands, faces, people, and never the word sticker)")
        els.append(e)
    if not els:
        raise ValueError("name at least one piece that bursts out (for Batman: bat signals, bats)")
    if len(els) > MAX_ELEMENTS:
        raise ValueError(f"at most {MAX_ELEMENTS} different pieces")
    style = " ".join(str(plan.get("style") or "glossy cartoon look, bold clean shapes, vivid colours").split())[:120]
    if FORBIDDEN.search(style):
        raise ValueError("the style line cannot contain text, logos, people or the word sticker")
    return {"subject": subject, "elements": els, "style": style}


def _list(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def video_prompt(plan: dict, rows: int = 2, cols: int = 2, cells: list[str] | None = None) -> str:
    """The Kling prompt for a rows x cols grid of burst cells (2x2 or 3x3). `cells` overrides the per-cell variations."""
    if not (1 <= rows <= MAX_GRID and 1 <= cols <= MAX_GRID):
        raise ValueError(f"the grid is at most {MAX_GRID}x{MAX_GRID}")
    p = lint_plan(plan)
    key = key_colour_for(p["elements"])
    screen = "#00FF00 green" if key == "green" else "#0000FF blue"
    n = rows * cols
    takes = list(cells or VARIATIONS)[:n]
    while len(takes) < n:
        takes.append(VARIATIONS[len(takes) % len(VARIATIONS)])
    layout = "; ".join(f"cell {i + 1} ({['top', 'middle', 'bottom'][min(i // cols, 2)] if rows == 3 else ['top', 'bottom'][i // cols]} row, "
                       f"{['left', 'middle', 'right'][i % cols] if cols == 3 else ['left', 'right'][i % cols]}): {takes[i]}" for i in range(n))
    return (
        f"A flat, perfectly even, solid {screen} screen with no shadows, no floor, no gradient, no text and no borders. Static camera, square frame, 3 seconds. "
        f"The frame is an invisible grid of {rows} by {cols} equal square cells and nothing ever crosses from one cell into another. "
        f"In EVERY cell at the same time, the same small burst effect plays: {_list(p['elements'])}, all related to {p['subject']}. "
        f"Timeline for each cell: from 0.0 to 0.4 seconds the cell is completely empty {key} screen. At 0.4 seconds the pieces appear at the exact centre of the cell and burst outward "
        f"in a spiralling vortex, growing a little as they fly. From about 1.2 seconds gravity takes over: the pieces slow down, arc and fall downward out of the cell. "
        f"By 2.6 seconds every piece has left the cell and the cell is completely empty {key} screen again until the end at 3.0 seconds. "
        f"The pieces are small and separate, never touching the cell edge; only the pieces listed are drawn, never one large central {p['subject']}. "
        f"Look: {p['style']}. Each cell is a different take of the same effect: {layout}."
    )


def describe(plan: dict, rows: int, cols: int) -> dict:
    """What the page shows next to the price: the screen colour, the pieces and the prompt that will be sent."""
    p = lint_plan(plan)
    return {"template": TEMPLATE_ID, "version": VERSION, "key": key_colour_for(p["elements"]), "grid": [rows, cols], "plan": p, "prompt": video_prompt(p, rows, cols)}
