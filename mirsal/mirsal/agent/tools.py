"""What the agent can DO: a small interface over the Studio's own engine, so "the chat's backend is the Studio" is literally true.

`ConsoleTools(console)` calls the same functions the Studio's buttons call (`Console.live`, `pipeline`, `gates`, search). Nothing here
re-implements generation, gating or search. `FakeTools` (tests) implements the same methods without a provider. The agent never spends
unless the user said so: every method that costs credits is called only after a confirmation (or the user's "don't ask me" setting)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from ..flow import gates, pipeline as pl
from ..generation import tasks


class ToolError(Exception):
    def __init__(self, msg: str, code: int = 400):
        super().__init__(msg)
        self.code = code


class ConsoleTools:
    def __init__(self, c, user: dict | None = None):
        self.c = c
        self.out = Path(c.out)
        self.user = user or {"id": "local", "role": "owner", "can_spend": True}

    @property
    def member(self) -> bool:
        return self.user.get("role") != "owner"

    def _see(self, gid: str) -> None:
        """A member reaches only the batches they own; anything else is 'not found' (a 404 never reveals that it exists)."""
        if not self.member:
            return
        try:
            res = pl.read_result(self.out, int(gid[1:]))
        except Exception:
            raise ToolError("No such batch", 404)
        if res.get("owner", "local") != self.user["id"]:
            raise ToolError("No such batch", 404)

    def _may_spend(self) -> None:
        if self.live() and not self.user.get("can_spend"):
            raise ToolError("This account cannot start paid generation (it would spend the owner's credits). Ask the owner to allow it.", 403)

    # ---- reads -------------------------------------------------------------------------------------------------------------------
    def live(self) -> bool:
        from ..generation import higgsfield
        return higgsfield.available()

    def credits(self) -> float | None:
        if self.member:                       # the owner's balance is not a member's business
            return None
        try:
            a = self.c.hf_account()
            return a.get("credits") if a.get("available") else None
        except Exception:
            return None

    def plan(self, prompt: str, grid: str, style_id: str, ai: bool) -> dict:
        """The plan for a request, from the Redis planner cache when this exact request (normalised: case, spaces, end punctuation) was planned
        before with the same templates and model: 0 model calls. A plan the AI failed to expand (it fell back to the built-in sets) is never cached."""
        from .. import transformations
        from ..generation import prompter
        from ..runtime import cache as cachemod
        from ..services import llm
        c = cachemod.default()
        versions = sorted(f.stem for f in prompter.TEMPLATES.glob("*.txt")) + [transformations.signature()]
        key = c.key("plan", cachemod.digest(cachemod.normalize_request(prompt), grid, style_id, bool(ai), ",".join(versions),
                                              llm.model() if ai and llm.configured() else "-"))
        hit = c.get(key, "plan")
        if hit:
            return hit
        try:
            plan = tasks.preview(prompt, grid, style_id, ai)
        except pl.PipelineError as e:
            raise ToolError(str(e), e.code)
        if not plan.get("expand_error"):
            c.set(key, plan, 7 * 24 * 3600)
        return plan

    def engine_label(self, ai: bool = True) -> str | None:
        """Which model writes the sticker ideas right now ("qwen3.5-4b (local)", "gpt-4.1-mini (cloud)"), None when the built-in sets are used. Shown as a step before the model is asked."""
        from ..services import llm
        if not ai or not llm.configured():
            return None
        return f"{llm.model().split('/')[-1].replace(':2', '')} ({'local' if llm.provider() == 'local' else 'cloud'})"

    def estimate(self, kind: str = "image") -> float | None:
        """What one call of the default model costs (a sheet; a video needs a built video sheet and is priced when it is sent)."""
        if not self.live():
            return None
        memo = getattr(self.c, "_estimates", None)
        if memo is None:
            memo = self.c._estimates = {}
        hit = memo.get(kind)
        if hit and time.time() - hit[0] < 60:                    # the card polls every second; a price does not change that fast
            return hit[1]
        try:
            v = self.c.live("cost", {"kind": kind}).get("credits")
        except Exception:
            return None
        memo[kind] = (time.time(), v)
        return v

    def generation(self, gid: str) -> dict:
        """The sticker list of one batch for the chat (ids, keys, emoji, status, reviews, file urls).

        Each sticker also carries what a person may DO with it that Python blocked (`allow`): `can` (use it anyway now), `allowed` (it carries a permission), `undo` (take it back now),
        `why` (the plain-words reason) and `final` (why it cannot be allowed). Without this the chat tile can show a blocked sticker but cannot offer the override that
        rule 10 requires on every surface (`gates.allow_info`, computed, never stored)."""
        self._see(gid)
        res = pl.read_result(self.out, int(gid[1:]))
        info = gates.allow_info(res)
        stickers = []
        for s in res["stickers"]:
            i = s["index"]
            allow = {kind: {"can": info[kind]["can"].count(i) > 0, "allowed": i in info[kind]["allowed"],
                            "undo": i in info[kind]["undo"], "why": info[kind]["why"].get(str(i)), "final": info[kind]["final"].get(str(i))}
                     for kind in gates.KINDS}
            stickers.append({"id": f"{gid}/S{i}", "index": i, "key": s["key"], "name": s.get("name"), "emoji": s.get("emoji"),
                             "tags": s.get("tags"), "title": s.get("title"), "proposed_title": (s.get("title_proposal") or {}).get("name"), "status": s["status"], "reason": s.get("reason"), "still": s["review"]["still"],
                             "anim": s["review"]["anim"], "anim_status": s.get("anim_status"), "allow": allow,
                             "waived": list(s.get("still_override") or []) + list(s.get("anim_override") or []),
                             "png": f"/out/{gid}/{s['png']}" if s.get("png") else None,
                             "webm": f"/out/{gid}/{s['webm']}" if s.get("webm") else None, "prompt": s.get("prompt")})
        return {"generation": gid, "stage": res.get("stage"), "error": res.get("error"), "prompt": res.get("prompt"), "problem": self._problem(res),
                "parent": f"G{int(res['parent']):03d}" if res.get("parent") else None, "grid": res.get("grid"), "stickers": stickers}

    def _problem(self, res: dict) -> dict | None:
        p = pl.problem_of(self.out, res)
        if p:
            p["retry_estimate"] = self.estimate("image")
        return p

    def job(self, jid: str) -> dict:
        from ..generation import jobs
        try:
            return jobs.read(self.out, jid)
        except jobs.JobError as e:
            raise ToolError(str(e), e.code)

    def search(self, q: str) -> list:
        """Matching stickers as chat cards: id, key, emoji, and a file url the page can show. Postgres pool search when it is up, else files."""
        def url(gen, png):
            return f"/out/{gen}/{png}" if png else None

        try:
            from ..store import db, sync
            if sync.is_default_out(self.out) and db.available():
                from ..store import pool
                with db.connect() as conn:
                    r = pool.search(conn, q, count=12, per_gen=12, viewer=self.user["id"] if self.member else None)
                return [{"id": h["sticker_id"], "key": h["key"], "png": url(h["generation_id"], h.get("png")), "emoji": "".join(h.get("emoji") or [])}
                        for h in r["hits"]]
        except Exception:
            pass
        rows = gates.search(self.out, q, 24)
        if self.member:
            rows = [r for r in rows if self._owns(r["generation"])]
        return [{"id": f"{r['generation']}/S{r['index']}", "key": r["key"], "png": url(r["generation"], r.get("png")), "emoji": r.get("emoji")}
                for r in rows]

    def _owns(self, gid: str) -> bool:
        try:
            return pl.read_result(self.out, int(gid[1:])).get("owner", "local") == self.user["id"]
        except Exception:
            return False

    def reference_from_sticker(self, sid: str) -> str:
        """A finished sticker as a reference image for the next sheet ("make 5 like 2"): copied into out/refs/ as R###, the Studio's own reference store."""
        gid, idx = sid.split("/")
        res = pl.read_result(self.out, int(gid[1:]))
        st = next(x for x in res["stickers"] if x["index"] == int(idx[1:]))
        data = (pl.gen_dir(self.out, int(gid[1:])) / st["png"]).read_bytes()
        return self.c.save_ref(data, f"{sid.replace('/', '_')}.png")["id"]

    # ---- writes (these can spend) -----------------------------------------------------------------------------------------------------
    def create(self, prompt: str, grid: str = "3x3", style_id: str = "flat_vector", ai: bool = True, parent: str | None = None,
               regen_of: str | None = None, refs: list | None = None, base_plan: dict | None = None) -> dict:
        """A new batch: the Studio's Generate. Live -> a sheet job (Higgsfield); otherwise the prepared-sheet lookup, exactly as the page does. `base_plan` is the plan the person
        approved on the card: it is what is sent (the cells, tags and slots of the card), never planned a second time."""
        self._may_spend()
        if parent:
            self._see(parent)
        try:
            if self.live():
                body = {"prompt": prompt, "grid": grid, "style_id": style_id, "ai": ai, "refs": refs or []}
                if parent:
                    body["parent"] = parent
                if regen_of:
                    body["regen_of"] = regen_of
                r = self.c.live("sheet", body, base_plan=base_plan)
                return {"job": r["job"], "task": r["task"], "estimate": r.get("estimate"), "generation": None, "live": True}
            if self.c.lock.locked():
                raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
            gid = pl.start(prompt, self.out, self.c.inp)
            pl.approve_plan(self.out, gid, "approved from the chat")
            self.c.submit(lambda: pl.run_stills(self.out, gid, self.c.cfg, self.c.pace))
            return {"job": None, "task": None, "estimate": None, "generation": f"G{gid:03d}", "live": False}
        except pl.PipelineError as e:
            raise ToolError(str(e), e.code)

    def generation_plan(self, gid: str) -> dict:
        """The saved plan (prompts.json) of a batch: the cells, tags, slots and template it was made from, to start a changed copy of it (a refinement keeps everything but the change)."""
        self._see(gid)
        try:
            return json.loads((pl.gen_dir(self.out, int(gid[1:])) / "prompts.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ToolError("That batch has no saved plan to change", 404)

    def more(self, gid: str) -> dict:
        """The next prepared variation of the same subject (no provider): the Studio's 'Create more' on a prepared set."""
        self._see(gid)
        try:
            if self.c.lock.locked():
                raise pl.PipelineError("busy: a job is running, wait for it to finish", 409)
            new = pl.more(self.out, self.c.inp, int(gid[1:]))
            self.c.submit(lambda: pl.run_stills(self.out, new, self.c.cfg, self.c.pace))
            return {"generation": f"G{new:03d}"}
        except pl.PipelineError as e:
            raise ToolError(str(e), e.code)

    def animate(self, gid: str, loop: bool = False) -> dict:
        """One click, as the Studio's animate button: approve the kept stills, build and approve the video sheet, start Kling."""
        self._see(gid)
        self._may_spend()
        try:
            r = self.c.live("video", {"generation": int(gid[1:]), "loop": loop})
            return {"job": r["job"], "estimate": r.get("estimate")}
        except pl.PipelineError as e:
            raise ToolError(str(e), e.code)

    def review(self, gid: str, decision: str, indexes: list, note: str = "from the chat", gate: str = "still") -> dict:
        """Human decisions at the stills gate (or `gate="anim"`) for the given stickers. Python's blocks stay final: a refused sticker is reported, not forced."""
        self._see(gid)
        done, refused = [], []
        for i in indexes:
            try:
                gates.review(self.out, int(gid[1:]), gate, decision, int(i), note)
                done.append(int(i))
            except pl.PipelineError as e:
                refused.append({"index": int(i), "why": str(e)})
        return {"done": done, "refused": refused}

    # ---- "Use it anyway" (CLAUDE.md rule 10): a judgement-call block a person may allow, and take back ----
    def allowable(self, gid: str, kind: str = "still", allow: bool = True) -> list[int]:
        """The stickers whose block is a judgement call and may therefore be allowed right now (or whose permission may be taken back).
        A technical block (Telegram's own limits) and a cell with no picture are never in this list: those are final."""
        self._see(gid)
        try:
            return gates.allowable(pl.read_result(self.out, int(gid[1:])), allow, kind)
        except pl.PipelineError:
            return []

    def allow(self, gid: str, indexes: list, kind: str = "still", allow: bool = True) -> dict:
        """A person's recorded, reversible permission for what Python blocked as a judgement call: the sticker is cut again with that
        check kept as a warning ("allowed by you"), free and in the background. The same call the Studio's tile and sheet make."""
        self._see(gid)
        g = int(gid[1:])
        done, refused = [], []
        for i in indexes:
            try:
                gates.check_allow(self.out, g, int(i), allow, kind)
                done.append(int(i))
            except pl.PipelineError as e:
                refused.append({"index": int(i), "why": str(e)})
        if not done:
            why = refused[0]["why"] if refused else "there is nothing to allow here"
            raise ToolError(why, 409)
        self.c.submit(lambda: gates.allow_cells(self.out, g, kind, done, allow, pl.cfg_for(pl.read_result(self.out, g), self.c.cfg), self.c.pace))
        return {"done": done, "refused": refused, "kind": kind, "allow": allow}

    # ---- the agentic creator's steps (agent/creator.py) ------------------------------------------------------------------------------------------
    def judge(self, gid: str) -> dict:
        """The vision judge's pre-review of the stills (it only advises). A judge that cannot run is a skipped check, never a failed run."""
        from ..vision import judge as vj
        self._see(gid)
        try:
            return vj.judge_generation(self.out, int(gid[1:]), "still", allowed=True)
        except Exception as e:
            return {"rejected": [], "approved": [], "unjudged": [], "skipped": str(e)[:200]}

    def pack_add(self, gid: str, name: str) -> dict:
        """Approve what was kept (G2 / G4), approve the final pack (G5) and add it to a new library pack: the Studio's "Add to a pack"."""
        self._see(gid)
        try:
            return gates.quick_add(self.out, int(gid[1:]), self.c.lib, None, name)
        except pl.PipelineError as e:
            raise ToolError(str(e), e.code)

    def packs(self) -> list:
        """The library's packs the person may use for effects (owner only: the effects routes are owner only)."""
        if self.member:
            return []
        return [{"id": p["id"], "name": p["name"], "count": len(p.get("stickers") or [])} for p in self.c.lib.snapshot()["packs"]]

    def effects_start(self, pack_id: str, allowed: bool = False) -> dict:
        """The same call as POST /api/effects: a new E### for every sticker of the pack, analysed in the background (free; `allowed` is the person's yes to AI vision)."""
        import threading
        from ..flow import effects as fx
        if self.member:
            raise ToolError("Particle effects are for the owner's account for now.", 403)
        try:
            e = fx.create(self.out, self.c.lib, pack_id=pack_id, sticker_ids="all", mode="video", grid="2x2", user=self.user["id"])
        except fx.EffectError as ex:
            raise ToolError(str(ex), getattr(ex, "code", 400))
        eid, who = e["id"], self.user["id"]

        def run():
            tok = pl.OWNER.set(who)
            try:
                fx.analyse(self.out, eid, allowed=allowed is True)
            except Exception as ex:
                try:
                    rec = fx.read(self.out, eid)
                    rec.update(status="ERROR", error=str(ex)[:300])
                    fx._write(self.out, rec)
                except Exception:
                    pass
            finally:
                pl.OWNER.reset(tok)
        threading.Thread(target=run, daemon=True).start()
        return {"id": eid, "pack_name": e["pack_name"], "count": len(e["stickers"])}

    def telegram_ready(self) -> tuple:
        from ..services import telegram
        if telegram.status(self.out)["configured"]:
            return True, ""
        return False, "Telegram is not connected."

    def telegram_send(self, pid: str) -> dict:
        from ..services import telegram
        try:
            return telegram.send(self.out, self.c.lib, pid)
        except telegram.TelegramError as e:
            raise ToolError(str(e), getattr(e, "code", 409) if getattr(e, "code", 409) < 500 else 409)

    def ready_indexes(self, gid: str) -> list:
        self._see(gid)
        res = pl.read_result(self.out, int(gid[1:]))
        return [s["index"] for s in res["stickers"] if s["status"] == "READY"]

    def name_proposals(self, gid: str, ask, allowed=None) -> list:
        """Look at the pictures of a batch (the person's yes to AI vision, `allowed`) and propose a better name where one does not fit: [{index, current, caption, fits, name}]."""
        from ..vision import consent, naming
        self._see(gid)
        try:
            return naming.propose(self.out, gid, allowed=allowed, ask=ask)
        except consent.ConsentRequired as e:
            raise ToolError(str(e), 409)

    def apply_titles(self, gid: str, indexes: list | None = None) -> dict:
        """Apply the names that were proposed and are waiting for the person's yes: {index: title}."""
        from ..vision import naming
        self._see(gid)
        return naming.apply(self.out, gid, indexes)

    def pending_titles(self, gid: str) -> dict:
        from ..vision import naming
        self._see(gid)
        return naming.pending(self.out, gid)

    def captions(self, gid: str, allowed=None) -> list:
        """The AI caption of every READY sticker of a batch (one vision-model call per cell that has none; a stored caption is read for free). `allowed` must be True: the
        person's yes to AI vision (vision/consent.py); the chat passes it from the session's `allow_vlm`."""
        from ..vision import consent, transcribe
        self._see(gid)
        try:
            return [c.to_dict() for c in transcribe.captions_for(self.out, gid, allowed=allowed)]
        except consent.ConsentRequired as e:
            raise ToolError(str(e), 409)


class FakeTools:
    """The same interface without a provider or files: what the agent tests drive. `calls` records every spend-capable call."""

    def __init__(self, generations: dict | None = None, live: bool = True, credits: float = 100.0):
        self.gens = generations or {}
        self._live, self._credits = live, credits
        self.calls: list = []
        self.proposed: dict = {}
        self.sent_plans: list = []
        self.plans: dict = {}
        self.fail_next_create = False
        self.judge_rejects: list = []
        self.job_generations: dict = {}
        self.job_status: dict = {}
        self.job_errors: dict = {}
        self.video_estimate = 8.0
        self.telegram = True
        self.n_jobs = 0
        self.n_gens = max([int(g[1:]) for g in self.gens] or [0])

    def live(self):
        return self._live

    def credits(self):
        return self._credits

    def plan(self, prompt, grid, style_id, ai):
        self.calls.append(("plan", prompt))
        words = [w for w in prompt.lower().split() if w not in ("make", "me", "a", "an", "some", "stickers", "sticker", "of", "create")]
        subject = " ".join(words[:3]) or "sticker"
        n = 9 if grid == "3x3" else 4 if grid == "2x2" else 1
        return {"subject": subject, "task_slug": subject.replace(" ", "_"), "grid": grid, "expanded_by": "fake", "template_id": "fake_t", "template_version": 1, "slots": {"subject_description": subject, "style_id": style_id}, "sheet_prompt": f"sheet of {subject}",
                "stickers": [{"index": i, "key": f"{subject.replace(' ', '_')}_{i}", "emoji": ["😀"], "prompt": f"{subject} {i}"} for i in range(1, n + 1)]}

    def engine_label(self, ai=True):
        return None

    def estimate(self, kind="image"):
        if not self._live:
            return None
        return self.video_estimate if kind == "video" else 2.0

    def generation(self, gid):
        card = self.generation_card(gid)
        out = {k: v for k, v in card.items() if k != "stickers"}      # a copy: the fixture is never mutated (a test asserts on its own stickers)
        out["stickers"] = []
        for s in card["stickers"]:                                    # FakeTools: what the chat tile needs to offer an override (the real tools compute it from gates.allow_info)
            st = {k: v for k, v in s.items() if k not in ("allow", "waived")}
            st["allow"] = {"still": {"can": s.get("status") == "FAILED", "allowed": bool(s.get("still_override")), "undo": False,
                                      "why": s.get("reason") if s.get("status") == "FAILED" else None, "final": None},
                          "animation": {"can": s.get("anim_status") == "FAILED", "allowed": bool(s.get("anim_override")), "undo": False,
                                        "why": s.get("anim_reason") if s.get("anim_status") == "FAILED" else None, "final": None}}
            st["waived"] = list(s.get("still_override") or []) + list(s.get("anim_override") or [])
            out["stickers"].append(st)
        return out

    def generation_card(self, gid):
        return self.gens[gid]

    def job(self, jid):
        return {"id": jid, "status": self.job_status.get(jid, "DONE"), "generation": self.job_generations.get(jid), "error": self.job_errors.get(jid)}

    def search(self, q):
        return [{"id": g["generation"] + "/S1", "key": g["stickers"][0]["key"], "png": None, "emoji": None} for g in self.gens.values()
                if q.lower().split()[0] in str(g).lower()]

    def create(self, prompt, grid="3x3", style_id="flat_vector", ai=True, parent=None, regen_of=None, refs=None, base_plan=None):
        if getattr(self, "fail_next_create", False):
            self.fail_next_create = False
            raise ToolError("the provider refused it; try again in a minute", 503)
        self.calls.append(("create", prompt, grid, parent, regen_of))
        if base_plan is not None:
            self.sent_plans.append(base_plan)
        if self._live:
            self.n_jobs += 1
            return {"job": f"J{self.n_jobs:03d}", "task": f"{self.n_jobs:03d}", "estimate": 2.0, "generation": None, "live": True}
        self.n_gens += 1
        gid = f"G{self.n_gens:03d}"
        self.gens[gid] = {"generation": gid, "stickers": [{"id": f"{gid}/S{i}", "index": i, "key": f"s{i}", "status": "READY", "still": "PENDING"}
                                                          for i in range(1, 10)]}
        return {"job": None, "task": None, "estimate": None, "generation": gid, "live": False}

    def generation_plan(self, gid):
        if gid in self.plans:
            return json.loads(json.dumps(self.plans[gid]))
        subj = (self.gens.get(gid) or {}).get("subject") or "subject"
        return {"template_id": "fake_t", "template_version": 1, "subject": subj, "slots": {"subject_description": subj, "style_id": "realistic", "cells": [{"pos": 1, "label": "pose"}]},
                "stickers": [{"index": i, "key": f"{subj}_{i}", "emoji": ["😀"]} for i in range(1, 10)]}

    def more(self, gid):
        self.calls.append(("more", gid))
        self.n_gens += 1
        return {"generation": f"G{self.n_gens:03d}"}

    def animate(self, gid, loop=False):
        self.calls.append(("animate", gid))
        self.n_jobs += 1
        return {"job": f"J{self.n_jobs:03d}", "estimate": 9.0}

    def review(self, gid, decision, indexes, note="", gate="still"):
        self.calls.append(("review", gid, decision, list(indexes)) if gate == "still" else ("review", gid, decision, list(indexes), gate))
        key = "still" if gate == "still" else "anim"
        for s in self.gens[gid]["stickers"]:
            if s["index"] in indexes:
                s[key] = "APPROVED" if decision == "APPROVE" else "REJECTED"
        return {"done": list(indexes), "refused": []}

    def allowable(self, gid, kind="still", allow=True):
        """The blocked stickers a person may allow (or take back): in the fake, every FAILED one of that kind carries no override flag."""
        if kind == "animation":
            return [s["index"] for s in self.gens[gid]["stickers"] if s.get("anim_status") == "FAILED" and not s.get("anim_override") == ()]
        return [s["index"] for s in self.gens[gid]["stickers"] if s.get("status") == "FAILED"]

    def allow(self, gid, indexes, kind="still", allow=True):
        self.calls.append(("allow", gid, list(indexes), kind, allow))
        key = "anim_override" if kind == "animation" else "still_override"
        done = []
        for s in self.gens[gid]["stickers"]:
            if s["index"] not in indexes:
                continue
            if allow:
                s[key] = [s.get("anim_reason" if kind == "animation" else "reason") or "blocked"]
                if kind == "animation":
                    s["anim_status"] = "READY"
                else:
                    s["status"], s["reason"] = "READY", None
                    s["still"] = "PENDING"
            else:
                s[key] = []
                if kind == "animation":
                    s["anim_status"] = "FAILED"
                else:
                    s["status"], s["reason"] = "FAILED", "inside_cell"
                    s["still"] = "BLOCKED"
            done.append(s["index"])
        return {"done": done, "refused": [], "kind": kind, "allow": allow}

    def judge(self, gid):
        self.calls.append(("judge", gid))
        return {"rejected": list(self.judge_rejects), "approved": [s["index"] for s in self.gens[gid]["stickers"] if s["index"] not in self.judge_rejects]}

    def pack_add(self, gid, name):
        self.calls.append(("pack_add", gid, name))
        return {"pack_id": "P1", "added": len([s for s in self.gens[gid]["stickers"] if s["status"] == "READY"]), "kind": "static"}

    def packs(self):
        return list(getattr(self, "pack_list", []))

    def effects_start(self, pack_id, allowed=False):
        self.calls.append(("effects_start", pack_id, allowed))
        p = next(x for x in self.packs() if x["id"] == pack_id)
        return {"id": "E001", "pack_name": p["name"], "count": p["count"]}

    def telegram_ready(self):
        return (True, "") if self.telegram else (False, "Telegram is not connected.")

    def telegram_send(self, pid):
        self.calls.append(("telegram_send", pid))
        return {"sets": [{"kind": "static", "name": "pack_by_bot", "link": "https://t.me/addstickers/pack_by_bot", "added": 9, "total": 9}]}

    def ready_indexes(self, gid):
        return [s["index"] for s in self.gens[gid]["stickers"] if s["status"] == "READY"]

    def name_proposals(self, gid, ask, allowed=None):
        self.calls.append(("name_proposals", gid, allowed))
        if allowed is not True:
            raise ToolError("AI vision is not allowed", 409)
        items = [{"index": s["index"], "current": s["key"].replace("_", " "), "caption": f"fake caption {s['index']}"} for s in self.gens[gid]["stickers"] if s["status"] == "READY"]
        got = ask(items) or {}
        rows = []
        for it in items:
            a = got.get(it["index"]) or {}
            fits = bool(a.get("fits", True)) or not a.get("name")
            rows.append({**it, "fits": fits, "name": None if fits else a["name"]})
            if not fits:
                self.proposed.setdefault(gid, {})[it["index"]] = a["name"]
        return rows

    def apply_titles(self, gid, indexes=None):
        self.calls.append(("apply_titles", gid))
        mine = self.proposed.get(gid, {})
        pick = {i: n for i, n in mine.items() if not indexes or i in indexes}
        for i, n in pick.items():
            for s in self.gens[gid]["stickers"]:
                if s["index"] == i:
                    s["title"] = n
            mine.pop(i, None)
        return pick

    def pending_titles(self, gid):
        return dict(self.proposed.get(gid, {}))

    def captions(self, gid, allowed=None):
        self.calls.append(("captions", gid, allowed))
        if allowed is not True:
            raise ToolError("AI vision is not allowed", 409)
        return [{"index": s["index"], "caption": f"fake caption {s['index']}", "error": None} for s in self.gens[gid]["stickers"] if s["status"] == "READY"]
