# Shared code and docs — remaining checklist

- [ ] API routers/schemas and graph lifecycle; UI state/watchers/cache/presenters T-024/025/031/034/035.
- [ ] Shared controls/styles, reading paths and remaining legacy-task reconciliation; inventory regenerated.
- [ ] W29 runtime retention and W33 parked frontend need decisions before removal.

Before implementation: reproduce against current source, preserve all contracts,
use one narrow failing→passing check per fix and copied data/providers off.
Check `redesign-ui-ux` before committing explicit paths. No owner verdict is inferred.

[Current findings/acceptance gates](../../app-audit-2026-10-19.md) · [Status](redesign-status.md) · [Root plan](../../../../plan.md)
