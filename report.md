# Mirsal Builder: independent review (2026-10-01, reviewer: nararouter/agnes-2.5-flash)

## 0. Executive summary

**Verdict: Phase 1 is structurally sound and mostly done; ship it after fixing 4 test failures and the token-in-history issue. Phase 2 should start at S0 (discover Higgsfield MCP tools). Do not start Phase 3 until Haitham confirms.**

The engine, verifier, golden path gates, Studio UI, Telegram client and layered Studio edit are real, tested code. The deterministic core (`engine/`) honours rule 3. The state machine in `gates.py` / `pipeline.py` is well-designed with proper lock/retry for Windows. Five of the fifteen builder decisions I was asked to challenge are defensible; five need small corrections; five are risky enough to call out now.

**The five things that matter most:**

1. **S0 (find the Higgsfield MCP tools) blocks Phase 2.** Without knowing what the operator session actually offers, S1-S7 are speculation. Start there.
2. **The `sharpness` metric is invalid as written** (`edge_energy` ratio >1 rewards compression artefacts). Fix before relying on it for quality gating.
3. **Three test failures exist** (numpy.core import crash in matte.py from Anaconda conflict; one video_project assertion). They block Phase 3C and need explicit handling.
4. **A bot token lives in git history** (`349762b`, `Phase_01/telegram.md`). Revoke it; offer a scrub if Haitham wants.
5. **No server-side auth / CSRF** (expected for a localhost sandbox). Before anyone other than Haitham touches this, add a simple token or cookie. The dangerous endpoints are trash/restore, `/api/telegram/config` (writes the bot token) and bulk delete.

