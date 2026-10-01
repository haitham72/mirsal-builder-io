# Phase 4 — LangGraph + Creative Intelligence

**Prerequisite:** Phase 3 exit is met.

**Goal:** the system understands creative direction and remembers it.
- A LangGraph graph orchestrates the Phase 1–3 pipeline.
- LLMs turn free text into **structured state**: intents, stable sticker IDs, concept plans, feedback.
- A vision model judges and annotates results.

Every user reference ends as an ID like `G012/S3`. Every change creates a new generation with lineage.

**Not in this phase:** an HTTP API or a frontend. Interaction is a terminal REPL. That is the whole of Phase 5. **Redis is introduced in this phase** (see below).

> Conversation is an interface; structured state is the system of record. The LLM orchestrates the deterministic pipeline and never generates media or judges pixels.

There are three checkpoints, reviewed in order: **4A** graph + references + feedback, **4B** persistent slots + transformation templates, **4C** annotation + multi-reference + memory.

---

## What Haitham sees at the end

```
python -m mirsal chat
> make my dog as banana stickers
  G012 · 9/9 · S1 Dancing banana 💃  S2 Shocked banana 😱  S3 Squashed banana 🫠  S4 Dog-banana …
> I like 2 and 7 but not 3 and 4
  noted: +G012/S2 +G012/S7  −G012/S3 −G012/S4
> make number 3 less flattened
  G013 (from G012) · regenerated S3 · others carried over
> which one is the shocked banana?
  G013/S2 — Shocked banana 😱
> animate
> /quit            # restart later: `mirsal chat --session <id>` resumes with full state
```

The Phase 1–3 commands (`create`, `more`/`another`, `animate`, `show`, `serve`) keep working. They now invoke the graph with a fixed intent and skip classification.

---

## Architecture

```
mirsal/mirsal/graph/
  state.py        # MirsalState (TypedDict) — IDs, object keys, structured objects only. NEVER bytes.
  graph.py        # build_graph(); Postgres checkpointer (langgraph-checkpoint-postgres on mirsal-db)
  nodes/          # one file per node
  resolver.py     # deterministic reference resolver (+ LLM fallback)
mirsal/mirsal/llm/
  client.py       # one wrapper: schema-validated structured output, timeout, retry, logs to model_calls
  schemas.py      # every LLM output schema (Pydantic)
mirsal/prompts/   # versioned prompt files: intent_v1.md, resolver_v1.md, planner_v1.md, judge_v1.md, annotator_v1.md, reducer_v1.md
mirsal/mirsal/transformations/
  base.py  registry.py  banana.py
# mirsal/mirsal/vision/ (VisionJudge) exists since Phase 3; 4C adds annotator.py
```

**Phase 1 code is wrapped, not rewritten:** `pipeline.start`, `run_stills` and `run_animate` become node bodies; `pipeline.emit` is the single event sink, and Phase 4 adds a Redis-Stream sink beside the `events.jsonl` one (same `{ts, stage, status, ms, detail}` payload).

**Models (configurable in `.env`):**
- Planner, and the judge while no local VLM exists: `claude-sonnet-5`.
- Intent, resolver fallback and reducer: `claude-haiku-4-5-20251001`.
- Every call has an explicit output schema. Invalid output gets one repair attempt, then the call fails cleanly.
- Every call is logged to `model_calls` (`kind`: `LLM_INTENT`, `LLM_PLAN`, `VLM_JUDGE`, …) with its prompt version.

**Graph:**

```
load_session → classify_intent → resolve_references ─┬─ NEW / ANOTHER ──→ plan → validate_plan → generate_sheet → process → quality_gate(≤3) → judge → regenerate_rejected(≤2) → annotate → persist → respond
                                                     ├─ EDIT_STICKERS ─→ build_cell_prompts → generate_cells(1×1 each) → process → judge → persist(new gen, inherit rest) → respond
                                                     ├─ ANIMATE ───────→ generate_video → process_video → persist → respond
                                                     ├─ FEEDBACK ──────→ persist_feedback → respond
                                                     ├─ ASK ───────────→ answer_from_db → respond            (no generation)
                                                     ├─ CHANGE_SETTINGS → update_session_settings → respond
                                                     └─ AMBIGUOUS ─────→ ask_one_clarification → respond
update_memory runs after respond on every turn.
```

**Golden-path gates become `interrupt()` nodes** (`phase_01.md` 1F; decisions in the Phase 2 `reviews` table):

