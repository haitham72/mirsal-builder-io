# Prompt: draw Mirsal Builder as Excalidraw diagrams

Paste everything below the line into an LLM that can read this repository (an IDE agent such as Claude Code, Cursor or Windsurf opened on the repo root). It must read the files itself; do not summarise the project for it.

---

You are drawing the architecture of **Mirsal Builder**, a local app that makes animated Telegram stickers (and particle effects) from text, images and chat. Your output is a set of **Excalidraw files** that anyone can open at excalidraw.com (File → Open) and understand in one look: clean, airy, consistent, every box with an icon, a title and a subtitle, arrows labelled with what flows.

## 1. Read first (facts come only from these; never invent a component)

- `README.md` (the index: what exists), `CLAUDE.md` (rules 10-13: the golden path, gates, "Use it anyway", spending)
- `docs/engine-and-studio.md` ("Lifecycle", "Engine", "Batch groups", "Remove batch", "Emptying the trash")
- `docs/generation.md` ("Prompts", "The Higgsfield CLI", "Jobs", "Credits and usage", "Several paid jobs at once")
- `docs/agent-and-chat.md` ("One turn", "Memory", "Models", "The agentic creator", "Several subjects, per-subject feedback, taste", "Particle sets in the chat", "Edits by what they mean")
- `docs/particles.md`, `docs/effects.md`, `docs/store-and-search.md`, `docs/api.md`
- `plan.md` and `docs/office_lan_plan.md`, `docs/tickets_plan.md` (PLANNED work: draw it only in diagram 7, dashed)
- When a doc is unclear, open the code it names (`mirsal/mirsal/agent/graph.py`, `flow/pipeline.py`, `flow/gates.py`, `generation/jobs.py`, `flow/particle_sets.py`) and draw what the code does.

## 2. The diagrams (one `.excalidraw` file each, in `docs/diagrams/`)

