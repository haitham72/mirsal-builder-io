# Live generation: how it is built

A typed request defaults to a 2×2 sheet of 4 stickers made by Higgsfield, and an approved video sheet becomes a Kling animation. Explicit 3×3 remains available. Both go through the **unchanged** engine and review
gates; the file store is the primary state (Postgres mirrors it). Converged 2026-10-21 (branch `code-audit`); history lives in git.

```
request ─(prompt template v3 + style + stroke [+ AI enhancer] [+ references])─► task (G1 approval)
        ─► sheet job ─► Higgsfield CLI (Nano Banana 2, 2k) ─► out/jobs/J###/result.png
        ─► Pick(sheet) ─► the unchanged stills run ─► G2 ─► video sheet (G3) ─► video job ─► Kling v3.0 ─► attach + slice ─► animations ─► pack
```

## Prompts (template-locked)

A saved template per grid (`sheet_3x3`, `sheet_2x2`, `single_1x1`, `video_independent` v2) is filled from a small slot JSON; nobody free-writes a prompt. New plans are v3 image (`TEMPLATE_VERSION=3`) + `video_independent` v2: each occupied cell gets a natural two-action narrative with an optional third payoff (3×3 cells labelled correctly; detached gesture hands allowed for explicit face gestures; exact first-frame return only with Loop). Face-only v4 auto-detects (`EMOJI_WORDS`); presets drive bank grids (core-v1 default for faceless 3×3); every cell carries motion. The AI enhancer is off by default, never runs while typing, and falls back with a reason on failure. Custom sheet/video prompt path (`apply_custom`, `with_expressive`); transformations ("dog as banana") via the registry + lexicons. New template **versions** only (add `_v5`, never edit one that was used).

## Higgsfield and Kling (the CLI)

`generation/higgsfield.py` is a thin subprocess wrapper — `account`, `cost`, `create` (WITHOUT waiting, returns the job id), `wait`, `download` — that never sees an auth token; tests set `MIRSAL_NO_REAL_CLI`. Catalog (`model_catalog.py`): Nano Banana 2 at 2k default for sheets, Kling v3.0 **pro-only** for animation (std/4k never offered), Grok 1080p options. Text-only video (burst clips, no start image) starts and ends empty. S0-era numbers, the "async untested" note and the one-at-a-time caution are history.

## Jobs (ticket-first)

`out/jobs/J###[-label].json` (`REQUESTED/CLAIMED/DONE/FAILED/TIMEOUT`, written at `claim` before waiting) + folder. Create → claim immediately → wait; resume-by-ticket refuses a second creation (409), so a crash never pays twice. Paid creation is serialized; waits run parallel up to `MIRSAL_PAID_PARALLEL` (default 3, max 8); the daily cap counts in-flight CLAIMED/TIMEOUT jobs. `MIRSAL_JOB_MODE=queue` + `mirsal worker` drains the durable queue (Postgres `job_queue`, migration 007). Commands: `mirsal prompt …`, `mirsal jobs`, `mirsal job …`, `mirsal hf status / models / run J###`.

## Credits and usage

Every paid or model call is a line in `out/model_calls.jsonl` (what, model, params, cost, latency, provider id, output). `usage.summary` rolls it up by model/kind/request; `spent_today` feeds the cap; the balance caches 6s. Enabled owner/admin accounts with spending permission are exempt from the daily cap (resolved from the persisted job user); everyone else needs the price shown + a go-ahead.

## Operator runbook

Generate → fulfil runs in the background; the Queue panel (bottom-left, next to the credits) shows running/failed. A stalled job: **Refresh** (free, local) → **Check** (free, one provider `get`; a DIVERGENCE is recorded) → **Continue** (same ticket) → **Retry** (SPENDS: priced, confirmed). TIMEOUT keeps its ticket; FAILED without a ticket is final; 5xx-while-waiting retries on the same ticket. A manual download completes its failed job (provider id match, no second charge). When Higgsfield is connected, a request naming a prepared subject is served from the watch folder instead of paid (signature-word match, grid must match). Loop defaults off; Gap is the `slot_fill` slider; edge preview/apply/undo + reslice from the stored video (no credits).

## Studio surface (additive)

Composer (Generate menu, references, style, loop, enhancer, outline), queue, edge controls, earlier batches — every control calls one API route. `Allow anyway` (`anim_override`/`still_override`) waives `OVERRIDABLE` blocks on recut. Never write inside the watch folders; `reveal`/`files` endpoints open them.
