# 2×2 defaults and independent cell video sequences — 2026-10-19

This section records independent-video **v1**. New plans now use
[v2 natural sequences](20-natural-cell-video-sequences.md), preserving a third
beat and permitting explicitly described detached gesture hands. The v1
template and saved-plan rebuild remain unchanged.

Haitham found 3×3 video laggy/low quality and reported that per-emoji action
sequences can become whole-sheet scenes: every emoji performs cell 1's action,
then every emoji performs cell 2's. New plans therefore default to **2×2** across
the deterministic planner/enhancer, task preview/reservation, HTTP defaults,
CLI, new Chat settings, Studio and new preset claims. Reaction sheets already
default to 2×2. Explicit 3×3 choices, nine-emoji manual batches and existing or
imported sheet geometry are preserved; changing a default does not recut data.
Next/more batch plans retain their actual grid rather than forcing 3×3.

`prompts/templates/video_independent_v1.txt` is a new template; none of the
previously used template files was edited. New plan slots save
`video_template: {id: video_independent, version: 1}` separately from the image
template version. Old slots without that field keep `video_short_v1` when
rebuilt. Custom user prompt text still wins. Past sent prompts/jobs are unchanged.

Each occupied cell gets one spatially bound line, for example:

```
Top-left (cell 1): State: joyful smile. Action 1: smiles widely. Then Action 2: bounces with a chuckle.
Top-right (cell 2): State: laughing. Action 1: squeezes its eyes shut. Then Action 2: shakes with laughter.
Bottom-left (cell 3): State: sobbing. Action 1: trembles with a sob. Then Action 2: streams tears from both eyes.
Bottom-right (cell 4): State: sad. Action 1: droops its eyelids. Then Action 2: sighs softly.
```

The wrapper says all occupied cells animate concurrently from the first frame,
each at its own pace; action numbers are local to that cell. It explicitly
forbids applying one cell's sequence to the others, whole-grid emotion changes,
swapping, copying and synchronized group choreography. Camera, identity, scale,
design, flat key background and cell boundaries stay fixed. Empty cells stay
empty. Face mode forbids bodies/hands; it never adds the hands/shoulders from a
body-character example to a face-only emoji. Loop on adds return-to-start;
Loop off keeps its existing non-loop contract.

The renderer takes the first two comma/then/while-separated motion clauses. If
there is only one, it adds a small local head tilt/blink (faces) or lean/settle
(characters); a missing motion gets a local expressive action. This is two short
actions per cell, rather than a long global storyboard. Only approved spatial
positions are described when the video sheet has empty cells.

Fake-only validation: default/explicit-grid contracts, four spatial state/action
lines, concurrent/local wording, legacy rebuild, loop/custom precedence, HTTP
preview, fresh/saved Studio and Chat toggles, and the actual prompt passed to a
fake video CLI. No paid video was generated. These checks prove the prompt
contract, not model compliance or an improvement in rendered quality. A paid
2×2 proof remains an owner money/quality decision.
