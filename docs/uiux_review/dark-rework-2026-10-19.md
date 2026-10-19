# Neutral/cyan dark theme and always-open New request

2026-10-19, `redesign-ui-ux`, based on `6170c0ec`. This phase changes the theme
and Studio composer visibility; the proposed left creation panel is not implemented.
Source hashes and browser observations: [measurements](dark-rework-2026-10-19.json).

## Result

- Neutral charcoal tiers replace the cyan-tinted canvas; the original cyan
  action/focus accent is retained. Chat has a quiet canvas, readable heading,
  separate user messages and raised composer/menus. Dark ambient blobs/dots/glow
  are disabled. Media colors and locked diagnostic issue colors stay intact.
- Shared primary hover is fixed: dark text stays on cyan rather than the
  generic secondary hover surface. **13.24:1 dark**, **5.17:1 light** at both
  widths, versus the audit's dark 1.26:1 defect (UX-02).
- New request is a labelled section that cannot collapse, for new and reopened
  batches. Its prompt/draft and internal Options/Prompt-engine disclosures stay.
  In the current layout it can scroll out of view; it is not a fixed sidebar yet.
- The user's missing-controls concern was resolved by the existing
  **Stickers / Sheet / Both** view switch, not a source repair. All choices remain.

## Verification

New Node regressions: **4 passing** (palette 3, composer 1). Their real assertions
failed before the change; harness path/stub corrections are not counted as
product failures. Only the narrow files were run. Earlier agent/JS/wrapper
baselines were not rerun or reclassified as fresh green evidence.

Playwright CLI on task-owned **http://127.0.0.1:8798/**, copied audit artwork plus
synthetic packs, saved Chat and reactions; all providers/real CLI, DB writes and
tracing disabled. The real-data :8770 and earlier :8797 servers were untouched.

| States | Desktop 1440 | Phone 390 | Outcome |
|---|---|---|---|
| Existing Chat / new Chat / settings popover | dark + light | dark + light | readable colors, isolated open/closed states |
| Home / Studio / Library / Reactions / pack / Settings | dark + light | dark + light | renders, no page-width overflow |
| Primary hover | dark + light | dark + light | contrast above |
| New request on reopened batch | dark + light | dark + light | section, prompt present, no outer disclosure |
| Stills and Animation × Stickers/Sheet/Both | dark + light | dark + light | 24 cases: 9 items in Stickers/Both, sheet-only in Sheet |
| Per-animation controls | dark + light | dark + light | 9 frame + 9 Adjust controls; Size/X/Y reachable |

**36 core states + 24 view cases**, no page errors/failed responses or mutation
POSTs in the recorded checks. Light colors match the pre-change sample; minor
box-shadow transition interpolation is not a palette difference. Eighteen light
states were retained after their pass because later edits were dark-only;
affected dark states were checked again. Dark reduced-motion probe reports no
ambient animation. Menus were explicitly reset between final screenshots, and
the composer check distinguishes its nested disclosures from an outer summary.

## Screenshots

| Evidence | Screenshot |
|---|---|
| Old Chat | [Before](dark-rework-shots/before-chat-1440-dark.jpg) |
| New Chat reading surface | [Desktop](dark-rework-shots/after-chat-history-1440-dark.jpg) |
| New conversation | [Desktop](dark-rework-shots/after-chat-new-1440-dark.jpg) |
| Conversation phone | [Phone](dark-rework-shots/after-chat-history-390-dark.jpg) |
| Open settings popover | [Phone](dark-rework-shots/after-chat-controls-390-dark.jpg) |
| Shared Home palette | [Home](dark-rework-shots/after-home-1440-dark.jpg) |
| Shared Library palette | [Library](dark-rework-shots/after-library-1440-dark.jpg) |
| Individual animation controls | [Studio](dark-rework-shots/after-studio-individual-390-dark.jpg) |
| Always-open New request | [Desktop](dark-rework-shots/after-new-request-1440-dark.jpg), [phone](dark-rework-shots/after-new-request-390-dark.jpg) |

## Still open

Final visual approval belongs to Haitham. The Studio left-panel layout is a
proposal, not shipped. Phone image/animation editor and Save layout, keyboard
tile/name gaps, frame focus/Escape, ownership text and remaining route-wide
states stay in plan.md. No paid/provider turn, send, export, deployment or merge
was performed. Public Higgsfield reference screenshots were not committed.