| file | what it shows | must include |
|---|---|---|
| `01-overview.excalidraw` | the whole system on one page | the screens (AI chat, Studio, Library, Create, Settings) → the HTTP API → engine / flow / generation / agent / store / services → the outside world (Higgsfield: Nano Banana 2 for sheets, Kling for video; LM Studio; OpenAI for the enhancer; Postgres; Redis; the Telegram bot; the `out/` files) |
| `02-golden-path.excalidraw` | how a sticker pack is made | request → plan (G1) → sheet → Python cuts and checks → stills (G2) → video sheet from approved stickers only (G3) → Kling video → frame-by-frame boundary check → animations (G4) → pack (G5) → Telegram. Back-arrows: **Use it anyway** on a blocked picture, reject → regenerate one sticker (1x1), take back. The verifier (44 checks) as a side box touching every stage |
| `03-ai-chat-turn.excalidraw` | what happens when someone types in the chat | the message → resolver / intent → **memory lookup** (this chat's session, previous sessions, per-subject memory and taste, the focused sticker) → the LangGraph agent's nodes → the tools (the same engine functions the Studio calls) → price card and go-ahead before any spend → the step trace → the reply and its cards. Show where memory is read and where it is written back |
| `04-paid-generation.excalidraw` | a paid job end to end | price shown → the person's go → job ticket written BEFORE waiting → Higgsfield CLI → result → batch; up to 3 jobs in flight; the ledger (`model_calls`); stalled-job recovery; the daily cap |
| `05-particles.excalidraw` | particles for a sticker | sticker → New version → three sources (sprites from the sticker · AI image sprites · Kling animated from scratch) → the simulator (Energy / Float / Swirl / Size) → Save (a row v1, v2…) / Save as new → Render → Add to pack (In pack ✓); rows live under the sticker; Echo test in chat |
| `06-data.excalidraw` | where things live | `out/` (batches `G###/result.json`, `library.json`, particle sets `P###`, effect runs `E###`, jobs `J###`, chat sessions `S###`, trash) mirrored to Postgres tables (generations with `group_id`, stickers, reviews, tasks, model_calls, sessions, sticker_index with vectors); Redis as a disposable cache; batch groups (a family: root + variations) |
| `07-next.excalidraw` | PLANNED, every box dashed and grey-tinted, titled "Planned (plan.md)" | FastAPI on uvicorn; streaming chat; the ticket logger; office sign-in on the LAN (HTTPS) → *Waiting for approval* → Telegram admin card (Approve / Reject / Admin) → 10 credits; Trending gallery (share, like, comment, use in my workflow) |

At most ~25 boxes per diagram. If a diagram needs more, split it (`03a`, `03b`) rather than crowd it.

## 3. The look (apply to every file)

- **Every box**: a rounded rectangle 280 × 110, text inside it in three lines: an **emoji icon + title** (bold feel: fontSize 22), then a **subtitle** of at most 6 words (fontSize 16), e.g. `🎨 Studio` / `explicit controls, every gate`. Use one fitting emoji per box (🎨 Studio, 💬 AI chat, ⚙️ engine, 🧠 agent, 🗄️ Postgres, ⚡ Redis, 🤖 LM Studio, 🎬 Kling, 🍌 Nano Banana, ✈️ Telegram, 📁 out/, ✅ gate, 🛑 check, 💳 credits, ✨ particles, 🔁 retry).
- **Colours by area** (backgroundColor, stroke a darker shade): screens `#e7f5ff`/`#1971c2`, engine and flow `#ebfbee`/`#2f9e44`, AI and agent `#f3f0ff`/`#6741d9`, paid providers `#fff4e6`/`#e8590c`, storage `#f8f9fa`/`#495057`, human gates `#fff9db`/`#f08c00`, blocks and checks `#fff5f5`/`#e03131`. Planned (diagram 7): stroke `#868e96`, `strokeStyle: "dashed"`, background `#f1f3f5`.
- **Layout**: left to right (or top to bottom for a pipeline), a 20 px grid, columns 360 px apart, rows 180 px apart, nothing overlapping, at least 60 px between boxes. Group a layer inside a large light frame rectangle with a 20 px label in its top-left corner (e.g. "Screens", "Engine", "Outside world").
- **Arrows**: bound to their boxes at both ends, a short label on each (`plan`, `price → go`, `frames`, `reads memory`, `writes`), `endArrowhead: "arrow"`. Back-arrows (retry, Use it anyway, take back) are curved (three points) and use the red or amber stroke of what triggers them. Two-way flows get two arrows, not one double-headed arrow.
- **Each file**: a title text at the top-left (fontSize 36, e.g. "How a sticker pack is made") and a small legend box at the bottom-right explaining the colours.
- Font: `fontFamily: 5` (Excalifont, the hand-drawn one) for everything; `roughness: 1`.

## 4. The file format (Excalidraw JSON, version 2: get this exactly right)

```json
{"type":"excalidraw","version":2,"source":"https://excalidraw.com","elements":[...],"appState":{"viewBackgroundColor":"#ffffff","gridSize":20},"files":{}}
```

Every element has: `id` (unique), `type`, `x`, `y`, `width`, `height`, `angle: 0`, `strokeColor`, `backgroundColor`, `fillStyle: "solid"`, `strokeWidth: 2`, `strokeStyle`, `roughness: 1`, `opacity: 100`, `groupIds: []`, `frameId: null`, `roundness` (`{"type":3}` for rectangles, `{"type":2}` for arrows), `seed` (an integer), `version: 1`, `versionNonce` (an integer), `isDeleted: false`, `boundElements` (array or null), `updated: 1`, `link: null`, `locked: false`.

- **Text inside a box**: a `text` element with `containerId` = the box id, `text` and `originalText` (the three lines joined by `\n`), `fontSize`, `fontFamily: 5`, `textAlign: "center"`, `verticalAlign: "middle"`, `lineHeight: 1.25`, `autoResize: true`; the box lists it in its `boundElements` as `{"type":"text","id":…}`.
- **Arrows**: `type: "arrow"`, `x`/`y` at the start point, `points` relative to it (`[[0,0],[dx,dy]]`, or three points for a curve), `startBinding: {"elementId": box, "focus": 0, "gap": 8}`, `endBinding` the same, `startArrowhead: null`, `endArrowhead: "arrow"`; **both boxes list the arrow** in their `boundElements` as `{"type":"arrow","id":…}`; the label is a text element with `containerId` = the arrow id (and the arrow lists it).

## 5. Check before you hand it over

Write and run a small script (Python or Node) that, for every file: parses the JSON; checks ids are unique; checks every `containerId`, `startBinding` and `endBinding` points to an existing element and that the target lists it back in `boundElements`; checks no two boxes overlap; counts boxes and arrows. Fix and re-run until it is clean, then print the counts per file. Also add `docs/diagrams/README.md`: one line per diagram, what it shows.

If generating the JSON by hand gets messy, generate it with a short script (a list of boxes with grid positions and a list of edges in, a valid `.excalidraw` file out) and keep that script as `docs/diagrams/build.py` so the diagrams can be regenerated.