```
plan ─► G1 interrupt ─► generate_sheet ─► process ─► judge(vlm) ─► G2 interrupt ─► build_video_sheet ─► G3 interrupt
     ─► generate_video ─► process_video(layout, inside_slot/cross_slot) ─► judge(vlm) ─► G4 interrupt ─► G5 interrupt ─► persist
```

- **One rule:** the graph only *waits*. The gate rules are Phase 1's Python, called from the node. They decide what may be approved, the gate order, and that Python blocks are final.
- A gate resumes from any surface and the effect is identical:
  - the console button (1F route);
  - a chat line ("approve all but 5 and 6" → FEEDBACK at an open gate → `reviews` rows, `actor = 'human'`);
  - later, the Phase 5 UI.
- The Postgres checkpointer keeps a paused gate across restarts. `mirsal chat --session <id>` resumes at the open gate.
- **LangSmith:** Phase 3's `obs/trace.py` seam (Part 3b) stays. LangGraph runs are traced natively in the same `LANGSMITH_PROJECT`, and gate feedback keeps the Phase 3 keys (`gate_still`, …). So the traces from before and after Phase 4 are comparable. The rule that no media bytes leave the machine is kept.

**Edits create new generations.**
- Editing S3 of G012 creates G013 with `parent_id = G012`. S3 is new; the other 8 are `inherited_from` the G012 stickers and reuse the same asset rows and files, with no copies.
- So a generation is always a full, self-contained 3×3 set, and history is never modified.
- Single-cell regeneration uses a 1×1 prompt and runs the engine with `GridSpec(1,1)`. The engine is unchanged.

---

## Redis (introduced here; used by 4A–4C and by Phase 5)

**Rule:** Redis is **fast and disposable**; Postgres is the truth. Everything in Redis can be rebuilt from Postgres or recomputed. Nothing is written only to Redis.

**Infra:**
- `redis:7` in `docker-compose.yml`, container `mirsal-redis`, **host port 6380**. 6379 is another project's `cache-redis`.
- `appendonly no`, `maxmemory 256mb`, `allkeys-lru`.
- `REDIS_URL` in `.env`; the client is `redis-py` 5.
- `mirsal doctor` checks Redis, and the engine boundary test adds `redis`: the engine must not import it.

**Key scheme:** every key is user-scoped: `mirsal:u:{user_id}:…`, with `user_id = local` until Phase 5 adds users. Keys carry every version that affects the value, so no cache hit ever crosses users or versions.

| Use | Key | Value / TTL |
|---|---|---|
| **Event stream** per generation | `…:events:{generation_id}` (Redis Stream) | Every graph node `XADD`s its events (the Phase 5 event names). The REPL tails it now; Phase 5 SSE reads it later, with **stream entry IDs as SSE event IDs**, so reconnect replay is native. `MAXLEN ~1000`; expires 24 h after `pack_complete`. |
| **Job progress** | `…:job:{generation_id}` (hash) | status, current node, attempt, started_at. Mirrors Postgres; for live display only. |
| **Session lock** | `…:lock:session:{session_id}` | `SET NX PX 300000`: one turn at a time per session. Released on finish; expiry covers crashes. |
| **Session hot state** | `…:session:{session_id}` | Read-through/write-through copy of the `sessions` row (summary, focus, settings). |
| **Planner cache** | `…:plan:{sha256(normalized request, style, grid, mode, planner_version, content_rules_version)}` | The Phase 3 plan JSON; 7 days. |
| **VLM judge cache** | `…:vlm:judge:{asset_sha256}:{model}:{judge_version}:{slot_hash}` | Judgement; 30 days. |
| **VLM annotation cache** | `…:vlm:annot:{asset_sha256}:{model}:{annotator_version}` | Annotation; 30 days. It falls back to `stickers.annotation` in Postgres on a miss. |
| **Pool: query parse** | `…:pool:parse:{sha256(normalized query)}:{parser_version}` | The parsed `{subject, action, …}`; 7 days. |
| **Pool: query embedding** | `…:pool:qvec:{sha256(text)}:{embed_model}` | The vector; 30 days. |
| **Pool: search results** | `…:pool:hits:{sha256(parsed query + filters)}:{pool_version}` | Hit ids; 10 minutes. `pool_version` is a counter bumped on every index insert or hide, so new stickers invalidate cached results automatically. |

