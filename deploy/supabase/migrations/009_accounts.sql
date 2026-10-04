-- Hosted only (Supabase). The account created by the Google sign-in, one row per person, joined to the app's own `users` row (006) by u_id.
-- Nothing here is applied by `python -m mirsal db migrate` (the PC never has Supabase Auth): apply it in the Supabase SQL editor or with psql, in order 009, 010, 011.
-- Re-runnable. The browser never queries these tables: the API uses the service role; RLS is on so that an accidentally exposed anon key reads nothing.

CREATE TABLE IF NOT EXISTS accounts (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  u_id          text UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,   -- the app's own U### (runtime/users.py `ensure_external`): nothing else has to change
  google_sub    text UNIQUE NOT NULL,                                          -- Supabase auth.users.id == the JWT "sub"; the same value as users.json `external`
  email         text,
  name          text,                                                          -- Google profile full_name / name: the greeting and the default pack name (text only, never an instruction)
  avatar_url    text,
  locale        text,
  test_credits  numeric(10,2) NOT NULL DEFAULT 10 CHECK (test_credits >= 0),   -- the 10 Higgsfield credits every new person may test with (plan.md section 7)
  disabled      boolean NOT NULL DEFAULT false,
  created_at    timestamptz NOT NULL DEFAULT now(),
  last_seen_at  timestamptz
);
CREATE INDEX IF NOT EXISTS accounts_email ON accounts (lower(email));

ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'accounts' AND policyname = 'accounts_self') THEN
    CREATE POLICY accounts_self ON accounts FOR SELECT USING (auth.uid()::text = google_sub);
  END IF;
END $$;
