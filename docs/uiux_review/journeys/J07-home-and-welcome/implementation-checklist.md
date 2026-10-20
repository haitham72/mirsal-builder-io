# Home and welcome — remaining checklist

- [x] UX-06 workspace identity (2026-10-20): `/api/generations` reports `paths.default` (store/sync.is_default_out, never guessed from a port); the rail logo shows a "Test" badge and title when it is false. `tests/test_users.py::test_the_owner_sees_whether_this_is_the_real_out_or_a_copy`, `tests/js/workspace_badge.test.js`.
- [ ] Owner visual review of the revised neutral/cyan theme.
- [ ] Owner verdict on films/art/wording and welcome playback; no new media generation authorized.

Before implementation: reproduce against current source, preserve all contracts,
use one narrow failing→passing check per fix and copied data/providers off.
Check `redesign-ui-ux` before committing explicit paths. No owner verdict is inferred.

[Current findings/acceptance gates](../../app-audit-2026-10-19.md) · [Status](redesign-status.md) · [Root plan](../../../../plan.md)
