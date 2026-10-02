-- Phase 5C: users and ownership. out/users.json is the primary store (digests only, never a token); this mirrors it so ownership joins in SQL.
-- Existing rows are backfilled to the one implicit owner, `local`. Re-runnable.
CREATE TABLE IF NOT EXISTS users (
  id           text PRIMARY KEY,                -- U001 (the implicit owner is `local` and has no row)
  name         text NOT NULL,
  role         text NOT NULL CHECK (role IN ('owner','member')),
  can_spend    boolean NOT NULL DEFAULT false,  -- may start paid generation (it spends the owner's credits)
  token_sha256 text NOT NULL DEFAULT '',
  disabled     boolean NOT NULL DEFAULT false,
  created_at   timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE generations ADD COLUMN IF NOT EXISTS owner text NOT NULL DEFAULT 'local';
CREATE INDEX IF NOT EXISTS generations_owner ON generations (owner);
