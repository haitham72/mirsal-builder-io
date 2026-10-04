# Burst creation: many packs from one liked sheet — PROPOSAL (nothing is built)

**Status: a proposal written 2026-10-03 for P14 of the UI/UX spec, which asked for the model to be stated BEFORE building.** Nothing in this file exists in code. It waits for Haitham's go-ahead
and for the questions in section 6. Until then the chat says "many packs of the same character is not supported yet" (`agent/editroute.unsupported`) and points here.

## 1. What the person does

1. They like a sheet in the chat (the batch in focus; after an edit it is the **fixed sheet**, `source/sheet_fixed.png`).
2. "I need more packs of this character." The assistant **reuses the same image** and prepares a short list of high-level **actions** for it ("playing football", "cooking", "at school", "sleeping").
3. The assistant says what it will make: *"I will create football, cooking, school, sleeping"* with ONE total price, and the person **picks** the actions they want (all, some, or adds their own).
4. Each picked action is expanded into its own sheet (a 3x3 of poses for that action, built from the parent's saved plan with the actions replaced) and sent to Higgsfield **asynchronously**, one queue each.
5. Each finished sheet comes back as a normal batch (cut, checked, gated like any other) and the chat shows them as they arrive, each named by what it is.

## 2. The model: a Burst of lanes (a "queue" is one lane)

There is no per-subject queue today: `generation/jobs.py` is one flat list of jobs, `paid_parallel()` (default 3) is a global limit, and a `tasks` row is one plan. So the new concept is small and
sits ABOVE the existing machinery instead of changing it:

```
out/bursts/B001.json   {id, user, created, parent (G###), image: R### (the sheet sent as the picture), subject, status,
                        lanes: [{n, action, queue: "Q001", status, estimate, job, task, generation, cost, error}], history[]}
```

* A **lane** is one action. Its `queue` id `Q###` is the lane's address in metadata (`B001/Q002`). A lane owns exactly one ordinary sheet job (`jobs.create(kind="sheet")`), so the **ticket-first rule,
  the daily cap, retry, resume and the parallel limit all apply unchanged** — a lane is not a second scheduler. "Async" means: all lanes' jobs are created and handed to `fulfil_async` together;
  `paid_parallel()` decides how many wait at the provider at once, the rest wait their turn.
* The sheet goes as the picture for every lane (case (b) of `agent/editroute.py`: the shape stays, the action changes), with the reference clause of that case.
* **One go-ahead for the whole burst** (rule 13): the card shows each lane and the total; nothing is created before the click; a lane that cannot start is reported and does not cost the others.
* A burst is **addressable by id** and reproducible from its stored data (rule 11): `POST /api/bursts {parent, actions[], go}` (409 with the estimate until `go: true`), `GET /api/bursts/{id}`,
  `POST /api/bursts/{id}/lanes/{n}/retry`. The chat is a client of those, like everything else.

## 3. The name: `{subject}_{action}_{queue}_{datetime}` against rule 9 and `runtime/names.py`

Rule 9 fixes the file name: `{media}-{subject}-{action}[-{pack}]-{UTC time}-{hash6}.{ext}` and **names are never renamed**. The requested metadata is
`{subject}_{action}_{queue}_{datetime}`. These fit if the queue lives in the **metadata**, not in the file name:

| where | what | why |
|---|---|---|
| file name (unchanged) | `img-iron_man-play_football-20261003T101500-a3f9c1.png` | `names.build` already carries subject, action, UTC time and a fingerprint; `names.parse` splits it back. Adding a fifth field would break `parse` for every stored name. The fingerprint is seeded with the generation id, so two lanes never collide. |
| the lane / batch metadata | `subject: iron_man, action: play_football, queue: Q002, burst: B001, datetime: 20261003T101500` | `result.json` of the lane's batch gets `burst: {id, queue, action}`; the Postgres `tasks.name_key` stays the plan's slug. The queue is searchable, never part of an identity. |
| the pack that results | `Iron man · play football` | readable in the Library; the id of the pack stays its own. |
| the lane's address | `B001/Q002` | the same shape as `G103/S2`: an id that survives any rename. |

A "better scheme" was looked for and not found: putting `Q###` in the file name makes names change when a lane is retried or re-queued, which is exactly what rule 9 forbids.

## 4. What it reuses (so the build is small)

`editroute.plan_for(plan, "action", action=...)` (the actions replaced, the poses kept) · `tools.sheet_reference` (the picture) · `jobs.create` / `fulfil_async` / `paid_parallel` (the queue) ·
`Console.live("sheet", ..., base_plan, ref_clause)` (the request) · `start_from_job` (the cut) · the gates (a human approves every lane's stickers as always).

## 5. Risks stated up front

1. **Money.** N lanes are N sheets (about 2 credits each). Mitigations: one priced card, a per-burst maximum of lanes (proposal: 6), the daily cap counts jobs in flight (already true), and a lane is never started without the click.
2. **A per-subject queue does not exist.** This proposal adds a record (`B###`) and an id (`Q###`), not a scheduler; if Haitham wants true per-subject ordering or priorities, that is a different and larger design.
3. **Action quality.** The suggested actions come from a table plus, with the person's yes to AI vision, the sheet itself; a bad suggestion is cheap to drop at the card, expensive after the click.
4. **Partial failure.** A lane fails alone (its job is FAILED, with Retry); the others finish. The burst's status is derived from its lanes, never stored separately.
5. **Chat state.** The assistant must not lose the burst on a restart: it is a file, and the card is rebuilt from it on every poll.

## 6. Questions for Haitham (answers go here, each answer deletes its question)

1. Is **6 lanes per burst** the right cap, and should the cap be a setting?
2. Should each lane become **its own pack** automatically, or only a batch the person adds to a pack (today's gate)? (Proposal: a batch; adding stays the person's click.)
3. May the suggestions use the **vision model** on the sheet (with the one-time AI vision yes), or only the built-in table?
4. Is `B###/Q###` acceptable as the lane id, or should a lane be addressed by its batch (`G###`) only?

## 7. Open: what happens next (former `plan.md` 16.3, P14)

**Nothing is built.** The idea is to reuse a liked sheet, prepare actions and one priced card, then create one async lane per action. Its go-ahead and four choices remain W27 in `waiting-for-haitham.md`. Sticker-owned particle sets, detached retention and ordinary animated-sticker delivery are settled in `particles_plan.md`; per-emoji motion remains W25. Until burst creation is authorized, chat still answers that many packs of the same character are unsupported (`agent/editroute.unsupported`).
