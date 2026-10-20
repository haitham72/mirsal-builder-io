# Shared-code work still remaining

Use [root plan](../../plan.md) and the [current audit](app-audit-2026-10-19.md), not
the old provisional CT task bank. That bank remains in git. Unclassified legacy
tasks in tasks.json require fresh reconciliation, not automatic implementation.

| Existing task | Current scope | Preserve / prove |
|---|---|---|
| T-024 | Saved-set burst slider presenter | Preserve FXSL ranges, null/readout behavior and data-psbp/data-id events |
| T-025 | Current Emoji preset slider presenter | Preserve rxVal/rxFmt, RXSIM/RXO ranges, data-rxo and Motion/Size/Advanced |
| T-031 | Download lifecycle adapters | Today's preset ZIP/JSON contracts, exact names and owned object-URL cleanup |
| T-034 | Shared preview presentation | Actual preset/Lottie/frame contexts; keep engine decisions and staged Cancel behavior |
| T-035 | Cache/presenter boundaries | Explicit ownership/invalidation; route return and pending edits survive |

Completed scope: [five reviewed refactors and folder layout](refactor-2026-10-20.md).
Reactions preview requests and its Studio/saved-set polling now have explicit
owners; other consumers still need their own scoped migrations.

Separate remaining work: other watcher/resource ownership and Studio edge synchronization;
staged values, busy retries and no extra recuts must be preserved.
Related remaining extractions: other feature state/controllers (AR-02),
styles/control states (AR-03), flow lifecycle beyond the extracted agent (AR-04), current
documentation reading paths (DOC-01). Inventory has been regenerated; broader
documentation cleanup remains. Generic range/segment helpers need current
consumer-specific scope before adding files. TESTCARD already exists.

One bounded change and narrow failing→passing regressions per fix; copied local
data, providers off, explicit paths and branch check before commit. No paid calls,
external sends, deployment, broad framework rewrite or removal of import choices.
