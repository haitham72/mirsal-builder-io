# The AI vision switch (2026-10-03, UI/UX spec P9-P10)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

A one-time decision is not a creation control. The first answer of a chat on the creation path (`CREATION_INTENTS`: never a hello, a fact about the person, a question or a "not yet") shows **Create it** and, on the right, ONE switch **Allow AI vision** with a subtle rotating glow while it is undecided (no "Not yet", no "Keep it off"; a typed "no" still cancels the plan). Pressing it calls the settings route, which writes
state only (`SessionStore.set_vision`): no message, no card, no turn. The next turn proceeds normally and acknowledges the permission once ("AI vision is on, as you allowed…" / "AI vision is off, as you chose…"); a refusal is respected by describe and names. The switch then reads the live setting
and flips on a press; the glow rests under `prefers-reduced-motion`.
