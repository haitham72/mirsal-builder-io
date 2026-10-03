# Supabase: what to apply and how (nothing here has been applied; no project exists yet)

1. Create a Supabase project. Auth > Providers > Google: enable it with a Google OAuth client (`Authorized redirect URI` = the one Supabase shows; the app's own return page is `https://<host>/auth/callback`).
2. In the SQL editor (or `psql "$SUPABASE_DB_URL" -f ...`) apply, in this order, after the repo's own `mirsal/migrations/001`..`008` have run against the same database (`python -m mirsal db migrate` with `MIRSAL_DATABASE_URL`):
   - `migrations/009_accounts.sql`  - one row per person (Google sub, name, 10 test credits). RLS on.
   - `migrations/010_user_analysis.sql` - what a person did and from where. Read `docs/deployment_plan.md` section 10 first: an IP address is personal data. RLS on, no policy.
   - `migrations/011_credit_ledger.sql` - the book behind the credits: reserve / settle / refund, atomic.
3. Use the **transaction pooler** connection string for the app (free tiers cap connections), the **service role key** only on the server.
4. Not built yet (they are the next steps of `docs/deployment_plan.md`, written against these tables): the code that writes `accounts` / `user_analysis` / `credit_ledger` from the engine, the retention job (`select purge_old_ip(30)` daily), `GET /api/me/export`, `DELETE /api/me`.

The files live here and not in `mirsal/migrations/` on purpose: the PC and the tests have no Supabase Auth (`auth.uid()`), so `db migrate` must not run them. When the hosted database is the only one, move them.
