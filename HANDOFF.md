# HANDOFF - 2026-10-16

Active checkout: `G:/Haitham/VsCode/Mirsal-Builder`, branch `redesign-ui-ux`.
Keep branches separate until Haitham asks for a merge; verify the branch before
committing. Public deployment and Google OAuth remain paused.

## Current save point

`3f35dcd3` contains durable agent checkpoints, SQLite profiles, six memory tests,
and the review. Documentation cleanup removes the superseded review brief and
incorrect safety claims. The five findings in
[docs/langgraph-memory-review.md](docs/langgraph-memory-review.md) remain unfixed;
the two P1 findings concern unrestricted resume routing and repeated vision calls.
Implementation details live in
[agent section 24](docs/agent-and-chat/24-durable-turns-and-profiles-2026-10-16.md).

Memory tests: 6 passed. Agent area: 322 tests, 5 failures, 10 errors; isolated
base: 322 tests, 4 failures, 9 errors. See the review for configuration limits and
the new Telegram checkpoint file-lock error. No paid provider was called.

## Picking up

- [plan.md](plan.md) holds unfinished redesign acceptance and follow-ups. Keep
  those tasks open until verified; this memory review did not complete them.
- Preserve redesign's duplicate-choice import dialogs when merging; main
  deliberately removed them. Keep Resize and Emoji/Lottie export contracts.
- Use the narrowest test tier. Full discovery and the slow tier are retired.
- Browser checks use copied output and disabled providers. Restart only a
  task-owned server; the previous task endpoint was `http://127.0.0.1:8796/`,
  whose current availability has not been checked in this session.
