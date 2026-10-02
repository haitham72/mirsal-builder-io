"""The agent graph (LangGraph): one turn of the chat as a small state machine over the Studio's engine.

    understand -> resolve -> [ new | another | edit | animate | feedback | review | ask | settings | search | confirm | cancel | smalltalk | clarify ]*  -> finish

`*`: a message can carry two intents ("I like 2 but make 5 happier"): the nodes run in order, then `finish`.

The graph only ORCHESTRATES. The rules that decide what may be approved, in which order, and that Python's blocks are final live in
flow/gates.py / flow/pipeline.py and are called through `tools`. The graph never touches pixels and never spends credits without a confirmation
(the "Create" button on a plan card, or a typed "yes") unless the user turned "ask before spending" off.

Every node writes to the turn's STEP TRACE, the small queue the chat shows while the agent works:

    ┌ generating teddy bear
    │
    ●  expand prompt >                       (a step; ">" opens its detail)
    │
    ●  added your preferences >
    │
    ◇  you consistently asked for a wider range of emotions     (a note: what the memory contributed)
    │
    └  plan ready · about 2 credits"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, TypedDict

from ..runtime import cache as cachemod
from .brain import Brain
from .memory import DEFAULT_SETTINGS, SessionError, SessionStore, gid_of, slug
from .resolver import DESCRIBE, Resolution, classify, is_sticker_answer, polarity_of, resolve, settings_from
from .tools import ConsoleTools, ToolError

INTERRUPTED = "That turn was interrupted before it finished (the server restarted); nothing was spent. Please say it again."
SUGGESTIONS = ["a teddy bear waving", "falcon stickers", "my dog as a banana", "Eid mubarak greetings"]
STYLE_NAMES = {"flat_vector": "flat vector", "pixar_3d": "Pixar 3D", "toon_cel": "toon cel", "glossy_3d": "glossy 3D"}


class Trace:
    """The visible step queue of one turn. Saved as it grows so the page (which polls) shows the agent working."""

    def __init__(self, store: SessionStore, sess: dict, msg: dict):
        self.store, self.sess, self.msg = store, sess, msg

    def _add(self, kind: str, label: str, detail=None, status: str = "done") -> dict:
        s = {"kind": kind, "label": label, "detail": detail, "status": status, "ts": round(time.time(), 3)}
        self.msg["steps"].append(s)
        self.store.save(self.sess)
        return s

    def task(self, label: str):
        return self._add("task", label, status="running")

    def step(self, label: str, detail=None):
        return self._add("step", label, detail)

    def note(self, label: str):
        return self._add("note", label)

    def end(self, label: str, ok: bool = True):
        return self._add("final", label, status="done" if ok else "error")

    def retitle(self, label: str) -> None:
        for s in self.msg["steps"]:
            if s["kind"] == "task":
                s["label"] = label
                break


@dataclass
class Turn:
    sid: str
    text: str
    selected: list
    action: dict | None
    sess: dict
    msg: dict
    trace: Trace
    intents: list = field(default_factory=list)
    conf: float = 0.0
    res: Resolution = field(default_factory=Resolution)
    reply: str = ""
    cards: list = field(default_factory=list)
    chips: list = field(default_factory=list)
    generation: str | None = None
    queue: list = field(default_factory=list)
    spent: float = 0.0
    _lock: Any = None


class State(TypedDict, total=False):
    turn: Any


def _credits(x) -> str:
    return "free" if not x else f"about {x:g} credit" + ("" if x == 1 else "s")


class Agent:
    def __init__(self, store: SessionStore, tools, brain: Brain | None = None, cache=None):
        self.store, self.tools = store, tools
        self.brain = brain or Brain()
        self.cache = cache or cachemod.default()
        self.graph = self._build()

    # ---- the graph ------------------------------------------------------------------------------------------------------------------
    def _build(self):
        from langgraph.graph import END, StateGraph
        g = StateGraph(State)
        nodes = {"understand": self.n_understand, "resolve": self.n_resolve, "new": self.n_new, "another": self.n_another,
                 "edit": self.n_edit, "animate": self.n_animate, "feedback": self.n_feedback, "review": self.n_review, "ask": self.n_ask,
                 "settings": self.n_settings, "search": self.n_search, "confirm": self.n_confirm, "cancel": self.n_cancel,
                 "smalltalk": self.n_smalltalk, "clarify": self.n_clarify, "finish": self.n_finish}
        for k, fn in nodes.items():
            g.add_node(k, fn)
        g.set_entry_point("understand")
        g.add_edge("understand", "resolve")
        targets = {k: k for k in nodes if k not in ("understand", "resolve")}
        g.add_conditional_edges("resolve", self.route, targets)
        for k in nodes:
            if k not in ("understand", "resolve", "finish"):
                g.add_conditional_edges(k, self.route, targets)
        g.add_edge("finish", END)
        return g.compile()

    def route(self, state: State) -> str:
        t: Turn = state["turn"]
        if t.res.needs_clarification and t.queue and t.queue[0] not in ("settings", "smalltalk"):
            t.queue.clear()
            return "clarify"
        return t.queue.pop(0) if t.queue else "finish"

    # ---- entry ------------------------------------------------------------------------------------------------------------------------
    def prepare(self, sid: str, text: str, selected: list | None = None, action: dict | None = None) -> Turn:
        """Take the session's lock (one turn at a time: a second message gets a 409, never a silent queue) and write the user's message and the
        assistant's "working" placeholder, so the page shows the turn at once. `execute` then runs the graph and releases the lock."""
        lock = self.cache.lock(f"session:{sid}")
        try:
            lock.__enter__()
        except cachemod.Busy:
            raise SessionError("The assistant is still working on your last message.", 409)
        try:
            sess = self.store.load(sid)
            for m in sess["messages"]:                           # we hold the lock, so nobody is running a turn: a "working" message is one that died with its server
                if m.get("status") == "working":
                    m.update(status="error", text=m.get("text") or INTERRUPTED)
            label = text.strip() if text.strip() else {"confirm": "Create", "cancel": "No"}.get((action or {}).get("type"), "")
            self.store.add_message(sess, "user", label)
            msg = self.store.add_message(sess, "assistant", "", status="working")
            self.store.save(sess)
        except Exception:
            lock.__exit__(None, None, None)
            raise
        t = Turn(sid, text, list(selected or []), action, sess, msg, Trace(self.store, sess, msg))
        t._lock = lock
        return t

    def execute(self, t: Turn) -> dict:
        try:
            try:
                self.graph.invoke({"turn": t})
            except Exception as e:                                  # the user sees a calm sentence, never the internals
                t.trace.end("something went wrong, nothing was spent", ok=False)
                t.reply = "Something went wrong on my side, and nothing was spent. Try again, or tell me a little differently."
                t.cards, t.chips = [], [{"label": "Try again", "text": t.text}] if t.text else []
                t.msg["error"] = f"{type(e).__name__}: {e}"[:300]
                self._finish(t, ok=False)
            return self.store.load(t.sid)["messages"][-1]
        finally:
            t._lock.__exit__(None, None, None)

    def run_turn(self, sid: str, text: str, selected: list | None = None, action: dict | None = None) -> dict:
        return self.execute(self.prepare(sid, text, selected, action))

    # ---- nodes ----------------------------------------------------------------------------------------------------------------------------
    def _named_batches(self, sess: dict, text: str) -> list[str]:
        """The batches the message names ("G012", "make G12/S3 happier") that exist and that this user may see, whether or not this chat has them yet."""
        gids = dict.fromkeys(f"G{int(m):03d}" for m in re.findall(r"\bg0*(\d{1,4})\b", text, flags=re.I))
        return [g for g in gids if self.store.subject_for_generation(sess, g) or self.store.outside_info(g)]

    def n_understand(self, state: State) -> dict:
        t: Turn = state["turn"]
        sess = t.sess
        pending = bool(sess.get("pending"))
        has_gen = bool((sess.get("focus") or {}).get("generation") or self.store.latest_pass(sess) or self._named_batches(sess, t.text))
        asked = sess.pop("awaiting", None)                     # a question I asked last turn lives for exactly one answer
        answered = False
        if t.action and t.action.get("type") in ("confirm", "cancel"):
            t.intents, t.conf = [t.action["type"].upper()], 1.0
        elif asked and asked.get("intents") and is_sticker_answer(t.text, bool(t.selected)):
            t.text = f"{asked['text']} {t.text}".strip()       # the original request plus the missing "which": everything downstream reads it as one sentence
            t.intents, t.conf, answered = list(asked["intents"]), 0.95, True
        else:
            t.intents, t.conf = classify(t.text, pending, has_gen, bool(t.selected))
            low = t.text.lower()
            if re.search(r"\b(approve|accept|reject|decline)\b", low) and has_gen:
                t.intents, t.conf = ["REVIEW"], 0.9
            if t.conf < 0.6 and self.brain.available:
                got = self.brain.classify(t.text, self.store.summary_text(sess))
                if got:
                    t.intents, t.conf = got, 0.7
        names = {"NEW": "a new set", "ANOTHER": "another pass", "EDIT_STICKERS": "an edit", "ANIMATE": "an animation", "FEEDBACK": "feedback",
                 "REVIEW": "a decision", "ASK": "a question", "CHANGE_SETTINGS": "a setting", "SEARCH": "a search", "CONFIRM": "your go-ahead",
                 "CANCEL": "a change of mind", "SMALLTALK": "a hello", "AMBIGUOUS": "something I need to ask about"}
        t.trace.task("reading your message")
        t.trace.step("understood: " + " + ".join(names.get(i, i.lower()) for i in t.intents) + (" · answering my question" if answered else ""))
        order = {"CONFIRM": "confirm", "CANCEL": "cancel", "CHANGE_SETTINGS": "settings", "FEEDBACK": "feedback", "REVIEW": "review",
                 "EDIT_STICKERS": "edit", "ANIMATE": "animate", "ANOTHER": "another", "NEW": "new", "ASK": "ask", "SEARCH": "search",
                 "SMALLTALK": "smalltalk", "AMBIGUOUS": "clarify"}
        t.queue = [order[i] for i in t.intents if i in order] or ["clarify"]
        return {}

    def _ctx(self, t: Turn) -> dict:
        sess = t.sess
        self.store.refresh(sess)
        focus = sess.get("focus") or {}
        gen = focus.get("generation") or (self.store.latest_pass(sess) or {}).get("generation")
        stickers, n, parent, known = [], 9, None, {}
        for subj in sess["subjects"]:
            for p in subj["passes"]:
                if p.get("generation"):
                    known[p["generation"]] = 9
        if gen:
            try:
                card = self.tools.generation(gen)
                stickers = [{"index": s["index"], "key": s["key"], "name": s.get("name") or s["key"], "tags": s.get("tags") or [], "emoji": s.get("emoji")}
                            for s in card["stickers"]]
                n = len(stickers) or 9
                known[gen] = n
                parent = card.get("parent")
            except Exception:
                pass
        latest = (self.store.latest_pass(sess) or {}).get("generation")
        return {"generation": gen, "n": n, "stickers": stickers, "focus_stickers": focus.get("stickers") or [], "selected": t.selected,
                "parent": parent, "latest": latest, "known": known}

    def n_resolve(self, state: State) -> dict:
        t: Turn = state["turn"]
        needs = [q for q in t.queue if q in ("edit", "feedback", "animate", "ask", "review", "another")]
        if not needs:
            return {}
        for gid in self._named_batches(t.sess, t.text):                       # "make G012/S3 happier": a batch the Studio made becomes a pass of this chat
            if not self.store.subject_for_generation(t.sess, gid) and self.store.adopt(t.sess, gid):
                t.trace.note(f"{gid} was made outside this chat (the Studio): I can work on it now")
        ctx = self._ctx(t)
        r = resolve(t.text, ctx)
        if not r.stickers and not r.needs_clarification and ("edit" in needs or "ask" in needs) and ctx["stickers"] and self.brain.available:
            nums = self.brain.pick_stickers(t.text, ctx["stickers"])
            if nums and ctx["generation"]:
                r.stickers, r.how = [f"{ctx['generation']}/S{i}" for i in nums], "language model"
        if "feedback" in needs and r.stickers and not (r.positive or r.negative):
            pol = polarity_of(t.text)                                     # "this is bad" + a clicked sticker: no number sat beside the opinion
            if pol == "NEGATIVE":
                r.negative = list(r.stickers)
            elif pol == "POSITIVE":
                r.positive = list(r.stickers)
        t.res = r
        if r.stickers:
            t.trace.step(f"found {', '.join(x.split('/')[1] for x in r.stickers)} in {r.generation}" + (f" · {r.how}" if r.how else ""))
        elif r.generation and needs and needs != ["another"]:
            t.trace.step(f"working in {r.generation}")
        return {}

    # -- new -----------------------------------------------------------------------------------------------------------------------------------
    def _prefs(self, t: Turn, subject_text: str) -> tuple[str, list]:
        """The user's memory as plan wording, and what it contributed (shown as steps and notes)."""
        sess, bits, notes = t.sess, [], []
        for trait in self.store.traits(sess):
            bits.append(trait)
            notes.append(f"you consistently asked for {trait}")
        for p in sess["preferences"]["persistent"]:
            bits.append(p)
        avoid = []
        for f in self.store.consume_temporary(sess):
            if f["polarity"] == "NEGATIVE":
                avoid += f["sticker_ids"]
        avoid = list(dict.fromkeys(avoid))
        if avoid:                                                      # the poses themselves go into the plan, not just a note: "avoid the poses of banana squashed, banana flat"
            bits.append("avoid the poses of " + ", ".join(dict.fromkeys(self._key_of(x.split("/")[0], x) for x in avoid[:4])))
        labels = [x.split("/")[1] for x in avoid]
        return (", ".join(dict.fromkeys(bits)), notes + ([f"you disliked {', '.join(labels)} last time, so those poses change"] if avoid else []))

    def n_new(self, state: State) -> dict:
        t: Turn = state["turn"]
        sess, st = t.sess, t.sess["settings"]
        guess = re.sub(r"^(?:please\s+)?(?:can you\s+)?(?:make|create|generate|give|draw|design|build)\s+(?:me\s+)?(?:some\s+|a\s+|an\s+)?|\bstickers?\b|\bpack of\b|\bset of\b",
                       " ", t.text, flags=re.I).strip(" .,!?") or t.text
        t.trace.retitle(f"generating {guess}")
        prefs, notes = self._prefs(t, guess)
        prompt = t.text.strip() + (f". {prefs[0].upper() + prefs[1:]}" if prefs else "")
        try:
            plan = self.tools.plan(prompt, st["grid"], st["style_id"], bool(st.get("ai", True)))
        except ToolError as e:
            t.reply = f"I couldn't turn that into a plan: {e}"
            t.trace.end("could not plan", ok=False)
            t.chips = [{"label": s, "text": s} for s in SUGGESTIONS[:3]]
            return {}
        names = [s["key"].replace("_", " ") for s in plan["stickers"]]
        t.trace.step("expand prompt", {"title": f"{len(names)} stickers", "lines": names})
        if prefs:
            t.trace.step("added your preferences", {"lines": [p.strip() for p in prefs.split(",") if p.strip()]})
        for n in notes:
            t.trace.note(n)
        tr = plan.get("transformation")
        if tr:                                    # "dog as banana": say that it is ONE new character, and which cells the template guarantees
            t.trace.note(f"a transformation: the whole character is a {tr['target']} with the {tr['subject']}'s face"
                         + (f"; {', '.join(tr['required'])} included" if tr.get("required") else "")
                         + (f"; left out as you asked: {', '.join(tr['forbidden'])}" if tr.get("forbidden") else ""))
        subject = plan.get("subject") or guess
        t.res.generation = None
        est = self.tools.estimate("image") if self.tools.live() else None
        card = {"type": "plan", "subject": subject, "grid": st["grid"], "style": STYLE_NAMES.get(st["style_id"], st["style_id"]),
                "count": len(names), "names": names, "estimate": est, "balance": self.tools.credits(), "prompt": prompt,
                "free": not self.tools.live(), **({"transformation": {k: tr[k] for k in ("id", "subject", "target", "required")}} if tr else {})}
        spend = self.tools.live()
        if spend and st.get("ask_before_spending", True):
            sess["pending"] = {"type": "create", "prompt": prompt, "subject": subject, "grid": st["grid"], "style_id": st["style_id"],
                               "ai": bool(st.get("ai", True)), "estimate": est}
            t.cards.append(card)
            t.reply = f"Here's the plan for **{subject}**: {len(names)} stickers, {STYLE_NAMES.get(st['style_id'], st['style_id'])}. {('It costs ' + _credits(est) + '. ') if est else ''}Shall I create it?"
            t.chips = [{"label": "Create it", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            t.trace.end(f"plan ready · {_credits(est)}")
            return {}
        self._start_create(t, {"prompt": prompt, "subject": subject, "grid": st["grid"], "style_id": st["style_id"], "ai": bool(st.get("ai", True))}, card)
        return {}

    def _start_create(self, t: Turn, p: dict, plan_card: dict | None = None, parent: str | None = None, regen_of: str | None = None,
                      refs: list | None = None, note: str = "") -> None:
        try:
            r = self.tools.create(p["prompt"], p["grid"], p["style_id"], p.get("ai", True), parent=parent, regen_of=regen_of, refs=refs)
        except ToolError as e:
            t.reply = f"I couldn't start that: {e}"
            t.trace.end("not started", ok=False)
            return
        self.store.add_pass(t.sess, p["subject"], generation=r.get("generation"), job=r.get("job"), prompt=p["prompt"], grid=p["grid"],
                            style_id=p["style_id"], parent=parent, note=note)
        if r.get("generation"):
            t.generation = r["generation"]
            t.sess["focus"] = {"generation": r["generation"], "stickers": []}
        t.spent += r.get("estimate") or 0
        t.cards.append({"type": "generation", "generation": r.get("generation"), "job": r.get("job"), "subject": p["subject"],
                        "parent": parent, "note": note})
        t.reply = (t.reply + " " if t.reply else "") + (f"Creating **{p['subject']}** now" + (f" ({_credits(r.get('estimate'))})" if r.get("estimate") else "") + ". The stickers appear below as they are ready.")
        t.trace.end("started · " + (r.get("job") or r.get("generation") or ""))

    def n_confirm(self, state: State) -> dict:
        t: Turn = state["turn"]
        p = t.sess.get("pending")
        if not p:
            t.reply = "There is nothing waiting for a go-ahead. What would you like to make?"
            t.chips = [{"label": s, "text": s} for s in SUGGESTIONS[:3]]
            return {}
        t.sess["pending"] = None
        t.trace.step(f"confirmed: {p['type']}")
        if p["type"] == "create":
            t.trace.retitle(f"generating {p['subject']}")
            self._start_create(t, p, parent=p.get("parent"), regen_of=p.get("regen_of"), refs=p.get("refs"), note=p.get("note", ""))
        elif p["type"] == "animate":
            t.trace.retitle(f"animating {p['generation']}")
            try:
                r = self.tools.animate(p["generation"], p.get("loop", False))
                t.generation = p["generation"]
                t.cards.append({"type": "generation", "generation": p["generation"], "job": r["job"], "subject": p.get("subject", ""), "animating": True})
                t.reply = f"Animating {p['generation']}" + (f" ({_credits(r.get('estimate'))})" if r.get("estimate") else "") + ". I'll show each one as it's ready."
                t.trace.end("animation started")
            except ToolError as e:
                t.reply = f"I couldn't start the animation: {e}"
                t.trace.end("not started", ok=False)
        elif p["type"] == "describe":                       # "Allow AI vision of generated media?" answered yes: asked once, remembered in the session
            t.sess["settings"]["allow_vlm"] = True
            t.trace.retitle(f"looking at {p['generation']}")
            self._run_describe(t, p["generation"], p.get("only") or [])
        elif p["type"] == "batch":
            t.trace.retitle("regenerating " + ", ".join(i["label"] for i in p["items"]))
            n = 0
            for it in p["items"]:
                self._start_create(t, {**it, "grid": "1x1", "style_id": p["style_id"], "ai": p.get("ai", True)}, parent=it["parent"],
                                   regen_of=it["regen_of"], refs=it.get("refs"), note=it["note"])
                n += 1
            t.reply = f"Regenerating {n} sticker{'s' if n != 1 else ''}; the other stickers stay as they are."
        return {}

    def n_cancel(self, state: State) -> dict:
        t: Turn = state["turn"]
        p = t.sess.get("pending")
        t.sess["pending"] = None
        if p and p.get("type") == "describe":
            t.sess["settings"]["allow_vlm"] = False
            t.trace.step("AI vision stays off")
            t.reply = "No problem, I won't send your stickers to a vision model. Say \"allow AI vision\" if you change your mind."
            return {}
        t.trace.step("cancelled, nothing was spent")
        t.reply = "No problem, nothing was spent. Tell me what to change, or what else to make."
        t.chips = [{"label": s, "text": s} for s in SUGGESTIONS[:3]]
        return {}

    # -- another / edit ---------------------------------------------------------------------------------------------------------------------
    def _focus_pass(self, t: Turn) -> tuple[dict | None, dict | None]:
        gen = t.res.generation or (t.sess.get("focus") or {}).get("generation") or (self.store.latest_pass(t.sess) or {}).get("generation")
        subj = self.store.subject_for_generation(t.sess, gen) if gen else None
        p = next((q for q in subj["passes"] if q.get("generation") == gen), None) if subj else None
        return subj, p

    def n_another(self, state: State) -> dict:
        t: Turn = state["turn"]
        subj, p = self._focus_pass(t)
        if not p:
            t.reply = "Which subject would you like another set of? Tell me what to make."
            return {}
        st = t.sess["settings"]
        t.trace.retitle(f"another pass of {subj['name']}")
        prefs, notes = self._prefs(t, subj["name"])
        prompt = p["prompt"] + (f". {prefs[0].upper() + prefs[1:]}" if prefs else "") + ". A different set of poses and expressions than before"
        for n in notes:
            t.trace.note(n)
        spec = {"prompt": prompt, "subject": subj["name"], "grid": p.get("grid") or st["grid"], "style_id": p.get("style_id") or st["style_id"], "ai": True}
        if not self.tools.live():
            try:
                r = self.tools.more(p["generation"])
                self.store.add_pass(t.sess, subj["name"], generation=r["generation"], prompt=p["prompt"], grid=spec["grid"],
                                    style_id=spec["style_id"], parent=p["generation"], note="another variation")
                t.generation = r["generation"]
                t.sess["focus"] = {"generation": r["generation"], "stickers": []}
                t.cards.append({"type": "generation", "generation": r["generation"], "job": None, "subject": subj["name"], "parent": p["generation"]})
                t.reply = f"Here is another take on **{subj['name']}**."
                t.trace.end("done")
            except ToolError as e:
                t.reply = str(e)
                t.trace.end("no more variations", ok=False)
            return {}
        est = self.tools.estimate("image")
        spec.update(type="create", estimate=est, parent=p["generation"], note=f"another pass of {p['generation']}")
        if t.sess["settings"].get("ask_before_spending", True):
            t.sess["pending"] = spec
            t.reply = f"I'll make another pass of **{subj['name']}** with different poses ({_credits(est)}). Go ahead?"
            t.chips = [{"label": "Create it", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            t.trace.end(f"ready · {_credits(est)}")
        else:
            self._start_create(t, spec, parent=p["generation"], note=spec["note"])
        return {}

    def n_edit(self, state: State) -> dict:
        t: Turn = state["turn"]
        subj, p = self._focus_pass(t)
        targets = t.res.stickers or (t.res.negative if t.res.negative else [])
        if not targets or not p:
            t.reply = "Which sticker should I change? Say a number, like \"make number 3 happier\", or click one."
            t.chips = []
            if p:
                t.sess["awaiting"] = {"intents": ["EDIT_STICKERS"], "text": t.text}
            return {}
        gen = targets[0].split("/")[0]
        edit = re.sub(r"\b(make|redo|regenerate|change|fix|replace|improve|number|no\.?|sticker|#)\s*|\b(g\d+\s*/?\s*s\d|s\d|\d+)\b|\b(it|that|this|these|those|them|one)\b", " ",
                      t.text, flags=re.I)
        edit = re.sub(r"\b(like|but|and|i|the|a)\b", " ", edit, flags=re.I)
        edit = re.sub(r"\s+", " ", edit).strip(" .,!?") or "a fresh take"
        if t.res.references:
            edit = "same look as " + ", ".join(self._key_of(gen, r["source"]) for r in t.res.references) + (f" ({edit})" if edit != "a fresh take" else "")
        card = self.tools.generation(gen)
        items = []
        for sid in targets[:4]:
            s = next((x for x in card["stickers"] if x["id"] == sid), None)
            if not s:
                continue
            base = (subj["name"] if subj else "sticker")
            prompt = f"{base}: {s['key'].replace('_', ' ')}, {edit}"
            refs = []
            for r in t.res.references:
                if r["target"] == sid and hasattr(self.tools, "reference_from_sticker"):
                    try:
                        refs.append(self.tools.reference_from_sticker(r["source"]))
                    except Exception:
                        pass
            items.append({"prompt": prompt, "subject": subj["name"] if subj else base, "parent": gen, "regen_of": sid, "refs": refs,
                          "note": f"{sid.split('/')[1]} redone: {edit}", "label": sid.split("/")[1]})
        if not items:
            t.reply = "I couldn't find those stickers in this batch."
            return {}
        t.trace.retitle("editing " + ", ".join(i["label"] for i in items))
        t.trace.step("expand prompt", {"lines": [i["prompt"] for i in items]})
        if t.res.references:
            t.trace.note("using " + ", ".join(r["source"].split("/")[1] for r in t.res.references) + " as the reference")
        est = self.tools.estimate("image")
        total = (est or 0) * len(items)
        spec = {"type": "batch", "items": items, "style_id": t.sess["settings"]["style_id"], "ai": True, "estimate": total}
        if self.tools.live() and t.sess["settings"].get("ask_before_spending", True):
            t.sess["pending"] = spec
            t.reply = f"I'll redo {', '.join(i['label'] for i in items)} ({edit}); the rest of the batch stays. {('That costs ' + _credits(total) + '. ') if total else ''}Go ahead?"
            t.chips = [{"label": "Do it", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            t.trace.end(f"ready · {_credits(total)}")
        else:
            t.sess["pending"] = spec
            t.trace.step("confirmed: edit")
            self.n_confirm({"turn": _with_pending(t, spec)})
        return {}

    def _key_of(self, gen: str, sid: str) -> str:
        try:
            s = next(x for x in self.tools.generation(gen)["stickers"] if x["id"] == sid)
            return s["key"].replace("_", " ")
        except Exception:
            return sid.split("/")[1]

    # -- animate ----------------------------------------------------------------------------------------------------------------------------
    def n_animate(self, state: State) -> dict:
        t: Turn = state["turn"]
        gen = t.res.generation or (t.sess.get("focus") or {}).get("generation") or (self.store.latest_pass(t.sess) or {}).get("generation")
        if not gen:
            t.reply = "There is nothing to animate yet. Let's make some stickers first."
            t.chips = [{"label": s, "text": s} for s in SUGGESTIONS[:3]]
            return {}
        ready = self.tools.ready_indexes(gen)
        if not ready:
            t.reply = f"{gen} has no finished stickers yet; I'll animate them once they're ready."
            return {}
        subj = self.store.subject_for_generation(t.sess, gen)
        t.trace.retitle(f"animating {gen}")
        t.trace.step(f"{len(ready)} stickers ready to move")
        spec = {"type": "animate", "generation": gen, "subject": subj["name"] if subj else "", "loop": False}
        if self.tools.live() and t.sess["settings"].get("ask_before_spending", True):
            t.sess["pending"] = spec
            t.reply = f"I'll animate the {len(ready)} stickers of {gen} (the price is shown when it is sent; about 8 credits for a 3×3 sheet). Go ahead?"
            t.chips = [{"label": "Animate", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            t.trace.end("ready")
        else:
            t.sess["pending"] = spec
            self.n_confirm({"turn": _with_pending(t, spec)})
        return {}

    # -- feedback / review ----------------------------------------------------------------------------------------------------------------------
    def n_feedback(self, state: State) -> dict:
        t: Turn = state["turn"]
        r = t.res
        if not (r.positive or r.negative):
            if r.stickers:                                                 # we know which, not what the user thinks of it
                n = r.stickers[0].split("/S")[1]
                t.reply = t.reply or f"What do you think of {', '.join(x.split('/')[1] for x in r.stickers)}?"
                t.chips = [{"label": "I like it", "text": f"I like number {n}"}, {"label": "Not for me", "text": f"I don't like number {n}"}]
                return {}
            t.reply = t.reply or "Which sticker do you mean? Say its number, or click it. (For example \"I like 2 and 7 but not 3\".)"
            if t.res.generation:
                t.sess["awaiting"] = {"intents": ["FEEDBACK"], "text": t.text}
            return {}
        persistent = bool(re.search(r"\b(never|always|from now on|every time|i never want|i always want)\b", t.text.lower()))
        if r.positive:
            self.store.add_feedback(t.sess, "POSITIVE", r.positive, t.text, "PERSISTENT" if persistent else "TEMPORARY")
        if r.negative:
            self.store.add_feedback(t.sess, "NEGATIVE", r.negative, t.text, "PERSISTENT" if persistent else "TEMPORARY")
        t.sess["focus"] = {"generation": r.generation, "stickers": r.positive[:1] or r.negative[:1]}
        bits = [f"+{x.split('/')[1]}" for x in r.positive] + [f"−{x.split('/')[1]}" for x in r.negative]
        t.trace.step("noted " + " ".join(bits))
        if persistent:
            t.trace.note("saved as a lasting preference because you said so")
        if "edit" not in t.queue:
            t.reply = f"Noted: {' '.join(bits)}. I'll use that for the next set." + (" (Saved as a lasting preference.)" if persistent else "")
            t.chips = [{"label": "Make another set", "text": "make another set"}] + (
                [{"label": f"Redo {r.negative[0].split('/')[1]}", "text": f"redo number {r.negative[0].split('/')[1][1:]}"}] if r.negative else [])
        return {}

    def n_review(self, state: State) -> dict:
        t: Turn = state["turn"]
        gen = t.res.generation or (t.sess.get("focus") or {}).get("generation")
        if not gen:
            t.reply = "There is nothing to review yet."
            return {}
        low = t.text.lower()
        decision = "REJECT" if re.search(r"\b(reject|decline)\b", low) else "APPROVE"
        ready = self.tools.ready_indexes(gen)
        m = re.search(r"\ball\b(?:\s+(?:of them|the stickers))?\s*(?:but|except)\s+(.*)", low)
        if m:
            from .resolver import _numbers
            skip = _numbers(m.group(1), 9)
            idx = [i for i in ready if i not in skip]
        elif re.search(r"\b(all|everything|them all)\b", low):
            idx = ready
        else:
            idx = [int(s.split("/")[1][1:]) for s in t.res.stickers]
        if not idx:
            t.reply = "Which stickers? For example \"approve all but 5 and 6\"."
            t.sess["awaiting"] = {"intents": ["REVIEW"], "text": t.text}
            return {}
        t.trace.retitle(("approving" if decision == "APPROVE" else "rejecting") + f" in {gen}")
        r = self.tools.review(gen, decision, idx, "from the chat")
        t.trace.step(f"{decision.lower()}d {', '.join('S' + str(i) for i in r['done'])}")
        verb = "Approved" if decision == "APPROVE" else "Rejected"
        t.reply = f"{verb} {', '.join('S' + str(i) for i in r['done'])}." + (
            " Python blocked " + ", ".join(f"S{x['index']}" for x in r["refused"]) + ", and a block is final." if r["refused"] else "")
        t.generation = gen
        t.cards.append({"type": "generation", "generation": gen, "job": None, "subject": ""})
        t.chips = [{"label": "Animate them", "text": "animate"}]
        t.trace.end("recorded as your decision")
        return {}

    # -- ask / search / settings / smalltalk / clarify ----------------------------------------------------------------------------------------------
    def n_ask(self, state: State) -> dict:
        t: Turn = state["turn"]
        r = t.res
        low = t.text.lower()
        if re.search(DESCRIBE, low):
            return self._describe(t)
        t.trace.retitle("looking it up")
        if r.stickers and re.search(r"\b(which|what|where|who)\b", low):
            gen = r.generation
            card = self.tools.generation(gen)
            hits = [s for s in card["stickers"] if s["id"] in r.stickers]
            t.reply = "; ".join(f"{s['id']}: {s['key'].replace('_', ' ')} {''.join(s['emoji']) if isinstance(s.get('emoji'), list) else s.get('emoji') or ''}".strip() for s in hits)
            t.cards.append({"type": "stickers", "stickers": hits})
            t.sess["focus"] = {"generation": gen, "stickers": [s["id"] for s in hits][:1]}
            t.trace.end("answered from what we made")
            return {}
        if re.search(r"\bhow many\b", low):
            self.store.refresh(t.sess)
            total = sum(p["ready"] for s in t.sess["subjects"] for p in s["passes"])
            appr = sum(p["approved"] for s in t.sess["subjects"] for p in s["passes"])
            t.reply = f"{total} stickers made in this chat, {appr} approved."
            t.trace.end("counted")
            return {}
        facts = self.store.summary_text(t.sess)
        ans = self.brain.answer(t.text, facts) if self.brain.available else None
        t.reply = ans or facts
        t.trace.end("answered" if ans else "here is what we have")
        return {}

    def _describe(self, t: Turn) -> dict:
        """"Describe the stickers": the person's yes to AI vision comes first, once per chat (`settings.allow_vlm`: None = not asked, True, False)."""
        gen = t.res.generation or (t.sess.get("focus") or {}).get("generation") or (self.store.latest_pass(t.sess) or {}).get("generation")
        if not gen:
            t.reply = "Which batch should I look at? Tell me a number like G012."
            return {}
        only = [int(x.split("/S")[1]) for x in t.res.stickers if x.startswith(gen + "/S")]
        allow = t.sess["settings"].get("allow_vlm")
        t.trace.retitle(f"looking at {gen}")
        if allow is False:
            t.reply = "AI vision is off for this chat, so I won't send the pictures to a model. Say \"allow AI vision\" and ask again."
            t.trace.end("AI vision is off", ok=False)
            return {}
        if allow is None:
            t.sess["pending"] = {"type": "describe", "generation": gen, "only": only}
            t.reply = (f"To describe {gen} I send its pictures to the vision model (the local one when LM Studio is running, otherwise the cloud one). "
                       "Allow AI vision of generated media? I only ask once.")
            t.chips = [{"label": "Allow AI vision", "action": "confirm"}, {"label": "Not now", "action": "cancel"}]
            t.trace.end("waiting for your yes")
            return {}
        self._run_describe(t, gen, only)
        return {}

    def _run_describe(self, t: Turn, gen: str, only: list) -> None:
        try:
            caps = self.tools.captions(gen, True)
        except ToolError as e:
            t.reply = str(e) if e.code != 404 else "I can't find that batch."
            t.trace.end("could not look", ok=False)
            return
        rows = [c for c in caps if not only or c["index"] in only]
        t.trace.step(f"asked the vision model about {len(rows)} sticker{'s' if len(rows) != 1 else ''}")
        t.reply = "\n".join(f"S{c['index']}: {c['caption']}" if c.get("caption") else f"S{c['index']}: I couldn't read this one" for c in rows) or f"{gen} has no finished stickers yet."
        t.sess["focus"] = {"generation": gen, "stickers": [f"{gen}/S{c['index']}" for c in rows][:3] if only else []}
        t.generation = gen
        t.trace.end("described")

    def n_search(self, state: State) -> dict:
        t: Turn = state["turn"]
        q = re.sub(r"\b(find|search|look for|do i have|show me|my|old|from before|sticker|stickers|a|the)\b", " ", t.text, flags=re.I).strip()
        q = re.sub(r"\s+", " ", q) or t.text
        t.trace.retitle(f"searching for {q}")
        hits = self.tools.search(q)
        t.trace.step(f"{len(hits)} match{'es' if len(hits) != 1 else ''}")
        if hits:
            t.cards.append({"type": "stickers", "stickers": hits[:9]})
            t.reply = f"Found {len(hits)} for \"{q}\"."
        else:
            t.reply = f"Nothing matches \"{q}\" yet. Want me to make it?"
            t.chips = [{"label": f"Make {q}", "text": f"make {q}"}]
        t.trace.end("done")
        return {}

    def n_settings(self, state: State) -> dict:
        t: Turn = state["turn"]
        try:
            from ..generation import prompter
            ids = list(prompter.STYLES)
        except Exception:
            ids = None
        new = settings_from(t.text, ids)
        if not new:
            t.reply = "Which setting? I can change the grid (2×2 or 3×3), the style, and whether I ask before spending."
            return {}
        t.sess["settings"].update(new)
        labels = {"grid": lambda v: f"{v} grid", "style_id": lambda v: STYLE_NAMES.get(v, v) + " style", "ask_before_spending": lambda v: "asking before I spend" if v else "no confirmation before spending",
                  "allow_vlm": lambda v: "AI vision allowed (I may send your stickers to the vision model)" if v else "AI vision off"}
        said = ", ".join(labels[k](v) for k, v in new.items() if k in labels)
        t.trace.task("changing settings")
        t.trace.step(said)
        t.trace.end("saved")
        t.reply = f"Done: {said}, from now on."
        return {}

    def n_smalltalk(self, state: State) -> dict:
        t: Turn = state["turn"]
        t.trace.task("saying hello")
        t.reply = "Hi! What will you create today?"
        t.chips = [{"label": s, "text": s} for s in SUGGESTIONS]
        t.trace.end("ready")
        return {}

    def n_clarify(self, state: State) -> dict:
        t: Turn = state["turn"]
        r = t.res
        if r.needs_clarification:
            asked = [i for i in t.intents if i not in ("AMBIGUOUS", "SMALLTALK", "CONFIRM", "CANCEL")]
            if asked:
                t.sess["awaiting"] = {"intents": asked, "text": t.text}
            t.reply = r.clarification or "Which one do you mean?"
            t.chips = [{"label": "#" + o.split("/S")[1], "text": f"number {o.split('/S')[1]}"} for o in r.options]
            t.trace.end("one question")
        else:
            t.reply = "I'm not sure what to make yet. Tell me a subject, like \"a teddy bear waving\", or pick one:"
            t.chips = [{"label": s, "text": s} for s in SUGGESTIONS]
            t.trace.end("asked what to make")
        return {}

    # -- finish: memory ------------------------------------------------------------------------------------------------------------------------------
    def n_finish(self, state: State) -> dict:
        t: Turn = state["turn"]
        self._finish(t)
        return {}

    def _finish(self, t: Turn, ok: bool = True) -> None:
        sess, msg = t.sess, t.msg
        if t.res.generation and t.res.stickers:
            sess["focus"] = {"generation": t.res.generation, "stickers": t.res.stickers[:3]}
        elif t.generation:
            sess["focus"] = {"generation": t.generation, "stickers": []}
        msg.update(text=t.reply, cards=t.cards, chips=t.chips, status="done" if ok else "error")
        if msg["steps"] and msg["steps"][-1]["kind"] != "final":
            t.trace.end("done" if ok else "stopped", ok=ok)
        self.store.add_interaction(sess, t.text or (t.action or {}).get("type", ""), t.reply, t.intents,
                                   {**t.res.to_dict(), "spent_estimate": t.spent}, t.generation or t.res.generation)
        if self.store.reduce(sess, summarise=(self.brain.summarise if self.brain.available else None)):
            t.trace.note("summarised the earlier part of this chat")
        self.store.save(sess)


def _with_pending(t: Turn, spec: dict) -> Turn:
    t.sess["pending"] = spec
    return t


def run_turn(console, sid: str, text: str, selected: list | None = None, action: dict | None = None, user: dict | None = None) -> dict:
    """The entry the server calls: the Studio's Console, one session id, the user's text (or a button action) and the UI selection."""
    user = user or {"id": "local", "role": "owner", "can_spend": True}
    store = SessionStore(console.out, user=user["id"], see_all=user.get("role") == "owner")
    agent = Agent(store, ConsoleTools(console, user), Brain(out=console.out))
    return agent.run_turn(sid, text, selected, action)


def _nobody_is_working(store: SessionStore, sid: str) -> bool:
    """A running turn holds the session's lock (see `Agent.prepare`); when it is free, a message that still says "working" died with its server."""
    try:
        with store.cache.lock(f"session:{sid}", 1000):
            return True
    except cachemod.Busy:
        return False


def hydrate(store: SessionStore, tools, sess: dict) -> dict:
    """The session as the page shows it: every generation card carries its live data (stickers with file urls, stage), and a card that is
    still a provider job carries the job's state until the job has produced a generation. Cheap enough to poll every second."""
    store.refresh(sess)
    if any(m.get("status") == "working" for m in sess["messages"]) and _nobody_is_working(store, sess["id"]):
        sess = store.load(sess["id"])                          # read again: the turn may have finished between the two reads
        for m in sess["messages"]:
            if m.get("status") == "working":
                m.update(status="error", text=m.get("text") or INTERRUPTED)
        store.save(sess)
    out = dict(sess)
    msgs = []
    for m in sess["messages"]:
        m = dict(m)
        cards = []
        for c in m.get("cards", []):
            c = dict(c)
            if c.get("type") == "generation":
                gid = c.get("generation")
                if not gid and c.get("job"):
                    try:
                        j = tools.job(c["job"])
                        c.update(job_status=j.get("status"), job_stage=j.get("stage"), job_error=j.get("error"), cost=j.get("cost"))
                        gid = j.get("generation")
                    except Exception:
                        pass
                if gid:
                    c["generation"] = gid
                    try:
                        c["data"] = tools.generation(gid)
                    except Exception:
                        pass
            cards.append(c)
        m["cards"] = cards
        msgs.append(m)
    out["messages"] = msgs
    out["working"] = any(m.get("status") == "working" for m in msgs)
    out["summary_text"] = store.summary_text(sess)
    return out
