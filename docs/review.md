# Seeded review of Mirsal Builder (single baseline; latest audit 2026-10-03, `better_ui/ux` @ `d49ab39`)

> This is the ONE review file an auditing LLM reads. It consolidates the
> 2026-10-02 audit (with its triage and status-a-day-later table, preserved in
> the appendix) and the 2026-10-03 code audit (the live body below, §§1-8).
> History lives in git. A new audit does not create a dated file: it reads this
> file, re-verifies every claim and finding against the code, updates the tables
> in place, and appends a dated entry to the log at the end (§9) recording what
> changed (NEW / fixed / confirmed / refuted).
>
> Method note (owner-directed, 2026-10-03): a code audit, not a test run. The
> long suites were not run at all (`unittest discover`, `node --test`,
> `tests.test_js`, `mirsal test slow`). Counts below are by reading code plus
> small `python -c` / `grep` probes. No provider was reached, no secret opened,
> no media opened to judge it. Branch reviewed: `better_ui/ux` at `d49ab39`
> (dirty: ~36 tracked files modified + 4 new source files; `out/` data churn
> excluded).

## 1. Verdict

**Ship with changes — sandbox-verified, not browser-verified.** The engine core holds: 44 verifier checks confirmed by running code, `OVERRIDABLE` exactly as documented, ticket-before-wait and price-before-click true on the sheet path, vision `FAIL_CLOSED` true, and the new waiver/edit/particle-set machinery is well-shaped. The three things that decide it: (1) **money is not double-spend safe on the particle/burst paths** — they accept no `Idempotency-Key` so a double-click pays twice (BLOCKER); (2) **a READY-but-unapproved sticker can reach a pack and Telegram** without G2/G4/G5, and an edited sticker keeps its old APPROVED verdict (both HIGH); (3) **the uncommitted UI work breaks the browser right now** — `/ui/job-recovery.js` 404s and `JR.*` calls in three shipped screens throw (HIGH). Below that sit the already-listed G3 no-override gap (HANDOFF §0, correctly tracked — finish it per that spec, don't re-debate it) and a set of real but narrower races: `allow_animations` unserialized, long slicers overwriting mid-slice reviews, settings route without the session lock, crash between `hf.create` and `claim`, price drift between estimate and `fulfil`. Nothing here says the architecture is wrong; the burst proposal is honest and worth building once Haitham answers its §6. Do not call anything verified until the §0 browser look (P1-P13 + particle screens + creator) is done on a scratch copy of `out/`.

## 2. What was run

2026-10-03 (code audit only, per owner):

```
git log --oneline -15 ; git rev-parse --abbrev-ref HEAD ; git rev-parse HEAD ; git status --short  → better_ui/ux, d49ab39, ~36 M + 4 new (job-recovery.js, recovery.py + tests) [RAN]
./venv/bin/python -c "from mirsal.engine import verify; ..."  → 44 total {sheet:6 still:12 slot:3 anim:13 video_sheet:2 video:4 pack:1 telegram:2 telegram_set:1}; OVERRIDABLE still:(blank_cell,foreground,inside_cell,no_spill,holes) animation:(inside_slot,cross_slot,loop_seam) [RAN]
grep -rn "psycopg|redis|langgraph|fastapi|pydantic|openai|anthropic" mirsal/mirsal/engine/  → NO HITS [RAN]
grep -c "read_result|write_result" + grep "@serialized" / grep "ACT\." / grep "data-act" / git ls-files mirsal/out | wc -l  → pipeline:49 gates:39 server:17; 5 fns serialized; 282 ACT defined / 276 data-act used / 0 used-without-handler; out/ 1464 tracked files [RAN]
./venv/bin/python -c "from mirsal.console import openapi; ..."  → 149 ops / 137 paths [RAN]
```

Deliberately not run (owner instruction): `python -m mirsal doctor`, `python -m unittest discover -s tests -t .`, `node --test tests/js/*.test.js`, `python -m tests.test_js`, `mirsal test fast/area/slow`, any spare-port server. Reference counts (~1025 Python / 151 node / 18 test_js) are CANNOT TELL here.

2026-10-02 (for the record; the only suite run to date): `doctor` ready; verifier count 44; `unittest discover` ~350 tests with 2 FAIL; `node --test agent.test.js` 9 pass; spare-port server not attempted (suite hung on `test_jobs` past 5 min).

## 3. Claims C0-C26 (live contract; re-verify every audit)

| # | Verdict | Standing | One-line evidence |
|---|---|---|---|
| C0 44 checks + OVERRIDABLE exact | VERIFIED [RAN] | confirmed 10-02 + 10-03 | `mirsal/mirsal/engine/verify.py:101-109` catalogue sums to 44; `verify.py:30-33` OVERRIDABLE exact |
| C1 judgement-block allow-able on every surface | REFUTED as universal [READ] | open, HANDOFF §0 | still/anim allow-able `flow/gates.py:329-330,345-361,378-391,541-613`; G3/video `no_outline_on_sheet,slots_match_approved,video_specs,layout_match` BLOCK final `gates.py:198-199,280-281,712-721`, no `allow_sheet` |
| C2 sheet layout never stops sheet | VERIFIED [READ] | confirmed | `SHEET_FATAL={sheet_decodes}` / `SHEET_PROCEED={grid_detected,sheet_size}` `flow/pipeline.py:363-364`; layout→WARN per sticker `:438-440`; `background_is_key` one-click `recut` `:474-491` |
| C3 vision never changes review.*, FAIL_CLOSED | VERIFIED [READ] | confirmed | `vision/judge.py:398` writes `judge/judge_anim` + hist only, reads review at `:373`; `FAIL_CLOSED` `:90-92`; `JudgeError→UNJUDGED` `:312-315,336` |
| C4 agent never spends w/o go-ahead; yes scoped | PARTLY [READ] | new bug 10-03 | typed-yes whole-message only `agent/resolver.py:229-243,337-340`; spend gated `agent/graph.py:379-387,1000-1006,1114-1122`; BUT `n_confirm` clears `pending` before animate/creator/describe/particles (`graph.py:541`, only create restores `:535-539`) — refused animate loses plan |
| C5 particles/bursts priced; cap counts in-flight; ticket first | PARTLY [READ] | new gaps 10-03 | price-first `flow/effects.py:197-204,518-525`, `flow/particle_sets.py:412-440`, `console/server.py:1189-1191,1259-1260`; parallel default 3 + inflight `generation/jobs.py:260-265,312-323,406`; ticket `jobs.py:408-409`; BUT particle/burst routes take no idem key, estimate→charge can drift, crash create→claim loses ticket (see F1-F3) |
| C6 engine import-clean; test would catch | PARTLY [RAN+READ] | weakness persists | code clean today (grep NO HITS); test `tests/test_store.py:248-252` imports 2 of ~10 engine modules, omits `openai`, runtime-only |
| C7 append-only history; S# stable; put refuses overwrite | VERIFIED [READ] | confirmed | `hist` append-only `flow/pipeline.py:332-335`; S# by position `engine/sheet.py:74-83`, `pipeline.py:300-305,631-634`; `LocalAssetStore.put` refuses different bytes `store/assets.py:65-76`; mirror `repo.py:119-244` upserts state by design, history append-only |
| C8 one writer of result.json | PARTLY [RAN+READ] | admitted gap | `_IO_LOCK` `pipeline.py:76`, exactly 5 fns `@serialized`; cross-process `runtime/writer_lock.py` held by serve+CLI; paid jobs separate `.paid.lock` `jobs.py:330-332`; HANDOFF admits two request threads interleave; long slicers write per-cell unserialized |
| C9 foreign page cannot drive server; /out/ cannot escape; member isolation | PARTLY [READ] | guards real, vectors untested | `_foreign` `console/server.py:700-716`, `_who` `:718-728`, `_authorize` `:730-765`, `/out/` resolve-check `:1101-1109`, `_clean` `store/assets.py:30-48`, HMAC `compare_digest` `:99-114`; tests pin symlink+`..`+`%2e` only — ADS/short-name/drive forms untested |
| C10 secrets never returned/logged; trace sends no media/paths | PARTLY [READ] | new gap 10-03 | token `services/telegram.py:59-62,133-134,185,192`, LLM key `services/llm.py:49-54,509,516,369-372`; `safe()` `obs/trace.py:87-102`; BUT `end()` ships `error` raw `:192-195`, `feedback()` ships `comment` raw `:210-215`, POSIX regex misses `/etc /data /app` `:77-78` |
| C11 idempotency incl. concurrent | PARTLY [READ] | new gap 10-03 | sequential true `server.py:457-480`, `store/idem.py:14` 24h, wired `:1485,1516-1517,1571,1601`, paid-creation lock `jobs.py:327-336`; BUT concurrent dup → 409 "still running" not first answer, particle routes no key |
| C12 Redis disposable; fallback same semantics | PARTLY [READ] | overstatement persists | disposable true `runtime/cache.py:67-69`, `runtime/events.py:38-52`, lock TTL 5min `cache.py:196`; BUT rate window restarts at 1 after death, memory locks/streams per-process, Postgres idem half covers real `out/` only |
| C13 memory structured not history | VERIFIED (bugs as described exist) [READ] | confirmed | subjects/feedback/focus `agent/memory.py:7-14`, `_cap` never trims subjects `:96-107`, `reduce` rewrites narrative only `:382-398` (tail kept, not END-trim); `context()` `:366-370` has zero callers; fresh batch `focus.stickers=[]` `graph.py:508,668,990,1587-1588` |
| C14 model text never trusted as HTML/instruction | VERIFIED [READ] | confirmed | `esc`+`md` `console/agent.js:6-8`, `AIU.esc` at `:138,242-243,256,261-262`, `AIU.md` at `:151`; `DATA_RULE`+`fence()` `services/llm.py:61-72`; intent/number whitelists `agent/brain.py:156,165-166` |
| C15 verifier crash→BLOCK verifier_error; fixtures | VERIFIED [READ] | confirmed | `except→BLOCK verifier_error` `engine/verify.py:172-174`, never waived `:128,152`, `gates.py:337-338,388`; fixture method name-only `tests/test_verify_gaps.py:175-183` (self-admitted) |
| C16 migrations re-runnable, never wipe | VERIFIED [READ] | confirmed | `IF NOT EXISTS` everywhere `001_init.sql`; `005_vectors.sql:5-14` guarded no-op; `store/db.py:67-80` + `vector_notes`; `ON CONFLICT DO NOTHING` `store/repo.py:95-97,155-157,190-192` |
| C17 pool never returns closest junk; search_text never filename | VERIFIED with one exception [READ] | new wart 10-03 | `subject — action — key — emoji — style`, "never the file name" `store/pool.py:72`; weights `0.5/0.4/0.1` `:218`; gates `:215-216`; `DUP_SIM=0.97` `:22` dead — actual collapse exact-match `:269-270`, comment overclaims |
| C18 creator can always get past a block | VERIFIED [READ] | hardened since 10-02 | `_stop_blocked` `agent/creator.py:76-91` (`allowable`→`Use it anyway`, else "Telegram's own limits"); free background recut `:94-105`; pictures on stop `graph.py:484-487` + bulk per kind `agent.js:223-227`; `waiting` card alone without picture = LOW gap |
| C19 particle model matches plan | VERIFIED [READ] | built after 10-02 | packs validated `flow/particle_sets.py:119-132`, standalone `[]` `:353-365`, append set `:477-489,509-558`, unpick never deletes `:732-759`, FAILED iff Telegram-limit `engine/effect_video.py:27,146-158` + `effects.py:386-387`, in-use delete 409 `:814-828`, restore same id `:831-843`, `for_pack` `:208-225` |
| C20 cropped sprites not stickers; edit rebuilds one sheet same S# | PARTLY [READ] | new 10-03 | crop true `flow/pipeline.py:755-779`, sprite flag `particle_sets.py:255-260`; pack-guard true `media/library.py:401-405`; edit in-place same name/S# `:817-848`, orig kept `:832-835`; BUT `sheet_fixed` write-only — `recut` `:480-483` / `recut_cells` `:525-530` never read it |
| C21 edit router classifies before generating | VERIFIED [READ+RAN] | built after 10-02 | redesign/action/tweak/editor `agent/editroute.py:96-109`; picture rules `:129-131`, `REF_CLAUSES` `:121-126`; `graph.py:1072-1078,1102-1105`; 400px min `agent/tools.py:227,248-252`; unsupported `:78-85`; "happier" no-sticker → whole-sheet tweak + documented `docs/agent-and-chat.md:334` |
| C22 vision consent is state never turn | VERIFIED [READ] | built after 10-02 | `set_vision` no message/card/turn `agent/memory.py:322-329`, `server.py:1498-1499`; first answer Create+Allow `graph.py:1572-1580`; toggle silent `agent.js:289,170-172,135`; `consent.py:14-16` |
| C23 one click one meaning; sheet never opens; id never in name | VERIFIED (code) [READ] | built after 10-02 | one `ACT.gcell` (`generate.js` via `cellOp`→`cellRun`); `issueSvg` rects only `data-act=gcell` `:137-149`; keyboard handler present; caption `t.key` only, id separate hover-copy `agent.js:261`; docs contradict (see F-doc) |
| C24 no dead stubs; guard covers handlers | PARTLY [READ+RAN count] | new break 10-03 | 282 ACT / 276 data-act / 0 used-without-handler; `tests/test_js.py:52-61` proves button→handler only; live break: `/ui/job-recovery.js` 404 + `JR.*` in 3 screens throws (HIGH) |
| C25 doctor is the single check, every area extends it | PARTLY [READ] | new gap 10-03 | `cli.py:788-917` + `runtime/health.py:65-75` cover old areas; nothing reports particle sets (863 lines, 14 routes), bursts, job-recovery |
| C26 API contract stable + honestly documented | PARTLY [READ] | confirmed | spec served `console/openapi.py:87-246` (149 ops/137 paths), `server.py:985-987`; reverse probe `tests/test_openapi.py:81-133` fails only on `NO_ROUTE`, skips 2, passes 500/403; docs group families not enumerate (~47/137 paths narrative-only); `/api/v1` alias + tracing headers undocumented |

## 4. Findings (most severe first; cap 25)

### F1 — Particle/burst double-spend: no Idempotency-Key [BLOCKER, READ]
Where: `mirsal/mirsal/console/server.py:1159-1166`, `:1266-1277`, `:1241-1263`; contrast `:1516-1517`. What: two rapid `go:true` clicks / two tabs / retry-after-timeout mint two `jobs.create` (`flow/effects.py:206-219`, `particle_sets.py:451-461`) and `fulfil` charges per job. Repro (no spend): fake CLI, two concurrent `more`+`go:true` with one key → today two `J*`; want one `J*` + `idempotent:true`. Fix: wrap all three in `c.idem()` with scope `f"particles:{kind}:{plan-id}:{digest(grid,picks,model,options)}"`, same 24h semantics as `live:`. Pin: concurrent same-key test asserting one `J*`.

### F2 — READY-but-unapproved sticker reaches pack + Telegram [HIGH, READ]
Where: `mirsal/mirsal/media/library.py:406-409`, `mirsal/mirsal/console/server.py:1361-1364`, `mirsal/mirsal/services/telegram.py:321-340`. What: READY+PENDING (or REJECTED-but-READY) enters a pack and ships without G2/G4/G5. Repro: READY+PENDING sticker → `POST /api/packs/{pid}/stickers` → today 200; want 409. Fix: require `review.still/anim == APPROVED` (or G5-final `add_final`) in `add_from_generation`, or gate route by role+explicit confirm. Pin: that 409 test + `telegram.send` refusal test.

### F3 — Edited pixels keep old APPROVED verdict [HIGH, READ]
Where: `mirsal/mirsal/flow/pipeline.py:817-848`, `:631-684` (propagates `:681`). What: edited sticker flows to pack/Telegram unjudged. Repro: APPROVE → edit → today `review` still APPROVED; want PENDING + re-check. Fix: reset affected `review` to PENDING + re-run applicable checks (or require re-approve before `final_indices`/pack). Pin: approve→edit→assert reset + pack refuses until re-approved.

### F4 — Uncommitted `/ui/job-recovery.js` 404s; `JR.*` throws in 3 screens [HIGH, READ]
Where: `mirsal/mirsal/console/index.html:27` vs `console/server.py:33` `UI_FILES` (`:937-939`); callers `console/agent.js:196`, `console/live.js:99-100,152`, `console/generate.js:511`. What: failed chat card / queue row / job poll becomes `ReferenceError`, not degraded panel. No test pins `index.html` scripts ⊆ `UI_FILES`. Fix: add `"job-recovery.js": "text/javascript"` to `UI_FILES` + servability test; consider `typeof JR!=='undefined'` guards. Pin: that servability test.

### F5 — Crash between `hf.create` and `claim` loses a paid ticket [HIGH, READ]
Where: `mirsal/mirsal/generation/jobs.py:408-409`; recovery ticket-keyed `generation/recovery.py:13-18,64-73`, `jobs.py:228-240`. What: provider job exists and will charge, file has no `external_task_id`, only path is fresh paid `retry`. Fix: write `creating` marker before `hf.create`, clear at `claim`; `reconcile` surfaces markers older than N min as "possibly charged — check dashboard". Pin: fake `create`→raise-before-`claim` → marker exposed, `requeue` refuses silent re-create.

### F6 — Shown price can drift before the charge; only Retry pinned [HIGH, READ]
Where: quote `console/server.py:1171-1192`, charge `generation/jobs.py:402-410` (re-prices, no comparison); guard only when `approved_cost` set `:403-404`, set only by Retry `generation/recovery.py:98-109`. What: provider reprice between estimate and `go:true` (or `live()`→worker `fulfil` in queue mode) charges an unapproved number. Fix: store `approved_cost` (= confirmed estimate) on every sheet/video job and keep `:403-404` enforcement on all paths. Pin: fake `cost` changing estimate→fulfil → 409 "price changed", zero `create`.

### F7 — `allow_animations` (+ `allow_cells`) unserialized; concurrent allows lose one [HIGH, READ]
Where: `mirsal/mirsal/flow/gates.py:540` vs `:564`; write at `:596`. What: concurrent still+anim allows interleave; second write drops first. Fix: add `@pl.serialized` to `allow_animations` (and `allow_cells`). Pin: two-thread still+anim test asserting both overrides survive.

### F8 — Long slicers overwrite mid-slice human reviews [HIGH, READ]
Where: `flow/gates.py:695-753` (`:743,745,750`), `flow/pipeline.py:368`, `:1009` (`:1040,1044,1048`), `gates.py:241`, `:653`. What: job holds `res` in closure, rewrites whole file per cell; mid-slice review lost on next cell write. Fix: hold `_IO_LOCK` for the job or re-read+merge before each per-cell write. Pin: start `slice_video` on fakes, inject `review` mid-run, assert survival.

### F9 — Settings route has no session lock; mid-turn toggle overwritten [HIGH, READ]
Where: `mirsal/mirsal/console/server.py:1486-1507` vs `agent/graph.py:150-173`. What: ask-before-spending turned ON mid-turn is reverted to OFF by the turn's next save, then creates without asking. Fix: wrap settings handler in same lock. Pin: concurrent turn+settings test asserting survival.

### F10 — G3 video-sheet blocks have no "Use it anyway" [HIGH, listed-open in HANDOFF §0, READ]
Where: `mirsal/mirsal/engine/verify.py:30-33` + `flow/gates.py:198-199,280-281,712-721`. What: contradicts rule 10; HANDOFF §0 already specs the fix (`gates.allow_sheet` + waive in `slice_video` + per-surface buttons + bulk). Fix: build exactly that spec. Pin: `test_g3_allow.py` per HANDOFF.

### F11 — Concurrent identical Idempotency-Keys get 409, not the first answer [MEDIUM, READ]
Where: `console/server.py:467-480`; `runtime/cache.py:195-225`. What: second caller must special-case 409; queue mode both pass memory lock. Fix: on `Busy`, bounded-wait for winner's record (~30s) then replay; document per-process-without-Redis. Pin: two threads same key slow `fn` → identical bodies, `fn` once.

### F12 — Two tracing sinks bypass `safe()`; path scrub misses roots [MEDIUM, READ]
Where: `obs/trace.py:192-195`, `:210-215` vs `:183-189`; regex `:77-78`. What: pasted path / wrapped `OSError` leaves the machine in `comment`/`error`. Fix: `safe()` both sinks; extend `_POSIX_PATH`; test `reason="/etc/super/secret/x.png"` through fake LangSmith asserting `<path>/x.png`. Pin: that round-trip test.

### F13 — `sheet_fixed` is write-only; next cut silently reverts the edit [MEDIUM, READ]
Where: writer `flow/pipeline.py:782-813`; readers `recut:480-483`, `recut_cells:525-530`. What: later "Cut it anyway"/recut reverts to unedited sheet. Fix: `recut`/`recut_cells` prefer `sheet_fixed` when present + `source.sheet_from` history, or downgrade docs (`docs/api.md:152`) to display-only. Pin: edit S1 → recut → edited pixels, S# unchanged.

### F14 — `/out/`+`/lib/` guards untested for ADS/short-name/drive forms [MEDIUM, READ]
Where: `console/server.py:1101-1109`, `:953-957`; tests only symlink+`..`+`%2e` `tests/test_hardening.py:190-220`; `/out/` handler doesn't use `assets._clean` (`store/assets.py:30-35`). What: `C:/`, `file::$DATA`, 8.3 names reach `resolve()` semantics never asserted. Fix: `_clean`-style rejection before `resolve()` + Windows-gated evil-path table. Pin: parametrized non-200 + no-leak test.

### F15 — `n_confirm` pending-clear asymmetry (non-create paths lose plan) [MEDIUM, READ]
Where: `agent/graph.py:541` vs `:535-539`, `:555-557`. What: refused animate loses plan. Fix: clear-after-success for all. Pin: FakeTools animate raises → pending retained.

### F16 — Fresh batch leaves `focus.stickers=[]`; "it / number 3" hits old batch [MEDIUM, READ]
Where: `agent/graph.py:508,668,990,1587-1588` + `agent/resolver.py:177-179`. "Him/her" fixed (`resolver.py:276,361`); bare `last guy→S9` fixed (`:53`). Remaining: seed focus from latest gen in `_finish` or fall back. Pin: create G013 then `it` → G013.

### F17 — Session lock 5min outlives dead server; chat stuck "Thinking" [MEDIUM, READ]
Where: `runtime/cache.py:196` + `graph.py:156-157`. What: dead Redis holder blocks chat 5 min; turn >5min loses message. Fix: shorter TTL + heartbeat/extend. Pin: hold lock, kill, assert 409 window + recovery.

### F18 — `max(id)+1` chat reuse drops Postgres rows [MEDIUM, READ]
Where: `agent/memory.py:77` + `:143-148` + `store/repo.py:589,603` (`ON CONFLICT DO NOTHING`). What: create→delete newest→create reuses Sid, new rows silently dropped. Fix: monotonic counter never reuse. Pin: row-count-grows test.

### F19 — Delete-during-turn resurrects chat [MEDIUM, READ]
Where: `agent/memory.py:143-148` + `graph.py:1613`. What: delete unlinks, final save recreates. Fix: exists-check/tombstone before final save. Pin: delete-during-turn → 404 persists.

### F20 — Engine boundary test weak [MEDIUM, READ+RAN]
Where: `tests/test_store.py:248-252` (2 of ~10 modules, watches `anthropic` not `openai`, runtime-only). Code clean today (grep NO HITS). Fix: subprocess-import every `mirsal.engine.*` + static banned-name assert. Pin: synthetic `import openai` in any engine module fails red/green.

### F21 — Sharpness/softness: WARN-only + None-skipped, nothing forces a look [MEDIUM, READ]
Where: `engine/verify.py:589-601` + siblings `:559-586` (`:596-597`, `verify.run:175-176`); thresholds `engine/config.py:58-59`. Awaiting Haitham eye verdict (HANDOFF "Softness threshold"). Fix: explicit `detail_vs_still: null (no reference)` warning record + G4 visibility. Pin: synth soft-clip → WARN present.

### F22 — `DUP_SIM` dead constant overclaims dedup [MEDIUM, READ]
Where: `store/pool.py:22` (zero references); actual `:269-270` exact-match. Fix: implement or delete. Pin: near-identical search_text test.

### F23 — Docs contradict code on sheet-cell open [MEDIUM, READ]
Where: `docs/design.md` §9 ("clicking elsewhere opens the tile") vs uncommitted `docs/engine-and-studio.md:385` ("never opens") vs code (`issueSvg` only `data-act=gcell`). Stale side is §9 (rule 12). Pin: node test asserting sheet rects never carry open action.

### F24 — Creator `waiting` card without picture [LOW, READ]
Where: `agent/graph.py:479-487`. Fix: attach card on waiting too. Pin: waiting message contains generation card.

### F25 — Doctor/health blind to newest areas [LOW, READ]
Where: `cli.py:788-917`, `runtime/health.py:65-75` (no particle sets/bursts/recovery). Fix: one doctor line + one health key via `ps.list_sets`. Pin: doctor output contains sets line.

Remaining one-liners: trace 900-statement save + 600KB poll per 0.7-4s [LOW] `graph.py:51-55`, `memory.py:117-126`, `repo.py:573-606`, `agent.js:379`; `docs/engine-and-studio.md:271` "blocked stickers have no x" stale [LOW]; HANDOFF chat chip `<select data-aggrid>` vs button `data-act=aggridtoggle` [LOW]; `out/` 1464 tracked vs docs "~900" [LOW]; `/api/v1` alias + tracing headers served but absent from `openapi.py:info` [LOW]; `migrate_report` marks no-op files applied [LOW]; member `GET /api/jobs` list unfiltered (10-02 F9 was refuted for the single route; list scope stays open) [LOW]; OpenAI-without-price + content-safety-no-code (held Haitham decisions — not re-argued) [MEDIUM/LOW].

## 5. What is solid (protect from "cleanups")

- Verifier single-table design (`OVERRIDABLE` vs `TECHNICAL`, `verifier_error` never waived) + `SHEET_PROCEED` cut-anyway + one-click `recut`.
- Ticket-first (`jobs.py:5-6,408-409`), priced-plan-card + whole-message yes (`resolver.py:229-243`), `_may_spend` 403 (`tools.py:43-45`), `FAIL_CLOSED` judge, `put`-refuses-overwrite, `ON CONFLICT DO NOTHING` history.
- Waiver single-path (`verify._apply_waiver` + `animation_verdict` + `gates._remember/_restore/_materialize`, `ok=False` + WARN "(allowed by you)").
- 409-busy discipline (`generate.js:20-22` quiet retry, `paid_parallel` default 3 with wait outside lock `jobs.py:413`, idempotent retry same replacement `openapi.py:186`).
- `assets._clean`, atomic temp-file writes, `WriterLock` cross-process, `health.redis` explicit fallback, `esc()` posture + `DATA_RULE`/`fence()`, unique-temp atomic writes (`runtime/atomic.py`).
- Particle-set model itself (packs validated, append-only settle, trash+restore same id, FAILED-iff-Telegram-limit) and `burst_plan.md` honesty (lanes over existing machinery, risks stated).
- `qRows`/`cellOp` wait-harness + in-diff JS tests; `tests/test_js.py` one-directional guard (thin but true as far as it goes).

## 6. Missing: tests, docs, features a v1 needs that nobody listed

- Tests (none run 10-03 by instruction; by reading only): same-key concurrent idem; G3-allow per-surface; READY+PENDING→pack 409; approve→edit→reset; `/ui/*.js` servability; settings-vs-turn race; `hf.create`→crash marker; price-drift 409; evil-path table; trace `feedback`/`end` scrub; `sheet_fixed`-preferred-by-recut; engine-boundary red/green; soft-clip WARN. The five to name: (1) particle double-click billing, (2) pack/Telegram gate on `review`, (3) edit resets verdict, (4) servability of every script in `index.html`, (5) price-approved-at-click enforced at `fulfil`.
- Docs: `docs/design.md` §9 (sheet-open + per-surface override + bulk pair + locked marks/no-dimming); `docs/engine-and-studio.md:271,315`; `docs/agent-and-chat.md` + `docs/design.md` for vision-chip glow + grid control; `docs/api.md` `allow` `kind` incl. sheet when built + `/api/v1` alias + tracing headers + family-prefix existence.
- Features: trash purge (spec in HANDOFF §0); G3 `allow_sheet` per HANDOFF; particle Telegram delivery (one open phase); burst creation only after Haitham §6 answers; backup command for `out/` (open since 10-02); Arabic prompt handling (open since 10-02); `Deprecation` header policy (open since 10-02).

## 7. Decisions challenged (standing; do not re-raise until asked)

- Paused FastAPI + `plan.md` §§1,2,4-15: respected. The hand-written `openapi.py` + one-directional `test_openapi` is load-bearing until migration — the strongest argument for generating the spec, but the switch waits for §16.1.
- "Never open media to judge it": respected. Leaves welcome-film spelling, tile art, loop-dissolve ghost, softness threshold to Haitham's eyes; numbers don't replace the browser look.
- OpenAI-without-plan-card + content-safety + `out/`-in-git: held questions Haitham said not to raise again (HANDOFF). Recorded only to keep the ledger honest.
- "Make it happier" no-sticker → whole-sheet tweak: defensible (bare mood = sheet-level direction), documented (`docs/agent-and-chat.md:334`). Watch the opposite failure via the plan card's scope line.
- "Screens are a sandbox" (rule 11): right call for the Mirsal app integration; risk is logic leaking into `console/` — enforce by lint, not by review repetition.
- Hardcoded local models: deliberate (no dependency on a running server); a `models.json` registry would give the same effect without code changes.

## 8. The ten changes first, in order

1. Wrap particle/burst paid routes in `c.idem()` (F1) — S.
2. Gate `add_from_generation` + `telegram.send` on `review` APPROVED; reset `review` on edit (F2+F3) — M.
3. Add `"job-recovery.js"` to `UI_FILES` + servability test + `typeof JR` guards (F4) — S.
4. `approved_cost` on every sheet/video job + enforce at `fulfil`; `creating` marker + reconcile (F5+F6) — M.
5. `@pl.serialized` on `allow_animations`/`allow_cells`; re-read+merge (or hold `_IO_LOCK`) in long slicers (F7+F8) — S/M.
6. Session lock around settings route; clear-pending-after-success for all confirm paths (F9+F15) — S.
7. Build HANDOFF-spec `allow_sheet` + per-surface buttons + bulk + docs (F10) — M.
8. `safe()` at `trace.end`/`feedback`; extend path regex; evil-path rejections + Windows-gated table (F12+F14) — S.
9. `recut`/`recut_cells` prefer `sheet_fixed` (+ `sheet_from` history) or downgrade docs (F13) — S/M.
10. Seed `focus.stickers` from latest gen; shorter lock TTL + heartbeat; monotonic chat ids; tombstone on delete (F16-F19) — M.

## Appendix A — 2026-10-02 triage ledger (preserved; statuses resolved 10-03)

| 10-02 item | Triage verdict | Standing now |
|---|---|---|
| F1 OpenAI without price | real, Haitham's decision | still a held decision (HANDOFF) |
| F2 `result.json` race | real, fixed (`pipeline.serialized`) | fixed; wider unserialized instances found 10-03 (F7/F8) |
| F3 `test_jobs.py` hangs | not reproduced | suite runs; one ordering flake recorded in HANDOFF |
| F4 ResourceWarnings | real, cosmetic | open |
| F5/F6/F13 stray text | false (fragments not in files) | closed |
| F7 no content-safety reason | real, decision | still held (HANDOFF) |
| F8 health returns Redis URL | false | closed |
| F9 members list every job | false (route filters by user) | closed for the single route; list scope stays LOW-open |
| F10 409-vs-404 timing | false | closed |
| F11 no `Deprecation` header | real, policy | open (contract polish) |
| F12 double click on Generate | cosmetic (idem-key harmless) | closed on sheet path; particle paths are the live variant (F1) |
| 10-02 top-10 recs 1-10 | 1,4 done; 2,6,7 still decisions; 3,5 not reproduced; 8 superseded (CLAUDE.md is the index); 9,10 open | see §6/§8 for what remains |

## 9. Audit log (append a dated entry per audit; never rewrite history)

- **2026-10-02** (`c67dea1`): first full audit. Verdict: ship with changes. 44 checks confirmed; suite ~350 tests 2 FAIL; 13 findings (F1-F13); triage above.
- **2026-10-03** (`d49ab39`, `better_ui/ux`, dirty): code audit only, no suites run (owner instruction). 6 parallel read-only tracks; claims extended C0-C26; 25 findings + one-liners (this file's §§3-4). Prompt updated with subagent split (§3.5) and gated long tests; glossary headers added to HANDOFF/plan/README.