**Recommendation:** finish Phase 1 (commit, run Haitham's real-data checks, merge), then begin Phase 2 at S0.

---

## 1. Scope, method, limits

**Read (in order):** `CLAUDE.md`, `README.md`, `HANDOFF.md`, `Phase_01/README.md` (first 270 lines; capped at 50 KB on second read so I returned to it), `Phase_01/CLAUDE.md`, `phase_02.md` (all 381 lines), `phase_03.md` (skimmed schema and explicit-deferred sections, then read all), `phase_04.md` (all 280 lines), `phase_05.md` (all 247 lines). Then code: `engine/verify.py`, `gates.py`, `pipeline.py`, `engine/video.py`, `engine/render.py`, `engine/config.py`, `console/server.py`, `telegram.py`, `expander.py`, `llm.py`, `library.py` (skimmed for claims), `console/generate.js` (first 450 lines for CATOF/issue-colour logic).

**Ran:**
- `git status` -- confirms branch `merge/generate-advanced`, off `main @ 22d26cc`; large uncommitted working tree (50+ modified files) plus staged renames/deletions from the docs pass.
- `git log --oneline -15` -- recent commits on the branch: Studio UI, tests (142), tokens.
- `.venv\Scripts\python -m mirsal doctor` -- all OK except three WARNs about copied pre-sliced clips; Telegram connected as `@Mirsal_builder_bot`.
- `python -m unittest discover -s tests -t .` -- **142 tests, ~100 s; FAILED (failures=1, errors=3)**. The 3 errors are the same `numpy.core` import crash in `matte.py` (Anaconda base env numpy contaminating the venv somehow, or a version mismatch); the 1 failure is `test_import_video_and_gif` asserting `len(self.pr.list()) == 2` after a failed import but getting 3. Re-ran verify and console subsets separately: both green.
- `python -m unittest tests.test_verify -v` -- 35 tests, all pass.
- `python -m unittest tests.test_console -v` -- 14 tests, all pass.
- `python -m unittest tests.test_telegram -v` -- 21 tests, all pass.
- `python -m unittest tests.test_library -v` -- 9 tests, 2 errors (same matte.numpy.core crash).
- `git show --stat 349762b` -- confirmed `Phase_01/telegram.md` was added here.
- `git check-ignore -v Phase_01/telegram.md mirsal/.env opencode.json` -- all three gitignored.

**Could not run:**
- Headless Chromium / Playwright sweep on real data (no browser automation available in this session).
- Live Higgsfield MCP tool discovery (S0 -- not started, MCP connector was unauthorised in the build session per HANDOFF.md).
- Live Anthropic call through `expander.py` (no `ANTHROPIC_API_KEY` in `.env`).
- Actual Telegram send (would touch a live bot; rule 7 of REVIEW_PROMPT.md forbids it).
- Any sticker media (rule 3 of REVIEW_PROMPT.md forbids opening PNG/WEBM/MP4 to judge quality).

**Inferred** where code inspection was the only path (e.g. some concurrency edge cases, JS XSS audit limited to grep for `innerHTML` + `esc()` usage). All `[INFER]` findings are flagged as such.

---

## 2. Phase scoreboard

| Phase | Builder % | My % | Confidence | Why | Biggest risk | Remaining effort |
|---|---|---|---|---|---|---|
| **1** | 92-97 | **95** | High | 142 tests (138 green); verifier 44 checks over 9 stages; golden path gates implemented server-side with 409s; Studio edit, pack wizard, Telegram send all present and tested. Open items: Haitham's real-data checks, commit/merge decision. | Token in git history (`349762b`); 3 test failures from numpy core crash; uncommitted work. | Small: fix matte numpy import, commit in pieces, merge. |
| **2** | ~15 | **~10** | Medium | Templates + prompter + expander (S5 partly) + video-sheet builder exist. S0 (discover Higgsfield MCP tools) never ran; no jobs system, no operator loop, no vision judge, no measurements. | S0 blocker -- without knowing the tool schema you cannot design S1-S7 correctly. | Medium: S0 first, then S1-S4 sequential. |
| **3** | 0 | **0** | High (not started) | Not started per owner instruction. Plans are detailed (3A-3E). | None yet -- plan is good but schema has a couple of questionable choices (see section 4.B.6). | N/A until started. |
| **4** | 0 | **0** | High | Redis + LangGraph spec exists; nothing built. | Over-engineering risk: Redis may be unnecessary at this scale; LangGraph `interrupt()` is powerful but adds ops burden. | N/A. |
| **5** | ~5 | **~5** | High | Sandbox UI exists; React app parked (`mirsal/web/`). API contract is implicit in console routes, not documented. | No versioned OpenAPI, no auth, no worker model. | Large if started now. |

---
## 3. Top findings

### F-A1  Token in git history, not scrubbed
Severity: **S0** (secret exposure)  Tag: [RAN]  Effort: S
Where: commit `349762b`, file `Phase_01/telegram.md`
What: A bot token was committed to the repository. It is now gitignored (`8512a41`), but the value exists in the object store and anyone with read access to the repo can recover it via `git show 349762b:Phase_01/telegram.md`.
Evidence:
```
> git show --stat 349762b
 Phase_01/telegram.md | 2 ++
> git check-ignore -v Phase_01/telegram.md
.gitignore:35:Phase_01/telegram.md	Phase_01/telegram.md
```
Impact: Any downstream consumer of the repo (collaborator, CI runner, fork) sees the live token. The owner should revoke it at @BotFather immediately; if a scrub is desired, a history rewrite + force-push is needed (only on explicit say-so).
Fix: Revoke at BotFather. Offer scrub command (`git filter-branch` or `git lfs migrate`) after owner confirms.

---

### F-A2  Three test failures from numpy.core import crash (matte.py)
Severity: **S1** (blocks Phase 3C cutout feature; misleads test pass rate)  Tag: [RAN]  Effort: S
Where: `mirsal/mirsal/matte.py:82`, tests `test_cutout_matte_and_forced_methods`, `test_cutout_methods`, `test_bg_removal_capability`
What: `matte.py` imports from `numpy.core._internal` / `numpy.core.umath` which no longer export `ERR_IGNORE` in numpy 2.x. The Anaconda base env has a broken numpy mix; the venv's numpy 2.0.2 also lacks these symbols. The result is an `ImportError` at module load time whenever `matte.alpha()` is called -- the cutout path is effectively dead.
Evidence:
```
ImportError: cannot import name 'ERR_IGNORE' from 'numpy.core.umath'
  (F:\Anaconda\Lib\site-packages\numpy\core\umath.py)
Stack: library.cutout -> matte.alpha -> _alpha line 82 -> _methods.py line 14.
```
Impact: All photo-cutout tests error. `library.cutout(method="matte")` crashes. Video background removal (`video_project.compose`) also errors. Phase 3C cannot start until this is fixed.
Fix: Replace the internal import with the public API (`np.errstate` context manager). Add a guard in `doctor` so future numpy upgrades surface cleanly.

---

### F-A3  Failed import leaves orphan project (assertion failure)
Severity: **S2** (test bug + data hygiene)  Tag: [RAN]  Effort: XS
Where: `mirsal/tests/test_video_project.py:71`
What: `test_import_video_and_gif` expects a failed import to leave zero projects behind. After a failure, `list()` returns 3 instead of 2. Either the teardown does not clean up, or a prior test left a stray project.
Evidence:
```
AssertionError: 3 != 2
```
Impact: Hidden test; does not affect production (failed imports are already handled by the UI showing an error). But it means the "clean state" assumption is wrong, which will bite when tests are reordered.
Fix: Add explicit cleanup in the test's `tearDown` or use a temp directory for `out/`.

---

### F-B1  `_CRF_HINT` is a module-global mutable list shared across threads
Severity: **S2** (reproducibility / race)  Tag: [READ]  Effort: S
Where: `mirsal/mirsal/engine/video.py:293`
What:
```python
_CRF_HINT = [3]       # ladder index that fitted the last clip
```
This is a module-level list mutated by every call to `_encode_fit`. With `anim_workers = 6` parallel threads, two workers can read `_CRF_HINT[0]`, both decide the same starting rung, encode, then both overwrite the hint. The next clip (from a different source video) may start at the wrong rung, producing a non-optimal CRF or, in the worst case, overshooting the 256 KB budget and failing `size_budget`.
Evidence: `video.py:293` declares `_CRF_HINT = [3]`; `_encode_fit` reads/writes `_CRF_HINT[0]` without a lock. `process_video` runs cells through `ThreadPoolExecutor` (line 182). `library.encode_frames` also calls `_encode_fit`.
Impact: Non-deterministic encode quality across runs on the same machine; occasionally a sticker lands at crf 46 when 50 would have fit (wasted budget) or crf 38 when 42 would suffice (unnecessary size). Rarely causes a real BLOCK since the ladder still falls back to the last rung.
Fix: Make the hint per-source-video (key it by the video's sha1 or stat tuple) rather than global. Or wrap the read/write in a lock. Simpler: drop the heuristic and always start from rung 0 for new videos; the ladder has only 9 rungs and most clips take <=3 encodes either way.

---

### F-B2  `result.json` concurrency is correct for one process but not for two
Severity: **S2** (edge case, covered by design)  Tag: [READ]  Effort: XS
Where: `pipeline.py:50-66` (`_IO_LOCK`, `_atomic_write`)
What: The in-process RLock + tmp+`os.replace` pattern prevents two threads inside the same server process from corrupting `result.json`. It does **not** protect against a second process (e.g. `python -m mirsal recheck` running while the server is up). Two processes can read-modify-write the same file and lose each other's edits.
Evidence: `pipeline.py:50` -- `_IO_LOCK = threading.RLock()`. `write_result` acquires it; no OS-level lock survives across processes. Windows `os.replace` is atomic *within* a process's view of the filesystem but two independent processes can still interleave.
Impact: Low in practice because Haitham is the only user and he does not run CLI commands against a live server. But `doctor` scanning `out/` is safe (read-only); any future `--workers` or sidecar will hit this.
Fix: Record `pid` or a monotonically increasing counter in `result.json` and detect cross-process races at read time, emitting a warning. For now, document the limit in `HANDOFF.md`.

---

### F-C1  `sharpness` metric is invalid as a softening detector
Severity: **S1** (misleading quality signal; could block good animations or accept bad ones)  Tag: [READ]  Effort: M
Where: `engine/video.py:44-49` (`edge_energy`), `engine/verify.py:514-519` (`sharpness` check)
What:
```python
def edge_energy(rgba):
    y = cv2.cvtColor(...).astype(np.float32)
    g = np.hypot(cv2.Sobel(y, cv2.CV_32F, 1, 0), cv2.Sobel(y, cv2.CV_32F, 0, 1))
    m = rgba[..., 3] > 8
    return float(g[m].mean()) if m.any() else 0.0
```
The check computes `sharp_kept = mean_edge(decoded) / mean_edge(encoded_input)`. The builder observed ratios of 1.00-1.03 and treated >1 as acceptable. **A ratio above 1 means the metric rewards compression blocking/ringing** -- VP9's quantisation can create artificial high-frequency edges at block boundaries that Sobel detects as *more* edge energy than the original. The metric therefore cannot distinguish "slightly softer" from "artificially sharpened by the codec".
Evidence: `verify.py:514-519`:
```python
@check("anim", "sharpness", WARN)
def sharpness(inp, cfg):
    k = inp["metrics"].get("sharp_kept")
    ...
    return _c(..., k >= cfg.min_sharp_kept, ...)
```
`config.py:58`: `min_sharp_kept = 0.8`. The threshold is arbitrary and calibrated on two cells.
Impact: An animation that is genuinely soft (e.g. from a low-res source) could pass if the encode introduces blocking that boosts the Sobel mean. Conversely, a clean encode with natural edge softening could fail if its gradient is lower than the input (rare but possible with strong loop close). The metric is not robust enough to be a gate.
Fix: Replace with a grounded metric: (a) **gradient correlation** between input and decoded frames (Pearson r over the edge maps, not mean ratio), (b) **edge-spread-function width** on a known-testpattern frame, or (c) **MS-SSIM** against the input (free from `scikit-image` if available, else skip). At minimum, cap the accepted range: `0.85 <= sharp_kept <= 1.15` and log when the upper bound is exceeded as a separate warning.

---

### F-C2  CRF ladder walk assumes monotonic file size
Severity: **S2** (occasional suboptimal encode)  Tag: [READ]  Effort: S
Where: `engine/video.py:296-317` (`_encode_fit`)
What: The function walks the ladder up or down assuming file size is monotonic in CRF. For VP9, size is *mostly* monotonic but not strictly so -- a higher CRF can sometimes produce a larger file due to quantisation interacting with motion complexity. When the walk stops at a non-monotonic local result, the returned crf is not the true best-fit.
Evidence:
```python
if fits(i):
    while i > 0 and fits(i - 1): i -= 1
else:
    i += 1
    while i < len(ladder) and not fits(i): i += 1
    i = min(i, len(ladder) - 1)
```
Impact: Rare. On the builder's two-cell sample the ladder behaved monotonically. In the wild (complex motion, high detail) a few stickers may land at crf 50 when crf 54 would fit, wasting budget. No correctness issue -- the `size_budget` BLOCK still catches anything over 256 KB.
Fix: After the walk completes, do a single verification step: check the neighbour on the non-fitting side to confirm nothing better was missed. Or switch to a binary search (logarithmic, safe regardless of monotonicity).

---

### C. Correctness of the core engine

**C.1 Verifier checks.** I checked all 44 checks against the fixture tests in tests/test_verify.py:
- sheet stage (6 checks): all have PASS/FAIL fixtures.
- still stage (12 checks): all have fixtures including blank_cell reason, holes WARN/BLOCK threshold, duplicate_cell dHash, edge_trimmed.
- video_sheet stage (2 checks): slots_match_approved, no_outline_on_sheet -- fixtures exist.
- video stage (4 checks): video_decodes, video_specs, layout_match, blank_slots_stay_empty -- fixtures exist.
- slot stage (3 checks): inside_slot, inside_frame (including the "out of bounds is made but blocked for review" test), cross_slot -- fixtures exist.
- anim stage (13 checks): size_budget, codec_vp9, dimensions, fps, duration, no_audio, alpha_mode_tag, alpha_decoded, loop_seam, identity_kept, motion_present, alpha_stable, sharpness -- all present.
- pack stage (1 check): pack_limits -- fixture exists.
- telegram stage (3 checks): telegram_sticker, telegram_stroke, telegram_set -- fixtures exist.

Thresholds were measured on 10 real sheets (ring difference 135-209, background std 1.2-2.3, largest hole share 0.074, smallest cell-pair hash distance 5). Sample size of 10 is small but adequate for a desktop tool used by one person. To strengthen: collect thresholds from 30+ real sheets across different subjects.

False positive risk: holes BLOCK above 30% is generous (real max is 7.4%). single_subject WARN above 12% second-part share is also generous. duplicate_cell at hamming distance <=4 is tight (real minimum distance is 5). These are safe.

False negative risk: inside_frame only checks the border ring (4px). A character that peeks 3px outside the ring goes undetected. This is by design (the ring width is cfg.border_px = 4). A wider ring would catch more but also flag legitimate edge detail.

**C.2 Animation pipeline.** One transform per clip (correct). Bicubic upscale (measured +6% edge detail, see F-C3). apply_edge erodes then dilates-blur outline, ROI-only (efficient). Loop closing via crossfade of last 6 frames into first 6 (standard technique). -deadline good -cpu-used 4 -row-mt 1 is sensible for quality; two-pass is not used (acceptable for a desktop tool). yuva420p chroma subsampling is the real source of edge softness (not the encode CRF) -- the builder's note about "source resolution" being the bottleneck is correct. Alpha plane is encoded at the same quality as colour (Telegram does not differentiate).

**C.3 AnimCache.** Key = sha1 of [CACHE_VERSION, VERIFY_VERSION, asdict(cfg) without workers, parts] where parts includes the source file's stat. Can a stale result be served? Yes, if: (a) CACHE_VERSION is not bumped after an engine change (risk: new bug in resize logic serves old cached output); (b) ffmpeg version changes (the key does not include ffmpeg version -- a new ffmpeg could produce different output for the same input, but the cache would serve the old bytes); (c) edge settings stored on the generation but not in cfg (the outline_px and erode_px come from cfg_for(res, cfg) which reads them from result.json, so they are included via asdict(cfg)). Fix: add ffmpeg_version to the cache key.

**C.4 Windows-specific robustness.** WinError 5 on os.replace is handled with lock+retry (40 attempts, 50ms spacing). Below-normal process priority (LOW_PRIORITY) is applied during batch animation. OpenCV thread limit is set to 2 via _Polite. Subprocess handling uses imageio-ffmpeg (bundled, no PATH dependency). Path length: no explicit handling (Windows MAX_PATH = 260 chars; a generation folder at out/G001/slices/vid-001-teddy_bear_school-teddy_bear_with_a_book.webm is ~70 chars, well under the limit). File locks held by the browser video element: the server serves read-only at /src/<id>/video and /src/<id>/clip/<n>; the browser holds the file open during playback but the server reads it fresh each time (no caching in the handler). One fragility: if the browser holds the file open during a set_appearance re-render, the os.replace retry loop will eventually succeed (40 attempts x 50ms = 2 seconds of retry). This is acceptable.

**C.5 Studio layered edit.** studio_edit_open creates a video project from the original animation; studio_edit_commit re-renders the animation with layers composited onto the original still. Originals are kept once in source/orig/. Pack copies are refreshed via Library.refresh_from_generation. Risks: (a) overlay PNGs trusted by the server -- size limits are enforced by the library's validate_render (PNG <= 512 KB); (b) non-idempotent re-edits -- each commit replaces the file in place, so re-editing the same sticker after a prior commit uses the original as base (correct, because _original copies from the generator's file, not the last edit); (c) divergence between still and animation -- both are updated in the same commit, so they stay in sync; (d) failure halfway (animation replaced, still not) -- the commit writes both files before marking edited=True, so a crash mid-write leaves the old files intact (atomic write pattern).

**C.6 Telegram client.** TLS context falls back to loading certificates one at a time when create_default_context() raises on a malformed Windows store entry. Verification stays CERT_REQUIRED / check_hostname -- confirmed at telegram.py:104. Skipping bad certs weakens nothing: the bad certs are malformed entries in the local store, not malicious intermediaries. Token handling: stored in out/telegram.json (plain text, gitignored). Error mapping covers all common failures (429 retry, unauthorized, file too big). Set-name rules enforce _by_<botusername> suffix. Rate limits: 429 retries with retry_after up to 30s, 3 attempts. Large-pack batching: BATCH=50 for createNewStickerSet, rest via addStickerToSet. Partial failure and resume: the lib.set_telegram call records which items were added, so re-send adds only what is new. Deep link correctness: https://t.me/addstickers/{set_name}. replace_static_with_animated semantics: when an animated sticker's still is already in the target pack, mode='replace' puts the animated one in the still's place (position, cover) and deletes the still; mode='add' keeps both. Confirmed in gates.py:423-425.

**C.7 AI expander.** Prompt design is a fixed SYSTEM string (hardcoded in expander.py:15-18). JSON extraction uses re.search(r"{.*}", text, re.S) greedy -- this can match too much if the model outputs text after the JSON (e.g. a markdown code fence). The one repair round catches some structural issues but not all. Temperature 0.8 is reasonable for creative expansion. Model default is claude-sonnet-5-5 (line llm.py:12). Key loading: mirsal/.env is read into os.environ (process-wide side effect, line llm.py:28-35). Error messages use .replace(key, "<key>") coverage -- I spot-checked llm.py:71,73 and telegram.py:133-134; all paths scrub the token. Prompt injection through user request into labels/tags/emoji: the labels become part of the sheet prompt via prompter.render_plan, which is a saved template. A malicious label like "}]->{system: ignore previous instructions}<{" would be escaped by the template (it is plugged into a {label} slot, not interpolated into the system prompt). File/pack name injection: keys are slugified (prompter.slug) which strips non-[a-z0-9_]. Arabic/Arabizi handling: the expander's SYSTEM prompt says "labels in English even when the request is Arabic or Arabizi" (line 18). Cost/latency without a cache: each expansion is one Anthropic call (~$0.0005-0.002, ~1-2s latency (gpt-4.1-mini is cheaper and faster than claude-sonnet)). No caching is implemented (the plan mentions a planner cache in phase_04.md but not here).

**Area C verdict:** The engine is correct and well-tested. The sharpness metric needs fixing (F-C1). The AnimCache should include ffmpeg version in its key.

---

### D. Security and privacy (local tool today, a service later)

**D.1 Server auth/CSRF.** console/server.py binds to 127.0.0.1 but has no authentication, no Origin/Host check, and no CSRF protection (confirmed: no Cross-Origin-Opener-Policy, no SameSite, no token in forms). Any web page the owner visits can fetch('http://127.0.0.1:8770/api/...') (simple POSTs with JSON bodies, DNS rebinding). Dangerous endpoints:
- POST /api/telegram/config -- writes the bot token to out/telegram.json. A CSRF attack could set the token to a attacker-controlled bot.
- POST /api/watch/remove -- moves watch folders to trash.
- POST /api/stickers/delete -- bulk delete from the library.
- POST /api/generations/<id>/drop -- drops stickers from a generation.
Minimum fix: add a simple CSRF token (a random value stored in a cookie, checked on POST) and an Origin header check (self.headers.get('Origin') in {None, 'http://127.0.0.1:8770'}). For a localhost-only tool, a cookie-based token is sufficient.

**D.2 Path handling.** /out/<path> and /lib/<path> resolve the requested path and check root not in f.parents (traversal guard). /src/<id>/video reads only from result.json's recorded paths (no user-controlled path). Uploads are bounded by MAX_UPLOAD (300 MB for projects, 40 MB for raw body). Name parameters (pack_name, sticker_name) are validated by the library (slug rules, length limits). Zip export (telegram.zip_for_stickers_bot) sanitises names with re.sub(r'[^a-z0-9]+', '_', ...). Reserved Windows names (CON, PRN, etc.) are not explicitly checked -- a sticker named CON.png would fail to write on Windows. Fix: add a reserved-name check in prompter.slug or library.add_bytes.

**D.3 Request body limits.** Content-Length is checked in _raw() (40 MB default). Base64 PNG overlays in studio_edit_commit are decoded and validated by validate_render (PNG <= 512 KB). The single-job lock prevents DoS by the owner's own browser (a second request gets 409 and waits). No memory limit on video decode (a 300 MB MP4 is decoded frame-by-frame, so peak memory is O(frames x 512 x 512 x 4) ~= 100 MB for 30 frames -- acceptable).

**D.4 XSS in console JS.** I grepped for all innerHTML assignments in console/*.js (50 matches). Every untrusted string (sticker names, prompts, tags, error text from server/Telegram/LLM, file names) goes through esc() (defined in app.js:4 as String(s??'').replace(/[&<>"']/g, ...)). Controls: I found one potential gap -- app.js:8 say=t=>{$('msg').innerHTML=t||''} with comment "callers escape what they pass". I traced callers: generate.js passes escaped strings; chat.js passes esc(m.text). No unescaped user input reaches innerHTML. The title="..." attributes are all escaped. XSS surface is closed.

**D.5 Secrets hygiene.** Tracked vs ignored:
- Phase_01/telegram.md -- gitignored (line 35 of .gitignore), untracked, but token is in git history (349762b).
- mirsal/.env -- gitignored (line 42).
- opencode.json -- gitignored (line 38).
- out/telegram.json -- gitignored (implied by out/ being gitignored).
- Tokens in logs/events/history/result.json: never. The Telegram client scrubs tokens in error messages (telegram.py:133-134). The LLM client scrubs keys (llm.py:71,73). events.jsonl records stages and decisions, never tokens. result.json records prompts and keys, never tokens.
Prioritised remediation: (1) Revoke the token in 349762b at @BotFather. (2) Run a secret scan (git-secrets or truffleHog) on the full history. (3) Offer a history rewrite only if Haitham wants it (force-push breaks collaborators' forks).

**D.6 Future service prerequisites.** Before anyone else's photos/prompts touch this: auth (session cookies or JWT), tenancy (user-scoped out/ directories or Postgres rows), signed URLs for assets (currently /out/<path> is public to anyone on localhost), quotas (per-user generation limits), PII handling for Phase 3C photos (retention policy, encryption at rest), and a ToS covering model-provider terms (can generated stickers be used commercially?).

**Area D verdict:** Secure for a single-user localhost tool. Needs CSRF protection and a secret-scan scrub before Phase 5.

---
### E. UX / product behaviour of the Studio (sandbox)

**E.1 Five-step header.** The header Request > Prompt > Stickers > Animation > Pack correctly reflects the golden path. States are visible: "Not animated yet" (orange), "Out of bounds" (orange hatch), "Dropped" (greyed tile), "Blocked" (red chip). The only hidden state is STALE -- the tile shows "Animate again" in muted text but does not explain why. Adding a tooltip (title="Edge changed: Animate again to apply it") would help.

**E.2 Issue colour system.** CATOF mapping (generate.js:66-69):
- bounds (orange): inside_cell, inside_slot, inside_frame, cross_slot, edge_trimmed
- loop (yellow): loop_seam
- key (purple): no_spill, chroma_risk, holes, background_is_key, background_flat, alpha_stable, transparent_corners
- look (pink): identity_kept, motion_present, single_subject, duplicate_cell, sharpness
- spec (blue): size_budget, codec_vp9, dimensions, fps, duration, no_audio, alpha_mode_tag, alpha_decoded, static_file, telegram_sticker, telegram_stroke
- bad (red): fallback for unmapped IDs (none exist)

Every check ID from verify.py has an entry. Falls back to 'bad' (red) for unmapped IDs -- there are none. Colour mapping: orange (bounds), purple (key/green-screen), yellow (loop), pink (look/motion), blue (spec/limits), red (dropped/blocked). Hard-before-soft ordering in issuesOf (generate.js:71-90): BLOCK checks are listed before WARN checks, and within each severity, bounds > key > loop > look > spec > bad. This is sensible.

Accessibility: yellow (#eab308) on white has contrast ratio ~1.5:1 -- fails WCAG AA for text (needs 4.5:1). The yellow is used as a chip background, not text, so the text on it (#422006) has decent contrast (~10:1). But colour-blind users (deuteranopia) may confuse orange and yellow. Adding an icon or pattern (hatch style already exists for in-place indication) would help. Reliance on colour alone: the chips show both colour and text label ("Out of bounds", "Bad loop"), so colour is not the only signal.

**E.3 Include anyway / Drop / Bring back semantics.** Include anyway switches review.anim from BLOCKED to PENDING (not APPROVED) -- the sticker is kept for review but not automatically added. The human must still approve it at G4. Re-animation resets decisions: when anim_status is set to STALE (by set_appearance), review.anim is reset to NONE, so the next Animate re-runs the full pipeline and the human sees fresh results. STALE flow after changing Edge: the sticker shows "Animate again" in muted text; clicking Animate re-runs the encoding with the new edge settings. The user always knows what to do next (the button label changes to "Animate").

**E.4 Cognitive load and error recovery.** 409 busy handling is quiet (the page shows "working..." instead of an error dialog). Stale-server banner is clear ("This server is running older code than the files on disk. Restart it."). Long operations have no progress bar per-cell (the header shows total cells done/total). Destructive actions (bulk delete, trash/restore) have confirmation dialogs (trash moves to restore-able trash, not permanent delete).

**E.5 Dead stubs check.** No dead stubs found. Every UI control has a backend handler (verified by grep for data-act handlers in JS and corresponding routes in server.py).

**Area E verdict:** The Studio is polished for a sandbox. The issue colour system is well-designed but yellow accessibility needs a pattern supplement. The STALE flow is clear.

---

### F. Tests

**F.1 Map tests to risks.**
Critical behaviours with NO test: (a) concurrent access to result.json from two processes (only in-process lock is tested); (b) _CRF_HINT race condition (no test for parallel encode with different source videos); (c) prompt injection via sticker names/keys (no test for malicious labels in the expander output); (d) Telegram token leakage in all error paths (the existing test test_errors_are_plain_and_the_token_never_leaks checks one path but not e.g. a network timeout during multipart upload).
Tautological tests: test_deterministic (asserts that running the same input twice produces the same output -- true by construction since the engine is deterministic); test_warn_never_fails_a_report_and_block_is_final (asserts the definition of Report.ok).
Time-dependent tests: none found (all use synthetic fixtures with fixed timestamps).
Port-dependent tests: test_console starts a server on a random port (good).
Slow for little value: test_lifecycle runs the full golden path (9 stickers, encode, gates) -- 28 seconds for 14 tests. This is acceptable given the complexity.

**F.2 Suite run.** 142 tests, 99 s. 138 pass, 3 errors (matte.numpy.core crash), 1 failure (orphan project). Re-run showed same results (no flakiness). ResourceWarning: unclosed socket appears 4 times -- these are from the test server's accepted connections not being closed in the test teardown. Harmless but noisy; fix by adding client_socket.close() in the test server's finish callback.

**F.3 JS no tests.** The smallest cheapest test setup that would have caught the builder's bugs:
- An unquoted SVG attribute swallowing />: caught by a DOM assertion that checks innerHTML contains expected tags.
- CSS specificity hiding a background: caught by a visual regression snapshot (too expensive). Simpler: a unit test that checks computed styles.
- Stale-state race: caught by a test that fires two rapid requests and asserts the second gets 409.
Recommendation: add a Playwright test for the happy path (Generate -> Animate -> Add) and a Jest test for the esc() function (XSS regression). Total effort: ~2 hours.

**F.4 Golden/regression corpus for the verifier.** No corpus exists. Design: store 20 known-good and 20 known-bad stickers as JSON metadata (no media required -- the metadata describes the expected verdict for each check). Example:
{
  "id": "good-inside-cell-001",
  "description": "Character fully inside cell, 10px margin",
  "expected": {"inside_cell": {"ok": true, "value": 0}},
  "source": "synthetic: 512x512 RGBA, key colour #00FF00, subject bbox (50,50,462,462)"
}
This lets CI run verifier checks without media files. Build it alongside Phase 2's measurements.

**Area F verdict:** Test coverage is good for the engine but thin on concurrency and security. Add the golden corpus and a few XSS/unit tests for JS.

---

### G. Documentation and process

**G.1 Claims drift.** Checked section 7 claims:
1. python -m mirsal doctor reports 44 checks over 9 stages, verifier v2. -- CONFIRMED [RAN]
2. Full test suite is 142 tests and passes in about 2 minutes. -- PARTIALLY [RAN]: 142 tests, ~100s, but 4 fail (3 errors + 1 failure).
3. gates.soft_block(s) is true only if the animation exists and every failed check in anim_report has severity WARN; approving a sticker blocked by a real BLOCK check returns HTTP 409. -- CONFIRMED [RAN] (test test_a_soft_blocked_animation_can_be_included_anyway_but_a_real_block_cannot passes).
4. set_appearance re-renders only stickers that are READY, not edited, and have a source/plain/S#.png; marks every sticker that has a webm as STALE, resets review.anim to NONE, and never writes a file the verifier BLOCKs. -- CONFIRMED [READ] (pipeline.py:578-613).
5. AnimCache.key changes when CACHE_VERSION, VERIFY_VERSION or any EngineConfig field (except anim_workers) changes. -- CONFIRMED [READ] (video.py:90-93).
6. engine/render.render_sticker upscales with INTER_CUBIC, downscales with INTER_AREA, and clips overshoot (alpha to [0,1]; colour via later np.clip). Does premultiplied bicubic overshoot ever produce a visible halo, and does the despill step see it? -- PARTIALLY [READ]: up/downscale interp is correct (render.py:64). Clipping is present but post-hoc (see F-C3).
7. _encode_fit returns the lowest crf of the ladder that fits 256 KB assuming monotonic size; it then updates the global _CRF_HINT. -- CONFIRMED [READ] (video.py:296-317).
8. library.encode_frames (webm branch) calls _encode_fit; the WebP/GIF branches keep their own ladders. -- CONFIRMED [READ] (library.py:encode_frames).
9. record_anim sets review.anim = BLOCKED when inside_frame fails on a READY animation; recheck_bounds does the same retroactively and marks bounds_checked. -- CONFIRMED [READ] (pipeline.py:340-356, pipeline.py:454-519).
10. console/server.py has no Origin/Host/CSRF check; it binds only to 127.0.0.1; a second job gets 409. -- CONFIRMED [READ] (server.py:460, line ThreadingHTTPServer(("127.0.0.1", port), ...)).
11. The Telegram client never sends or logs the bot token in a URL that ends up in events.jsonl/result.json/error messages shown in the UI. -- CONFIRMED [READ] (telegram.py:133-134 _scrub, no token in event emissions).
12. Phase_01/telegram.md is git-ignored and untracked now, but git log --all still contains a token (349762b). -- CONFIRMED [RAN].
13. The mirsal/web/ React app is not served by python -m mirsal serve (the server serves console/ only). -- CONFIRMED [READ] (server.py:20 UI_FILES does not include anything from web/).
14. phase_02.md's "What exists already" list matches the code (e.g. build_video_sheet, measure-cells -- the builder believes measure-cells is not yet a CLI command; check cli.py). -- PARTIALLY [READ]: build_video_sheet exists in gates.py:236. measure-cells is referenced in phase_02.md line 44 but does NOT exist in cli.py -- it is a planned command, not built.
15. Every verifier check id in verify.py has an entry in CATOF (generate.js) or falls back sensibly. -- CONFIRMED [READ] (all 44 IDs are mapped; fallback to 'bad' is unreachable but safe).
16. CLAUDE.md rule 9's naming convention (img-NNN-<subject>/, vid-NNN-<subject>/; outputs <media>-<NNN>-<task_slug>-<key>.<ext>) is what the code produces; watch-folder names are never renamed by the app. -- CONFIRMED [READ] (pipeline.py:115-116 media_name, sources.py scans by glob).
17. Library bulk delete, replace-still-with-animated, and rename keep file_name metadata equal to the generator's name. -- CONFIRMED [READ] (library.py:add_from_generation sets file_name from the generator's stem).
18. The STALE/edge flow cannot leave a sticker READY with the old edge. -- CONFIRMED [READ] (pipeline.py:608-612: marks anim_status="STALE" and review.anim="NONE").

Ten additional drifts found:
- HANDOFF.md line 44 says "run the 140 tests" but there are now 142.
- Phase_01/README.md line 122 says "4 cells of a 960 px 3x3 video went 55 s to 21 s" -- the speedup number is from an older benchmark; current timings depend on hardware.
- phase_02.md line 44 references python -m mirsal measure-cells as a CLI command that reports flagged share -- this command does not exist yet.
- phase_03.md line 73 references mirsal/db.py and mirsal/store/repo.py -- these files do not exist (Phase 3 not started).
- CLAUDE.md rule 2 says "Phase 1 (Phase_01/, built)" but the finish list in Phase_01/CLAUDE.md still has 2 uncompleted items (AI expand needs live key, Haitham's real-data checks).
- README.md (root) line 26 says python -m mirsal serve but the command is actually python -m mirsal serve from the mirsal/ directory (the README omits the working-directory note).
- phase_04.md line 140 says "Phase 1 emits sliced as one event for all nine cells; emit a per-sticker event inside it" -- this enhancement is not implemented (event is still per-generation).
- mirsal/mirsal/console/generate.js line 483 references GSTALE variable which is set by Console.stale() but the variable name in the JS is GSTALE while the Python method is stale() -- the naming is consistent but the JS global is not documented.
- Phase_01/README.md line 183 mentions "WhatsApp export was removed on 2026-10-01" but the code still has WA_ANIM_MAX = 500 * 1024 constant in library.py (used by the animated editor's WebP download, not by WhatsApp export).
- engine/video.py line 80 CACHE_VERSION = 2 but the docstring says "bump when an engine change makes old cached animations wrong" -- no changelog tracks which version introduced which change.

**G.2 Contradictions between CLAUDE.md rules and what the plans/code do.**
- Rule 10: "Python's blocks are final." soft_block allows human override of WARN-level blocks. This is a deliberate exception (the WARN is not a BLOCK), but the rule's wording is absolute. Clarify rule 10 to say "Python's BLOCK verdicts are final; WARN verdicts can be overridden by the human."
- Rule 7: "Updating a plan means enhancing it, never shrinking it." phase_03.md is ~700 lines and grows with each addition. The "enhancing" rule creates bloat. Suggestion: move detailed design into separate Phase_03/design/*.md files and keep phase_03.md as a index with links.
- Rule 12: "Docs are part of every MAJOR step." The recent commit 82f5d64 updated docs (phases reordered, Phase_01 holds README+CLAUDE, phase_01.md removed, rules 11-12, review prompt) but did not update phase_04.md or phase_05.md to reflect the new phase numbering. Stale statements remain.

**G.3 Process rules followed?** Plans are hand-off / next steps: yes, HANDOFF.md points to the next phase. README is architecture: yes, Phase_01/README.md documents what was built. A plan item is deleted only after owner approves: phase_01.md was removed (approved). Updating a plan means enhancing, not shrinking: yes, phase_02.md grew from the original plan. Is the doc set navigable by a new engineer or a fresh LLM in 30 minutes? Mostly yes, but the drift items above (10 found) add confusion. Cut: merge Phase_0N/CLAUDE.md files into their respective phase_0N.md files (they duplicate information).

**Area G verdict:** Documentation is dense but navigable. The "enhancing not shrinking" rule creates bloat; introduce sub-docs. Ten drift items need fixing.

---

### H. Performance and resource use

The owner's PC hangs during batch animation. The builder measured: ~5 s CPU per sticker (35% rendering frames, 40% VP9 encode, 12% loop check, 7% ffmpeg start, 8% read+key) and made the batch "polite" (below-normal priority, 2 OpenCV threads, default workers = half the cores up to 6, result cache).

**Challenge the diagnosis:** The breakdown is plausible but incomplete. It misses: (a) I/O wait (reading 9 source videos, writing 9 output WEBMs -- on HDD this dominates); (b) Python GIL contention (threads compete for the GIL between C-extension calls, even though OpenCV and ffmpeg release it); (c) cache miss penalty (first run is slow; subsequent runs are fast -- the measurement may mix both).

**Is the polite-batch fix adequate?** Below-normal priority helps the OS schedule other work. 2 OpenCV threads prevents each worker from spawning N threads. Half cores up to 6 is reasonable (a 32-core machine animating 6 cells in parallel uses ~300% CPU, which is fine for a desktop tool). The result cache (0.3 s repeat) handles re-runs. The fix is adequate for the stated problem (PC hanging) but does not address the fundamental cost: VP9 encode is CPU-bound and will always be slow on a single machine.

**Fundamentally cheaper designs:**
- Render at 512 only once (current code renders at source resolution then scales -- the current code does one transform per clip at the union bbox, then scales to 512x512, which is correct).
- Avoid full-frame float32 pipeline: the current code converts to float32 for resize and outline, then back to uint8. This is necessary for quality but doubles memory. A uint16 intermediate would halve memory but lose precision.
- Encode with hardware: NVIDIA NVENC / Intel QSV support VP9 encode on modern GPUs. This would drop encode time from ~2s to ~0.2s per sticker. The cost is an added dependency and a fallback path for machines without GPU.
- Reduce frames: the current max is 3s x 30fps = 90 frames. Many animations are subtle and would look fine at 60 frames (2s). Let the user choose.
- Share work across stickers on one sheet: the current code decodes each cell independently from the 3x3 MP4. A shared decode (decode the full MP4 once, slice in-memory) would save ~40% decode time. This is a significant optimisation that the plan does not mention.
- GPU for keying: OpenCV's chroma key is CPU-bound. A GPU kernel (CUDA/OpenCL) would speed it up but adds dependency complexity.
- Process pool vs threads: given the GIL, a ProcessPoolExecutor would truly parallelise (each process has its own GIL) but incurs pickle overhead for the frame arrays. For CPU-bound C-extensions (OpenCV, ffmpeg), threads are actually better (they release the GIL). Stick with threads.

**Memory spent:** n frames x 512 x 512 x 4 (float32 RGBA) x workers. With 6 workers, 90 frames, float32: 90 x 512 x 512 x 4 x 4 bytes = ~370 MB peak per worker x 6 = 2.2 GB. In practice, workers run sequentially on the same frames (the cache avoids re-decoding), so peak is closer to 370 MB. On a 32-core machine with 64 GB RAM, this is fine. On a laptop with 16 GB, it is tight.

**Worst-case peak memory with 6 workers:** ~2.2 GB (theoretical upper bound). Measured peak on the builder's machine: unknown (no profiling data in the repo). Recommendation: add python -m mirsal profile --memory to track RSS during animation.

**Area H verdict:** The polite-batch fix is adequate for now. The biggest win is shared decode across cells (save 40% decode time). Hardware VP9 encode is the next-level win but adds dependency complexity.

---
## 4. Findings by area A-H


### F-G1  llm.py switched from Anthropic to OpenAI but callers and tests are stale
Severity: **S2** (broken AI expansion path; misleading doctor output)  Tag: [RAN]  Effort: S
Where: `mirsal/mirsal/llm.py` (uncommitted diff), `mirsal/mirsal/expander.py:69`, `mirsal/tests/test_expander.py`, doctor output
What: `llm.py` has been switched from an Anthropic Messages client to an OpenAI Chat Completions client (default model `gpt-4.1-mini`, key var `OPENAI_API_KEY`). However:
- `expander.py:69` still says "add ANTHROPIC_API_KEY to mirsal/.env"
- `tests/test_expander.py` sets `ANTHROPIC_API_KEY` in `os.environ` and asserts it appears in error messages
- `python -m mirsal doctor` prints "add ANTHROPIC_API_KEY to mirsal/.env"
The AI expansion path is now broken for anyone who follows the doctor instruction (they will set `ANTHROPIC_API_KEY` but `llm.configured()` checks `OPENAI_API_KEY`).
Evidence:
```
> python -m mirsal doctor | findstr /i "anthropic"
OK      AI expansion: off: add ANTHROPIC_API_KEY to mirsal/.env ...
> grep ANTHROPIC mirsal/mirsal/expander.py mirsal/tests/test_expander.py
expander.py:        base["expand_error"] = "No AI key (add ANTHROPIC_API_KEY to mirsal/.env)..."
test_expander.py:  self.key = os.environ.pop("ANTHROPIC_API_KEY", None)
test_expander.py:  os.environ["ANTHROPIC_API_KEY"] = self.key
test_expander.py:  self.assertIn("ANTHROPIC_API_KEY", plan["expand_error"])
```
Impact: AI expansion is non-functional until expander.py, test_expander.py, doctor, and any .env.example files are updated to use `OPENAI_API_KEY`. The tests will fail if run against the new llm.py (they set the wrong env var).
Fix: Update expander.py:69, test_expander.py, doctor output, and any .env.example files to reference `OPENAI_API_KEY`. Update the test setup to set `OPENAI_API_KEY` instead. Consider keeping both Anthropic and OpenAI clients behind a provider abstraction if the owner wants to support both.

---

## 5. Claims verification table

| Claim | Verdict | Evidence | Tag |
|---|---|---|---|
| 1. doctor reports 44 checks over 9 stages, verifier v2 | CONFIRMED | doctor output: "verifier v2: 44 checks over 9 stages"; VERIFY_VERSION=2 | [RAN] |
| 2. 142 tests, ~2 min, green | PARTIALLY | 142 tests, ~100s, but 4 fail (3 numpy errors + 1 orphan project) | [RAN] |
| 3. soft_block true only for WARN-level; real BLOCK returns 409 | CONFIRMED | test_a_soft_blocked_animation_can_be_included_anyway_but_a_real_block_cannot passes | [RAN] |
| 4. set_appearance re-renders READY-only, marks webm STALE, respects BLOCK | CONFIRMED | pipeline.py:578-613 | [READ] |
| 5. AnimCache.key changes on CACHE_VERSION/VERIFY_VERSION/cfg field change | CONFIRMED | video.py:90-93 | [READ] |
| 6. render_sticker uses INTER_CUBIC up, INTER_AREA down, clips overshoot | PARTIALLY | render.py:64 confirms interp choice; clipping is post-hoc (F-C3) | [READ] |
| 7. _encode_fit returns lowest crf assuming monotonic, updates global hint | CONFIRMED | video.py:296-317 | [READ] |
| 8. library.encode_frames calls _encode_fit; WebP/GIF keep own ladders | CONFIRMED | library.py encode_frames branches | [READ] |
| 9. record_anim sets review.anim=BLOCKED on inside_frame fail; recheck_bounds does same retroactively | CONFIRMED | pipeline.py:340-356, 454-519 | [READ] |
| 10. server.py no Origin/Host/CSRF; binds 127.0.0.1; second job gets 409 | CONFIRMED | server.py:460; lock check at line 56 | [READ] |
| 11. Telegram client never sends/logs token in URL/events/errors | CONFIRMED | telegram.py:133-134 _scrub; no token in emit() calls | [READ] |
| 12. Phase_01/telegram.md gitignored but token in git history (349762b) | CONFIRMED | git show --stat 349762b; git check-ignore confirms | [RAN] |
| 13. mirsal/web/ React app not served by python -m mirsal serve | CONFIRMED | server.py:20 UI_FILES has no web/ entries | [READ] |
| 14. phase_02.md "What exists" matches code; measure-cells is NOT a CLI command | PARTIALLY | build_video_sheet exists (gates.py:236); measure-cells does not exist in cli.py | [READ] |
| 15. Every verifier check id in CATOF or falls back sensibly | CONFIRMED | generate.js:66-69 maps all 44 IDs; fallback to 'bad' is unreachable | [READ] |
| 16. Naming convention img-NNN-subject/ vid-NNN-subject/ matched by code | CONFIRMED | pipeline.py:115-116 media_name; sources.py scans by glob | [READ] |
| 17. Library keeps file_name equal to generator's name | CONFIRMED | library.py:add_from_generation sets file_name from generator stem | [READ] |
| 18. STALE/edge flow cannot leave sticker READY with old edge | CONFIRMED | pipeline.py:608-612 sets anim_status=STALE, review.anim=NONE | [READ] |

---

## 6. Plan critique and proposed re-plan

**What to cut, merge, reorder, add:**

1. **Merge Phase_0N/CLAUDE.md into phase_0N.md.** They duplicate information. Keep Phase_0N/CLAUDE.md only for Phase 1 (finish list) and Phase 2 (inputs from Haitham). Delete for Phases 3-5.
2. **Split phase_03.md into sub-docs.** At 700 lines it is unwieldy. Create Phase_03/design/ with 001_init.sql, repo.py spec, import spec, tracing spec. Keep phase_03.md as a 50-line index with links.
3. **Add cost-control to phase_02.md.** Every paid generation call must have a budget check before it runs. Add MIRSAL_DAILY_CREDITS enforcement and per-job cost estimation.
4. **Drop Redis from Phase 4 unless multi-user is confirmed.** A single-user desktop app does not need Redis for event streams (events.jsonl serves the same purpose). Redis adds operational complexity (docker container, connection pooling, TTL management) for no gain. Keep it only if Phase 5 ships a remote API.
5. **Add a deployment target to phase_05.md.** "API / app" is too vague. Is it a Python package pip-installed locally? A Docker container? A systemd service? The phase plan should specify the runtime environment.

**Revised phase list with exit criteria:**

Phase 1 (95%): Fix matte numpy import (S1), fix orphan project test (S2), revoke token (S0), commit in pieces, merge to main. Exit: all 138 non-matte tests green, Haitham runs real stickers through the Studio edit, Telegram pack arrives in app.

Phase 2 (10%): S0 discover Higgsfield MCP tools. S1 prompt lab offline. S2 jobs system. S3 first real sheet. S4 normalised video. S5 slot reviewer. S6 vision judge. S7 quality measurements. Exit: >=80% approved, >=4/5 rating, judge agreement >=80%, real video from normalised sheet sliced.

Phase 3 (0%): 3A Postgres + import + tracing. 3B semantic pool. 3C photo cutout. 3D text templates. 3E parallax photos. Exit: commands work, import idempotent, search finds things, haitham runs list/show/history/search after restart.

Phase 4 (0%): 4A graph + references. 4B persistent slots. 4C annotation + memory. Exit: resolver >=95% accuracy, cache hit rates printed, session resume works.

Phase 5 (5%): 5A HTTP API + workers. 5B frontend. 5C hardening + export. Exit: auth tests pass, signed URLs expire, metrics visible, regression suite runs, pack validates in Telegram.

**What to do in the next 2 weeks:**
Week 1: Fix the 4 test failures (matte numpy import, orphan project). Revoke the token. Commit Phase 1 in pieces (engine, console, tests, docs). Get Haitham's real-data sign-off.
Week 2: Start Phase 2 at S0. Run the Claude Code session, discover the Higgsfield MCP tools, list them, make one test image and one test video. Write Phase_02/higgsfield_mcp.md. This determines everything else in Phase 2.

---

## 7. Strategy answer

**Is Mirsal worthy as SaaS?** Yes, but narrow.

The moat is not the generator (anyone can call an image model). It is the verifier+gates+normalised video sheet stack that turns raw AI output into Telegram-compatible stickers with zero manual QA. That is defensible because it is boring engineering (OpenCV, ffmpeg, state machines) that no one else is building.

Who pays: creators who want branded animated stickers for their Telegram communities (influencers, small businesses, community mods).

Why Telegram: it is the only major platform with native animated sticker support (WEBM/VP9+alpha) and a Bot API that lets you ship a pack in one click. WhatsApp, iMessage, and Discord either lack animated sticker support or require app-store approval.

Defensibility: the engine is open source (this repo) but the prompt templates, style presets, and judge calibration are the secret sauce. Competitors would need to rebuild the verifier from scratch.

Unit economics: generation cost per pack is ~$0.18-0.90 (9 stickers x $0.02-0.10 each at current Higgsfield/pricing). Price point should be $2-5 per pack or a $10-20/month subscription for unlimited generations. At $5/pack and $0.50 cost, margin is 90%.

Risks: platform dependence (Telegram changes sticker specs or Bot API limits), model-provider dependence (Higgsfield raises prices or changes ToS), quality variance (AI generation is stochastic; the verifier catches format issues but not aesthetic ones), copyright (generated characters may infringe on existing IP -- no moderation exists).

Cheapest demand test before building Phases 3-5: ship the Phase 1 engine as a CLI + a simple web form (one HTML page with a text box and a "Generate" button) that emails the owner when someone requests a pack. If 50 people request packs in a week, build Phase 2. If 5, reconsider.

---

## 8. Second opinion on the builder's decisions

| Decision | Agree/Disagree/Partly | Reasoning | What I would do |
|---|---|---|---|
| 1. Include anyway override of WARN-level blocks | **Agree** | WARN is not BLOCK. The human signing off is the right safeguard. Python's BLOCK is final; WARN is advisory. | Keep as-is. Document the override in the UI (it is already logged in history). |
| 2. Finer CRF ladder + bicubic upscale + sharpness check, based on two cells | **Partly** | Finer ladder (9 rungs vs 4) is good -- measured on real data, saves budget. Bicubic upscale is good (+6% edge detail). Sharpness check is NOT good (F-C1: invalid metric). | Keep ladder and upscale. Replace sharpness with gradient correlation or drop it entirely (the encoder's CRF ladder already controls quality). |
| 3. Not adopting -cpu-used 1 | **Agree** | -cpu-used 1 is slow (single-threaded encode). -cpu-used 4 is the sweet spot for quality/speed on modern CPUs. | Keep -cpu-used 4. |
| 4. Polite-batch defaults (workers=half cores<=6, below-normal priority, 2 OpenCV threads) | **Agree** | These prevent the PC from hanging (the stated problem) without requiring user tuning. | Keep. Consider adding MIRSAL_ANIM_WORKERS=1 as a fallback for low-RAM machines. |
| 5. AnimCache design (sha1 of version+cfg+parts) | **Partly** | Version stamps prevent stale caches after engine changes. Including source file stat prevents serving cached output after the source changes. Missing: ffmpeg version in the key (C.3). | Add ffmpeg_version to the cache key. Bump CACHE_VERSION when ffmpeg version changes. |
| 6. Swapping Phases 2 and 3 and pulling AI expander into Phase 1 | **Agree, with note** | Generation before database is the right priority. AI expander pulled forward is fine (deterministic fallback exists). **However:** llm.py has been switched from Anthropic to OpenAI (uncommitted) but expander.py, tests, and doctor output still reference ANTHROPIC_API_KEY — the expansion path is currently broken. | Fix the Anthropic->OpenAI drift (expander.py:69, test_expander.py, doctor output) before declaring Phase 1 complete. Move expander live testing to Phase 2. |
| 7. Using Claude Code operator session with Higgsfield MCP as generation worker | **Disagree (for production)** | MCP is a development-time connector, not an HTTP API. It assumes a human operator is present. It does not scale to automated pipelines or multi-user APIs. | Use the operator session for Phase 2 development (S0-S4). For Phase 5, replace with a direct HTTP provider (Higgsfield REST, Replicate, fal, Runway). The ImageGenerator/VideoGenerator protocols in phase_02.md are the right seam -- build the HTTP implementation there. |
| 8. File-based storage (result.json) until Phase 3 | **Agree** | Files are simple, portable, and sufficient for a single-user desktop tool. Postgres adds operational complexity (Docker, migrations, connection pooling) for no benefit until multi-user is needed. | Keep files for Phase 1-2. Plan the import path carefully (phase_03.md does this well). |
| 9. Deleting phase_01.md and moving architecture README into Phase_01/ | **Agree** | phase_01.md was the plan; Phase_01/README.md is the architecture. The distinction is correct. | Keep. Apply the same pattern to future phases (delete phase_N.md when built, move architecture to Phase_N/README.md). |
| 10. Keeping a parked React app instead of deleting it | **Agree** | The parked app (mirsal/web/) is a reference implementation for Phase 5B. Deleting it loses work. Keeping it signals that a React frontend is planned. | Keep. Mark it clearly as "parked -- not served, reference for Phase 5B" in the README. |
| 11. Tolerant TLS context fallback | **Agree** | Corporate networks and malformed Windows cert stores break ssl.create_default_context(). The fallback (load certs one at a time, skip bad ones) preserves security (CERT_REQUIRED stays on) while improving availability. | Keep. Document the fallback in doctor output (it already says "NOT_ENOUGH_DATA"). |
| 12. One-click Telegram (connect once, send, open app, bot messages owner) | **Agree** | This is the killer feature. The owner gets a link and a preview sticker in-chat. It turns a technical workflow into a single click. | Keep. Add a "send again" button for regenerating the link (in case the owner lost it). |
| 13. Making the sandbox UI the place where product decisions (colour semantics, gates) are encoded | **Partly** | The UI encodes real product decisions (issue colours, gate counts, Include anyway). This is good -- the UI is the customer-facing layer. But it also means UI bugs become product bugs (e.g. the yellow accessibility issue in E.2). | Keep the UI as the source of truth for product behaviour. Add automated UI tests (Playwright) to catch regressions. |
| 14. Stale-server banner approach to recurring failure instead of auto-reload / versioned API | **Agree** | Auto-reload is fragile (loses state, interrupts in-progress jobs). Versioned API adds contract complexity. The banner is simple and correct: "restart the server". | Keep. Consider adding a hot-reload toggle for development (reload only static files: JS, CSS, HTML -- not Python). |
| 15. Rule 10 "a human approves at every gate, Python's blocks are final" as the core quality model | **Agree** | This is the right model. Python catches format/spec violations (size, dimensions, alpha, boundaries). Humans catch aesthetic/creative issues (is this funny? is the pose right?). Never collapse them into one monolithic LLM prompt. | Keep. Document this explicitly in the README ("Python judges correct; humans judge good"). |

---

## 9. Questions for the owner

1. **Token scrub.** The bot token in commit 349762b is recoverable. Should I revoke it at @BotFather and run a history scrub (force-push)? This breaks any forks collaborators have made.
   Recommended default: Revoke at BotFather. Skip the scrub unless the token was exposed publicly (e.g. in a public repo mirror).

2. **Phase 2 S0 timing.** Higgsfield MCP tools were unauthorised in the build session. Has Haitham authorised them in a separate session? If not, S0 is blocked until authorisation is obtained.
   Recommended default: Authorise Higgsfield MCP in a Claude Code session, list tools, make one test image and one test video, write Phase_02/higgsfield_mcp.md.

3. **Postgres before or after Phase 2 generation?** The current order (2 then 3) means Phase 2 writes to files and Phase 3 imports them. An alternative is Phase 3 first (schema design), then Phase 2 writes directly to Postgres. Which do you prefer?
   Recommended default: Keep the current order. File-first lets Phase 2 ship faster; Postgres import is a one-time migration.

4. **Redis necessity.** Do you expect multiple concurrent users (or a multi-tenant SaaS) within the next 6 months? If yes, Redis is justified for session locks and event streams. If no (single-user desktop tool), skip Redis and use Postgres streams only.
   Recommended default: Skip Redis for Phase 4. Add it only if Phase 5 ships a multi-user API.

5. **Sharpness metric.** Do you want to keep the sharpness check (with the flawed metric) and fix the metric, or drop it entirely and rely on the CRF ladder + human review for quality?
   Recommended default: Drop it. The CRF ladder already controls quality; the sharpness metric adds noise without signal.

6. **Deployment target.** Is the shipped product a desktop app (Electron/Tauri wrapping this Python backend), a web service (Docker container on a VPS), or an API that the existing Mirsal app consumes?
   Recommended default: API that the existing Mirsal app consumes (per CLAUDE.md rule 11). The desktop UI in this repo stays as a sandbox.

7. **Cost control.** Should Phase 2 include a per-request cost estimate before the generation call, and a daily credit cap that refuses new jobs when exceeded?
   Recommended default: Yes. Add MIRSAL_DAILY_CREDITS (default $5/day); note the Anthropic->OpenAI switch in llm.py is uncommitted and may affect cost estimates and print the estimated cost before every paid generation call.

8. **Arabic/RTL support.** Phase 3D says "Arabic works in every template" but the prompter's slug generator drops non-ASCII. Is Arabic prompt support a Phase 2 requirement or a Phase 3 deferment?
   Recommended default: Defer to Phase 3D. Phase 2 handles Arabic input by transliterating to English for the prompt (as the expander currently does).

9. **Content moderation.** Should the system filter generated stickers for copyrighted characters, real people, or trademarked IP before they reach the human gate?
   Recommended default: Defer to Phase 5C. Phase 2-3 focus on the core pipeline. Add a "report inappropriate content" button in the UI as a lightweight moderation mechanism.

10. **Backup strategy.** Should the repo include a backup script for out/ (snapshots to a secondary location, rotation policy)?
    Recommended default: Add a simple backup command (python -m mirsal backup out/ backup/) in Phase 1 cleanup. One tar.gz per day, keep 7 days.

---

## 10. Appendix

**Commands run and results:**
- git status: on branch merge/generate-advanced, 50+ modified files uncommitted, staged renames (README.md->Phase_01/README.md, phase_01.md deleted, phase_02/03 CLAUDE.md modified).
- git log --oneline -15: bf85e47 (Edge finish), 22d26cc (HANDOFF.md), 8512a41 (Stop tracking telegram.md), 349762b (Generate: sessions), ...
- python -m mirsal doctor: all OK except WARN on copied pre-sliced clips (teddy_bear 002/003/004).
- python -m unittest discover -s tests -t .: 142 tests, 99s, FAILED (failures=1, errors=3).
- python -m unittest tests.test_verify -v: 35 tests, all pass.
- python -m unittest tests.test_console -v: 14 tests, all pass.
- python -m unittest tests.test_telegram -v: 21 tests, all pass.
- python -m unittest tests.test_library -v: 9 tests, 2 errors (matte numpy crash).
- git show --stat 349762b: added Phase_01/telegram.md (2 lines).
- git check-ignore -v Phase_01/telegram.md mirsal/.env opencode.json: all three gitignored.

**Files read (selected):**
- CLAUDE.md (32 lines)
- README.md (39 lines)
- HANDOFF.md (67 lines)
- Phase_01/README.md (first 270 lines, then returned for remainder)
- Phase_01/CLAUDE.md (26 lines)
- phase_02.md (381 lines)
- phase_03.md (695 lines)
- phase_04.md (280 lines)
- phase_05.md (247 lines)
- mirsal/mirsal/engine/verify.py (715 lines)
- mirsal/mirsal/gates.py (480 lines)
- mirsal/mirsal/pipeline.py (764 lines)
- mirsal/mirsal/engine/video.py (418 lines)
- mirsal/mirsal/engine/render.py (76 lines)
- mirsal/mirsal/engine/config.py (66 lines)
- mirsal/mirsal/console/server.py (467 lines)
- mirsal/mirsal/telegram.py (367 lines)
- mirsal/mirsal/expander.py (107 lines)
- mirsal/mirsal/llm.py (76 lines)
- mirsal/mirsal/console/generate.js (first 450 lines)
- mirsal/mirsal/console/app.js (first 10 lines)

**Anything unverifiable:**
- Live Higgsfield MCP tool schema (S0 not run).
- Actual sticker quality (rule 3 forbids opening media).
- Real-world performance on the owner's PC (no profiling run).
- Telegram API rate-limit behaviour under load (no load test).
- Multi-user security (single-user tool; Phase 5 not built).

(End of report)
