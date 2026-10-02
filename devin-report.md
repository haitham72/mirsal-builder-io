# Devin Report: 5 Issues Investigation

**Date:** 2026-10-02  
**Repository:** haitham72/mirsal-builder-io  
**Branch:** merge/generate-advanced

---

## Blue Screen Fix (Fixed During Debugging)

### Issue

When the AI model returns a blue screen instead of green (can happen with green subjects like watermelon/avocado), the chroma keying would fail silently, producing a "blue screen" result (the background not removed) and the chat would wait indefinitely.

### Root Cause

In `pipeline.py` line 325, the logic for setting the chroma key was inverted:

```python
cfg = cfg_for(res, replace(base, chroma="green") if key != "blue" else base)
```

When `key == "blue"`, it used `base` (which has `chroma="green"` by default). This meant blue screens were keyed as green, which failed completely.

### Fix Applied

Changed line 325 in `pipeline.py` to:

```python
cfg = cfg_for(res, replace(base, chroma="blue") if key == "blue" else replace(base, chroma="green"))
```

Now:

- When key is blue → set chroma to blue
- When key is green → set chroma to green

### Additional Safety Gate

Added validation in `chroma.py` `calibrate()` function (line 39):

- New `validate=True` parameter
- When enabled, raises `ValueError` if key difference is too low (< 30.0)
- This catches wrong chroma key usage (e.g., green key on a blue screen) before it produces a bad result
- Applied in `video.py` `_one_cell()` for video processing

### Test Verification

The existing test `test_a_blue_screen_sheet_is_keyed_as_blue_and_marked_only_because_it_is_blue` in `test_live.py` passes, confirming the fix works correctly.

---

---

## Issue 1: Animation Thumbnail Silhouette Ghost

### Description

Sticker animations loop to the thumbnail silhouette 1-2 frames at 50% opacity - faint but visible and annoying.

### Root Cause

The `close_loop` function in `mirsal/mirsal/engine/video.py` (lines 92-101) blends the tail frames into the head frames to create a seamless loop. The blending logic:

```python
def close_loop(frames: np.ndarray, m: int) -> np.ndarray:
    n = len(frames)
    if m < 1 or n < 2 * m + 2:
        return frames
    out = frames[: n - m].astype(np.float32).copy()
    for k in range(m):
        w = k / m               # first frame = pure tail (continues the last frame), then fade to the head
        out[k] = (1 - w) * frames[n - m + k].astype(np.float32) + w * frames[k].astype(np.float32)
    return np.clip(out + 0.5, 255).astype(np.uint8)
```

The issue is that `w = k / m` means:

- When k=0 (first blended frame): w=0 → pure tail (last frame)
- When k=m-1 (last blended frame): w≈1 → nearly pure head (first frame)

This creates a visible "ghost" of the last frame overlaying the first frame at the loop point. The 50% opacity mentioned by the user corresponds to the middle of the blend (k ≈ m/2).

### Fix

Change the blending to use a more aggressive fade curve that reduces the ghost effect. Instead of linear interpolation, use an exponential or power curve that fades the tail more quickly:

```python
def close_loop(frames: np.ndarray, m: int) -> np.ndarray:
    n = len(frames)
    if m < 1 or n < 2 * m + 2:
        return frames
    out = frames[: n - m].astype(np.float32).copy()
    for k in range(m):
        # Use power curve: tail fades faster, head fades in slower
        w = (k / m) ** 2  # quadratic curve reduces ghost
        out[k] = (1 - w) * frames[n - m + k].astype(np.float32) + w * frames[k].astype(np.float32)
    return np.clip(out + 0.5, 255).astype(np.uint8)
```

Alternatively, make the fade frames configurable via `EngineConfig.loop_fade_curve` with options: 'linear', 'quadratic', 'cubic'.

---

## Issue 2: Loop Seam Cannot Be Allowed

### Description

When an animation fails with "Bad loop: no animation: the loop does not close", there is no way to allow it like other warnings.

### Root Cause

This is **intentional design**, not a bug. In `mirsal/mirsal/gates.py` line 314:

```python
OVERRIDABLE = ("inside_slot", "cross_slot")      # the two slot-geometry checks of a returned video are judgement calls; every technical block stays final
```

Only slot geometry blocks (character leaving/crossing its slot) are overridable by humans. The loop seam check is a **technical block** (format/codec/loop quality) and is final by design.

The error message in `gates.py` line 335 confirms this:

```python
raise refuse(f"This one failed a technical check ({', '.join(bad)}: format, size or codec) and cannot be allowed. Only a character that leaves or crosses its slot can be allowed.")
```

### Why This Design

