# Natural cell video sequences (2026-10-20)

New plans save `video_template={id:video_independent,version:2}`. This version
uses one natural direction per occupied cell instead of State/Action 1/Action 2
labels. `generation/video_sequences.py` owns the deterministic wording; the
template keeps the concurrent, independent-cell and fixed-camera constraints.

For a 3x3 grid, top-right is cell 3 and mid-left is cell 4. For a 2x2 grid,
top-right remains cell 2. Positions always follow the actual row-major geometry;
the default grid remains 2x2.

Example direction for an occupied cell in a looping 3x3 sheet:

> Top-right (cell 3): The sad and drooping face with a single tear cries softly,
> then starts sobbing in a cute way, and finally wipes away the tear with a small
> detached hand. The detached hand emerges from behind the face for the gesture
> and withdraws behind it afterwards, with no visible arm connecting it to a body.
> It then returns smoothly to its exact first-frame expression and position.

Two motion beats are always present; a third payoff is retained when supplied.
`then`/`finally` and legacy comma/semicolon clauses provide beat boundaries.
`while` stays inside its beat as simultaneous detail. Extra legacy clauses are
retained together in the final beat. Sparse motions receive a local expressive
follow-through. Default sad/crying face plans get a crying/sobbing/tear-wiping
progression, stored in their new slot text.

The enhancer now asks for two meaningful actions and an optional third, flowing
as a short emotional progression. Face-mode requests explicitly distinguish
face-only image labels from optional detached-hand video gestures. Up to 600
characters of model motion are stored so the final gesture is not cut at the
old 220-character boundary.

Face images remain head/face only. A hand may appear in a face video only when
that cell's motion calls for it: it emerges from behind the face, performs its
gesture and withdraws, with no connecting arm or body. Cells without a gesture
do not inherit a hand. Full-body character plans keep their existing anatomy.

Loop on appends an exact first-frame expression/position return to each cell.
Loop off adds no return instruction. Custom prompt precedence remains unchanged.
Saved video_independent v1 and video_short v1 templates and their rendering
remain unchanged; past sent prompts and jobs are not rewritten.

Validation: 29 focused checks passed: generation defaults, face-image constraints,
enhancer, a model's third payoff beyond 220 characters, and actual prompt delivery
through a fake video CLI for both 2x2 and 3x3 sheets. No paid animation was
generated; provider compliance and visual quality remain unmeasured.
