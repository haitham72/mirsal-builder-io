# Devin Report: 4 Issues Investigation

**Date:** 2026-10-02  
**Repository:** haitham72/mirsal-builder-io  
**Branch:** merge/generate-advanced

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

## Summary

| Issue                         | Severity | Type    | Action                                                 |
| ----------------------------- | -------- | ------- | ------------------------------------------------------ |
| 1. Animation ghost silhouette | Medium   | Bug     | Change `close_loop` to use quadratic fade curve        |
| 2. Loop seam not overridable  | N/A      | Design  | Intentional - keep as-is                               |
| 3. Chat generation hangs      | High     | Bug     | Add client-side timeout + fix server-side job handling |
| 4. Missing model selection UI | Medium   | Feature | Add cloud/local selector, model list, thinking toggle  |

**Priority Order:**

1. Fix chat generation hang (Issue 3) - blocks core functionality
2. Fix animation ghost (Issue 1) - affects visual quality
3. Add model selection UI (Issue 4) - feature enhancement
4. Document loop seam design (Issue 2) - no action needed
