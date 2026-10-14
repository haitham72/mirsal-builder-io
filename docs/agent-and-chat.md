# The agent and the chat: how it is built

The chat is an **interface**; structured state is the system of record. A language model orchestrates the deterministic pipeline and never
generates media or judges pixels. Every reference a user makes ends as an id like `G012/S3`; every change is a new generation with a parent;
the gate rules stay Python's (a human approves, the vision model only pre-reviews, Python's blocks are final).

The chat's backend **is the Studio**: the agent calls the same functions the Studio's buttons call (`Console.live`, `pipeline`, `gates`, search),
through `agent/tools.py`. Nothing is re-implemented.

```
 browser (console/chat-core.js)            server (console/server.py)                 engine
 ─────────────────────────             ──────────────────────────                 ──────
 What will you create today?  ──POST /api/chat/sessions/{id}/messages──►  Agent.prepare (session lock, user + "working" message)
 poll GET /api/chat/sessions/{id}      thread: Agent.execute ─► LangGraph:  understand → resolve → intent nodes → finish
 (steps appear as they are written)               │   tools: plan · estimate · create · animate · review · search · generation
 plan card · carousel · chips                     └──────────────► Console.live / pipeline / gates  (jobs, Higgsfield, verifier, gates)
```

## Sections

This is an index: each section is its own file under [`agent-and-chat/`](agent-and-chat/); read only the one a task needs.

