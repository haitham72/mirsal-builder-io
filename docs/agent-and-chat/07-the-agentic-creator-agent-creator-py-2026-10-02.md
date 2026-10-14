# The agentic creator (`agent/creator.py`, 2026-10-02)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

One go-ahead from a request to a sticker pack on Telegram. Since 2026-10-09 the chat's **stage** starts it (Animation: `scope: video`, ending after the animations; Export: `scope: video` to the Telegram send; "Stages and the batch follow-up"); the gear keeps only
**Approve everything for me** (bypass). Stored in the session's `settings.creator = {on, scope, bypass}` (`POST /api/chat/sessions/{id}/settings {creator: {...}}`); `on` and `scope` are only read for a session that has no stage yet (`stages.of`).

With the creator on, a request gets ONE plan card: the price of the whole run (`sheet + animation`, each from the provider's own cost call), "then straight to Telegram", and the buttons "Create and send to Telegram / Not yet". The click is the only go-ahead; after it
the run is a state machine over the `tools` interface (the engine functions the Studio's buttons call): `sheet > cut and check > look at the pictures > approve > [animate > approve the animations] > pack > Telegram`, stored in `sess["creator_run"]` and advanced by
`Agent.creator_tick` (the session's lock, advancing as many steps as are immediately possible), which `Console.drive_creator` calls every 2.5 s in a thread of its own until the run is `done`, `stopped`, `waiting` or `failed` (one driver per chat; the poll of the chat resumes a run after a restart).
Each stop or finish is a message of its own in the chat, with the buttons for what to do next; the card shows the steps. A completed batch with another queued retains its completion message; only the last completed run offers the follow-up. A provider job marked DONE can still be slicing: `anim_status: PROCESSING` keeps the creator waiting until the engine has finished its checks. The verifier and review gates then decide normally.

- **Bypass on**: the person's standing approval is used at G2 (stills), G4 (animations) and G5 (pack); each is a human decision in the batch's history with the note "agentic creator: the person's standing approval". **Bypass off**: the run stops at G2 and G4 and waits for one click
  ("Approve and continue", or typing "continue").
- **Any rejection stops the run, with or without bypass**: a cell Python blocked (judgement calls offer "Use it anyway"; Telegram limits or an empty cell offer an explanation and a way to drop it), a sticker the vision judge would reject (it only advises: "Continue without S2" rejects it by the person's decision, "Continue with them" keeps it),
  an animation Python blocked, a failed job, a sheet Python blocked (with the "Try the sheet again" button; the run follows the new sheet), a Telegram pack the platform would refuse, Telegram not connected (the pack stays in the library; "Try again" sends it). Nothing is deleted.

### Creator overrides and recovery

`_stop_blocked` offers `creator_allow` for the indexes returned by `tools.allowable`, plus skip and stop. Technical blocks explain why they cannot be allowed. `resume` records pending allow/unallow actions; `_run_allows` calls the same free engine override as Studio. `_creator_say` attaches the generation card beside the run card, so the rejected picture and its override are visible. Video-sheet overrides are handled separately by `_stop_sheet`. These controls are built, not a pending creator redesign.

`advance(..., checkpoint=...)` saves before work and after each step, including changes that leave step/status unchanged, such as setting `video_job`. The console's in-process animation call tags the durable job request with `creator_run` and invokes `on_job` after writing the job file but before scheduling provider fulfilment. The callback saves the run's job pointer. If that pointer was not saved, `ConsoleTools.creator_job` can recover the same user's tagged video job on the next tick, without starting a replacement animation. These keywords are internal; HTTP bodies cannot choose a creator tag or callback.

Restart driving still begins on the next chat poll, after the session lock is available. A tagged job left REQUESTED before scheduling, or a failed/timed-out ticket, may still need Queue recovery. This is a checkpoint/link fix, not a guarantee of automatic recovery at every external side effect. Ticket-first protects replay of the same job id; it does not deduplicate a newly created job id. Paid live crash validation remains outstanding.


- **Money**: nothing is spent before the click; the run makes exactly one sheet call and, for `Full video`, one animation call. If the animation's price is more than 25% above the one shown, the run stops BEFORE sending it ("Animate for about N" is the person's new go-ahead). The server-side
  rules remain enforced: `can_spend`, the daily cap for members and unowned jobs (enabled owner/admin accounts are exempt), one paid call at a time, every call in `out/model_calls.jsonl`.
- **Tests**: `tests/test_creator.py` (the state machine on `FakeTools`: the happy path, waiting without bypass, a blocked cell, a vision rejection, a blocked sheet and its retry, a failed job, Telegram down, a price rise, a blocked animation, stop, a second request) and
  `tests/test_creator_live.py` (the real server, the fake Higgsfield CLI and the fake Bot API: a request, one click, nine stickers in a pack on "Telegram"). Not yet run against the real Higgsfield or a real bot: it needs Haitham's go and a spare bot (`docs/waiting-for-haitham.md` W6).
