# Work split: main agent and local Qwen

Haitham's preference: the main agent handles complex reasoning and agentic work; the local model handles vision and straightforward chat tasks.

## Main agent

- Inspect code, identify causes, plan changes and coordinate tools.
- Implement and review code, API contracts, database changes and recovery behavior.
- Define evaluation cases, expected outputs and scoring rules.
- Validate local-model answers against schemas and known expected results.
- Interpret failures, perform targeted fixes and record results.
- Handle ambiguity, multi-step decisions and tasks requiring repository or system state.

## Local Qwen

Endpoint: `http://localhost:1234/api/v1/chat`; model: `qwen/qwen3.5-9b`.

- Vision pre-review of supplied sticker images.
- Simple chat responses and clarifying questions from supplied context.
- Draft example utterances, concise summaries and straightforward text transformations.
- Answer bounded evaluation prompts with explicit output formats.

Use reasoning off for straightforward cases, no tools/plugins, isolated requests and no cloud fallback. The main agent supplies the context the model needs; the local model does not inspect repository files or execute changes itself.

## Evaluation workflow

1. The main agent defines a small task and its acceptance criteria.
2. The local model processes independent examples; preserve responses and failures.
3. The main agent checks outputs with deterministic validators or explicit expected answers.
4. Recheck only failed or changed cases; avoid repeating an entire passing dataset.
5. Store prompts, inputs, results, timings and limitations in this folder.

The existing 30-sticker run is complete in `results.md`. Additional candidates are the five malformed verdicts' repair path, simple chat/reference-resolution cases and controlled vision examples with known defects. Prepare expected results from existing fixtures; Haitham does not need to author datasets or run tests.

Model-to-model agreement is not human accuracy. Subjective agreement remains unmeasured without independent labels; it does not create a mandatory manual-testing task. Application model routing changes are separate implementation work and must follow the app's existing ownership and spending rules.