**Phase 1 stage -> Phase 5 event names** (the stream uses the Phase 5 names; keep the Phase 1 `stage` in the payload so both vocabularies stay searchable):

| Phase 1 stage / status | Stream event |
|---|---|
| `requested` done | `generation_started` |
| `sheet_picked` done | `sheet_generated` (source = prepared or model) |
| `keyed` start | `sticker_processing` |
| `sliced` done (per cell, **new:** emit one per sticker) | `sticker_ready` / `sticker_failed` |
| `video_requested` | `animation_started` |
| `video_cell` done | `animation_ready` / `animation_failed` |
| `plan_reviewed` / `stills_reviewed` / `video_sheet_reviewed` / `anim_reviewed` / `pack_final` (1F) | `review_requested` when the gate opens, `review_decided` per decision |
| `video_sheet_built` (1F) | `video_sheet_ready` |
| `video_returned` (1F) | `animation_started` (source = upload or ticket) |
| any `error` | `generation_failed` |

Enhancement owed to Phase 4: Phase 1 emits `sliced` as one event for all nine cells; emit a per-sticker event inside it so "S1 ready before S9" (the 5A exit test) is observable.

**Normalization for the planner cache:** only case, whitespace and irrelevant punctuation. It must **never** merge semantic differences: "dog as banana" and "dog with bananas" produce different keys (there is a test).
- `prompt` and `NEW` use the cache.
- `ANOTHER`, edits and `--fresh` bypass it.

**Redis exit:**
- [ ] `FLUSHALL` mid-session: the next turn still works (cache misses only), and an in-flight generation's display falls back to the Postgres snapshot.
- [ ] A repeated `prompt` request is a cache hit: 0 LLM calls, shown in `model_calls`. A repeated `search` beats the Phase 3 no-cache latency baseline.
- [ ] The as/with normalization test passes.
- [ ] Two concurrent turns on one session: the second waits or gets a clear "busy".
- [ ] Cache hit rates are printed by `mirsal doctor --stats`.

---

## 4A — Graph, references, feedback

**Intents:** `NEW, ANOTHER, EDIT_STICKERS, ANIMATE, FEEDBACK, ASK, CHANGE_SETTINGS, AMBIGUOUS` + `SEARCH` (routes to the Phase 3 pool). A message can carry several: "I like 2 but make 5 happier" is FEEDBACK + EDIT.

**Resolver, deterministic first:**
- Regex and rules handle numbers, `#3`, ordinals (first…ninth, last), lists ("2 and 7"), exclusions ("but not 3 and 4"), and "previous" = the last generation **in the current branch**, not the highest ID.
- Only unresolved phrases go to the LLM, together with the current generation's names, concepts and emoji from Postgres, e.g. "the shocked one" → `concept = *_SHOCK`.
- **Priority:** explicit ID > (Phase 5: UI selection) > number > semantic concept > current focus > recent generation.
- **Ambiguity:** if two candidates are plausible, ask one short question. If the mapping is clear ("make number 3 happier"), never ask.
- **Output schema:** `{intent, generation_id, sticker_ids, reference_generation_ids, confidence, needs_clarification, clarification}`.

**Feedback:**
- "I like 2 and 7 but not 3 and 4" → `{positive: [S2, S7], negative: [S3, S4], type: MIXED}` + optional `preserve` / `change` phrases.
- Negative feedback applies to the referenced assets for the next generation only, and **never** becomes a lasting preference.
- Only explicit statements ("I never want dark outlines") become persistent preferences.
- Record only what was said about the sticker. Never infer the user's emotions ("I hate 3" means negative feedback on S3, nothing more).
- No "did you like it?" prompts.

**Settings:** `duration` (≤3 s), `fps` (≤30), `style`, `animation on/off`, `chroma auto/green/blue`. They live in `session.settings`, which is the only configuration source; the chat just edits it. Sticker count stays fixed at 9 (see Deferred).

**Migration `005_sessions.sql`:**
- `sessions`: id, title, summary jsonb, current_focus jsonb, settings jsonb, preferences jsonb, timestamps.
- `interactions`: id, session_id, seq, user_message, assistant_message, intents, resolved jsonb, result_generation_id, created_at.
- `feedback`: id, session_id, interaction_id, generation_id, sticker_id, polarity, scope TEMPORARY|PERSISTENT, text, preserve jsonb, change jsonb.
- `generation_references`: source/target generation and sticker, `role` STYLE|POSE|SUBJECT|EXPRESSION|COMPOSITION|COLOR|ANIMATION, created_at.
- `stickers` gains `inherited_from`.
- LangGraph checkpoint tables.

