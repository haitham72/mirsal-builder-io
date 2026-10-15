# UI/UX review — grouped journeys

> **Current implementation (2026-10-15):** [current-status.md](current-status.md), [execution evidence](implementation-log.md), [real redesign images](redesign-shots/README.md), and [remaining work](../../plan.md). These override historical review status below.


> **Historical source validation (pre-redesign):** [revalidation.md](revalidation.md) checks all 36 findings against newer source: 21 retain their source basis; 15 changed scope. Task status is updated in tasks.json. Browser acceptance for the rewritten reaction screen remains unrun.

For the original audit context, see [concurrent-work.md](concurrent-work.md): another LLM edited the shared checkout while this review was running. The original audit recorded proposed fixes; subsequent source implementation is documented in current-status.md and implementation-log.md.

Each journey has an overview, detailed **issue → proposed fix** document, and an implementation checklist linking the bounded task catalog. Shared findings intentionally appear in more than one journey; the same finding/task ID means one implementation, not repeated work. Screenshots remain in a single shared shots folder to avoid copies.

## Journey folders

| Journey | Detailed issues and proposed fixes | Execution checklist |
|---|---|---|
| J1 Create a sticker set in Studio | [Issues → proposed fixes](journeys/J01-studio/issues-and-proposed-fixes.md) | [Checklist](journeys/J01-studio/implementation-checklist.md) |
| J2 Create through AI chat | [Issues → proposed fixes](journeys/J02-ai-chat/issues-and-proposed-fixes.md) | [Checklist](journeys/J02-ai-chat/implementation-checklist.md) |
| J3 Library, pack, viewer, Edit and Timeline | [Issues → proposed fixes](journeys/J03-library-and-editors/issues-and-proposed-fixes.md) | [Checklist](journeys/J03-library-and-editors/implementation-checklist.md) |
| J4 Reaction wall, emoji editor, presets and batch selection | [Issues → proposed fixes](journeys/J04-reaction-presets/issues-and-proposed-fixes.md) | [Checklist](journeys/J04-reaction-presets/implementation-checklist.md) |
| J5 Pack reactions, motion and standalone effects | [Issues → proposed fixes](journeys/J05-pack-reactions/issues-and-proposed-fixes.md) | [Checklist](journeys/J05-pack-reactions/implementation-checklist.md) |
| J6 Rejected pictures, reasons and reversible overrides | [Issues → proposed fixes](journeys/J06-rejection-and-overrides/issues-and-proposed-fixes.md) | [Checklist](journeys/J06-rejection-and-overrides/implementation-checklist.md) |
| J7 Home and welcome | [Issues → proposed fixes](journeys/J07-home-and-welcome/issues-and-proposed-fixes.md) | [Checklist](journeys/J07-home-and-welcome/implementation-checklist.md) |
| J8 Settings, Trash, Tickets, Help and Trending | [Issues → proposed fixes](journeys/J08-settings-help-and-trending/issues-and-proposed-fixes.md) | [Checklist](journeys/J08-settings-help-and-trending/implementation-checklist.md) |
| J9 ZIP, collection and Telegram dialogs | [Issues → proposed fixes](journeys/J09-export-dialogs/issues-and-proposed-fixes.md) | [Checklist](journeys/J09-export-dialogs/implementation-checklist.md) |
| J10 Dark and light comparisons | [Issues → proposed fixes](journeys/J10-dark-and-light-themes/issues-and-proposed-fixes.md) | [Checklist](journeys/J10-dark-and-light-themes/implementation-checklist.md) |
| J11 Phone Library, pack, viewer and reaction editor | [Issues → proposed fixes](journeys/J11-phone-layout/issues-and-proposed-fixes.md) | [Checklist](journeys/J11-phone-layout/implementation-checklist.md) |
| Shared Shared code structure, inventory and documentation | [Issues → proposed fixes](journeys/shared-components-and-docs/issues-and-proposed-fixes.md) | [Checklist](journeys/shared-components-and-docs/implementation-checklist.md) |

## Shared evidence and handoff

- [Canonical plan](../uiux_plan.md): 87 bounded tasks, 50 for 6.1-sol-medium and 37 for luna-6-high.
- [Ranked findings](findings.md): 36 findings and cited evidence.
- [Walked states](screens.md): 73 recorded states, all 11 journeys and explicit limits.
- [Duplication map](duplication_map.md), [code report](code_reader.md), [docs report](docs_reader.md).
- [Before/after sketches](mocks/sketches.md).
- [Manifest](manifest.json): 48 source screenshots + 11 contact sheets = 59 images.

The original audit performed no source implementation. The later redesign phases are now recorded in implementation-log.md; historical audit files remain unchanged as evidence.

[Ready-to-use reviewer/coder prompt](reviewer-coder-prompt.md).