A bad loop seam means the animation does not loop smoothly - it will have a visible jump when played repeatedly. This is a technical quality issue, not a creative judgment. Unlike slot geometry (where a character slightly leaving its cell might still be acceptable for the user's intent), a bad loop is objectively wrong for a looping sticker.

### Options

1. **Keep as-is** (recommended): The current design is correct. A bad loop should be fixed by re-generating the animation, not by allowing a broken one.
2. **Add to OVERRIDABLE** (not recommended): Add `"loop_seam"` to the `OVERRIDABLE` tuple. This would allow users to accept broken loops, but defeats the purpose of the quality check.
3. **Improve loop closing**: If the loop seam is too strict, adjust the thresholds in `EngineConfig` (loop_seam_max, loop_seam_ratio) or improve the `close_loop` algorithm.

### Recommendation

Keep the current design. If users are hitting this frequently, investigate whether the loop seam thresholds are too strict or the loop closing algorithm needs improvement.

---

## Issue 3: Chat Generation Hangs on "generate {subject}"

### Description

Casual AI mode replies very fast, but when saying "generate {subject}" it correctly expands inline, then shows "thinking" and never completes - the chat is taken hostage.

### Root Cause

The issue is **server-side** in the agent graph execution. The flow is:

1. User sends "generate {subject}" via `/api/chat/sessions/{sid}/messages`
2. Server's `chat_send` (server.py:416) creates a **daemon thread** to run `agent.execute(turn)` in the background
3. The agent graph runs: `understand` → `resolve` → `new` → `confirm` → `finish`
4. In `n_new` (graph.py:257), it calls `self.tools.plan()` which calls `tasks.preview()` (tools.py:70)
5. If live mode is on, `tools.create()` calls `self.c.live("sheet", body)` (tools.py:156) - the Higgsfield API

**The hang occurs because:**

1. **No timeout on Higgsfield API call**: The `self.c.live("sheet", body)` call has no explicit timeout. If the Higgsfield API hangs or is slow, the daemon thread blocks forever.

2. **No timeout on LLM call**: The `tasks.preview()` call (which uses the LLM to expand the prompt) may also have no timeout.

3. **Daemon thread isolation**: The thread is marked as `daemon=True` (server.py:427), which means it will be killed when the main process exits, but while the server is running, a hung thread will never release the session lock.

4. **Session lock not released**: The session lock is acquired in `agent.prepare()` (graph.py:137-141) and released in `agent.execute()`'s finally block (graph.py:167). However, if the thread hangs in a blocking I/O call, the finally block never executes.

The client-side polling in `agent.js` (lines 232-239) is correct - it polls indefinitely while `s.working` is true. The problem is the server never sets `working` to false because the thread is stuck.

### Investigation Steps

1. Check the server logs for the `/api/chat/sessions/{sid}/messages` endpoint
2. Check if the generation job is being created correctly
3. Check if the job status is being updated in the backend
4. Check if there's a timeout in the LangGraph agent that's not being caught

### Temporary Fix

Add a timeout to the polling so it doesn't hang forever:

```javascript
function startPoll() {
  clearTimeout(A.poll);
  A.since = A.since || Date.now();
  const tick = async () => {
    if (route_ !== "agent" || document.hidden || !A.sid) {
      A.busy = false;
      return;
    }
    let s = null;
    try {
      s = await loadSession(A.sid, true);
    } catch (e) {
      s = null;
    }
    if (!s) {
      if (A.sid) {
        A.busy = false;
        busyUi();
        A.poll = setTimeout(tick, 2500);
      }
      return;
    }
    // Add timeout: stop polling after 5 minutes
    if (Date.now() - A.since > 300000) {
      A.busy = false;
      A.since = 0;
      busyUi();
      toast("The generation timed out. Please try again.", 1);
      return;
    }
    if (AIU.needPoll(s)) {
      A.busy = !!s.working;
      A.poll = setTimeout(
        tick,
        s.working ? 700 : Date.now() - A.since > 120000 ? 4000 : 1600,
      );
    } else {
      A.busy = false;
      A.since = 0;
      busyUi();
      await loadSessions();
      agList();
    }
  };
  A.poll = setTimeout(tick, 500);
}
```

### Recommendation

This is a server-side issue. The client-side timeout is a band-aid. The real fix is to:

1. Ensure the server properly handles generation job failures
2. Ensure the server updates job status even on errors
3. Add proper error propagation from the LangGraph agent to the client

---

## Issue 4: Local Model Selection UI Missing

### Description

The user wants:

1. A cloud/local selector in the UI
2. List of available LM Studio models (not hardcoded)
3. Thinking on/off toggle

### Current State

In `mirsal/mirsal/llm.py`:

- Line 85-95: `provider()` returns 'local', 'openai', or 'none' based on environment variables
- Line 59-63: `local_model()` is hardcoded to `qwen3.5-4b:2` - it does NOT query LM Studio for available models
- Line 155: `reasoning_effort` is set to "none" by default for local models (no UI toggle)

In `mirsal/mirsal/console/agent.js`:

- Line 98-100: The pill shows "Local · {model}" or "Cloud · {model}" but there's no selector
- No UI for choosing cloud vs local
- No UI for listing available models
- No UI for thinking on/off

### Required Changes

#### 1. Add Model List API

Create a new endpoint `/api/models/list` that queries LM Studio for available models:

```python
# In console/server.py or a new models.py
async def list_models():
    """List available models from LM Studio."""
    from mirsal.llm import local_url
    try:
        url = f"{local_url()}/models"
        # Make request to LM Studio's /models endpoint
        # Return list of models
    except Exception as e:
        return {"models": [], "error": str(e)}
```

#### 2. Add Cloud/Local Selector UI

In `agent.js`, add a selector in the settings panel:

```javascript
function setSet() {
  const el = $("ai-set");
  if (!el) return;
  el.classList.toggle("on", A.setOpen);
  if (!A.setOpen) return;
  const st = A.sess
    ? A.sess.settings
    : {
        grid: "3x3",
        ask_before_spending: true,
        provider: "auto",
        model: null,
        thinking: false,
      };
  const a = A.agent || {};
  el.innerHTML = `<div class=r><div><b>AI Provider</b><small>Cloud or local model</small></div>
   <div class=ai-seg>
    <button data-act=agsetprov data-v=auto class="${st.provider === "auto" ? "on" : ""}">Auto</button>
    <button data-act=agsetprov data-v=local class="${st.provider === "local" ? "on" : ""}">Local</button>
    <button data-act=agsetprov data-v=openai class="${st.provider === "openai" ? "on" : ""}">Cloud</button>
   </div></div>
  <div class=r><div><b>Model</b><small>${st.provider === "local" ? "Available LM Studio models" : "OpenAI model"}</small></div>
   <select data-act=agsetmodel>${(a.models || []).map((m) => `<option value="${m}" ${st.model === m ? "selected" : ""}>${m}</option>`).join("")}</select></div>
  <div class=r><div><b>Thinking</b><small>Show reasoning steps</small></div>
  <button type=button class="ai-sw${st.thinking ? " on" : ""}" data-act=agsetthink role=switch aria-checked="${!!st.thinking}" aria-label="Thinking"></button></div>
  <div class=r><div><b>Grid</b><small>How many stickers in one sheet</small></div><div class=ai-seg><button data-act=agsetgrid data-v=3x3 class="${st.grid === "3x3" ? "on" : ""}">3×3</button><button data-act=agsetgrid data-v=2x2 class="${st.grid === "2x2" ? "on" : ""}">2×2</button></div></div>
  <div class=r><div><b>Ask before spending</b><small>Show the price and wait for your go-ahead</small></div><button type=button class="ai-sw${st.ask_before_spending ? " on" : ""}" data-act=agsetask role=switch aria-checked="${!!st.ask_before_spending}" aria-label="Ask before spending"></button></div>`;
}
```

#### 3. Add Settings Handlers

```javascript
ACT.agsetprov = async (el) => saveSet({ provider: el.dataset.v });
ACT.agsetmodel = async (el) => saveSet({ model: el.value });
ACT.agsetthink = async () =>
  saveSet({ thinking: !(A.sess ? A.sess.settings.thinking : false) });
```

#### 4. Update Backend to Respect Settings

The `/api/chat/sessions/{sid}/settings` endpoint needs to handle the new settings and pass them to the LLM calls.

#### 5. Update LLM Client

In `llm.py`, the `complete` function needs to respect the `thinking` setting:

```python
def complete(..., thinking: bool = False, ...):
    # ...
    if prov == "local":
        if thinking:
            optional["reasoning_effort"] = "medium"  # or "high"
        else:
            optional["reasoning_effort"] = "none"
```

### Recommendation

This is a feature request, not a bug. The changes required are:

1. Add LM Studio model list API
2. Add UI selectors for provider, model, and thinking
3. Wire up settings to the LLM client

This is a significant UI/UX enhancement that should be prioritized based on user demand.

---

## Issue 5: AI Chat UX Failures - Selection, Moderation, Model Selection

### Description

The user reported multiple UX failures in the AI chat:

1. **Clicking an image doesn't pass metadata**: When clicking on a sticker image and saying "this is bad", the system asks "which one say a number" instead of automatically using the clicked image's metadata (generation ID, sticker index).

2. **No selective regeneration**: Instead of regenerating only the selected stickers (e.g., keep 1-4, regenerate 5-9 as a 2x2 sheet), the system wants to recreate the entire 3x3 sheet.

3. **No content moderation**: The user asked for "superman in dubai" and one result was "superman as UAE woman in burkah" which is extremely racist. There was no content moderation check, and the vision judge (VLM) didn't kick in to flag this.

4. **Model selection UI is hardcoded**: The UI shows only "qwen3.5-4b:2" with no selection between:
   - Cloud vs local provider
   - Full list of available LM Studio models (currently hardcoded)
   - List of registered cloud providers
   - Thinking on/off toggle for LM Studio

### Root Cause Analysis

#### 1. Image Click Doesn't Pass Metadata

**Current behavior in `agent.js` lines 196-198:**

```javascript
ACT.agtile = (el) => {
  if (el.closest(".car-track") && el.closest(".car-track").dataset.dragged)
    return;
  const id = el.dataset.id;
  if (!id || id[0] === "w") return;
  if (A.sel.has(id)) A.sel.delete(id);
  else A.sel.add(id);
  document
    .querySelectorAll(`.ag-tile[data-id="${CSS.escape(id)}"]`)
    .forEach((t) => t.classList.toggle("is-sel", A.sel.has(id)));
  selChips();
};
```

The tile click adds the sticker ID to `A.sel` (selection set), which is sent in the message payload. However:

- The resolver (`resolver.py` lines 148-154) only uses the selection when the text contains "these/this/those/selected/them/it"
- When the user says "this is bad" without those trigger words, the resolver falls back to asking for a number
- The selection is cleared after sending (`agent.js` line 228), so the context is lost

**Why it asks for a number:**
In `resolver.py` line 497:

```python
if not (r.positive or r.negative):
    t.reply = t.reply or "Tell me which numbers you like or don't, for example \"I like 2 and 7 but not 3\"."
```

The feedback node only looks at `r.positive` and `r.negative`, which are populated by the polarity rules (lines 126-140). If the user says "this is bad" without "like/hate/dislike" keywords, the polarity rules don't match, so it asks for clarification.

#### 2. No Selective Regeneration

**Current behavior in `graph.py` n_feedback (lines 493-513):**

- When feedback is given, it only records the feedback in memory (`add_feedback`)
- It does NOT trigger a selective regeneration
- The chips offered are "Make another set" and "Redo {sticker}" but "Redo" only regenerates that ONE sticker, not a selection

**Why it doesn't do selective regeneration:**

- The `n_feedback` node only adds feedback to memory
- There is no edge from feedback to a selective create with subset of stickers
- The agent's graph doesn't have a "regenerate selected as N×N" node

#### 3. No Content Moderation

**CRITICAL FINDING:** The actual prompt used was completely innocent:

```
Subject: a round blue face with big eyes and a smiling mouth.
Style: flat vector illustration, bold clean shapes, solid vibrant colours, friendly proportions.
```

The prompt contains NO references to:

- Superman
- Dubai/UAE
- Burkah
- Woman
- Cultural or religious references

**The model hallucinated racist content entirely on its own.** Higgsfield's image generation model decided to generate "superman as UAE woman in burkah" from a prompt about a "round blue face with big eyes". This is a severe provider safety failure.

**Current state:**

- The vision judge (`vision/judge.py`) only judges sticker quality (concept, expression, style, artefacts)
- It does NOT judge content safety (racism, hate speech, offensive content)
- The judge's system prompt (line 36-44) only mentions quality, not safety
- There is no separate moderation step before or after generation
- The provider's content filter FAILED completely

**Why it didn't flag racist content:**

- The judge's `REASONS` list (line 31-33) does not include content safety codes
- The system prompt doesn't instruct the model to check for offensive/racist content
- Higgsfield's own safety filters failed to catch this racist output
- The user only sees the result after it's generated

#### 4. Model Selection UI is Hardcoded

**Current state in `llm.py`:**

- Line 24: `LOCAL_MODEL = "qwen3.5-4b:2"` - hardcoded, never queries LM Studio
- Line 59-63: `local_model()` returns the hardcoded value or env var override
- Line 85-95: `provider()` chooses local|openai|auto but never lists available models
- Line 6: `reasoning_effort: "none"` is hardcoded for local models (no UI toggle)

**Current state in `agent.js`:**

- Line 98-100: The pill shows the model name but has no selector
- Line 216-219: Settings panel only has grid and "ask before spending" - no model selection
- No UI for:
  - Choosing between cloud/local
  - Listing available LM Studio models
  - Listing registered cloud providers
  - Toggling thinking mode

### Required Changes

#### 1. Fix Image Click Metadata Passing

**Option A: Improve resolver rules (minimal change)**

- Add "this is bad" / "this one is offensive" to NEG pattern in `resolver.py` line 19
- Add "make another one like this" / "redo this" to positive patterns
- Ensure selection is used when text refers to "this" without explicit trigger words

**Option B: Always use selection when available (better UX)**

- When a sticker is clicked and the user says anything that could refer to it, default to using the selection
- Only ask for clarification if the selection is ambiguous (multiple stickers selected)

**Option C: Add explicit actions (best UX)**

- Add context menu on sticker tiles: "Regenerate this", "Keep this, regenerate others", "Report offensive"
- Pass action type with the message so the agent knows the intent without parsing text

#### 2. Add Selective Regeneration

**Add new graph node `n_regenerate_selected`:**

```python
def n_regenerate_selected(self, state: State) -> dict:
    t: Turn = state["turn"]
    selected = t.res.stickers  # ['G012/S3', 'G012/S5', ...]
    if not selected:
        return {}
    # Calculate optimal grid size for the selected count
    n = len(selected)
    grid = "1x1" if n == 1 else "2x2" if n <= 4 else "3x3"
    # Create new generation with only selected stickers as references
    refs = [{"source": s, "target": None, "role": "STYLE"} for s in selected]
    r = self.tools.create(t.sess.get("focus", {}).get("generation"), grid=grid, refs=refs)
    t.trace.retitle(f"regenerating {n} sticker(s) as {grid}")
    return {"generation": r["generation"]}
```

**Wire it in the graph:**

- Add edge from `n_feedback` to `n_regenerate_selected` when action type is "regenerate_selected"
- Add edge from `n_edit` to `n_regenerate_selected` when selected count > 1

#### 3. Add Content Moderation

**Option A: Extend vision judge to include safety (recommended)**

- Add safety reasons to `REASONS`: `"OFFENSIVE_CONTENT"`, `"HATE_SPEECH"`, `"RACIST_CONTENT"`, `"SEXUAL_CONTENT"`, `"VIOLENCE"`
- Update system prompt to check for content safety
- Add safety check to sheet generation before cutting

**Option B: Separate moderation layer (better for production)**

- Add a moderation API call (OpenAI moderation API or similar) before generation
- Check the prompt and generated image for policy violations
- Block generation before spending credits

**Option C: Provider-side filtering (rely on Higgsfield)**

- Higgsfield may have content filters
- Expose their filtering status in the job result
- Show the user why a generation was rejected

#### 4. Add Model Selection UI

**Add model list API in `server.py`:**

```python
if path == "/api/models/list":
    """List available models from LM Studio and configured cloud providers."""
    models = []
    # Local models from LM Studio
    try:
        from mirsal import llm
        if llm.local_reachable():
            resp = json.loads(urllib.request.urlopen(f"{llm.local_url()}/models", timeout=5).read())
            models.extend([{"id": m["id"], "provider": "local", "name": m["id"]} for m in resp.get("data", [])])
    except Exception:
        pass
    # Cloud models (configured)
    if os.environ.get(llm.KEY_VAR):
        models.append({"id": llm.DEFAULT_MODEL, "provider": "openai", "name": "OpenAI GPT-4.1-mini"})
    return self._json(200, {"models": models})
```

**Add UI selectors in `agent.js`:**

```javascript
function setSet() {
  const el = $("ai-set");
  if (!el) return;
  el.classList.toggle("on", A.setOpen);
  if (!A.setOpen) return;
  const st = A.sess
    ? A.sess.settings
    : {
        grid: "3x3",
        ask_before_spending: true,
        provider: "auto",
        model: null,
        thinking: false,
      };
  const a = A.agent || {};
  el.innerHTML = `<div class=r><div><b>AI Provider</b><small>Cloud or local model</small></div>
   <div class=ai-seg>
    <button data-act=agsetprov data-v=auto class="${st.provider === "auto" ? "on" : ""}">Auto</button>
    <button data-act=agsetprov data-v=local class="${st.provider === "local" ? "on" : ""}">Local</button>
    <button data-act=agsetprov data-v=openai class="${st.provider === "openai" ? "on" : ""}">Cloud</button>
   </div></div>
  <div class=r><div><b>Model</b><small>${st.provider === "local" ? "Available LM Studio models" : "OpenAI model"}</small></div>
   <select data-act=agsetmodel>${(a.models || []).map((m) => `<option value="${m.id}" ${st.model === m.id ? "selected" : ""}>${m.name}</option>`).join("")}</select></div>
  <div class=r><div><b>Thinking</b><small>Show reasoning steps</small></div>
   <button type=button class="ai-sw${st.thinking ? " on" : ""}" data-act=agsetthink role=switch aria-checked="${!!st.thinking}" aria-label="Thinking"></button></div>
  <div class=r><div><b>Grid</b><small>How many stickers in one sheet</small></div><div class=ai-seg><button data-act=agsetgrid data-v=3x3 class="${st.grid === "3x3" ? "on" : ""}">3×3</button><button data-act=agsetgrid data-v=2x2 class="${st.grid === "2x2" ? "on" : ""}">2×2</button></div></div>
  <div class=r><div><b>Ask before spending</b><small>Show the price and wait for your go-ahead</small></div><button type=button class="ai-sw${st.ask_before_spending ? " on" : ""}" data-act=agsetask role=switch aria-checked="${!!st.ask_before_spending}" aria-label="Ask before spending"></button></div>`;
}
```

**Add handlers:**

```javascript
ACT.agsetprov = async (el) => saveSet({ provider: el.dataset.v });
ACT.agsetmodel = async (el) => saveSet({ model: el.value });
ACT.agsetthink = async () =>
  saveSet({ thinking: !(A.sess ? A.sess.settings.thinking : false) });
```

**Load models on agent load:**

```javascript
async function loadAgent() {
  const r = await api("/api/chat/agent");
  if (r.ok) A.agent = r.j;
  const mr = await api("/api/models/list");
  if (mr.ok) A.agent.models = mr.j.models;
  pill();
}
```

**Update LLM client to respect thinking setting:**
In `llm.py`, update `complete` to use `reasoning_effort` based on setting:

```python
if prov == "local" and not thinking:
    optional["reasoning_effort"] = "none"
```

### Recommendation

**Priority Order:**

1. **Fix image click metadata passing** (HIGH) - Blocks basic chat UX
2. **Add content moderation** (HIGH) - Safety issue (racist content was generated)
3. **Fix "which sticker" response routing** (HIGH) - Number replies treated as new generation instead of edit
4. **Add selective regeneration** (MEDIUM) - Feature enhancement, improves efficiency
5. **Add model selection UI** (MEDIUM) - Feature enhancement, gives user control

**Quick wins:**

- Improve resolver rules to handle "this is bad" (1 hour)
- Add "OFFENSIVE_CONTENT" to vision judge reasons (30 minutes)
- Add thinking toggle to settings UI (30 minutes)
- Fix intent classification for number-only responses to context (1 hour)

**Larger projects:**

- Add selective regeneration graph node (2-3 hours)
- Add model list API and full UI (4-6 hours)
- Implement proper moderation layer (separate from judge) (8+ hours)

---

## Issue 6: Number Response to "Which Sticker" Treated as New Generation

### Description

When the system asks "which sticker has the issue?" and the user replies with a number (e.g., "5"), instead of routing to image edit, the system treats it as a new generation request ("5" as a subject).

### Root Cause

**In `resolver.py` (lines 142-147):**
When the user says "5", the resolver correctly identifies it as sticker 5:

```python
# 4. plain numbers ("make number 3 happier", "animate 2 and 5")
if base and not r.stickers:
    nums = _numbers(low, base_n)
    if nums:
        r.stickers = [f"{base}/S{i}" for i in nums]
        r.how = "number"
```

**In `resolver.py` (lines 217-229):**
The intent classification requires an action verb to classify as EDIT_STICKERS:

```python
elif has_generation and (refs or concept_edit) and re.search(r"\b(make|redo|regenerate|change|fix|replace|swap|improve|less|more|bigger|smaller|happier|sadder|funnier|cuter|different)\b", t):
    intents, conf = ["EDIT_STICKERS"], 0.8
# ... other rules ...
elif len(t.split()) <= 8 and not t.endswith("?"):
    intents, conf = ["NEW"], 0.62  # "falcon dancing", "teddy bear with a book": a bare subject is a request
```

When the user says just "5" (no action verb):

- It's not a CONFIRM/CANCEL (no pending)
- It's not ANIMATE/SEARCH/SETTINGS (no keywords)
- It's not EDIT_STICKERS (no action verb like "make", "redo", "change")
- It's not FEEDBACK (no "like/hate/dislike")
- It's not SMALLTALK
- It falls through to line 229: `len(t.split()) <= 8` → classified as NEW (bare subject)

**The problem:** The intent classifier doesn't have context awareness. It doesn't know that the previous message was a clarification question "which sticker has the issue?". It treats every message independently.

### Required Fix

**Option A: Add context-aware intent classification (best UX)**

In `graph.py` `n_understand`, pass the previous message context to `classify`:

```python
def classify(text: str, has_pending: bool, has_generation: bool, has_selection: bool = False, previous_message: str | None = None) -> tuple[list, float]:
    # ... existing rules ...

    # NEW: If previous message was a clarification question and current is a number/selection, treat as ANSWER
    if previous_message and re.search(r"\b(which|what|which one)\b", previous_message.lower()):
        nums = _numbers(t, 9)  # assume 3x3 max
        if nums:
            return ["ANSWER"], 0.9

    # ... rest of rules ...
```

**Option B: Add special handling in resolver (minimal change)**

In `resolver.py`, add a check for number-only responses:

```python
def resolve(text: str, ctx: dict) -> Resolution:
    # ... existing code ...

    # NEW: If text is just a number and there's a generation, assume it's "edit this sticker"
    if base and not r.stickers and re.match(r"^\d+$", t.strip()):
        nums = _numbers(t, base_n)
        if nums:
            r.stickers = [f"{base}/S{i}" for i in nums]
            r.how = "number"
            # Mark it as an edit intent so the graph routes correctly
            r._implicit_edit = True  # new flag

    # ... rest of code ...
```

Then in `graph.py` `n_resolve`, check for this flag:

```python
def n_resolve(self, state: State) -> dict:
    t: Turn = state["turn"]
    # ... existing code ...

    # NEW: If resolver marked as implicit edit, add EDIT_STICKERS to queue
    if getattr(t.res, "_implicit_edit", False) and "EDIT_STICKERS" not in t.queue:
        t.queue = ["EDIT_STICKERS"] + t.queue

    # ... rest of code ...
```

**Option C: Add ANSWER intent (most robust)**

Add ANSWER to INTENTS in `brain.py`:

```python
INTENTS = ("NEW", "ANOTHER", "EDIT_STICKERS", "ANIMATE", "FEEDBACK", "REVIEW", "ASK", "CHANGE_SETTINGS", "SEARCH", "SMALLTALK", "AMBIGUOUS", "ANSWER")
```

Add classification rule in `resolver.py`:

```python
def classify(text: str, has_pending: bool, has_generation: bool, has_selection: bool = False) -> tuple[list, float]:
    # ... existing rules ...

    # NEW: Number-only or selection-only response = ANSWER intent
    if re.match(r"^\d+$", t.strip()) or (has_selection and re.match(r"^(these|this|those|them|it)$", t)):
        return ["ANSWER"], 0.9

    # ... rest of rules ...
```

Add n_answer node in `graph.py`:

```python
def n_answer(self, state: State) -> dict:
    t: Turn = state["turn"]
    if t.res.stickers:
        t.reply = f"Got it, sticker {', '.join(str(s.split('/')[1][1:]) for s in t.res.stickers)}. What should I do with it?"
        t.chips = [{"label": "Regenerate it", "text": f"regenerate {t.res.stickers[0].split('/')[1][1:]}"},
                  {"label": "Edit it", "text": f"edit {t.res.stickers[0].split('/')[1][1:]}"},
                  {"label": "Keep it", "text": f"keep {t.res.stickers[0].split('/')[1][1:]}"}]
    else:
        t.reply = "I couldn't tell which sticker you meant. Click on it or tell me the number."
    return {}
```

### Recommendation

**Option C (Add ANSWER intent)** is the most robust because:

- It explicitly handles the "answering a question" case
- It doesn't assume the user wants to edit (asks what to do)
- It's consistent with the agent's design (explicit intents)
- It handles both number-only and selection-only responses

**Quick fix:** Option B (implicit edit flag) is faster to implement (1 hour) but less flexible.

**Priority:** HIGH - This is a major UX frustration. The user can't efficiently give feedback on specific stickers.

---

## Issue 7: Moving Several Stickers to Another Pack Moves Only One

### Description

Reported by Haitham, 2026-10-02:

- Moving multiple emojis to another pack **only moves them 1 by 1**.
- Selecting several should offer **delete / create pack** as bulk actions.
- When several are selected and moved to a **new** pack, only one moves, and the
  selection **persists on the remaining stickers** — wrong: all of them should move at once.

### Root Cause

**Selection exists, the move handler ignores it.**

`mirsal/mirsal/console/packs.js:44` starts a drag with a single id:

```javascript
S_PACK.addEventListener('dragstart',e=>{const c=e.target.closest('.cell[data-id]');if(!c)return;DRAG=c.dataset.id;...
```

and the drop handler (`packs.js:52-55`) posts exactly one move:

```javascript
const res=await post(`/api/packs/${PACK_ID}/stickers/${sid}/move`,{to:r.dataset.id});
```

`SEL` (the multi-select) is only read by `selBarHtml(n)` / `mqResult` for bulk
*reorder* and *delete* (`packs.js:17`), never by the drop handler. The picker path
has the same shape: `ACT.lcmove` (`packs.js:80-81`) posts one `s.id`.

So with N selected, the drag carries `DRAG` = the id of the cell under the cursor,
one POST runs, and `SEL` is never cleared — which is exactly the observed
"one moved, selection still on the rest".

### Required Changes

1. **Bulk move on drop**: on `drop`, if `SEL.size > 1 && SEL.has(DRAG)`, loop the
   selected ids and POST each `/api/packs/{from}/stickers/{id}/move` (or better, add
   `POST /api/packs/{id}/stickers/move` taking `{to, ids:[]}` so it is one round trip
   and one transaction).
2. **Bulk actions bar**: when `n > 1`, `selBarHtml` should offer **Move to pack…**,
   **New pack…** (creates a pack and moves the selection into it) and **Delete**,
   alongside the existing reorder controls.
3. **Clear the selection after a successful move** (`SEL.clear(); selRefresh();`) and
   re-render the grid, so nothing "persists on the remaining stickers".
4. **Server-side**: check that `/api/packs/{id}/stickers/{sid}/move` refuses a move to
   a pack the caller does not own, and make the multi-move atomic (all or nothing).

### Test That Would Pin It

`tests/test_library.py`: select 3 stickers, POST the bulk move, assert all 3 have the
new `pack_id`, the source pack lost 3, and the response reports `moved == 3`.

---

## Issue 8: VLM / Vision Follow-ups

### Description

Reported by Haitham, 2026-10-02, four separate items:

1. **Chat does not know what it made.** Asked *"what did you just create"*, it replied
   that it doesn't know.
2. **No per-frame vision view.** There should be an option to open the **full sheet**
   and mark **each frame with its VLM transcription**, whether the sheet was 3×3 or
   2×2. That logic does not exist — write the function/module for it.
3. **Consent UX.** Instead of the old per-run *"allow VLM / no"*, ask once:
   **"Allow AI vision of generated media?"** — a single decision per session.
4. **The loop artifact is still there.** The first frame still shows a transition used
   to ease the looping; it looks horrible — report it (it is Issue 1 above, still open).

### Root Cause / Current State

**1. "what did you just create" → "idk" `[INFER]`**

`memory.summary_text()` (`mirsal/mirsal/agent/memory.py:252-281`) rebuilds the turn
context from `subjects[]`, `passes[]`, likes/dislikes and preferences. It only contains
a pass if the **chat** created it (`add_pass`, `memory.py:165`). A generation started
from the Studio/CLI is never recorded in the session, so the deterministic summary has
nothing to answer with, and `brain.answer(t.text, facts)` (`graph.py:570`) is handed an
empty fact list. The judge's verdicts are also invisible: `vision/judge.py:398` writes a
history line with `actor="vlm"` into `result.json`, but no history line is ever folded
into `summary_text`.

Confirm by: generate in the Studio, then ask the same question in chat — expect the
same "don't know". If instead the Studio generation *does* appear, the bug is in
`subject_for_generation` keying (`memory.py:211-212`).

**2. Per-frame transcription does not exist `[READ]`**

`vision/judge.py` already judges per sticker (`judge_generation` → `_structured("VLM_STICKER", …)`,
`judge.py:308`) and stores a verdict with reasons (`judge.py:398-407`), and it also has a
sheet-level call (`judge.py:332`, `_flatten(sheet_png, 768)`). What is missing is the
**frame → text** product: no route returns a caption per cell, and the UI has no view for it.

**3. Consent is per call, not per session `[READ]`**

The vision judge is triggered from the pipeline/`judge` action; there is no session-level
flag in `settings` (`memory.py:28 DEFAULT_SETTINGS` has `grid`, `ask_before_spending`, `ai`
only — no `allow_vlm`). So every run re-asks.

**4. Loop artifact `[READ]`** — this is Issue 1 of this report (`close_loop`,
`engine/video.py:92-101`). The quadratic curve proposed there is not enough; see below.

### Required Changes (the function to write)

New module `mirsal/mirsal/vision/transcribe.py`:

```python
"""Per-frame vision: one caption per cell of a sheet, cached, session-consent aware."""

@dataclass
class FrameCaption:
    generation_id: str
    index: int            # 0..n-1, works for 3x3, 2x2, any grid
    grid: tuple[int, int] # (rows, cols) read from result.json, never assumed
    png: str              # path relative to out/
    caption: str
    verdict: str | None   # APPROVE / REJECT from the same judge call, or None
    reasons: list[str]

def captions_for(out: Path, gid: str, *, force: bool = False) -> list[FrameCaption]:
    """Every cell of generation `gid` with its VLM caption. Grid-agnostic: reads
    `result.json`'s grid and stickers[], so 2x2 and 3x3 use the same code path.
    Cached on the same key scheme as vision/judge.py:289 (sha256(png) + model + version)."""

def sheet_with_captions(out: Path, gid: str, ...) -> dict:
    """JSON for the UI: {grid, cells: [{index, png, caption, verdict, reasons}]}."""
```

Wire-up:

- `GET /api/generations/{id}/captions` → `sheet_with_captions` (owner + the batch's owner).
- Consent: add `allow_vlm: bool` to `DEFAULT_SETTINGS` (`memory.py:28`), written once from
  `POST /api/chat/sessions/{sid}/settings` (`server.py:1012-1021` already has an
  allow-list — add the key), surfaced as the single prompt
  **"Allow AI vision of generated media?"** shown the first time a session would
  otherwise trigger a judge run. When false, `judge_generation` is skipped and the
  stickers stay READY and unjudged (`FAIL_CLOSED` behaviour, `judge.py:90-92`).
- UI: in the sheet view, click a cell → the VLM caption + verdict under it; a toggle
  "Show AI captions" that is enabled by the same session setting.

### Test That Would Pin It

`tests/test_vision.py`: build a 2×2 fixture (not only 3×3), assert `captions_for`
returns 4 entries with indices 0-3 and the grid read from `result.json`; assert a
second call with `force=False` does not hit the model; assert `allow_vlm=False`
produces 0 model calls and leaves `review.still == "PENDING"`.

### 4. Loop transition — still open

Haitham still sees the first-frame transition used to ease looping. The `close_loop`
blend in `mirsal/mirsal/engine/video.py:92-101` writes `m` blended frames at the head of
the clip, so the very first frames *are* a cross-fade — that is what is being seen.

If the quadratic curve already proposed in Issue 1 is not enough, the options are:
(a) reduce `m` to 1 and only blend the single wrap frame, (b) blend in the **tail** instead
(fade the last `m` frames toward frame 0, so the head stays pure), or (c) drop blending and
make the generator return a clip whose first and last frame are already identical. Any of
these must keep `loop_seam` passing — that check is a technical BLOCK and is not
overridable (`gates.py:314`, Issue 2).

---

## Summary

| Issue                                 | Severity | Type        | Action                                                                        |
| ------------------------------------- | -------- | ----------- | ----------------------------------------------------------------------------- |
| 1. Animation ghost silhouette         | Medium   | Bug         | Change `close_loop` to use quadratic fade curve                               |
| 2. Loop seam not overridable          | N/A      | Design      | Intentional - keep as-is                                                      |
| 3. Chat generation hangs              | High     | Bug         | Add client-side timeout + fix server-side job handling                        |
| 4. Missing model selection UI         | Medium   | Feature     | Add cloud/local selector, model list, thinking toggle                         |
| 5. AI Chat UX failures                | High     | Bug/Feature | Fix metadata passing, add moderation, selective regen, model UI               |
| 6. Number response treated as new gen | High     | Bug         | Add ANSWER intent or context-aware classification for clarification responses |
| 7. Bulk move to another pack         | High     | Bug/Feature | Make the drop handler use the selection; add Move/New pack/Delete bulk bar; clear selection after |
| 8. VLM follow-ups                    | High     | Feature     | Chat memory of Studio generations; per-frame captions module + route; one-time "Allow AI vision of generated media?" setting; loop transition |

**Priority Order:**

1. Fix image click metadata passing (Issue 5) - blocks basic chat UX
2. Add content moderation (Issue 5) - safety issue (racist content was generated)
3. Fix number response routing (Issue 6) - UX blocker for giving feedback
4. Fix chat generation hang (Issue 3) - blocks core functionality
5. Fix animation ghost (Issue 1) - affects visual quality
6. Add selective regeneration (Issue 5) - feature enhancement
7. Add model selection UI (Issue 4/5) - feature enhancement
8. Document loop seam design (Issue 2) - no action needed
