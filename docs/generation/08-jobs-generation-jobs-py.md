# Jobs (`generation/jobs.py`)

<sub>Part of [generation.md](../generation.md).</sub>

`out/jobs/J###.json` (`REQUESTED|CLAIMED|DONE|FAILED|TIMEOUT`; a job created since 2026-10-04 is labelled `J058-<subject>-<kind>.json` with its files in `J058-<subject>-<kind>/`, the subject from its task, else its batch, else the request's label; the id stays `J058` and `jobs._path` / `jobs.job_dir` find either form; J001-J057 keep their bare names) as before, plus `params`, `cost_estimate` and, for sheets, the `generation` it started. `fulfil(out, jid)`:

1. resolves the selection through the catalog (and refuses references the model cannot take);
2. `generate cost` and the optional daily cap `MIRSAL_DAILY_CREDITS`, checked before payment. Enabled owner/admin accounts with `can_spend` are exempt; members and jobs without a trusted account remain capped;
3. `generate create` **without `--wait`**, then `claim` with the returned id **immediately** (ticket first, mirrored into `out/tasks/NNN.json`);
4. `generate wait`, download the result (`higgsfield.download`: plain HTTPS through the **tolerant TLS context** `telegram._ssl_context()`, which skips a malformed entry in a Windows certificate store; the default context failed with `[ASN1: NOT_ENOUGH_DATA]` on one PC AFTER the job had been paid, which leaves the job `FAILED` with its ticket: **Check** or **Continue** downloads it without a second charge. Telegram, the LLM client, embeddings, tracing and this download all use that one context), `done` (copies it to `out/jobs/J###/result.<ext>`, writes the ledger line with cost, params and the Higgsfield id).

A job already CLAIMED resumes by its ticket and never creates a second paid job: `fulfil` refuses (409) to create for ANY job that holds a stored ticket unless it is CLAIMED, `requeue` of a ticketed job is a `resume` (it waits for the same provider job), and a CLAIMED job whose wait timed out is resumed, not created again. One paid call at a time (a lock in the process and a file lock `out/.paid.lock` across processes): the job is read AGAIN under that lock, so two runs of one job pay once and the loser (`JobBusy`) reports what is true, pays nothing and marks nothing failed; `done()` (the ledger row the daily cap sums) runs under the same lock, so the next call sees this one's spend. `POST /api/live/sheet | video` and the task form of `POST /api/generations` accept `Idempotency-Key` (the Studio sends one per click). Transient wait errors with a ticket exhaust bounded retries into `TIMEOUT`; terminal errors or failures without a ticket end as `FAILED` with the reason.
`Console.fulfil_async` runs it in a thread (or hands it to the durable queue, below); on a finished **sheet** `Console.start_from_job` builds a `Pick` from the result file (the app never writes into the watch folders), starts
the generation linked to the task, and runs the stills; on a finished **video** `attach_video_from_job` attaches and slices it. A video job needs a video sheet **approved at G3**.

### The durable queue and workers (`generation/jobqueue.py`, migration `007_job_queue`)

By default a job is fulfilled by a thread of the server, so a server restart loses the wait and the follow-up. With **`MIRSAL_JOB_MODE=queue`** (and Postgres up) the server only *enqueues* the job
(`job_queue` row `QUEUED`); one or more **`python -m mirsal worker`** processes claim rows (`FOR UPDATE SKIP LOCKED`: two workers never get the same job), run `jobs.fulfil` and mark the row; the
server's ingest loop then follows up every `DONE` row exactly once (`Console.follow_up`: a sheet starts the stills run, a video is attached and sliced), leased for ten minutes so a crash before it
finished just lets the lease run out. Jobs that were finished while the server was down are followed up when it starts.

| row | meaning |
|---|---|
| `QUEUED` | waiting (also after a retry with backoff 30 s, 60 s, ...) |
| `RUNNING` | a worker holds it (`locked_by`, `locked_at`); a row with no finish after the job timeout + 5 min is **reaped** back to `QUEUED` (the ticket in the job file makes the next run resume, not pay again) |
| `DONE` | the job file holds the result; `ingested_at` says the server followed up |
| `FAILED` | **the provider** said no: never retried automatically, because a retry can spend credits; a human retries (`mirsal queue retry J004`, or the Studio's Retry) |
| `DEAD` | **the worker itself** failed `max_attempts` (3) times (disk, a bug): needs a human |

`out/jobs/J###.json` stays the truth for the request, ticket and result; the table only says who runs it and when (`mirsal queue sync` re-enqueues unfinished job files after a database reset).
Workers add durability and isolation, **not paid concurrency**: the paid-call lock is shared, so one paid call runs at a time on the machine however many workers there are.
`GET /api/health` shows the mode and the counts; `mirsal queue status` prints them with the rows that need a human.
