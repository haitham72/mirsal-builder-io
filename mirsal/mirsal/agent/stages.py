"""How far a NEW chat request goes (Haitham, 2026-10-09; the fifth stop 2026-10-11): the chat's stage, one of five, picked on the chat bar's slider.

    prompt    -> "Prompt": the plan only (cells, tags, the sheet prompt) and Generate / Edit: nothing is spent, no job starts
    emojis    -> "Stickers": the sheet and the cut stickers, stopping at G2 for the person (the default, today's turn)
    animation -> "Animation": stickers + the video: the agentic creator with scope video, ENDING after "approve the animations" (G4): no pack, no Telegram
    export    -> "Telegram": the creator run to the Library pack and the Telegram send (D1). The id stays `export` so saved chats keep their meaning
    api       -> "Export": everything above, then the pack is sent to the backend API (AddCollection, services/collection.py; owner only, like Telegram)

The stage is `settings.stage` of the chat session. It maps onto the creator (agent/creator.py); it never forks it. Animation and export stop at G2 and G4
for one click unless the creator's bypass ("Approve everything for me", `settings.creator.bypass`) is on (D2). A session written before the stage existed
keeps working: `creator.on` with `scope: video` reads as export, anything else as emojis. Pure: no I/O, no model, no tools."""
from __future__ import annotations

STAGES = ("prompt", "emojis", "animation", "export", "api")
DEFAULT = "emojis"
MAX_BATCHES = 4          # = generation/tasks.MAX_BATCHES: a pack has at most four batches (an emoji pack's four preset grids)
INFO = {"prompt": {"label": "Prompt", "hint": "plan only, free"},
        "emojis": {"label": "Stickers", "hint": "sheet and stickers"},
        "animation": {"label": "Animation", "hint": "+ animation"},
        "export": {"label": "Telegram", "hint": "+ pack and Telegram"},
        "api": {"label": "Export", "hint": "+ send to the API"}}


def of(settings: dict | None) -> str:
    """The stage of a session's settings; an old session's creator switches migrate on read (on + video -> export)."""
    st = settings or {}
    if st.get("stage") in STAGES:
        return st["stage"]
    c = st.get("creator") or {}
    return "export" if c.get("on") and c.get("scope") == "video" else DEFAULT


def valid(stage) -> bool:
    return stage in STAGES


def run_spec(stage: str, bypass: bool = False) -> dict:
    """What a new request does at this stage: {plan_only, creator, scope, end, bypass}. `end` is where a creator run stops: 'animation' (after G4) or
    'export' (after the Telegram send) or 'api' (after the AddCollection send); None when the creator is not used."""
    stage = stage if stage in STAGES else DEFAULT
    creator = stage in ("animation", "export", "api")
    return {"stage": stage, "plan_only": stage == "prompt", "creator": creator, "scope": "video" if creator else "images",
            "end": stage if creator else None, "bypass": bool(bypass) if creator else False}


def animates(stage: str) -> bool:
    """The stage's price includes the animation (the plan card shows sheet + animation)."""
    return stage in ("animation", "export", "api")


def batch_label(no: int, plan: dict | None = None) -> str:
    """"Batch 02 · social" / "Batch 01 · actions 1-9": what the cards call one batch of a pack. An emoji pack's batch is a preset grid
    (core-v1 -> core); any other request's batch k is bank actions 9(k-1)+1 .. 9k."""
    p = ((plan or {}).get("slots") or {}).get("preset")
    if p:
        return f"Batch {no:02d} · {str(p).split('-')[0]}"
    n = 9
    grid = (plan or {}).get("grid")
    if isinstance(grid, (list, tuple)) and len(grid) >= 2:
        n = int(grid[0]) * int(grid[1])
    elif isinstance(grid, str) and "x" in grid:
        a, b = grid.split("x")[:2]
        n = int(a) * int(b)
    return f"Batch {no:02d} · actions {n * (no - 1) + 1}-{n * no}"
