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

from ..generation import styles
from ..runtime import cache as cachemod
from . import creator
from .brain import Brain
from .memory import DEFAULT_SETTINGS, SessionError, SessionStore, gid_of, slug
from . import editroute, refine, subjects
from .profile import Profile
from .resolver import DESCRIBE, NAME_QUESTION, Resolution, beyond, classify, is_sticker_answer, particles_intent, polarity_of, resolve, settings_from, smalltalk_kind, profile_facts, request_text
from .profile import profile_said
from .tools import ConsoleTools, ToolError

INTERRUPTED = "That turn was interrupted before it finished (the server restarted). Check the Queue for any job already started before trying again."


def _interrupt_message(msg):
    msg.update(status="error", text=msg.get("text") or INTERRUPTED)
    msg.setdefault("steps", []).append({"kind": "note", "label": INTERRUPTED, "status": "done"})
CONTINUE_RX = r"^(?:continue|go on|go ahead|proceed|carry on|keep going|approve and continue|resume)\b"
CREATION_INTENTS = {"NEW", "NEW_MULTI", "ANOTHER", "REFINE", "EDIT_STICKERS", "EDIT_ROUTE", "ANIMATE", "CONFIRM", "EFFECTS", "PARTICLES", "CREATOR", "RETRY"}
SUGGESTIONS = ["a teddy bear waving", "falcon stickers", "my dog as a banana", "Eid mubarak greetings"]
STYLE_NAMES = {p["id"]: p["label"].lower() for p in styles.PRESETS}          # the names the cards and replies use: the real presets, never a list of the chat's own


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

    def rules_note(self, reason: str):
        """"answered by rules: <why>": the model was asked and could not answer, so the rules decided. Placed before the ending step (the collapsed trace shows the last step's label)."""
        steps = self.msg["steps"]
        steps.insert(len(steps) - 1 if steps and steps[-1]["kind"] == "final" else len(steps),
                     {"kind": "note", "label": "answered by rules: " + " ".join(str(reason).split())[:160], "detail": None, "status": "done", "ts": round(time.time(), 3)})
        self.store.save(self.sess)

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
    prev_pending: dict | None = None             # the plan that was waiting when this message arrived (a new one replaces it, and the reply says so)
    er: dict | None = None                       # what an edit request means (agent/editroute.classify_edit): the editor, or a tweak / an action / a redesign
    answer: str = ""                             # the typed answer to my "which sticker?" (t.text then holds the original request + the answer): "12" is checked against the batch's size
    unsure_review: bool = False                  # an approve / reject sentence with a negation in it: nothing is decided, the person is asked
    profile_answer: dict | None = None           # the reply to my own "what should I call you?": {"name": "Haitham"}, never a subject
    prefix: str = ""                             # what the profile node said, put before the rest of the turn's answer ("Nice to meet you, Sam! ..." then the plan)
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
        nodes = {"understand": self.n_understand, "resolve": self.n_resolve, "new": self.n_new, "multi": self.n_multi, "effects": self.n_effects, "particles": self.n_particles, "editroute": self.n_editroute, "unsupported": self.n_unsupported, "refine": self.n_refine, "another": self.n_another,
                  "edit": self.n_edit, "undo": self.n_undo, "animate": self.n_animate, "export": self.n_export, "feedback": self.n_feedback, "review": self.n_review, "ask": self.n_ask,
                 "settings": self.n_settings, "search": self.n_search, "confirm": self.n_confirm, "cancel": self.n_cancel,
                 "smalltalk": self.n_smalltalk, "profile": self.n_profile, "clarify": self.n_clarify, "retry": self.n_retry, "names": self.n_names, "names_decide": self.n_names_decide, "creator": self.n_creator, "finish": self.n_finish}
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
                    _interrupt_message(m)
            label = text.strip() if text.strip() else {"confirm": "Create", "cancel": "No", "creator_go": "Approve and continue", "creator_stop": "Stop", "creator_skip": "Continue without those", "creator_force": "Continue with them",
        "creator_force_video": "Animate at the new price", "names_apply": "Apply the new names", "names_keep": "Keep my names", "retry_sheet": "Try the sheet again"}.get((action or {}).get("type"), "")
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
        self.brain.last_error = None                                  # per turn: `_finish` says "answered by rules" only for a failure of THIS turn
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
    def _nm(self, sess: dict, gid) -> str:
        """What the person calls a batch: its subject ("Eid mubarak greetings"), never the bare id "G096" (the id stays in the card's small print and the tooltips)."""
        gid = str(gid or "")
        subj = self.store.subject_for_generation(sess, gid) if gid else None
        name = (subj or {}).get("name") or ((self.store.outside_info(gid) or {}).get("prompt") if gid else "") or ""
        name = " ".join(str(name).split())[:48]
        return (name[:1].upper() + name[1:]) if name else gid

    def _named_batches(self, sess: dict, text: str) -> list[str]:
        """The batches the message names ("G012", "make G12/S3 happier") that exist and that this user may see, whether or not this chat has them yet."""
        gids = dict.fromkeys(f"G{int(m):03d}" for m in re.findall(r"\bg0*(\d{1,4})\b", text, flags=re.I))
        return [g for g in gids if self.store.subject_for_generation(sess, g) or self.store.outside_info(g)]

    @staticmethod
    def _profile_reply(text: str) -> str | None:
        """A short reply that can be the answer to my "what should I call you?": "haitham", "it's Haitham", "Sam!". Not a question, not a request, not a no."""
        s = text.strip().strip("\"'“”‘’.!")
        named = profile_facts(s)[0].get("name")
        if named:
            return named
        if not s or "?" in s or len(s.split()) > 3 or re.search(r"\b(?:make|create|generate|draw|give|no|nope|not|never|why|sticker|stickers)\b", s.lower()):
            return None
        return " ".join(w[:1].upper() + w[1:] for w in s.split()) if re.fullmatch(r"[^\W\d_][^\W\d_'’ -]{0,40}", s) else None

    def _route_context(self, sess: dict, asked: dict | None) -> str:
        """What the model router sees besides the message: the person's profile, the question I asked last turn, the plan I am holding, then the chat's summary.
        Without these, "haitham" after "what should I call you?" reads like a subject."""
        bits = [self._profile().facts_text() or "The person: nothing known yet."]
        if asked:
            bits.append("My last question: " + ("what should I call you?" if asked.get("profile") else str(asked.get("text") or "")[:200]))
        held = sess.get("pending") or {}
        if held:
            bits.append(f"A plan I am holding (not started, waiting for the go-ahead): {held.get('subject') or held.get('type')}.")
        return "\n".join(bits + [self.store.summary_text(sess)])

    def n_understand(self, state: State) -> dict:
        t: Turn = state["turn"]
        sess = t.sess
        pending = bool(sess.get("pending"))
        t.prev_pending = sess.get("pending")
        has_gen = bool((sess.get("focus") or {}).get("generation") or self.store.latest_pass(sess) or self._named_batches(sess, t.text))
        asked = sess.pop("awaiting", None)                     # a question I asked last turn lives for exactly one answer
        answered = False
        if t.action and t.action.get("type") in ("confirm", "confirm_new", "cancel"):
            t.intents, t.conf = [t.action["type"].upper()], 1.0
        elif t.action and t.action.get("type") == "retry_sheet":
            t.intents, t.conf = ["RETRY"], 1.0
        elif t.action and str(t.action.get("type", "")).startswith("creator_"):
            t.intents, t.conf = ["CREATOR"], 1.0
        elif (sess.get("creator_run") or {}).get("status") in ("waiting", "stopped") and re.match(CONTINUE_RX, t.text.strip().lower()):
            t.action = {"type": "creator_go"}
            t.intents, t.conf = ["CREATOR"], 0.95
        elif t.action and t.action.get("type") in ("names_apply", "names_keep"):
            t.intents, t.conf = ["NAMES_DECIDE"], 1.0
        elif asked and asked.get("profile") and self._profile_reply(t.text):
            t.profile_answer = {asked["profile"]: self._profile_reply(t.text)}       # "haitham" right after my "what should I call you?" is the answer, never a subject
            t.intents, t.conf, answered = ["PROFILE"], 0.95, True
        elif asked and asked.get("intents") and is_sticker_answer(t.text, bool(t.selected)):
            t.answer = t.text
            t.text = f"{asked['text']} {t.text}".strip()       # the original request plus the missing "which": everything downstream reads it as one sentence
            t.intents, t.conf, answered = list(asked["intents"]), 0.95, True
            if "EDIT_ROUTE" in t.intents:
                t.er = editroute.classify_edit(asked["text"])
        else:
            t.intents, t.conf = classify(t.text, pending, has_gen, bool(t.selected))
            low = t.text.lower()
            if re.search(r"\b(approve|accept|reject|decline)\b", low) and has_gen:
                if re.search(r"\b(?:don'?t|do not|dont|can'?t|cannot|won'?t|will not|never|not|no)\b", low):
                    t.intents, t.conf, t.unsure_review = ["AMBIGUOUS"], 0.5, True          # "don't approve 3" approved S3 before: a decision is never guessed from a negation
                else:
                    t.intents, t.conf = ["REVIEW"], 0.9
            if t.conf < 0.6 and self.brain.available:
                got = self.brain.classify(t.text, self._route_context(sess, asked), focus=self.store.focus_context(sess))
                if got:
                    t.intents, t.conf = got, 0.7
            if has_gen and t.intents and t.intents[0] not in ("CONFIRM", "CANCEL", "SMALLTALK", "PROFILE", "CHANGE_SETTINGS", "REVIEW", "SEARCH", "CREATOR", "PARTICLES", "UNDO", "EXPORT"):         # a question ("can you rotate him?") is an ASK until the rules read it
                if editroute.unsupported(t.text):
                    t.intents, t.conf = ["UNSUPPORTED"], 0.9
                else:
                    er = editroute.classify_edit(t.text)
                    if er:                                              # the UI/UX spec P11-P13: every edit of what is open is one of: the editor, a tweak, a new action, a redesign
                        t.intents, t.conf, t.er = ["EDIT_ROUTE"], 0.9, er
            if t.intents and t.intents[0] != "PARTICLES" and particles_intent(t.text, bool(sess.get("particles"))):
                t.intents, t.conf = ["PARTICLES"], 0.9                  # "generate more", "also use them for the Princess pack": about the particle set this chat has in focus
            if t.intents and t.intents[0] in ("EDIT_STICKERS", "NEW", "FEEDBACK", "AMBIGUOUS"):
                refine_it = self._wants_refine(t, has_gen)
                if refine_it:
                    t.intents, t.conf = ["REFINE"], 0.9
        names = {"NEW": "a new set", "NEW_MULTI": "several new sets", "EFFECTS": "particle effects", "PARTICLES": "particles", "EDIT_ROUTE": "an edit", "UNSUPPORTED": "something I cannot do yet", "REFINE": "a change to a batch", "ANOTHER": "another pass", "EDIT_STICKERS": "an edit", "UNDO": "an undo", "ANIMATE": "an animation", "EXPORT": "an export", "FEEDBACK": "feedback",
                 "REVIEW": "a decision", "ASK": "a question", "CHANGE_SETTINGS": "a setting", "SEARCH": "a search", "CONFIRM": "your go-ahead",
                 "CANCEL": "a change of mind", "RETRY": "a new try of a sheet", "NAMES": "a look at the names", "CREATOR": "the creator", "NAMES_DECIDE": "your answer about the names", "SMALLTALK": "a hello", "PROFILE": "something about you", "AMBIGUOUS": "something I need to ask about"}
        t.trace.task("reading your message")
        t.trace.step("understood: " + " + ".join(names.get(i, i.lower()) for i in t.intents) + (" · answering my question" if answered else ""))
        order = {"CONFIRM": "confirm", "CONFIRM_NEW": "confirm", "CANCEL": "cancel", "CHANGE_SETTINGS": "settings", "FEEDBACK": "feedback", "REVIEW": "review",
                  "EDIT_STICKERS": "edit", "UNDO": "undo", "ANIMATE": "animate", "EXPORT": "export", "ANOTHER": "another", "NEW": "new", "NEW_MULTI": "multi", "EFFECTS": "effects", "PARTICLES": "particles", "EDIT_ROUTE": "editroute", "UNSUPPORTED": "unsupported", "REFINE": "refine", "ASK": "ask", "SEARCH": "search",
                 "SMALLTALK": "smalltalk", "PROFILE": "profile", "AMBIGUOUS": "clarify", "RETRY": "retry", "NAMES": "names", "NAMES_DECIDE": "names_decide", "CREATOR": "creator"}
        t.queue = [order[i] for i in t.intents if i in order] or ["clarify"]
        return {}

    def _ctx(self, t: Turn) -> dict:
        sess = t.sess
        self.store.refresh(sess)
        focus = sess.get("focus") or {}
        gen = focus.get("generation") or (self.store.latest_pass(sess, with_generation=True) or {}).get("generation")
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
        latest = (self.store.latest_pass(sess, with_generation=True) or {}).get("generation")
        return {"generation": gen, "n": n, "stickers": stickers, "focus_stickers": focus.get("stickers") or [], "selected": t.selected,
                "parent": parent, "latest": latest, "known": known}

    def n_resolve(self, state: State) -> dict:
        t: Turn = state["turn"]
        needs = [q for q in t.queue if q in ("edit", "editroute", "feedback", "animate", "ask", "review", "another", "names")]
        if not needs:
            return {}
        for gid in self._named_batches(t.sess, t.text):                       # "make G012/S3 happier": a batch the Studio made becomes a pass of this chat
            if not self.store.subject_for_generation(t.sess, gid) and self.store.adopt(t.sess, gid):
                t.trace.note(f"{gid} was made outside this chat (the Studio): I can work on it now")
        ctx = self._ctx(t)
        r = resolve(t.text, ctx)
        gone = beyond(t.text, int(ctx["known"].get(r.generation or ctx["generation"], ctx["n"]) or 9), t.answer) if (r.generation or ctx["generation"]) else []
        if gone and not r.stickers and not r.needs_clarification:       # "number 12" in a batch of 9: say what the batch has, never ask again in the same words
            size = int(ctx["known"].get(r.generation or ctx["generation"], ctx["n"]) or 9)
            r.needs_clarification, r.options = True, []
            r.clarification = f"{self._nm(t.sess, r.generation or ctx['generation'])} has {size} stickers, so there is no number {', '.join(str(g) for g in gone)}. Which one do you mean, 1 to {size}?"
        elif gone:
            t.trace.note(f"there is no number {', '.join(str(g) for g in gone)}: that batch has {ctx['n']} stickers")
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
            t.trace.step(f"found {', '.join(x.split('/')[1] for x in r.stickers)} in {self._nm(t.sess, r.generation)}" + (f" · {r.how}" if r.how else ""))
        elif r.generation and needs and needs != ["another"]:
            t.trace.step(f"working in {self._nm(t.sess, r.generation)}")
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
        asked = request_text(t.text)                    # "hello from haitham, make me a camel in lamborgini" -> "make me a camel in lamborgini": the speaker's words go, every content word stays
        guess = re.sub(r"^(?:please\s+)?(?:can you\s+)?(?:make|create|generate|give|draw|design|build)\s+(?:me\s+)?(?:some\s+|a\s+|an\s+)?|\bstickers?\b|\bpack of\b|\bset of\b",
                       " ", asked, flags=re.I).strip(" .,!?") or asked
        t.trace.retitle(f"generating {guess}")
        sid, said_text, assumed = self._style_for(t, asked)
        prefs, notes = self._prefs(t, guess)
        notes = list(notes) + assumed
        prompt = said_text.strip() + (f". {prefs[0].upper() + prefs[1:]}" if prefs else "")
        eng = self.tools.engine_label(bool(st.get("ai", True)))
        t.trace.step(f"writing {int(st['grid'][0]) * int(st['grid'][-1])} sticker ideas" + (f" with {eng}" if eng else " from the built-in sets"))   # shown at once: the model can take a few seconds
        try:
            plan = self.tools.plan(prompt, st["grid"], sid, bool(st.get("ai", True)))
        except ToolError as e:
            t.reply = f"I couldn't turn that into a plan: {e}"
            t.trace.end("could not plan", ok=False)
            t.chips = [{"label": s, "text": s} for s in SUGGESTIONS[:3]]
            return {}
        scene = str(plan.get("scene") or "")
        names = [n + (f" {scene}" if scene and scene.split()[-1].lower() not in n.lower() else "")       # the card says what every cell is drawn with: "camel waving in Lamborghini"
                 for n in (s["key"].replace("_", " ") for s in plan["stickers"])]
        t.trace.step("expand prompt", {"title": f"{len(names)} stickers", "lines": names})
        if plan.get("expand_error"):                # the AI could not write the ideas (not reachable, bad answer): say so, the built-in sets were used instead
            t.trace.note("the AI could not write the ideas (" + str(plan["expand_error"])[:140] + "): I used the built-in sets")
        if prefs:
            t.trace.step("added your preferences", {"lines": [p.strip() for p in prefs.split(",") if p.strip()]})
        for n in notes:
            t.trace.note(n)
        tr = plan.get("transformation")
        if tr:                                    # "dog as banana": say that it is ONE new character, and which cells the template guarantees
            t.trace.note(f"a transformation: the whole character is a {tr['target']} with the {tr['subject']}'s face"
                         + (f"; {', '.join(tr['required'])} included" if tr.get("required") else "")
                         + (f"; left out as you asked: {', '.join(tr['forbidden'])}" if tr.get("forbidden") else ""))
        subject = (plan.get("described") if plan.get("scene") else None) or plan.get("subject") or guess         # the normalised request ("camel in Lamborghini"), never the bare character
        t.res.generation = None
        pm = self.tools.prepared_match(prompt) if self.tools.live() else None
        est = 0 if pm else (self.tools.estimate("image") if self.tools.live() else None)
        card = {"type": "plan", "subject": subject, "grid": st["grid"], "style": STYLE_NAMES.get(sid, sid),
                "count": len(names), "names": names, "estimate": est, "balance": self.tools.credits(), "prompt": prompt,
                "prepared": bool(pm),
                "free": not self.tools.live(), **({"transformation": {k: tr[k] for k in ("id", "subject", "target", "required")}} if tr else {})}
        spend = self.tools.live()
        cs = creator.settings_of(sess)
        if cs["on"]:
            return self._creator_plan(t, subject, prompt, names, est, card, cs)
        if spend and st.get("ask_before_spending", True):
            sess["pending"] = {"type": "create", "prompt": prompt, "subject": subject, "grid": st["grid"], "style_id": sid,
                               "ai": bool(st.get("ai", True)), "estimate": est, "plan": compact_plan(plan)}
            t.cards.append(card)
            t.reply = f"Here's the plan for **{subject}**: {len(names)} stickers, {STYLE_NAMES.get(st['style_id'], st['style_id'])}" + (" (I have this prepared: 0 credits)" if pm else "") + ". Shall I create it?"
            t.chips = ([{"label": "Create it", "action": "confirm"}] + ([{"label": "Make a new one (paid)", "action": "confirm_new"}] if pm else []) + [{"label": "Not yet", "action": "cancel"}])
            t.trace.end(f"plan ready · {_credits(est)}")
            return {}
        self._start_create(t, {"prompt": prompt, "subject": subject, "grid": st["grid"], "style_id": sid, "ai": bool(st.get("ai", True)), "plan": compact_plan(plan)}, card)
        return {}

    # -- the agentic creator: one go-ahead from the request to the pack on Telegram (agent/creator.py) --------------------------------------------------------
    def _creator_plan(self, t: Turn, subject: str, prompt: str, names: list, est, card: dict, cs: dict) -> dict:
        sess, st = t.sess, t.sess["settings"]
        if (sess.get("creator_run") or {}).get("status") in ("running", "waiting"):
            t.reply = "The creator is still working on your last pack. Wait for it, or press Stop on its card."
            t.trace.end("busy", ok=False)
            return {}
        v_est = self.tools.estimate("video") if cs["scope"] == "video" and self.tools.live() else None
        total = round((est or 0) + (v_est or 0), 2) or None
        spec = {"type": "creator", "prompt": prompt, "subject": subject, "grid": st["grid"], "style_id": st["style_id"], "ai": bool(st.get("ai", True)), "estimate": est,
                "video_estimate": v_est, "scope": cs["scope"], "bypass": cs["bypass"]}
        card.update(estimate=total, creator={"scope": cs["scope"], "bypass": cs["bypass"], "sheet": est, "video": v_est})
        ready, why = self.tools.telegram_ready()
        what = "the stickers as a static pack" if cs["scope"] == "images" else "the stickers animated"
        how = "approving everything for you and stopping at the first rejection" if cs["bypass"] else "stopping at each approval for one click from you"
        t.reply = (f"Creator plan for **{subject}**: {len(names)} stickers, then {what}, then to Telegram, {how}. "
                   + ("" if ready else "Telegram is not connected yet, so I will stop before sending. ") + "Shall I run it?")
        t.trace.step("creator: " + " > ".join(label for _, label in creator.STEPS[cs["scope"]]))
        if self.tools.live() and st.get("ask_before_spending", True):
            sess["pending"] = spec
            t.cards.append(card)
            t.chips = [{"label": "Create and send to Telegram", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            t.trace.end(f"plan ready · {_credits(total)}")
            return {}
        self._start_creator(t, spec)
        return {}

    def _start_creator(self, t: Turn, p: dict) -> None:
        sess = t.sess
        self._start_create(t, p)
        card = next((c for c in reversed(t.cards) if c.get("type") == "generation"), None)
        if not card:
            return
        run = creator.new_run(prompt=p["prompt"], subject=p["subject"], grid=p["grid"], style_id=p["style_id"], scope=p.get("scope", "images"), bypass=p.get("bypass", False),
                              estimate=p.get("estimate"), video_estimate=p.get("video_estimate"))
        run["job"], run["generation"] = card.get("job"), card.get("generation")
        creator._log(run, "started: " + ("the sheet is being drawn" if run["job"] else "the sheet is ready"))
        sess["creator_run"] = run
        t.cards.append({"type": "creator", "run_id": run["id"]})
        t.reply = f"Running the creator for **{p['subject']}**. I will stop and tell you if anything is rejected."
        t.chips = []

    def n_creator(self, state: State) -> dict:
        """The person's button on the creator card (continue / skip / force / stop), or "continue" typed while it waits."""
        t: Turn = state["turn"]
        run = t.sess.get("creator_run")
        act = str((t.action or {}).get("type") or "creator_go")
        if not run:
            t.reply = "There is no creator run to continue."
            return {}
        creator.resume(run, act, (t.action or {}).get("indexes"))
        t.trace.task("continuing the creator" if act != "creator_stop" else "stopping the creator")
        t.trace.step({"creator_go": "approved", "creator_skip": "continuing without those stickers", "creator_force": "continuing with them anyway",
                      "creator_allow": "you allowed a block Python flagged: cutting it again", "creator_unallow": "the permission is taken back",
                      "creator_force_video": "animation price accepted", "creator_stop": "stopped"}.get(act, act))
        t.trace.end("done")
        t.reply = "Stopped. Nothing more will be made or spent; what exists stays in the Studio." if act == "creator_stop" else "Continuing."
        t.cards.append({"type": "creator", "run_id": run["id"]})
        return {}

    def creator_tick(self, sid: str) -> str:
        """Advance the session's creator run as far as it can go right now and say, as a message of its own, what happened when it stops, waits or finishes. Takes the session's lock like any
        turn (a person's message in the middle gets its 409 for a moment, never a clash). Returns the run's status ('none' without a run, 'busy' when a turn holds the lock)."""
        lock = self.cache.lock(f"session:{sid}")
        try:
            lock.__enter__()
        except cachemod.Busy:
            return "busy"
        try:
            sess = self.store.load(sid)
            run = sess.get("creator_run")
            if not run:
                return "none"
            if run["status"] == "running":
                creator.advance(self.tools, run, sess["settings"].get("allow_vlm") is True, self.tools.telegram_ready,
                                checkpoint=lambda current: self.store.save(sess))
            mark = f"{run['status']}:{run['step']}"
            if run["status"] in ("stopped", "waiting", "done") and run.get("said") != mark:
                run["said"] = mark
                self._creator_say(sess, run)
            self.store.save(sess)
            return run["status"]
        finally:
            lock.__exit__(None, None, None)

    def _creator_say(self, sess: dict, run: dict) -> None:
        name = run["subject"]
        if run["status"] == "done":
            links = [s["link"] for s in (run.get("telegram") or {}).get("sets", [])]
            text, chips = f"Done: **{name}** is on Telegram. " + " ".join(links), []
        elif run["status"] == "waiting":
            text, chips = f"**{name}**: {run['waiting']['why']}.", run["waiting"]["chips"]
        else:
            text, chips = f"**{name}**: stopped, {run['stop']['why']}", run["stop"]["chips"]
        cards = [{"type": "creator", "run_id": run["id"]}]
        # The picture travels with the message (CLAUDE.md rule 10: a rejection is never a bare word). A run that stopped on a block shows
        # the batch's own carousel, so the rejected stickers are visible where the buttons that decide about them are.
        if run["status"] == "stopped" and run.get("generation") and run["stop"].get("kind") != "error":
            cards.append({"type": "generation", "generation": run["generation"], "subject": name})
        self.store.add_message(sess, "assistant", text, chips=chips, cards=cards)

    def _start_create(self, t: Turn, p: dict, plan_card: dict | None = None, parent: str | None = None, regen_of: str | None = None,
                      refs: list | None = None, note: str = "") -> bool:
        """Start a batch from an approved plan (`p["plan"]` is sent as it is: the card and the batch are the same). True when it started; False leaves the reply explaining why."""
        try:
            force_live = (t.action or {}).get("type") == "confirm_new"      # "Make a new one": a fresh provider sheet at the normal price, never the prepared set
            r = self.tools.create(p["prompt"], p["grid"], p["style_id"], p.get("ai", True), parent=parent, regen_of=regen_of, refs=refs, base_plan=p.get("plan"), ref_clause=p.get("ref_clause"), **_edge_kw(p), force_live=force_live)
        except ToolError as e:
            t.reply = f"I couldn't start that: {e}"
            t.trace.end("not started", ok=False)
            return False
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
        return True

    def n_confirm(self, state: State) -> dict:
        t: Turn = state["turn"]
        p = t.sess.get("pending")
        if not p:
            t.reply = "There is nothing waiting for a go-ahead. What would you like to make?"
            t.chips = [{"label": s, "text": s} for s in SUGGESTIONS[:3]]
            return {}
        t.trace.step(f"confirmed: {p['type']}")
        if p["type"] == "multi":
            t.trace.retitle(f"generating {p.get('label') or 'several packs'}")
            done, failed = self._start_items(t, p["items"])
            if failed:                                       # what could not start stays waiting; what started is not asked again
                t.sess["pending"] = {**p, "items": [i for i, _ in failed], "estimate": None}
                t.chips = [{"label": "Try the rest", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            else:
                t.sess["pending"] = None
            return {}
        if p["type"] == "create":
            t.trace.retitle(f"generating {p['subject']}")
            if self._start_create(t, p, parent=p.get("parent"), regen_of=p.get("regen_of"), refs=p.get("refs"), note=p.get("note", "")):
                t.sess["pending"] = None
            else:                                           # a refused start must not cost the plan: the person presses the same button again
                t.reply += " I kept your plan: press Create it to try again, or Not yet to drop it."
                t.chips = [{"label": "Create it", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            return {}
        t.sess["pending"] = None
        if p["type"] == "review":
            return self._do_review(t, p["generation"], p["decision"], p["indexes"])
        elif p["type"] == "creator":
            t.trace.retitle(f"creating {p['subject']} for Telegram")
            self._start_creator(t, p)
        elif p["type"] == "animate":
            t.trace.retitle(f"animating {self._nm(t.sess, p['generation'])}")
            try:
                r = self.tools.animate(p["generation"], p.get("loop", False))
                t.generation = p["generation"]
                t.cards.append({"type": "generation", "generation": p["generation"], "job": r["job"], "subject": p.get("subject", ""), "animating": True})
                t.reply = f"Animating **{self._nm(t.sess, p['generation'])}**" + (f" ({_credits(r.get('estimate'))})" if r.get("estimate") else "") + ". I'll show each one as it's ready." \
                    + (" Once they're moving, say \"export\" and I'll pack and send them." if p.get("then") == "pack_send" else "")
                t.trace.end("animation started")
            except ToolError as e:
                t.reply = f"I couldn't start the animation: {e}"
                t.trace.end("not started", ok=False)
        elif p["type"] == "pack_send":
            t.trace.retitle(f"sending {self._nm(t.sess, p['generation'])} to Telegram")
            try:
                pack = self.tools.pack_add(p["generation"], p.get("subject") or self._nm(t.sess, p["generation"]))
                rep = self.tools.telegram_send(pack["pack_id"])
            except ToolError as e:
                t.sess["pending"] = p
                t.reply = f"I couldn't send it: {e} Nothing was packed."
                t.chips = [{"label": "Pack and send", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
                t.trace.end("not sent", ok=False)
                return {}
            links = " ".join(s["link"] for s in rep.get("sets", []))
            t.reply = f"Done: **{self._nm(t.sess, p['generation'])}** is on Telegram. {links}".strip()
            t.trace.end("sent")
        elif p["type"] == "names":                          # the same consent, asked because the person wanted names looked at
            if self._ready_now(p["generation"]) == []:      # nothing cut yet: no vision call, one calm sentence, the pending goes
                t.reply = f"{self._nm(t.sess, p['generation'])} has no finished stickers yet — I'll look at them once they're cut."
                t.trace.end("nothing to look at yet")
                return {}
            t.sess["settings"]["allow_vlm"] = True
            t.trace.retitle(f"looking at {self._nm(t.sess, p['generation'])}")
            self._run_names(t, p["generation"])
        elif p["type"] == "describe":                       # "Allow AI vision of generated media?" answered yes: asked once, remembered in the session
            if self._ready_now(p["generation"]) == []:
                t.reply = f"{self._nm(t.sess, p['generation'])} has no finished stickers yet — I'll look at them once they're cut."
                t.trace.end("nothing to look at yet")
                return {}
            t.sess["settings"]["allow_vlm"] = True
            t.trace.retitle(f"looking at {self._nm(t.sess, p['generation'])}")
            self._run_describe(t, p["generation"], p.get("only") or [])
        elif p["type"] == "particles":
            self._do_particles(t, p)
        elif p["type"] == "batch":
            t.trace.retitle("regenerating " + ", ".join(i["label"] for i in p["items"]))
            n = 0
            for it in p["items"]:
                self._start_create(t, {**it, "grid": "1x1", "style_id": it.get("style_id") or p["style_id"], "ai": p.get("ai", True)}, parent=it["parent"],
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

    # ---- feedback about a whole subject, several subjects at once, and what the chat learned about the person ----------------------------------------------
    def _profile(self) -> Profile:
        return Profile(self.store.out, getattr(self.store, "user", "local"))

    def _subject_names(self, sess: dict) -> list[str]:
        return [s["name"] for s in sess["subjects"] if any(p.get("generation") for p in s["passes"])]

    def _has_sticker_ref(self, t: Turn) -> bool:
        from .resolver import _numbers
        if t.selected or _numbers(t.text, 9) or re.search(r"\bg\d+\s*/?\s*s\d", t.text.lower()):
            return True
        return bool((t.sess.get("focus") or {}).get("stickers") and re.search(r"\b(it|that|this)\b", t.text.lower()))

    def _wants_refine(self, t: Turn, has_gen: bool) -> bool:
        """A change to a whole subject, not to numbered stickers: it names a subject of this chat and says what to change ("the cherries were so realistic, make them cartoonish"), or it is an
        edit with no sticker pointed at ("make him bigger", "same but red"). "make me a banana in clay style" is a new request and stays one."""
        if not has_gen or t.selected or re.search(r"\b(?:make|create|generate|give|draw|design)\s+me\b|\b(?:a|an|some|\d+)\s+(?:\w+\s+)?(?:stickers?|packs?|sets?)\b", t.text.lower()):
            return False
        segs = refine.mentions(t.text, self._subject_names(t.sess))
        if segs and any(refine.extract(c)["matched"] for _, c in segs):
            return True
        return t.intents[0] == "EDIT_STICKERS" and not self._has_sticker_ref(t) and refine.extract(t.text)["matched"]

    def _style_for(self, t: Turn, text: str) -> tuple[str, str, list]:
        """(style id, the text without style words, what was assumed): the style named in the sentence wins; else what this person has asked for twice or more (said on the card, one click to
        undo); else the chat's setting."""
        from ..generation import styles as _styles
        st = t.sess["settings"]
        sid, rest = refine.style_of_request(text)
        if sid:
            return sid, rest, []
        if st.get("style_id") != _styles.DEFAULT:
            return st["style_id"], text, []
        d = self._profile().defaults().get("style_id")
        if d:                                                          # a remembered taste is offered, never applied unasked (Haitham, 2026-10-04: "paper cut" appeared on a plan nobody asked for)
            return st["style_id"], text, [f"you asked for {refine.LABEL.get(d[0], d[0])} {d[1]} times before: say \"{refine.LABEL.get(d[0], d[0]).lower()}\" to use it here"]
        return st["style_id"], text, []

    def _items_card(self, title: str, items: list, st: dict, est_each, extra: dict | None = None) -> dict:
        total = round(est_each * len(items), 2) if est_each else None
        return {"type": "multi", "title": title, "grid": st["grid"], "estimate": total, "balance": self.tools.credits(), "free": not self.tools.live(),
                "items": [{"subject": i["subject"], "count": len(i["plan"].get("stickers") or []), "names": [s["key"].replace("_", " ") for s in (i["plan"].get("stickers") or [])][:9],
                           "style": STYLE_NAMES.get(i["style_id"], i["style_id"]), "changes": i.get("changes") or []} for i in items], **(extra or {})}

    def _offer_items(self, t: Turn, label: str, items: list, est_each, card: dict, reply: str) -> dict:
        """The plan card of several batches: ONE total price and one go-ahead (or, with 'Ask before spending' off or without a provider, they start at once)."""
        sess, st = t.sess, t.sess["settings"]
        t.cards.append(card)
        if self.tools.live() and st.get("ask_before_spending", True):
            sess["pending"] = {"type": "multi", "items": items, "estimate": card["estimate"], "subject": label, "label": label}
            t.reply = reply + " Shall I create them?"
            t.chips = [{"label": "Create them", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            t.trace.end(f"plan ready · {_credits(card['estimate'])}")
            return {}
        self._start_items(t, items)
        return {}

    def _start_items(self, t: Turn, items: list) -> tuple[list, list]:
        """Start every batch of the plan together (the provider jobs run side by side, `jobs.paid_parallel`). Returns (started, [(item, why)] that could not start)."""
        done, failed = [], []
        for it in items:
            try:
                r = self.tools.create(it["prompt"], it["grid"], it["style_id"], it.get("ai", True), parent=it.get("parent"), base_plan=it.get("plan"), refs=it.get("refs"), ref_clause=it.get("ref_clause"), **_edge_kw(it))
            except ToolError as e:
                failed.append((it, str(e)))
                continue
            self.store.add_pass(t.sess, it["subject"], generation=r.get("generation"), job=r.get("job"), prompt=it["prompt"], grid=it["grid"], style_id=it["style_id"],
                                parent=it.get("parent"), note=it.get("note", ""))
            if r.get("generation"):
                t.sess["focus"] = {"generation": r["generation"], "stickers": []}
            t.spent += r.get("estimate") or 0
            t.cards.append({"type": "generation", "generation": r.get("generation"), "job": r.get("job"), "subject": it["subject"], "parent": it.get("parent"), "note": it.get("note", "")})
            if it.get("delta"):                                          # what the person asked for, counted as a taste only now that it is really made
                try:
                    self._profile().vote_delta(it["delta"], it.get("note", ""))
                except Exception:
                    pass
            done.append(it)
        names = ", ".join(f"**{i['subject']}**" for i in done)
        if done:
            t.reply = (t.reply + " " if t.reply else "") + f"Creating {names}" + (f" ({_credits(t.spent)})" if t.spent else "") + ". Each one appears below as it is ready."
        if failed:
            t.reply = (t.reply + " " if t.reply else "") + "I could not start " + ", ".join(f"**{i['subject']}**" for i, _ in failed) + f": {failed[0][1]}."
        t.trace.end(f"started {len(done)}" + (f", {len(failed)} refused" if failed else ""), ok=bool(done))
        return done, failed

    def n_multi(self, state: State) -> dict:
        """"Create three sticker packs of fruits": the chat picks three different subjects of the category, plans each, and asks once for the total."""
        t: Turn = state["turn"]
        sess, st = t.sess, t.sess["settings"]
        got = subjects.parse_multi(t.text)
        if not got:
            t.reply = "How many packs, and of what? For example \"three sticker packs of fruits\"."
            return {}
        n, cat = got
        t.trace.retitle(f"planning {n} packs of {cat}")
        avoid = [s["name"] for s in sess["subjects"]]
        names, how = subjects.pick(cat, n, avoid, ask=self.brain.pick_subjects if self.brain.available else None, seed=int(time.time() * 1000) % 1000000007)
        if not names:
            t.reply = f"I have no list for \"{cat}\" yet. Tell me the {n} subjects, for example \"strawberry, cherries, banana\"."
            t.trace.end("asked for the subjects")
            return {}
        t.trace.step(f"chose {len(names)} {cat}" + (" with the language model" if how.startswith("model") else " from my built-in list"), {"title": ", ".join(names), "lines": names})
        if len(names) < n:
            t.trace.note(f"I could only find {len(names)} different ones")
        sid, _, assumed = self._style_for(t, t.text)
        for a in assumed:
            t.trace.note(a)
        items = []
        for name in names:
            try:
                plan = self.tools.plan(name, st["grid"], sid, bool(st.get("ai", True)))
            except ToolError as e:
                t.trace.note(f"I could not plan {name}: {e}")
                continue
            items.append({"prompt": name, "subject": plan.get("subject") or name, "grid": st["grid"], "style_id": sid, "ai": bool(st.get("ai", True)), "plan": compact_plan(plan),
                          "note": f"one of {len(names)} packs of {cat}"})
        if not items:
            t.reply = "I couldn't plan any of them."
            t.trace.end("could not plan", ok=False)
            return {}
        est = self.tools.estimate("image") if self.tools.live() else None
        title = f"{len(items)} packs of {cat}"
        card = self._items_card(title, items, st, est, {"assumed": assumed})
        reply = f"Here's the plan for {title}: " + ", ".join(f"**{i['subject']}**" for i in items) + f", {len(items) * (len(items[0]['plan'].get('stickers') or []))} stickers in all, {STYLE_NAMES.get(sid, sid)}."
        return self._offer_items(t, title, items, est, card, reply)

    def n_effects(self, state: State) -> dict:
        """Legacy Kling intent enters the same scoped wizard; spending stays behind its quote and click."""
        t = state['turn']
        packs = [p for p in self.tools.packs() if p['count']]
        hit = self._named(t.text, packs)
        pick = hit[0] if len(hit)==1 else packs[0] if len(packs)==1 else None
        if pick:
            t.cards.append({'type':'particles_scope', 'pack_id':pick['id'], 'pack':pick['name'], 'kind':'video'})
            t.reply = f"Open Video from scratch for **{pick['name']}**. It starts and ends empty; the price appears before your paid click."
        else:
            return self._particles_make(t)
        return {}

    # -- particle sets (docs/agent-and-chat.md, particle sets in the chat) -------------------------------------------------------------------------------------------------
    _PSTOP = {"pack", "packs", "set", "sets", "stickers", "sticker", "the", "a", "an", "my", "particle", "particles", "them", "it", "also", "more", "generate", "make", "draw", "delete", "remove",
              "restore", "use", "for", "on", "in", "to", "some", "few", "create", "add", "bring", "back", "get", "me", "of", "with", "and", "please", "i", "want", "need"}

    def _words(self, s: str) -> set:
        return {refine.stem(w) for w in re.findall(r"[a-z\u0600-\u06ff]+", s.lower()) if w not in self._PSTOP}

    def _named(self, text: str, rows: list) -> list:
        """The rows (packs or sets, by their name) that the message names: all the words of a name, else any word of it."""
        said = self._words(text)
        full = [r for r in rows if self._words(r["name"]) and self._words(r["name"]) <= said]
        return full or [r for r in rows if self._words(r["name"]) & said]

    def n_particles(self, state: State) -> dict:
        """"make particles for my Barbie pack" / "generate more" / "delete the bat particles" / "restore ..." / "also use them for the Princess pack". Reads and free list edits happen at once; a sheet
        (credits) is a plan with its price that waits for the go-ahead, like every other paid thing in the chat."""
        t: Turn = state["turn"]
        t.trace.retitle("particles")
        kind = particles_intent(t.text, bool(t.sess.get("particles"))) or "make"
        try:
            return getattr(self, "_particles_" + kind)(t)
        except ToolError as e:
            t.reply = f"I could not do that: {e}"
            t.trace.end("could not", ok=False)
            return {}

    def _particle_scope(self, t):
        focus = t.sess.get('focus') or {}
        gen = t.res.generation or focus.get('generation')
        explicit = re.search(r'\bG(\d+)\b', t.text, re.I)
        if explicit:
            gen = f"G{int(explicit[1]):03d}"
        ids = list(t.selected or t.res.stickers or focus.get('stickers') or [])
        number = re.search(r'\b(?:sticker|S)\s*(\d+)\b', t.text, re.I)
        if number and gen:
            ids = [f"{gen}/S{int(number[1])}"]
        packs = self._named(t.text, self.tools.packs())
        pid = packs[0]['id'] if len(packs)==1 else None
        return self.tools.particle_owners(pack_id=pid, generation=None if pid else gen, sticker_ids=ids or None), gen, ids

    def _focus_set(self, t: Turn, sets: list) -> tuple[dict | None, str]:
        """Explicit set name overrides; otherwise newest owned set, focused set, sole set, then chips."""
        hit = self._named(t.text, sets)
        if len(hit)==1:
            return hit[0], ''
        if len(hit)>1:
            return None, 'several'
        owners, gen, ids = self._particle_scope(t)
        wanted = {o['sticker_id'] for o in owners}
        mine = [s for s in sets if any(o['sticker_id'] in wanted for o in s.get('owner', []))]
        if mine:
            ordered = [pid for o in owners for pid in o.get('particles', [])]
            newest = next((s for pid in reversed(ordered) for s in mine if s['id']==pid), None)
            return newest or max(mine, key=lambda s:(s.get('created') or 0, s['id'])), ''
        fid = (t.sess.get('particles') or {}).get('set')
        pick = next((s for s in sets if s['id']==fid), None)
        words = self._words(t.text) - {'burst', 'render', 'save', 'next'}
        if pick or (len(sets)==1 and not words):
            return pick or sets[0], ''
        return None, '' if ids or owners else ' '.join(sorted(words))

    def _no_set(self, t: Turn, sets: list, why: str, verb: str) -> dict:
        if why == "several":
            t.reply = "Several particle sets match. Which one? " + ", ".join(f"**{s['name']}**" for s in self._named(t.text, sets)[:4])
        elif why:
            t.reply = f"I could not find a particle set called \"{why}\" to {verb}." + (" You have " + ", ".join(f"**{s['name']}**" for s in sets[:4]) + "." if sets else " There are none yet: say \"make particles for my <pack> pack\".")
        else:
            t.reply = f"Which particle set should I {verb}? " + (", ".join(f"**{s['name']}**" for s in sets[:4]) if sets else "There are none yet.")
        t.chips = [{"label":s["name"], "text":f"{verb} {s['name']} particles"} for s in sets[:4]]
        t.trace.end("asked which set")
        return {}

    _ALONE = re.compile(r"\b(?:on (?:their|its) own|alone|stand-?alone|no pack|without (?:a |any )?(?:pack|sticker)s?)\b", re.I)

    def _particles_alone(self, t: Turn, why: str = "") -> dict:
        """Particles on their own (Haitham, 2026-10-05): no sticker owns them; the set is made from the request when the price is confirmed."""
        from ..flow import particle_sets as ps
        els = ps.request_elements(self._ALONE.sub(" ", t.text), 4)
        if not els:
            t.reply = "Which particles? For example: particles for lipsticks and ribbons."
            return {}
        if not self.tools.live():
            t.reply = "Drawing particles needs the Higgsfield CLI, and it is not available here. Nothing was started."
            t.trace.end("no provider", ok=False)
            return {}
        spec = {"type": "particles", "op": "alone", "request": t.text, "pack": None, "pack_name": None, "set": None, "set_name": None, "grid": "2x2", "elements": els,
                "estimate": self.tools.estimate("image")}
        return self._offer_particles(t, spec, (why or "") + f"I'll draw {len(els)} particles on their own: {', '.join(els)}. No sticker owns them; you can preview, render and download them, or make a pack of them")

    def _particles_make(self, t: Turn) -> dict:
        packs = [p for p in self.tools.packs() if p["count"]]
        owners, gen, ids = self._particle_scope(t)
        if self._ALONE.search(t.text):
            return self._particles_alone(t)
        from ..flow import particle_sets as _ps
        hit0 = self._named(t.text, packs) if packs else []
        named = [] if hit0 else _ps.request_elements(t.text, 4)
        if named and not owners and not gen:                 # "create particles for lipsticks and ribbons": which pack, or on their own?
            if not packs:
                return self._particles_alone(t, "You have no packs yet, so ")
            last = packs[-1]
            t.reply = f"Sure: {', '.join(named)}. For which pack, or on their own?"
            t.chips = ([{"label": p["name"], "text": f"make particles for my {p['name']} pack"} for p in packs[-3:][::-1] if p is not last]
                       + [{"label": f"The last pack, {last['name']}", "text": f"make particles for my {last['name']} pack"},
                          {"label": "On their own", "text": f"create particles on their own for {' and '.join(named)}"}])
            t.trace.end("asked which pack")
            return {}
        if gen and not owners:
            t.cards.append({'type':'particles_approve', 'generation':gen})
            t.reply = 'Approve this batch as a pack first, so the particles have a sticker to live in.'
            return {}
        if not packs:
            t.reply = 'Choose a batch to approve as a pack, then create particles for its stickers.'
            return {}
        hit = self._named(t.text, packs)
        pick = hit[0] if len(hit) == 1 else packs[0] if len(packs) == 1 else None
        if not hit and owners:
            pick = next((p for p in packs if p['id'] == owners[0]['pack_id']), None)
        if not pick:
            t.reply = ("Which pack? " if not hit else "Several packs match. Which one? ") + "Say its name, for example \"make particles for my " + (hit or packs)[0]["name"] + " pack\"."
            t.chips = [{"label": p["name"], "text": f"make particles for my {p['name']} pack"} for p in (hit or packs)[:4]]
            t.trace.end("asked which pack")
            return {}
        if not self.tools.live():
            t.reply = "Drawing particles needs the Higgsfield CLI, and it is not available here. Nothing was started."
            t.trace.end("no provider", ok=False)
            return {}
        owners = owners or self.tools.particle_owners(pack_id=pick["id"])
        current, _ = self._focus_set(t, self.tools.particle_sets())
        if current and owners and "fresh" not in t.text.lower():
            return self._particles_more(t)
        els = self.tools.particle_options(pick["id"], 4)
        spec = {"type": "particles", "op": "make", "pack": pick["id"], "pack_name": pick["name"], "set": None, "grid": "2x2", "elements": els, "estimate": self.tools.estimate("image"), "owners": owners, "fresh": "fresh" in t.text.lower()}
        return self._offer_particles(t, spec, f"I'll draw {len(els)} particles for the **{pick['name']}** pack: {', '.join(els)}. When the sheet is back they join a set owned by its selected stickers")

    def _particles_more(self, t: Turn) -> dict:
        sets = self.tools.particle_sets()
        s, why = self._focus_set(t, sets)
        if not s:
            return self._no_set(t, sets, why, "add particles to")
        if not self.tools.live():
            t.reply = "Drawing particles needs the Higgsfield CLI, and it is not available here. Nothing was started."
            return {}
        if (s.get('source') or {}).get('kind') in ('video', 'stickers'):
            owners = s.get('owner') or []
            t.cards.append({'type':'particles_scope', 'pack_id':owners[0]['pack_id'] if owners else None, 'pack':s['name'], 'kind':'video' if s['source']['kind']=='video' else 'pack', 'set':s['id']})
            t.reply = f"Open Generate more for **{s['name']}**. New cells join the same set; any AI price appears before the paid click."
            return {}
        els = (s.get("elements") or [])[:4]
        if not els:
            t.reply = f"**{s['name']}** has no particle names to draw yet. Tell me which, for example \"generate more hearts and stars for {s['name']}\"."
            return {}
        spec = {"type": "particles", "op": "more", "set": s["id"], "set_name": s["name"], "pack": None, "grid": "2x2", "elements": els, "estimate": self.tools.estimate("image")}
        return self._offer_particles(t, spec, f"I'll draw {len(els)} more particles for **{s['name']}** ({', '.join(els)}). The cells it has stay as they are; the new ones are added")

    def _offer_particles(self, t: Turn, spec: dict, what: str) -> dict:
        card = {"type": "particles_plan", "op": spec["op"], "pack": spec.get("pack_name"), "pack_id": spec.get("pack"), "set": spec.get("set"), "name": spec.get("set_name"),
                "grid": spec["grid"], "elements": spec["elements"], "estimate": spec["estimate"]}
        if spec.get('estimate') is None:
            t.reply = 'The price is unavailable. Try again to get a price before starting.'
            return {}
        t.sess["pending"] = spec
        if self.tools.live() and t.sess["settings"].get("ask_before_spending", True):
            t.cards.append(card)
            t.reply = f"{what} ({_credits(spec['estimate'])}). Go ahead?"
            t.chips = [{"label": "Draw them", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            t.trace.end("ready")
        else:
            self.n_confirm({"turn": _with_pending(t, spec)})
        return {}

    def _do_particles(self, t: Turn, p: dict) -> None:
        if p["op"] == "alone":
            t.trace.retitle("drawing particles")
            try:
                r = self.tools.particles_alone(p["request"], p["grid"])
            except ToolError as e:
                t.sess["pending"] = p
                t.reply = f"I couldn't start the sheet: {e}. I kept the plan: press Draw them to try again, or Not yet to drop it."
                t.chips = [{"label": "Draw them", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
                t.trace.end("not started", ok=False)
                return
            t.sess["particles"] = {"set": r["set"], "pack": None}
            t.cards.append({"type": "particles", "set": r["set"], "name": r.get("name") or r["set"], "pack_id": None, "job": r["job"], "estimate": r.get("estimate"), "drawing": True})
            t.reply = f"Drawing {len(p['elements'])} particles on their own" + (f" ({_credits(r.get('estimate'))})" if r.get("estimate") else "") + ". When the sheet is cut they arrive in the set; open it to preview, render and download them, or make a pack of them."
            t.trace.end("sheet started")
            return
        if p["op"] == "delete":
            try:
                self.tools.particles_delete(p["set"], True)
            except ToolError as e:
                t.reply = f"I couldn't delete it: {e}"
                return
            t.reply = f"**{p['set_name']}** is in the trash; nothing is destroyed. Say \"restore the {p['set_name']}\" or press Restore under Library > Particles > Deleted."
            return
        t.trace.retitle("drawing particles")
        try:
            r = self.tools.particles_start(p.get("set"), p.get("pack"), p["grid"], p["elements"], owners=p.get("owners"), fresh=p.get("fresh", False))
        except ToolError as e:
            t.sess["pending"] = p                                    # a refused start must not cost the plan
            t.reply = f"I couldn't start the sheet: {e}. I kept the plan: press Draw them to try again, or Not yet to drop it."
            t.chips = [{"label": "Draw them", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            t.trace.end("not started", ok=False)
            return
        t.sess["particles"] = {"set": r["set"], "pack": p.get("pack")}
        t.cards.append({"type": "particles", "set": r["set"], "name": p.get("set_name") or f"{p.get('pack_name')} particles", "pack_id": p.get("pack"), "job": r["job"], "estimate": r.get("estimate"), "drawing": True})
        t.reply = f"Drawing {len(p['elements'])} particles" + (f" ({_credits(r.get('estimate'))})" if r.get("estimate") else "") + ". When the sheet is cut they join the set by themselves; open the pack's particle studio to move them."
        t.trace.end("sheet started")

    def _particles_render(self, t):
        sets = self.tools.particle_sets()
        s, why = self._focus_set(t, sets)
        if not s:
            return self._no_set(t, sets, why, 'render')
        owners, _, _ = self._particle_scope(t)
        pid = (owners[0] if owners else (s.get('owner') or [{}])[0]).get('pack_id')
        if not pid:
            t.reply = 'Link these particles to a sticker first.'
            return {}
        r = self.tools.particles_burst(s['id'], pid)
        t.sess['particles'] = {'set':s['id'], 'pack':pid}
        t.cards.append({'type':'particles', 'set':s['id'], 'name':s['name'], 'pack_id':pid})
        t.reply = f"Rendered a burst from **{s['name']}**. Open it to review and add it to the pack."
        return {}

    def _particles_add(self, t):
        sets = self.tools.particle_sets()
        s, why = self._focus_set(t, sets)
        if not s:
            return self._no_set(t, sets, why, 'add')
        owners, _, _ = self._particle_scope(t)
        pid = (owners[0] if owners else (s.get('owner') or [{}])[0]).get('pack_id')
        if not pid:
            t.reply = 'Link these particles to a sticker first.'
            return {}
        self.tools.particles_add(s['id'], pid)
        t.reply = f"**{s['name']}**: in the pack ✓."
        return {}

    def _particles_delete(self, t: Turn) -> dict:
        sets = self.tools.particle_sets()
        s, why = self._focus_set(t, sets)
        if not s or (not self._named(t.text, sets) and why == ""):
            return self._no_set(t, sets, why, "delete")
        used = [u["name"] for u in s.get("used_in") or []]
        if used:                                                     # in use: say which packs and wait (the API refuses without confirm, too)
            t.sess["pending"] = {"type": "particles", "op": "delete", "set": s["id"], "set_name": s["name"]}
            t.reply = f"**{s['name']}** is used by {', '.join(used)}. Deleting it takes it off those packs (it goes to the trash and can be restored). Delete it?"
            t.chips = [{"label": "Delete it", "action": "confirm"}, {"label": "Keep it", "action": "cancel"}]
            return {}
        self.tools.particles_delete(s["id"], False)
        t.reply = f"**{s['name']}** is in the trash; nothing is destroyed. Say \"restore the {s['name']}\" or press Restore under Library > Particles > Deleted."
        return {}

    def _particles_restore(self, t: Turn) -> dict:
        gone = self.tools.particle_deleted()
        hit = self._named(t.text, gone) or (gone if len(gone) == 1 else [])
        if len(hit) != 1:
            t.reply = ("Which deleted set? " + ", ".join(f"**{s['name']}**" for s in (hit or gone)[:4])) if gone else "Nothing is in the trash."
            return {}
        self.tools.particles_restore(hit[0]["id"])
        t.sess["particles"] = {"set": hit[0]["id"], "pack": None}
        t.reply = f"**{hit[0]['name']}** is back, with its cells and sticker links."
        return {}

    def _particles_assign(self, t: Turn) -> dict:
        sets = self.tools.particle_sets()
        named = self._named(t.text, sets)
        fid = (t.sess.get('particles') or {}).get('set')
        s = named[0] if len(named)==1 else next((x for x in sets if x['id']==fid), None)
        if not s:
            return self._no_set(t, sets, '', 'reuse')
        owners, _, _ = self._particle_scope(t)
        if not owners:
            t.reply = 'Choose the sticker to link these particles to.'
            return {}
        self.tools.particles_link(s['id'], [o['sticker_id'] for o in owners])
        names = [p['name'] for p in self.tools.packs() if p['id'] in {o['pack_id'] for o in owners}]
        t.reply = f"**{s['name']}** is linked to those stickers ({', '.join(names)}). Nothing was spent; it is the same set."
        return {}

    def n_refine(self, state: State) -> dict:
        """"The cherries were so realistic, make them more cartoonish; the banana was so small, make it bigger": each subject's stored plan gets its change written in, and a new sheet is made as a
        child of the old batch (the old one stays). One card, one total price, one go-ahead."""
        t: Turn = state["turn"]
        sess, st = t.sess, t.sess["settings"]
        names = self._subject_names(sess)
        segs = refine.mentions(t.text, names)
        if not segs:
            subj, p = self._focus_pass(t)
            segs = [(subj["name"], t.text)] if subj and p else []
        if not segs:
            t.reply = "Which pack should I change? Name it, for example \"make the cherries more cartoonish\"."
            return {}
        t.trace.retitle("changing " + ", ".join(n for n, _ in segs))
        items, skipped = [], []
        for name, clause in segs:
            delta = refine.extract(clause)
            if not delta["matched"] and self.brain.available:
                m = self.brain.refine_delta(clause, name) or {}
                from ..generation import styles as _styles
                sid = m.get("style_id") if m.get("style_id") in {p["id"] for p in _styles.PRESETS} else None
                size = m.get("size") if m.get("size") in ("larger", "smaller") else None
                colour = re.sub(r"[^a-z ]", "", str(m.get("colour") or "").lower())[:20] or None
                delta.update(style_id=sid, size=size, colour=colour, matched=bool(sid or size or colour))
            subj = next((s for s in sess["subjects"] if s["name"] == name), None)
            p = next((q for q in reversed(subj["passes"]) if q.get("generation")), None) if subj else None
            if not delta["matched"] or not p:
                skipped.append(name)
                continue
            try:
                base = self.tools.generation_plan(p["generation"])
            except ToolError:
                skipped.append(name)
                continue
            new_plan = refine.apply(base, delta, clause, name)
            changes = refine.describe(delta)
            sid = new_plan["slots"].get("style_id") or st["style_id"]
            t.trace.step(f"{name}: " + ", ".join(changes), {"title": f"from {self._nm(sess, p['generation'])}", "lines": [clause]})
            items.append({"prompt": p["prompt"], "subject": name, "grid": p.get("grid") or st["grid"], "style_id": sid, "ai": True, "plan": compact_plan(new_plan), "parent": p["generation"],
                          "note": "changed: " + ", ".join(changes), "changes": changes, "delta": {k: delta.get(k) for k in ("style_id", "size", "colour")}})
        if not items:
            t.reply = "I could not tell what to change" + (f" about {', '.join(skipped)}" if skipped else "") + ". Tell me the style (\"more cartoonish\"), the size (\"bigger\") or a colour (\"more red\")."
            t.trace.end("asked what to change")
            return {}
        est = self.tools.estimate("image") if self.tools.live() else None
        title = "changes to " + " and ".join(i["subject"] for i in items)
        card = self._items_card(title, items, st, est, {"refine": True})
        reply = "Here's what I will change: " + "; ".join(f"**{i['subject']}**: {', '.join(i['changes'])}" for i in items) + ". Each is a new sheet from the same prompt with just that change; the originals stay."
        if skipped:
            reply += f" (I did not understand what to change about {', '.join(skipped)}.)"
        return self._offer_items(t, title, items, est, card, reply)

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
        spec.update(type="create", estimate=est, parent=p["generation"], note=f"another pass of {self._nm(t.sess, p['generation'])}")
        if t.sess["settings"].get("ask_before_spending", True):
            t.sess["pending"] = spec
            t.reply = f"I'll make another pass of **{subj['name']}** with different poses ({_credits(est)}). Go ahead?"
            t.chips = [{"label": "Create it", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            t.trace.end(f"ready · {_credits(est)}")
        else:
            self._start_create(t, spec, parent=p["generation"], note=spec["note"])
        return {}

    # -- an edit of what is open, by what it means (UI/UX spec P11-P13) -------------------------------------------------------------------------------
    def n_unsupported(self, state: State) -> dict:
        t: Turn = state["turn"]
        t.reply = editroute.unsupported(t.text) or "I can't do that yet."
        t.trace.end("not supported yet")
        return {}

    def _explicit_targets(self, t: Turn) -> list:
        """The stickers the person POINTED at in this message (a number, an id, a selection, "the shocked one"): a slice. A pronoun ("him", "it") is the character, so the whole sheet."""
        return list(t.res.stickers) if t.res.how in ("number", "explicit id", "selection", "concept", "make A like B", "feedback clauses") else []

    def n_editroute(self, state: State) -> dict:
        """"can you rotate him?" -> the EDITOR (a transformation or a cleaning of one slice, free); "make him cry" / "now make him play football" / "make it as a lemon" -> drawn again, and what is sent
        depends on the case (agent/editroute.py): the sheet as the picture for a tweak and a new action, no picture for a redesign; the parent's own saved prompt is what changes, never a sentence
        rebuilt from the words. The batch is the one in focus, the sheet the person picked in this chat."""
        t: Turn = state["turn"]
        er = t.er or editroute.classify_edit(t.text) or {}
        gen = t.res.generation or (t.sess.get("focus") or {}).get("generation") or (self.store.latest_pass(t.sess, with_generation=True) or {}).get("generation")
        if not gen or not er:
            t.reply = "There is nothing to change yet. Let's make some stickers first."
            return {}
        if er["route"] == "editor":
            return self._editor_offer(t, gen, er)
        return self._regen_offer(t, gen, er)

    def _editor_offer(self, t: Turn, gen: str, er: dict) -> dict:
        t.trace.retitle("opening the editor")
        pointed = self._explicit_targets(t)
        focus = (t.sess.get("focus") or {}).get("stickers") or []
        sid = (pointed or [s for s in focus if s.startswith(gen + "/")] or [None])[0]
        if not sid:
            t.reply = "Which sticker should I open in the editor? Say a number, like \"flip number 3\", or click one."
            t.sess["awaiting"] = {"intents": ["EDIT_ROUTE"], "text": t.text}
            t.trace.end("asked which sticker")
            return {}
        index = int(sid.split("/S")[1])
        what = {"rotate": "rotating", "flip": "flipping", "crop": "cropping", "clean": "cleaning", "text": "adding text"}.get((er.get("ops") or ["rotate"])[0], "that")
        t.sess["focus"] = {"generation": gen, "stickers": [sid]}
        t.reply = (f"Sure — {what} {self._key_of(gen, sid)} ({sid.split('/')[1]}) is a job for the editor, not a new picture, so nothing is spent. "
                   "Want me to boot up the editor for you? When you save, you come straight back here with the slice updated.")
        t.chips = [{"label": "Open the editor", "editor": {"generation": gen, "index": index}}]
        t.trace.end("editor offered")
        return {}

    def _regen_offer(self, t: Turn, gen: str, er: dict) -> dict:
        case = er["case"]
        what = {"tweak": er.get("delta"), "action": er.get("action"), "redesign": er.get("subject")}[case]
        try:
            base = self.tools.generation_plan(gen)
        except ToolError as e:
            t.reply = f"I can't read the prompt of {self._nm(t.sess, gen)} to change it: {e}"
            return {}
        subj = self.store.subject_for_generation(t.sess, gen)
        old = (subj or {}).get("name") or base.get("subject") or "the stickers"
        name = what if case == "redesign" else old
        st = t.sess["settings"]
        t.trace.retitle({"tweak": "changing a detail", "action": "a new action", "redesign": f"redesigning as {what}"}[case])
        pointed = self._explicit_targets(t)[:4]
        est = self.tools.estimate("image") if self.tools.live() else None
        if pointed:
            return self._regen_slices(t, gen, base, pointed, case, what, name, est)
        plan = editroute.plan_for(base, case, subject=er.get("subject"), action=er.get("action"), delta=er.get("delta"), said=t.text)
        refs, clause, sheet_px = [], None, None
        if editroute.sends_image(case):
            try:
                ref = self.tools.sheet_reference(gen)
            except ToolError as e:
                t.reply = f"I can't send the sheet of {self._nm(t.sess, gen)} as the picture: {e}"
                return {}
            refs, clause, sheet_px = [ref["ref"]], editroute.reference_clause(case, what), ref.get("px")
        rows, cols = (plan.get("grid") or [3, 3])[:2] if isinstance(plan.get("grid"), (list, tuple)) else (3, 3)
        sid = plan["slots"].get("style_id") or st["style_id"]
        change = {"tweak": f"change only: {what}", "action": f"new action: {what}", "redesign": f"new design: {what}"}[case]
        item = {"prompt": name, "subject": name, "grid": f"{rows}x{cols}", "style_id": sid, "ai": True, "plan": compact_plan(plan), "parent": gen, "refs": refs, "ref_clause": clause,
                "note": f"{case}: {what}", "changes": [change], **self._edge(gen)}
        t.trace.step(f"{case}: {what}", {"title": f"from {self._nm(t.sess, gen)}", "lines": [f"the picture: {'this sheet (' + str(sheet_px) + ' px)' if refs else 'none: the actions are approved, the design is new'}"]})
        card = self._items_card(f"{name}: {change}", [item], st, est, {"edit": case, "image": bool(refs)})
        how = {"tweak": f"I'll send **this sheet** as the picture with the same prompt and change only: {what}.",
               "action": f"The shape stays: I'll send **this sheet** as the picture with the same prompt, and every character does “{what}” instead.",
               "redesign": f"Same actions, new design: I'll make **{what}** from the same prompt as {old}, and **no picture is sent** (the actions are approved, only the design changes)."}[case]
        return self._offer_items(t, f"{name} ({case})", [item], est, card, f"Got it. {how} A new sheet; the original stays.")

    def _regen_slices(self, t: Turn, gen: str, base: dict, pointed: list, case: str, what: str, name: str, est) -> dict:
        """One or a few slices drawn again as 1x1: only THAT slice goes to the provider, as the picture where the case sends one, with its own cell of the parent's prompt."""
        st = t.sess["settings"]
        items, notes = [], []
        for sid in pointed:
            try:
                sp = editroute.plan_for(self.tools.slice_plan(sid), case, subject=what if case == "redesign" else None, action=what if case == "action" else None, delta=what if case == "tweak" else None, said=t.text)
            except ToolError as e:
                t.reply = f"I can't read the prompt of {sid.split('/')[1]}: {e}"
                return {}
            refs, clause = [], None
            if editroute.sends_image(case):
                r = self.tools.slice_reference(sid)
                refs, clause = [r["ref"]], editroute.reference_clause(case, what, slice_=True)
                notes.append(f"{sid.split('/')[1]} is {r['from_px']} px" + (f", under the {r['min_px']} px minimum, so it was scaled up to {r['px']} px" if r.get("scaled") else f", over the {r['min_px']} px minimum, so it is sent as it is"))
            label = sid.split("/")[1]
            items.append({"prompt": f"{name}: {self._key_of(gen, sid)}, {what}", "subject": name, "parent": gen, "regen_of": sid, "refs": refs, "ref_clause": clause, "plan": compact_plan(sp), "label": label,
                          "style_id": sp["slots"].get("style_id") or st["style_id"], "note": f"{label} redone ({case}): {what}", **self._edge(gen)})
        total = (est or 0) * len(items)
        spec = {"type": "batch", "items": items, "style_id": st["style_id"], "ai": True, "estimate": total}
        labels = ", ".join(i["label"] for i in items)
        t.trace.step(f"{case}: {what}", {"title": "only the slice goes to the provider", "lines": notes or ["no picture is sent"]})
        say = f"I'll redo {labels} ({case}: {what}); the rest of the batch stays." + (" " + "; ".join(notes) + "." if notes else "") + (f" That costs {_credits(total)}." if total else "")
        if self.tools.live() and st.get("ask_before_spending", True):
            t.sess["pending"] = spec
            t.reply = say + " Go ahead?"
            t.chips = [{"label": "Do it", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            t.trace.end(f"ready · {_credits(total)}")
        else:
            t.sess["pending"] = spec
            t.reply = say
            self.n_confirm({"turn": _with_pending(t, spec)})
        return {}

    def _edge(self, gen: str) -> dict:
        """The edge finish of the batch an edit is made from (white stroke px, fringe trim px), so the child looks like its parent and not like the defaults. {} when it cannot be read."""
        try:
            e = self.tools.edge_of(gen) or {}
        except Exception:
            e = {}
        return {k: e[k] for k in ("outline", "erode") if e.get(k) is not None}

    def _person_edit(self, t: Turn) -> dict:
        """"him", "the guy", "last guy" with nothing said about what to change: the person means the character of the chat, so the batch is assumed (the focus; "last" = the newest of the chat) and the
        one thing asked is WHAT to change, never "which sticker?" and never a new sheet called "last guy"."""
        gen = t.res.generation or (t.sess.get("focus") or {}).get("generation") or (self.store.latest_pass(t.sess, with_generation=True) or {}).get("generation")
        if not gen:
            t.reply = "There is nothing to change yet. Let's make some stickers first."
            return {}
        t.sess["focus"] = {"generation": gen, "stickers": []}
        t.generation = gen
        t.reply = f"I'll work on **{self._nm(t.sess, gen)}**, the batch we have open. What should I change about him? For example \"make him wear a hat\" or \"make him happier\"."
        t.chips = [{"label": "Make him happier", "text": "make him happier"}, {"label": "Give him a hat", "text": "give him a hat"}]
        t.trace.step("assumed the character of " + self._nm(t.sess, gen))
        t.trace.end("asked what to change")
        return {}

    def n_edit(self, state: State) -> dict:
        """Numbered stickers (and a clicked selection) drawn again as 1x1. AN EDIT REUSES THE PARENT'S PROMPT (Haitham, 2026-10-02): the 1x1 is the parent's own plan for that cell (`tools.slice_plan` ->
        `gates.regen_plan`: its style, key colour, template version and cell label) with the change appended to the cell's label, the parent's own picture of that sticker goes as the reference
        with a clause that allows the change, and the batch keeps the parent's edge finish. Nothing is rebuilt from the words of the sentence."""
        t: Turn = state["turn"]
        subj, p = self._focus_pass(t)
        targets = t.res.stickers or (t.res.negative if t.res.negative else [])
        if t.res.how == "person reference" and not targets:
            return self._person_edit(t)
        if not targets or not p:
            t.reply = "Which sticker should I change? Say a number, like \"make number 3 happier\", or click one."
            t.chips = []
            if p:
                t.sess["awaiting"] = {"intents": ["EDIT_STICKERS"], "text": t.text}
            return {}
        gen = targets[0].split("/")[0]
        edit = editroute.delta_of(t.text)
        fresh = editroute.fresh_take(edit)
        if fresh:
            edit = ""
        like = ", ".join(self._key_of(gen, r["source"]) for r in t.res.references)
        said = (("same look as " + like) if like else "") + (f" ({edit})" if like and edit else edit if edit else "") or "a fresh take"
        card = self.tools.generation(gen)
        st = t.sess["settings"]
        items, notes = [], []
        for sid in targets[:4]:
            s = next((x for x in card["stickers"] if x["id"] == sid), None)
            if not s:
                continue
            try:
                sp = self.tools.slice_plan(sid)
            except ToolError as e:
                t.reply = f"I can't read the prompt of {sid.split('/')[1]} to change it: {e}"
                return {}
            if edit:
                sp = editroute.add_to_label(sp, edit)
            elif like:
                sp = editroute.add_to_label(sp, "same look as " + like)
            base = (subj["name"] if subj else "sticker")
            refs, clause = [], None
            ref_roles = []
            for r in t.res.references:
                if r["target"] in (None, sid) and hasattr(self.tools, "reference_from_sticker"):
                    try:
                        refs.append(self.tools.reference_from_sticker(r["source"]))
                        ref_roles.append({"source": r["source"], "role": r["role"]})
                    except Exception:
                        pass
            if ref_roles:
                clause = editroute.reference_roles_clause(ref_roles, edit)
            if not refs and not fresh:                                      # the sticker as it is, to be changed (a fresh take is drawn from the prompt alone)
                try:
                    r = self.tools.slice_reference(sid)
                    refs, clause = [r["ref"]], editroute.reference_clause("tweak", edit, slice_=True)
                    notes.append(f"{sid.split('/')[1]} is {r['from_px']} px" + (f", under the {r['min_px']} px minimum, so it was scaled up to {r['px']} px" if r.get("scaled") else f", over the {r['min_px']} px minimum, so it is sent as it is"))
                except Exception:
                    refs, clause = [], None
            items.append({"prompt": f"{base}: {s['key'].replace('_', ' ')}, {said}", "subject": subj["name"] if subj else base, "parent": gen, "regen_of": sid, "refs": refs, "ref_clause": clause,
                          "plan": compact_plan(sp), "style_id": sp["slots"].get("style_id") or st["style_id"], "note": f"{sid.split('/')[1]} redone: {said}", "label": sid.split("/")[1], **self._edge(gen)})
        if not items:
            t.reply = "I couldn't find those stickers in this batch."
            return {}
        t.trace.retitle("editing " + ", ".join(i["label"] for i in items))
        t.trace.step("same prompt, one change", {"title": f"from {self._nm(t.sess, gen)}", "lines": [i["prompt"] for i in items] + notes})
        if t.res.references:
            t.trace.note("using " + ", ".join(r["source"].split("/")[1] for r in t.res.references) + " as the reference")
        est = self.tools.estimate("image")
        total = (est or 0) * len(items)
        spec = {"type": "batch", "items": items, "style_id": st["style_id"], "ai": True, "estimate": total}
        more = f" I did the first 4 of {len(targets)}; ask again for the rest." if len(targets) > 4 else ""
        say = f"I'll redo {', '.join(i['label'] for i in items)} ({said}) from the same prompt; the rest of the batch stays." + (" " + "; ".join(notes) + "." if notes else "") + more
        if self.tools.live() and st.get("ask_before_spending", True):
            t.sess["pending"] = spec
            t.reply = say + (f" That costs {_credits(total)}." if total else "") + " Go ahead?"
            t.chips = [{"label": "Do it", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            t.trace.end(f"ready · {_credits(total)}")
        else:
            t.sess["pending"] = spec
            t.reply = say
            t.trace.step("confirmed: edit")
            self.n_confirm({"turn": _with_pending(t, spec)})
        return {}

    def n_undo(self, state: State) -> dict:
        """"undo" / "revert": the last REFINEMENT of this chat is taken back, the simple way. A plan still waiting for the go-ahead is dropped (nothing was spent); otherwise the newest batch the chat made FROM
        another one (an edit, a refinement, a redesign, another pass) is marked undone and the focus returns to the batch it came from, so "it" / "him" / "number 3" mean the earlier version again.
        Nothing is deleted or un-paid: the newer batch stays in History, and a job still drawing is not stopped. Feedback ("I hate 4") and approvals are not refinements and are not undone here."""
        t: Turn = state["turn"]
        sess = t.sess
        if sess.get("pending"):
            what = t.prev_pending or sess["pending"]
            sess["pending"] = None
            names = ", ".join(i.get("label") or i.get("subject") or "" for i in (what or {}).get("items") or []) if (what or {}).get("type") == "batch" else str((what or {}).get("subject") or (what or {}).get("label") or "")
            t.reply = f"Undone: I dropped the plan{(' for **' + names + '**') if names.strip(', ') else ''}. Nothing was spent."
            t.trace.end("plan dropped, nothing spent")
            return {}
        last = None
        for subj in sess["subjects"]:
            for p in subj["passes"]:
                if p.get("parent") and not p.get("undone") and (last is None or p["created"] >= last[1]["created"]):
                    last = (subj, p)
        if not last:
            t.reply = "There is nothing to undo yet: I have not changed anything in this chat. Tell me what to change, and I can take it back."
            t.trace.end("nothing to undo")
            return {}
        subj, p = last
        parent = p["parent"]
        p["undone"] = True
        sess["focus"] = {"generation": parent, "stickers": []}
        t.generation = parent
        again = (f"the new batch ({p['generation']}) stays in History" if p.get("generation") else "the new batch is still being drawn and cannot be stopped; it will stay in History")
        t.reply = f"Undone. We are back on **{self._nm(sess, parent)}**, the version before your last change ({parent}); {again}, nothing is deleted. Say what you want changed on this one."
        t.cards.append({"type": "generation", "generation": parent, "job": None, "subject": subj["name"], "note": "back to this version"})
        t.trace.step(f"back to {parent}")
        t.trace.end("done")
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
            t.reply = f"{self._nm(t.sess, gen)} has no finished stickers yet; I'll animate them once they're ready."
            return {}
        subj = self.store.subject_for_generation(t.sess, gen)
        t.trace.retitle(f"animating {self._nm(t.sess, gen)}")
        t.trace.step(f"{len(ready)} stickers ready to move")
        spec = {"type": "animate", "generation": gen, "subject": subj["name"] if subj else "", "loop": False}
        if self.tools.live() and t.sess["settings"].get("ask_before_spending", True):
            t.sess["pending"] = spec
            t.reply = f"I'll animate the {len(ready)} stickers of **{self._nm(t.sess, gen)}** (the price is shown when it is sent; about 8 credits for a 3×3 sheet). Go ahead?"
            t.chips = [{"label": "Animate", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
            t.trace.end("ready")
        else:
            t.sess["pending"] = spec
            self.n_confirm({"turn": _with_pending(t, spec)})
        return {}

    def _ready_now(self, gen: str) -> list | None:
        """ready_indexes, or None when the batch cannot be read (the caller then runs the existing path, which says so in words)."""
        try:
            return self.tools.ready_indexes(gen)
        except Exception:
            return None

    def n_export(self, state: State) -> dict:
        """Pack the open batch and send it to Telegram. Nothing moves yet: the animation goes first (its own go-ahead); a batch that already
        moves is packed and sent after one confirmation, because sending is outward."""
        t: Turn = state["turn"]
        gen = t.res.generation or (t.sess.get("focus") or {}).get("generation") or (self.store.latest_pass(t.sess, with_generation=True) or {}).get("generation")
        if not gen:
            t.reply = "There is nothing to send yet. Let's make some stickers first."
            t.chips = [{"label": s, "text": s} for s in SUGGESTIONS[:3]]
            return {}
        name = self._nm(t.sess, gen)
        subj = self.store.subject_for_generation(t.sess, gen)
        subject = (subj or {}).get("name") or ""
        t.trace.retitle(f"sending {name} to Telegram")
        try:
            animated = [s["index"] for s in self.tools.generation(gen)["stickers"] if s.get("anim_status") == "READY"]
        except ToolError:
            animated = []
        if not animated:
            spec = {"type": "animate", "generation": gen, "subject": subject, "loop": False, "then": "pack_send"}
            if self.tools.live() and t.sess["settings"].get("ask_before_spending", True):
                t.sess["pending"] = spec
                t.reply = f"I'll animate **{name}** first (the price is shown when it is sent), then pack it and send it to Telegram. Go ahead?"
                t.chips = [{"label": "Animate", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
                t.trace.end("ready")
            else:
                t.sess["pending"] = spec
                self.n_confirm({"turn": _with_pending(t, spec)})
            return {}
        spec = {"type": "pack_send", "generation": gen, "subject": subject}
        if self.tools.live() and t.sess["settings"].get("ask_before_spending", True):
            t.sess["pending"] = spec
            t.reply = f"Pack **{name}** ({len(animated)} animated) and send it to Telegram?"
            t.chips = [{"label": "Pack and send", "action": "confirm"}, {"label": "Not yet", "action": "cancel"}]
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
        bulk = False
        m = re.search(r"\ball\b(?:\s+(?:of them|the stickers))?\s*(?:but|except)\s+(.*)", low)
        if m:
            from .resolver import _numbers
            skip = _numbers(m.group(1), 9)
            idx, bulk = [i for i in ready if i not in skip], True
        elif re.search(r"\b(all|everything|them all)\b", low):
            idx, bulk = ready, True
        else:
            idx = [int(s.split("/")[1][1:]) for s in t.res.stickers]
        if not idx:
            t.reply = "Which stickers? For example \"approve all but 5 and 6\"."
            t.sess["awaiting"] = {"intents": ["REVIEW"], "text": t.text}
            return {}
        if bulk and len(idx) > 1:                                    # a decision on many stickers at once is confirmed, never read off one sentence
            names = ", ".join("S" + str(i) for i in idx)
            t.sess["pending"] = {"type": "review", "generation": gen, "decision": decision, "indexes": idx, "subject": self._nm(t.sess, gen)}
            t.reply = f"{'Approve' if decision == 'APPROVE' else 'Reject'} {names} in **{self._nm(t.sess, gen)}**? Say yes to record it, or no."
            t.chips = [{"label": "Yes, " + decision.lower(), "action": "confirm"}, {"label": "No", "action": "cancel"}]
            t.trace.end("waiting for your yes")
            return {}
        return self._do_review(t, gen, decision, idx)

    def _do_review(self, t: Turn, gen: str, decision: str, idx: list) -> dict:
        t.trace.retitle(("approving" if decision == "APPROVE" else "rejecting") + f" in {self._nm(t.sess, gen)}")
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
        prof = self._profile()
        who = prof.name()
        if re.search(NAME_QUESTION, low):                               # "what is my name?": what the person told me (their profile), never a guess from the stickers
            if re.search(r"\babout me\b", low):
                known = prof.facts_text()
                t.reply = (known.replace("The person: ", "What you told me: ") if known else "Nothing yet.") + " Tell me anything else you'd like me to remember."
            elif who:
                t.reply = f"You're {who}."
            else:                                                       # one honest question, and the answer that follows sticks (n_understand reads it as the name)
                t.reply = "I don't know your name yet. What should I call you?"
                t.sess["awaiting"] = {"profile": "name", "text": t.text}
            t.trace.end("answered from what you told me")
            return {}
        facts = ((prof.facts_text() + "\n") if prof.facts_text() else "") + self.store.summary_text(t.sess)
        ans = self.brain.answer(t.text, facts) if self.brain.available else None
        t.reply = ans or facts
        t.trace.end("answered" if ans else "here is what we have")
        return {}

    def _describe(self, t: Turn) -> dict:
        """"Describe the stickers": the person's yes to AI vision comes first, once per chat (`settings.allow_vlm`: None = not asked, True, False)."""
        gen = t.res.generation or (t.sess.get("focus") or {}).get("generation") or (self.store.latest_pass(t.sess) or {}).get("generation")
        if not gen:
            t.reply = "Which batch should I look at? Tell me its name or its number (like G012)."
            return {}
        only = [int(x.split("/S")[1]) for x in t.res.stickers if x.startswith(gen + "/S")]
        allow = t.sess["settings"].get("allow_vlm")
        t.trace.retitle(f"looking at {self._nm(t.sess, gen)}")
        if allow is False:
            t.reply = "AI vision is off for this chat, so I won't send the pictures to a model. Say \"allow AI vision\" and ask again."
            t.trace.end("AI vision is off", ok=False)
            return {}
        if allow is None:
            t.sess["pending"] = {"type": "describe", "generation": gen, "only": only}
            t.reply = (f"To describe **{self._nm(t.sess, gen)}** I send its pictures to the vision model (the local one when LM Studio is running, otherwise the cloud one). "
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
        t.reply = f"**{self._nm(t.sess, gen)}**\n" + "\n".join(f"S{c['index']}: {c['caption']}" if c.get("caption") else f"S{c['index']}: I couldn't read this one" for c in rows) or f"{self._nm(t.sess, gen)} has no finished stickers yet."
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
            if re.search(r"\bvision\b|\bvlm\b", t.text.lower()):
                t.sess["vision_asked"] = True                              # the one-time question is not asked again in this chat; the vision setting itself is untouched
                t.reply = ("Understood, I will not ask about AI vision again in this chat, and \"ask before spending\" is unchanged. AI vision stays as it is: say \"allow AI vision\" or \"don't use AI vision\" "
                           "when you decide. If you ask me to describe or rename stickers, I still need your yes first.")
                return {}
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

    def n_retry(self, state: State) -> dict:
        """"Try the sheet again" on a batch whose sheet Python blocked (`flow/explain.py`). The button states the price, so the click is the go-ahead; the new sheet is a new batch
        with the same words, the blocked one stays as it is (nothing is deleted)."""
        t: Turn = state["turn"]
        gid = str((t.action or {}).get("generation") or "")
        try:
            card = self.tools.generation(gid)
        except ToolError as e:
            t.reply = str(e)
            return {}
        if not card.get("problem"):
            t.reply = "That sheet is fine, there is nothing to redo."
            return {}
        name = self._nm(t.sess, gid)
        grid = "x".join(str(x) for x in (card.get("grid") or [3, 3])) if isinstance(card.get("grid"), list) else (card.get("grid") or t.sess["settings"]["grid"])
        subj = self.store.subject_for_generation(t.sess, gid)
        p = next((q for q in (subj or {}).get("passes", []) if q.get("generation") == gid), {})
        t.trace.retitle(f"a new sheet for {name}")
        t.trace.step("the first sheet could not be cut: " + str(card["problem"].get("check") or ""))
        self._start_create(t, {"prompt": card.get("prompt") or name, "subject": (subj or {}).get("name") or name, "grid": grid,
                               "style_id": p.get("style_id") or t.sess["settings"]["style_id"], "ai": True},
                           note=f"a new sheet for {name}: the first could not be cut")
        run = t.sess.get("creator_run")
        new = next((c for c in reversed(t.cards) if c.get("type") == "generation"), None)
        if run and new and run.get("generation") == gid and run["status"] in ("stopped", "waiting"):        # the creator follows the new sheet
            run.update(job=new.get("job"), generation=new.get("generation"), step="sheet", status="running", stop=None, waiting=None, skip=[])
            creator._log(run, "a new sheet was started")
            t.cards.append({"type": "creator", "run_id": run["id"]})
        return {}

    # -- names: the vision model looks at the pictures and proposes a better name where the current one does not fit ----------------------------------------------
    def n_names(self, state: State) -> dict:
        t: Turn = state["turn"]
        gen = t.res.generation or (t.sess.get("focus") or {}).get("generation") or (self.store.latest_pass(t.sess) or {}).get("generation")
        if not gen:
            t.reply = "Which batch should I look at? Make some stickers first, or tell me its name."
            return {}
        allow = t.sess["settings"].get("allow_vlm")
        t.trace.retitle(f"looking at {self._nm(t.sess, gen)}")
        if allow is False:
            t.reply = "AI vision is off for this chat, so I won't send the pictures to a model. Say \"allow AI vision\" and ask again."
            t.trace.end("AI vision is off", ok=False)
            return {}
        if allow is None:
            t.sess["pending"] = {"type": "names", "generation": gen}
            t.reply = (f"To check the names of **{self._nm(t.sess, gen)}** I send its pictures to the vision model (the local one when LM Studio is running, otherwise the cloud one). "
                       "Allow AI vision of generated media? I only ask once.")
            t.chips = [{"label": "Allow AI vision", "action": "confirm"}, {"label": "Not now", "action": "cancel"}]
            t.trace.end("waiting for your yes")
            return {}
        self._run_names(t, gen)
        return {}

    def _run_names(self, t: Turn, gen: str) -> None:
        try:
            rows = self.tools.name_proposals(gen, self.brain.name_check if self.brain.available else (lambda items: None), allowed=True)
        except ToolError as e:
            t.reply = str(e) if e.code != 404 else "I can't find that batch."
            t.trace.end("could not look", ok=False)
            return
        self._names_reply(t, gen, rows)
        t.trace.end("checked")

    def _names_reply(self, t: Turn, gen: str, rows: list) -> None:
        nm = self._nm(t.sess, gen)
        t.generation = gen
        t.trace.step(f"looked at {len(rows)} sticker{'s' if len(rows) != 1 else ''}")
        change = [r for r in rows if not r["fits"]]
        if not rows:
            t.reply = f"**{nm}** has no finished stickers to look at yet."
        elif not change:
            t.reply = f"I looked at all {len(rows)} stickers of **{nm}**: the names fit the pictures."
        else:
            t.reply = f"I looked at **{nm}**. These names do not fit the picture:\n" + "\n".join(f"S{r['index']}: \"{r['current']}\" -> **{r['name']}**" for r in change)
            t.chips = [{"label": "Apply the new names", "action": "names_apply", "generation": gen}, {"label": "Keep my names", "action": "names_keep", "generation": gen}]

    def n_names_decide(self, state: State) -> dict:
        t: Turn = state["turn"]
        gen = str((t.action or {}).get("generation") or "")
        if (t.action or {}).get("type") == "names_keep":
            t.reply = "Kept: the names stay as they are."
            return {}
        try:
            done = self.tools.apply_titles(gen)
        except ToolError as e:
            t.reply = str(e)
            return {}
        t.generation = gen or None
        t.trace.task("renaming")
        t.trace.step(f"renamed {len(done)} sticker{'s' if len(done) != 1 else ''}")
        t.trace.end("recorded in each sticker's history")
        t.reply = ("Renamed " + ", ".join(f"S{i}" for i in sorted(done)) + ". The files and the search keep their own names; only what you read changed.") if done else "There was nothing waiting to rename."
        return {}

    def auto_name(self, sid: str, gid: str) -> bool:
        """Once AI vision is allowed, a batch that has finished stickers gets looked at without being asked: the answer arrives as a message of its own in the chat (a turn the assistant starts
        itself, so it takes the session's lock like any turn and is skipped, to be tried at the next poll, when the person is mid-turn). Once per batch (`named`). Returns True when it ran."""
        lock = self.cache.lock(f"session:{sid}")
        try:
            lock.__enter__()
        except cachemod.Busy:
            return False
        try:
            sess = self.store.load(sid)
            if sess["settings"].get("allow_vlm") is not True or gid in sess.setdefault("named", []):
                return False
            try:
                if not self.tools.ready_indexes(gid):
                    return False
            except ToolError:
                return False
            sess["named"].append(gid)
            msg = self.store.add_message(sess, "assistant", "", status="working")
            self.store.save(sess)
            t = Turn(sid, "", [], None, sess, msg, Trace(self.store, sess, msg))
            t.trace.task(f"looking at {self._nm(sess, gid)}")
            try:
                rows = self.tools.name_proposals(gid, self.brain.name_check if self.brain.available else (lambda items: None), allowed=True)
                self._names_reply(t, gid, rows)
                t.trace.end("checked")
                ok = True
            except Exception as e:
                t.reply, ok = "I could not look at the pictures this time; nothing changed.", False
                t.trace.end("could not look", ok=False)
                msg["error"] = f"{type(e).__name__}: {e}"[:300]
            msg.update(text=t.reply, cards=t.cards, chips=t.chips, status="done" if ok else "error")
            self.store.save(sess)
            return True
        finally:
            lock.__exit__(None, None, None)

    def n_smalltalk(self, state: State) -> dict:
        t: Turn = state["turn"]
        kind = smalltalk_kind(t.text)
        t.trace.task({"thanks": "saying you're welcome", "bye": "saying goodbye", "ack": "noting that", "no": "noting that"}.get(kind, "saying hello"))
        t.reply = {"thanks": "You're welcome! Tell me what to change, or what to make next.", "bye": "Bye! Your stickers will be here when you come back.",
                   "ack": "Anytime. Tell me what to change, or what to make next.", "no": "Okay. Tell me when you want to make something."}.get(kind, f"Hi{' ' + who if (who := self._profile().name()) else ''}! What will you create today?")
        t.chips = [{"label": s, "text": s} for s in SUGGESTIONS]
        t.trace.end("ready")
        return {}

    def n_profile(self, state: State) -> dict:
        """What the person says about themselves ("hello from haitham", "it is 'haitham'", "I live in Dubai", the answer to my "what should I call you?") goes to THEIR profile
        (out/profile/<user>.json, agent/profile.py) and nothing else changes: no subject, no plan, and a plan I am holding stays held. The rules read it first; the model only reads what
        they could not (several facts, a correction, a reference), and whatever it proposes passes profile.validate_facts before anything is written. The reply says what was saved."""
        t: Turn = state["turn"]
        prof = self._profile()
        facts = dict(t.profile_answer or profile_facts(t.text)[0])
        if not facts and self.brain.available:
            facts = self.brain.extract_profile(t.text, prof.facts_text()) or {}
        t.trace.task("remembering what you told me")
        saved = prof.set_facts(facts, t.text)
        if not saved:
            t.prefix = "I didn't catch what to remember. Say it like \"my name is Haitham\" or \"I live in Dubai\"."
            t.trace.end("nothing saved", ok=False)
            return {}
        held = (t.sess.get("pending") or {}).get("subject")
        dropped = ""
        if held and "name" in saved and re.sub(r"[^a-z]", "", str(held).lower()) in (re.sub(r"[^a-z]", "", saved["name"].lower()), re.sub(r"[^a-z]", "", t.text.lower())):
            t.sess.pop("pending", None)                                 # a plan "for haitham" was the name misread as a subject (before 2026-10-04): it goes, said once
            dropped, held = f" I dropped the plan for \"{held}\": that was your name, not a sticker subject.", None
        said = profile_said(saved)
        hello = f"Nice to meet you, {saved['name']}! " if "name" in saved else "Got it! "
        more = "NEW" in t.intents                                       # "hi, I'm Sam, make me a falcon": the request goes on after this
        t.prefix = hello + f"I'll remember {said}." + dropped + ("" if more else f" Your plan for {held} is still waiting: say \"create it\" when you're ready." if held else " What will you create today?")
        if not held and not more:
            t.chips = [{"label": s, "text": s} for s in SUGGESTIONS]
        t.trace.end("saved: " + said)
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
        elif t.unsure_review:
            t.reply = "I did not decide anything: I could not tell whether you want to approve or reject. Say it plainly, for example \"approve 3\" or \"reject 4 and 5\"."
            t.trace.end("asked what to decide")
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

    VISION_ASK = ("One more thing, once: may I look at your stickers with a vision model (the local one when LM Studio is running, otherwise the cloud one)? "
                  "I would check each picture, describe it, and suggest a better name when the current one does not fit. Nothing is sent until you say yes.")

    def _vision_ack(self, t: Turn) -> None:
        """The person flipped the AI vision switch since the last turn (`SessionStore.set_vision`: state only, no turn of its own). This turn goes on as usual and says so once, in its own words."""
        ack = t.sess.pop("vision_ack", None)
        if ack:
            t.reply = (t.reply + "\n\n" if t.reply else "") + ("AI vision is on, as you allowed: I can look at your stickers now (names, captions)." if ack == "allowed"
                                                                 else "AI vision is off, as you chose: no picture goes to a vision model. Say \"allow AI vision\" or use the switch any time.")

    def _ask_vision_early(self, t: Turn) -> bool:
        """The first answer of a chat also asks, once, whether AI vision may be used (`settings.allow_vlm`: None = never asked). It is a pair of buttons that change only that setting,
        so it never replaces a pending go-ahead (the plan's Create stays what it was) and a person who ignores it is simply not asked again in this chat."""
        sess = t.sess
        if sess["settings"].get("allow_vlm") is not None or sess.get("vision_asked"):
            return False
        if not set(t.intents) & CREATION_INTENTS:
            return False                                  # only on the creation path: a hello, a name, a question or a "not yet" has nothing to look at
        if sess.get("awaiting") or (sess.get("pending") or {}).get("type") in ("describe", "names") or any(x in ("CONFIRM", "CANCEL") for x in t.intents) and not sess["interactions"]:
            return False                                  # a question of mine is open (which sticker? the describe consent): one question at a time
        sess["vision_asked"] = True
        t.reply = (t.reply + "\n\n" if t.reply else "") + self.VISION_ASK
        # a one-time decision is not a creation control (UI/UX spec P9): the plan keeps only Create it (a typed "no" still cancels), and the question is ONE switch on the right with a glow. Pressing it
        # writes the setting through the settings route and makes no chat turn (P10); leaving it alone is "not now" and is not asked again in this chat.
        t.chips = [c for c in t.chips if c.get("action") != "cancel"] + [{"label": "Allow AI vision", "on": "AI vision on", "off": "AI vision off", "setting": {"allow_vlm": True}, "side": "right", "glow": True}]
        return True

    def _finish(self, t: Turn, ok: bool = True) -> None:
        sess, msg = t.sess, t.msg
        if t.prefix:
            t.reply = t.prefix + ("\n\n" + t.reply if t.reply else "")
        if t.res.generation and t.res.stickers:
            sess["focus"] = {"generation": t.res.generation, "stickers": t.res.stickers[:3]}
        elif t.generation:
            sess["focus"] = {"generation": t.generation, "stickers": []}
        if ok:
            self._vision_ack(t)
        if ok and self._ask_vision_early(t):
            pass
        old, new = t.prev_pending, sess.get("pending")
        if old and new and new is not old and (old.get("type"), old.get("subject")) != (new.get("type"), new.get("subject")) and not (t.action or {}).get("type") in ("confirm", "cancel") \
                and t.intents and t.intents[0] not in ("CONFIRM", "CANCEL"):
            gone = old.get("subject") or old.get("type")
            t.reply = (t.reply + " " if t.reply else "") + f"(This replaces the plan I was holding for {gone}: nothing was spent on it.)"
        if self.brain.last_error:                                      # the model was asked in this turn and could not answer: the rules answered, and the person is told why
            t.trace.rules_note(self.brain.last_error)
        msg.update(text=t.reply, cards=t.cards, chips=t.chips, status="done" if ok else "error")
        if msg["steps"] and msg["steps"][-1]["kind"] != "final":
            t.trace.end("done" if ok else "stopped", ok=ok)
        self.store.add_interaction(sess, t.text or (t.action or {}).get("type", ""), t.reply, t.intents,
                                   {**t.res.to_dict(), "spent_estimate": t.spent}, t.generation or t.res.generation)
        if self.store.reduce(sess, summarise=(self.brain.summarise if self.brain.available else None)):
            t.trace.note("summarised the earlier part of this chat")
        self.store.save(sess)


def _edge_kw(item: dict) -> dict:
    """The edge finish (white stroke, fringe trim) an edit carries from its parent batch, as keyword arguments for `tools.create`; nothing for a new request, so every other caller is unchanged."""
    return {k: int(item[k]) for k in ("outline", "erode") if item.get(k) is not None}


def compact_plan(plan: dict) -> dict:
    """The plan a card shows, as it is stored in `pending`: the template, the slots and the cells; the prompts are rebuilt from them (`tasks.plan_again`), so the stored plan is small and the
    batch that runs is exactly the one that was approved."""
    keep = {k: v for k, v in (plan or {}).items() if k not in ("sheet_prompt", "video_prompt")}
    keep["stickers"] = [{k: v for k, v in s.items() if k != "prompt"} for s in (plan or {}).get("stickers") or []]
    return keep


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
                _interrupt_message(m)
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
                if c.get("job"):
                    try:
                        j = tools.job(c["job"])
                        c.update(job_status=j.get("status"), job_stage=j.get("stage"), job_error=j.get("error"), cost=j.get("cost"),
                                 job_info={k: j.get(k) for k in ("id", "status", "error", "external_task_id", "provider_check")})
                        gid = gid or j.get("generation")
                    except Exception:
                        pass
                if gid:
                    c["generation"] = gid
                    try:
                        c["data"] = tools.generation(gid)
                    except Exception:
                        pass
            if c.get("type") == "creator" and (sess.get("creator_run") or {}).get("id") == c.get("run_id"):
                c["run"] = dict(sess["creator_run"], steps=creator.labels(sess["creator_run"]))        # the card shows the run as it is now
            cards.append(c)
        m["cards"] = cards
        msgs.append(m)
    out["messages"] = msgs
    out["working"] = any(m.get("status") == "working" for m in msgs)
    out["summary_text"] = store.summary_text(sess)
    return out
