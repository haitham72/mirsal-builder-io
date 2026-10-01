"""Subject -> the full named set. The user asks for `{subject}`; the AI expands it into N distinct, animatable stickers and gives every one its key name,
tags and emoji. The AI only fills a small JSON; code lints it (and gets one repair round), then the SAVED TEMPLATE builds every prompt (prompter.render_plan),
so the prompt text is never free-written by the model. No key, no network, or a bad answer: the deterministic sets of `prompter.expand` are used and the
plan says so (`expanded_by`)."""
from __future__ import annotations

import json
import re

from . import llm, prompter

GREEN_WORDS = {"green", "leaf", "leaves", "plant", "grass", "palm", "mint", "lime", "olive", "emerald", "cactus", "tree", "frog", "watermelon", "avocado", "broccoli"}
BANNED = {"text", "caption", "logo", "watermark", "flag", "transparent", "shadow"}

SYSTEM = """You plan sticker packs. You are given a short request (any language) and a grid size. Reply with ONE JSON object and nothing else:
{"subject_description": "<one line: the single character/subject, its look, identical in every cell>",
 "cells": [ {"label": "<the expression plus body language, 6-14 words, English>", "motion": "<one sentence: how this character moves when animated in place, English>", "key": "<snake_case action, 1-4 words, no subject>", "tags": ["<0-3 extra snake_case search words>"], "emoji": ["<1-2 emoji that fit the pose>"]} ]}
Rules: exactly N cells, all completely different; cover a WIDE range of emotions and reactions (for example joy, love, laughter, pride, doubt, sadness, anger, shock, fear, embarrassment, boredom, mischief, sleepiness), each exaggerated and readable at small size, and in a different state of action (standing, walking, running, jumping, sitting, lying down, leaning, reaching, spinning), so no two share a pose or a silhouette; every label animatable (a character that can move in place);
no text, captions, logos, flags or real people in any label; keep the user's subject and constraints, never add another character; labels in English even when the request is Arabic or Arabizi."""


def _lint(cells, n: int, subject_slug: str, request: str) -> list[str]:
    problems = []
    if not isinstance(cells, list) or len(cells) != n:
        return [f"need exactly {n} cells, got {len(cells) if isinstance(cells, list) else 'none'}"]
    labels, keys = set(), set()
    for i, c in enumerate(cells, 1):
        if not isinstance(c, dict):
            problems.append(f"cell {i} is not an object"); continue
        label = str(c.get("label", "")).strip()
        key = prompter.slug(str(c.get("key") or label))
        if not label:
            problems.append(f"cell {i} has no label")
        if label.lower() in labels:
            problems.append(f"cell {i} repeats the label '{label}'")
        labels.add(label.lower())
        if not key or key in keys:
            problems.append(f"cell {i} key '{key}' is empty or repeated")
        keys.add(key)
        if len(f"{subject_slug}_{key}") > 60:
            problems.append(f"cell {i} key is too long")
        if BANNED & set(re.findall(r"[a-z]+", label.lower())):
            problems.append(f"cell {i} label '{label}' uses a banned word ({', '.join(sorted(BANNED & set(re.findall(r'[a-z]+', label.lower()))))})")
        em = c.get("emoji")
        if not isinstance(em, list) or not [e for e in em if isinstance(e, str) and e.strip()]:
            problems.append(f"cell {i} needs at least one emoji")
        mo = c.get("motion", "")
        if not isinstance(mo, str):
            problems.append(f"cell {i} motion must be a sentence")
        elif BANNED & set(re.findall(r"[a-z]+", mo.lower())):
            problems.append(f"cell {i} motion uses a banned word")
        if not isinstance(c.get("tags", []), list):
            problems.append(f"cell {i} tags must be a list")
    return problems


def _parse(text: str):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("the answer has no JSON object")
    return json.loads(m.group(0))


REVIEW_SYSTEM = """You review sticker slot JSON. You are given a request and a slot object with subject_description and cells (label, key, tags, emoji). Reply with ONE JSON object and nothing else:
{"ok": true/false, "problems": ["<short concrete problem>"]}.
Rules: cells must be distinct and animatable (a character that can move in place); subject_description must match the request without adding another character; every cell needs 1-2 fitting emoji. Say ok only when all hold."""


def review(slots: dict, n: int, subject_slug: str, request: str, complete=None) -> dict:
    """The small slot reviewer (S5): code lint first, then a cheap second model answering {ok, problems[]}.
    The reviewer never edits the template; a failed review fails cleanly to the built-in sets."""
    cells = []
    for c in slots.get("cells") or []:
        tags = list(c.get("tags") or [])
        em = c.get("emoji")
        cells.append({"label": c.get("label", ""), "key": tags[0] if tags else prompter.slug(str(c.get("label", ""))),
                      "tags": tags[1:], "emoji": [em] if isinstance(em, str) and em.strip() else (em or [])})
    problems = _lint(cells, n, subject_slug, request)
    if not str(slots.get("subject_description", "")).strip():
        problems.append("subject_description is empty")
    if problems:
        return {"ok": False, "problems": problems, "model": None}
    complete = complete or llm.complete
    if complete is llm.complete and not llm.configured():
        return {"ok": True, "problems": [], "model": None}  # lint passed; no second model without a key
    try:
        text, meta = complete(REVIEW_SYSTEM, f"Request: {request}\nSlots: {json.dumps(slots, ensure_ascii=False)}",
                              json_mode=True)
        ans = _parse(text)
        probs = [str(p) for p in ans.get("problems", []) if str(p).strip()]
        return {"ok": bool(ans.get("ok")) and not probs, "problems": probs, "model": meta.get("model")}
    except (llm.LLMError, ValueError) as e:
        return {"ok": True, "problems": [], "model": None, "review_error": str(e)[:200]}


