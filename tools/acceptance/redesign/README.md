# Redesign browser acceptance

Run from the repository root with the Windows venv and Playwright CLI skill.
`prepare.py` creates a fresh temp output, copies only G146 artwork, and imports a
synthetic 3×3 G156 video. It writes the scratch location to
`output/playwright/scratch.txt`; runtime output is never staged.

Start a task-owned server on free localhost port 8797 with `MIRSAL_OUT` pointing
to that scratch output and `MIRSAL_NO_REAL_CLI=1`, all LLM/agent/vision providers
`none`, DB writes disabled and tracing off. The scripts use that address and
save screenshots under docs/uiux_review/redesign-shots. Do not use live output.

Use `playwright-cli -s=<isolated session> run-code --filename <script>` after
opening the local server and taking its snapshot. `sliders.js` runs the eight
cells; `retry.js` separately checks real busy retries; `reactions.js` checks the
two surfaces; `frame.js` preserves the frame editor; `hover-contrast.js` is the
computed-contrast regression. `extended.js` shows the extended checks; its final
saved version targets the one retry cell (restore both width/theme arrays for a
fresh full run). Nonempty reactions and a saved long synthetic session must be
seeded in the scratch output as described in the acceptance report.

The versioned report and JSON evidence are in
docs/uiux_review/acceptance-2026-10-19.md and .json. The scripts are evidence
tools, not paid-model quality tests or owner visual approval.