**4A exit:**
- [ ] With a stub LLM + fake providers, fully offline, these resolve exactly: "number 2", "second", "#2", "the last one", "2 and 7 but not 3 and 4", "the previous one", "that one" (focus), "make 5 like 2" → `{source: S2, target: S5, role: STYLE_OR_CREATIVE}`.
- [ ] A live resolver eval of 40 labelled utterances scores ≥95% exact-ID accuracy, recorded in `docs/phase4_measurements.md`.
- [ ] Restart mid-session: `--session` resumes with focus, generations, feedback and settings intact.
- [ ] An edit produces a new generation; the parent's rows and files are unchanged.

---

## 4B — Persistent slots + transformation templates

**The Phase 3 planner is extended, not replaced.** Extraction, style presets, content rules, the enhance template and the golden examples all stay. 4B adds persistent slots, templates, and session context: preferences, feedback, references.

**The planner's output grows:**
- The Phase 3 plan (`extraction`, `character_lock`, `style_lock`, `cells[]`) gains `transformation` {type, source_subject, target_subject} and per-cell slot fields {`concept_id`, `subject`, `target`, `creative_role`, `required`}.
- The **slot** is persistent meaning; the prompt is generated from the slot. Later "make number 1 more energetic" edits S1's slot, so there is nothing to re-infer.
- **Validation (deterministic):** exactly 9 slots, no duplicate concept_ids, every slot has a prompt + name + emoji + subject/target, and required template slots are present. Poses within the pack must differ: the same action with a slightly changed mouth is a duplicate.
- The animate-friendly concept rules and the creative boundary are the same as in Phase 3.

**Transformation intents:**
- `SUBJECT_AS_TARGET` ("dog as banana" → the dog *becomes* banana-like and keeps its identity);
- `SUBJECT_WITH_TARGET` ("dog with bananas" is **not** a transformation);
- `SUBJECT_HOLDING_TARGET`, `SUBJECT_EATING_TARGET`, `TARGET_AS_SUBJECT`, `TARGET_THEMED_SUBJECT`.

**Templates** (`TransformationTemplate`: `detect(request)`, `build_slots(spec)`, `validate_slots(slots)`, `enrich_prompt(slot, ctx)`), plus a registry.

**Banana template (`subject_as_banana`, v1.0):**
- It triggers on "{subject} as banana", "{subject} banana stickers/emoji", "banana version of {subject}", "{subject} turned into banana".
- Required slots: `BANANA_DANCE, BANANA_SHOCK, BANANA_SQUASH, SUBJECT_BANANA, SUBJECT_BANANA_ACTION`.
- Slots 6–9 are dynamic (emotion, reaction, comedy, signature). Banana gets this template because it is especially good for physical-comedy stickers.
- The engine is generic: any target works ("cat as strawberry", "camel as cupcake") through a generic `subject_as_target` template with the required concepts dance/shock/squash of the target.

**Rules:**
- Priority: explicit user instruction > template > persistent preferences > retrieved examples > model improvisation.
- **The user overrides templates:** "dog as banana, no dancing" removes `BANANA_DANCE`; "all nine different banana reactions" replaces the structure.
- The LLM decides the *realization* (a moonwalk vs arms-up for BANANA_DANCE) but can't swap the slot's meaning (not "sleeping banana").
- **Subject identity:** with a reference image (Phase 5 upload), the slots carry identity traits (breed, markings, ear shape, proportions) for the prompt.
- Store `transformation_id` and `transformation_version` on the generation. The full plan is already in `generations.plan`, and `planner_version` has existed since Phase 3. Old generations keep their versions when templates change.
- **Prompt injection:** user text and reference content are creative data, never instructions. Schema validation rejects any output outside the plan schema.

**Migration `006_transformations.sql`:** `generations` gains `transformation_id`, `transformation_version`. (`plan` jsonb already exists from Phase 3.)

**Template catalog is code, not a DB table** (deliberate). Templates live in `transformations/*.py` with a `version` constant, so changes are reviewed and covered by the 4B tests. A DB-editable catalog, with trigger patterns editable without a deploy, is deferred until non-developers need to edit templates.