def expand(task: str, grid: tuple = (3, 3), *, use_ai: bool = False, complete=None, review_ai: bool = False) -> dict:
    """The plan for a typed request, in `prompter.expand`'s exact shape, plus `expanded_by` ('ai' | 'deterministic'), `expand_model`, `expand_error`.
    `complete(system, user) -> (text, meta)` is injectable for tests. `review_ai` runs the slot reviewer after the lint."""
    base = prompter.expand(task, grid)
    base["expanded_by"] = "deterministic"
    if not use_ai:
        return base
    complete = complete or llm.complete
    if complete is llm.complete and not llm.configured():
        base["expand_error"] = f"No AI key (add {llm.KEY_VAR} to mirsal/.env): using the built-in sets."
        return base
    rows, cols = grid
    n = rows * cols
    subject_slug = prompter.slug(" ".join(w for w in base["subject"].split() if w not in prompter.COLORS | prompter.STOP)) or "sticker"
    user = f"Request: {task}\nGrid: {rows}x{cols}, N = {n} cells."
    problems, meta, ai = [], {}, None
    for attempt in range(2):                                  # one answer, one repair round, then the built-in sets
        try:
            text, meta = complete(SYSTEM, user if not problems else user + "\nYour last answer had these problems, fix them and answer again:\n- " + "\n- ".join(problems))
            ai = _parse(text)
            problems = _lint(ai.get("cells"), n, subject_slug, task)
            if not problems and not str(ai.get("subject_description", "")).strip():
                problems = ["subject_description is empty"]
        except (llm.LLMError, ValueError) as e:
            if isinstance(e, llm.LLMError):
                base["expand_error"] = str(e)[:240]
                return base
            problems = [f"not valid JSON: {e}"]
        if not problems:
            break
    if problems:
        base["expand_error"] = "The AI answer did not pass the checks (" + "; ".join(problems)[:200] + "): using the built-in sets."
        return base
    if review_ai:
        rv = review({"subject_description": str(ai.get("subject_description", "")), "cells": [
            {"label": c.get("label", ""), "tags": [prompter.slug(str(c.get("key") or c.get("label", "")))]
             + [str(t) for t in (c.get("tags") or [])],
             "emoji": "".join([e for e in (c.get("emoji") or []) if isinstance(e, str)])} for c in ai["cells"]]},
            n, subject_slug, task, complete=complete)
        base["review"] = {k: v for k, v in rv.items() if k != "review_error"}
        if not rv["ok"]:
            base["expand_error"] = "The slot reviewer rejected the answer (" + "; ".join(rv["problems"])[:200] + "): using the built-in sets."
            return base
    cells = []
    words = " ".join([task, ai["subject_description"]] + [str(c.get("label", "")) for c in ai["cells"]]).lower()
    for i, c in enumerate(ai["cells"], 1):
        key = f"{subject_slug}_{prompter.slug(str(c.get('key') or c['label']))}"
        extra = [prompter.tag(str(t)) for t in (c.get("tags") or [])][:3]
        emoji = "".join([e.strip() for e in c["emoji"] if isinstance(e, str) and e.strip()][:2])
        cell = {"pos": i, "label": str(c["label"]).strip(), "tags": prompter.clean_tags(key, extra), "emoji": emoji}
        if str(c.get("motion") or "").strip():
            cell["motion"] = str(c["motion"]).strip()[:220]
        cells.append(cell)
    slots = dict(base["slots"])
    slots.update(subject_description=str(ai["subject_description"]).strip(), cells=cells,
                 key_colour="blue" if GREEN_WORDS & set(re.findall(r"[a-z]+", words)) else "green")
    built = prompter.render_plan(slots, base["template_id"], base["template_version"])
    base.update(slots=slots, sheet_prompt=built["sheet_prompt"], video_prompt=built["video_prompt"], expanded_by="ai", expand_model=meta.get("model"))
    base.pop("expand_error", None)
    if complete is llm.complete:  # ledger only for real calls (fakes in tests never log)
        from . import model_calls as _mc
        _mc.append(None, "LLM_PLAN", "openai", str(meta.get("model") or llm.model()), status="OK",
                   latency_ms=meta.get("ms"), tokens_in=meta.get("tokens_in"), tokens_out=meta.get("tokens_out"),
                   extra={"task": task, "grid": f"{rows}x{cols}", "reviewed": review_ai,
                          "review_model": (base.get("review") or {}).get("model")})
    base["stickers"] = [{"index": c["pos"], "id": f"prompt{c['pos']:02d}", "prompt": built["prompts"][c["pos"]], "key": c["tags"][0], "tags": c["tags"], "emoji": c["emoji"]}
                        for c in cells]
    return base
