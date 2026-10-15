# UI/UX redesign — remaining work

Updated2026-10-15 on redesign-ui-ux. Read [current status](docs/uiux_review/current-status.md), [execution evidence](docs/uiux_review/implementation-log.md) and [design images](docs/uiux_review/redesign-shots/README.md) first. Historical catalog scopes are not automatically current bugs.

The original nine reaction/pack requirements are implemented and accepted through narrow checks plus sampled native desktop/phone dark/light interactions: set metadata/menu, Manage stickers, selected Motion/Change, one Advanced, simplified burst row/download, no pack tabs, Library Open in Studio, Open and save as an independent row, and backend erosion_px default0. Their original requirements remain in git history and the journey issue/proposed-fix documents. They are removed from this next-work list only after the evidence was recorded.

Studio tokens/grouping, shared staged previews, Resize/Position fixtures, count labels and cross-journey surface/dialog work are delivered. This does not complete every engineering extraction in the87-task catalog.

## Current user choices and concurrent changes

- Retain the duplicate **choice router**: Open existing batch / Import again as a new batch, plus the batch-specific choices. Keep grid mismatch consent and explicit recovery. Haitham selected this after review of5ad67e2d; do not enforce a fresh cut for every manual upload.
- Grey thumbnail source/collection behavior from5ad67e2d is imported unchanged in a439eec4. Its conflicting import-policy portion was excluded; no runtime artifacts were ported. Requested verification32 Python tests and5 UI tests passed.
- Keep Resize off=one uniform scale, on=hot spot matched to approved still. Keep Emoji-style emoji-free export and Lottie-style self-contained export distinct.

## Remaining, in priority order

1. Review the new screenshots with Haitham. Open wording decisions remain: F-31 effects/reactions naming and cloud pricing copy. No additional approval is required for independent engineering work.
2. Extended native checks: slow/off-route refresh overlap, long existing Chat histories and exhaustive opened/hover/editor states. Current acceptance is sampled and free; no real provider turn, collection send or Telegram send was run.
3. Shared-code catalog follow-ups: watcher lifecycle/edge synchronization (T-005 onward/T-058), scalar range/segment presenters, download/preview/cache adapters and remaining inventory/reading-path cleanup. T-024/025/031/034/035 stay pending in tasks.json. Do not recreate obsolete rxWatch/rxRun batch generation, All/Done/Not done filter, or old preset menu (T-007/018/047); the current preset library replaced them.
4. Optional Lottie additions remain unimplemented: Pre-run, Time scale, sticker-silhouette emitter and supported blend modes. This branch is authorized for them, but the visual pass did not add them. Feasibility and byte-identical default proof are required before implementation; do not add a runtime rasterizer merely for silhouettes.
5. Finish the broader catalog's remaining refactors/docs one bounded task at a time. Preserve endpoints, units, ownership, cache keys, cancellation and per-picture reversible decisions. A visual migration is not evidence that these extractions are complete.

## Execution boundaries

Use this isolated worktree/branch; check the branch before each commit. Keep source area docs, design docs, task status and execution evidence together. Run the narrowest relevant test once per change; no full discovery and no tests for docs. Explicit staged paths only. Own server port/copy of out; never owner8770 or live data. No paid calls or sends, no merges/deployment. Never switch, stash or reset another session's checkout.