**4B exit:**
- [ ] "dog as banana" → all 5 required slots; "dog with bananas" → not `SUBJECT_AS_TARGET`; "dog as banana but no dancing" → `BANANA_DANCE` absent; "cat as strawberry" → the generic template's required concepts.
- [ ] "make the third one less flattened" edits `BANANA_SQUASH` by slot; "make the banana ones more expressive" targets the banana-family slots.
- [ ] Validator rejections are tested (duplicates, a missing required slot, a missing emoji).
- [ ] Live: 10 transformation requests, with the slot pass rate recorded.

---

## 4C — Annotation, multi-reference, memory

**The vision judge exists since Phase 3** (Python checks, the VLM judge, the sheet check, the reasons list, the down-policy and concurrency cap). In 4C the judge gets **slot context**: `concept_id`, `creative_role`, the transformation, and the required template slots. It can then reject `MISSING_REQUIRED_ELEMENT` and `PACK_INCONSISTENCY` against the template, not just the cell prompt.

**Annotation** (for approved stickers; the same model, a separate prompt):
- `{visual_summary, subject, pose, expression, style_profile {outline, finish, proportions, palette, shading}, colors, animation_notes[]}`.
- Cached in Redis by `(asset sha256, model, annotator_version)`, with a fallback to `stickers.annotation`; the same image is never re-annotated.

**Truth hierarchy:** the image is what exists; the annotation describes what is visible; the original prompt records intent; the LLM's interpretation is the weakest. They are not interchangeable.

**Multi-reference:**
- "Use the style from 2 and the pose from 7" → `[{ref: S2, role: STYLE}, {ref: S7, role: POSE}]`.
- "Keep the style but make it a strawberry" separates the STYLE source from the SUBJECT source.
- The prompt gets: the new subject + the preserved properties + the roles + the explicit change.

**Memory + context:**
- Raw interactions are always kept.
- Every `REDUCER_WINDOW` (15) interactions, the reducer writes a session summary: focus, recent generations, preferences, feedback and lineage. **It always keeps IDs**: `G047/S3`, never "the last banana".
- `build_context(level)`:
  - `MINIMAL` = summary + request + settings;
  - `STANDARD` = + the relevant metadata + one reference;
  - `HIGH_FIDELITY` = + the actual reference images + annotations + original prompts + lineage. It is used for "exactly like this / same character / same style / same pose".
- Never send all 9 images, all prompts or the whole history on every turn.
- **Retrieval:** within a session, use Postgres metadata first (concept, name, emoji, annotation JSONB). Across sessions ("find my old glossy fruit sticker"), use the Phase 3 pool. 4C appends annotation summaries to `search_text` and runs `pool reindex`. Never embed raw interactions. When fidelity matters, fetch the real image, not just its embedding.

**Migration `007_annotation.sql`:** `stickers` gains `annotation jsonb`. (`judge` jsonb has existed since Phase 3; the hot annotation and judge caches are in Redis.)

**4C exit:**
- [ ] Annotation cache: the same asset sha256 + model + annotator version is never re-annotated (a test counts the calls).
- [ ] "Use the style from 2 and the pose from 7" → `[{S2, STYLE}, {S7, POSE}]`, stored in `generation_references`, and the new prompt carries both roles.
- [ ] Slot-context judge: a sheet missing `BANANA_SQUASH` is rejected with `MISSING_REQUIRED_ELEMENT` (stub VLM).
- [ ] Reducer test: after summarizing 20 interactions, every generation ID, sticker ID, preference, focus and feedback item is still present.
- [ ] "Which one is the shocked banana?" is answered from metadata with no generation and no image re-analysis.
- [ ] Live: annotation spot-check, where Haitham confirms 20 visual summaries match their stickers, recorded.

---

## Explicitly deferred / dropped
- A sticker count other than 9 (`make it 12`) is **dropped** for now. The 3×3 sheet is the core mechanism; revisit with a different grid in a later phase if needed.
- MCP exposure of tools: not planned. Internal Python services are enough; add it only for a real remote-worker or agent-integration need.
- Model escalation (fast model → judge → better model): later, after the measurements exist.

## Hands to Phase 5
- One `run_turn(session_id, text, selected_sticker_ids=[])` entry point that streams node events.
- `search(query, filters) -> {hits, gap}` from the Phase 3 pool (Redis-cached since Phase 4), for the Phase 5 search box.
- Full structured state in Postgres.
- Every behaviour that the UI only needs to display.