| section | what it covers |
|---|---|
| [Files](agent-and-chat/01-files.md) | Paths below are relative to the repository root. |
| [One turn](agent-and-chat/02-one-turn.md) | 1. `understand`: rules first (`classify`); a model only when confidence is under 0.6. Intents: `NEW, ANOTHER, EDIT_STICKERS, UNDO, ANIMATE, EXPORT, FEEDBACK,… |
| [Memory](agent-and-chat/03-memory.md) | A session is `{id, title, settings, focus, subjects[], preferences, feedback[], interactions[], summary, pending, messages[]}`. |
| [The step trace](agent-and-chat/04-the-step-trace.md) | The small queue the chat shows while the agent works (`message.steps[]`, `{kind, label, detail, status}` with kind `task / step / note / final`): |
| [The screen (`#/agent`, the landing page of the Studio shell)](agent-and-chat/05-the-screen-agent-the-landing-page-of-the-studio.md) | Hero: "What will you create today?" over a cyan aurora that follows the pointer (a dot grid appears under it; reduced motion switches the ambient motion off). |
| [Models (`services/llm.py`)](agent-and-chat/06-models-services-llm-py.md) | `MIRSAL_LLM_PROVIDER`, `MIRSAL_AGENT_PROVIDER`, `MIRSAL_VISION_PROVIDER` (`local / openai / auto`) pick the backend per use. `MIRSAL_LLM_PROVIDER=none / open… |
| [The agentic creator (`agent/creator.py`, 2026-10-02)](agent-and-chat/07-the-agentic-creator-agent-creator-py-2026-10-02.md) | One go-ahead from a request to a sticker pack on Telegram. Since 2026-10-09 the chat's stage starts it (Animation: `scope: video`, ending after the anima… |
| [Stages and the batch follow-up (`agent/stages.py`, 2026-10-09)](agent-and-chat/08-stages-and-the-batch-follow-up-agent-stages-py-2.md) | The slider is one per person and a boundary both ways (Haitham, 2026-10-11). Six stops: Auto (the default) · Prompt · Stickers · Animation · Telegram ·… |
| [The chat in Telegram (`services/tg_chat.py`, 2026-10-09)](agent-and-chat/09-the-chat-in-telegram-services-tg-chat-py-2026-10.md) | The same agent, on the bot already configured in Settings (the admin cards' bot; `admin_bot.start` long-polls it, only under `serve --lan`). Every private |
| [The vision judge (`mirsal/vision/`)](agent-and-chat/10-the-vision-judge-mirsal-vision.md) | A pre-reviewer, never the gate. `python -m mirsal judge G002 [--anim] [--force]` (or `POST /api/generations/{id}/judge`): each READY sticker is shown on a grey |
| [Redis (disposable; `mirsal-redis`, port 6380)](agent-and-chat/11-redis-disposable-mirsal-redis-port-6380.md) | Everything here can be rebuilt from files and Postgres; `FLUSHALL` costs cache misses plus the short-lived state below. With Redis down, `mirsal/runtime/cach… |
| [Events and SSE](agent-and-chat/12-events-and-sse.md) | `pipeline.emit` writes `events.jsonl` (the record) and publishes the same event under the Phase 5 names: `generation_started, sheet_generated, sticker_proces… |
| [Tests](agent-and-chat/13-tests.md) | `tests/test_chat_interaction.py` (the reported description/display sequence, still evidence, consent, streamed deltas, replacement scope and unclear edits),… |
| [Conversation quality pass (2026-10-02, from the six reviews)](agent-and-chat/14-conversation-quality-pass-2026-10-02-from-the-si.md) | Rules, in `agent/resolver.py` and `agent/graph.py`; guarded by `tests/test_chat_quality.py` (every test is a sentence that went wrong): |
| [Person references, edits that reuse the parent prompt, undo (2026-10-03)](agent-and-chat/15-person-references-edits-that-reuse-the-parent-pr.md) | Code: `agent/resolver.py` (`PERSON_REF`, `LAST_PERSON`, `beyond`, `UNDO_RX`), `agent/editroute.py` (`delta_of`, `add_to_label`, `fresh_take`, the `like` clau… |
| [Several subjects, per-subject feedback, taste (2026-10-03)](agent-and-chat/16-several-subjects-per-subject-feedback-taste-2026.md) | Code: `agent/subjects.py`, `agent/refine.py`, `agent/profile.py`, nodes `n_multi` / `n_refine` in `agent/graph.py`; guarded by `tests/test_chat_multi.py` and… |
| [The bar under the chat box (2026-10-03)](agent-and-chat/17-the-bar-under-the-chat-box-2026-10-03.md) | `drawBar` (`chat-core.js`) paints the bar into `#ag-bar` (the style chip `.ag-cur` and the sheet size) and the style tiles into `#ag-styles`. |
| [Particle sets in the chat (2026-10-04)](agent-and-chat/18-particle-sets-in-the-chat-2026-10-04.md) | `resolver.particles_intent` selects make, more, link/assign, render/add, delete or restore. The node is `Agent.n_particles`; tools call `flow/particle_sets.p… |
| [Reference roles in numbered edits](agent-and-chat/19-reference-roles-in-numbered-edits.md) | `resolver.resolve` already records reference roles. Numbered edits now attach references whose target is the edited sticker or unspecified, and `reference_ro… |
| [Edits by what they mean (2026-10-03, UI/UX spec P11-P13)](agent-and-chat/20-edits-by-what-they-mean-2026-10-03-ui-ux-spec-p1.md) | `agent/editroute.py` (pure, rules only) reads every request about what is open into exactly one of: the editor, or a regeneration of one of three kinds.… |
| [The AI vision switch (2026-10-03, UI/UX spec P9-P10)](agent-and-chat/21-the-ai-vision-switch-2026-10-03-ui-ux-spec-p9-p1.md) | A one-time decision is not a creation control. The first answer of a chat on the creation path (`CREATION_INTENTS`: never a hello, a fact about the person, a… |
| [Support (Help & Support; `flow/support.py`, `flow/support_kb.py`, `flow/faq.py`, `flow/notifications.py`, `console/support.js`; 2026-10-05)](agent-and-chat/22-support-help-support-flow-support-py-flow-suppor.md) | Help is where a person describes a problem in their own words. The support agent answers from what is documented, and a person takes over when that is not en… |
| [Manual emoji batches](agent-and-chat/23-manual-emoji-batches.md) | Paste exactly nine emojis in AI chat, optionally with a subject or the name of an owned pack. The agent checks repeats against stickers saved in that pack an… |
