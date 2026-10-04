-- Tickets (flow/tickets.py, docs/tickets_plan.md): the Postgres copy of out/tickets/T###.json, one row per ticket, rewritten on every change.
-- The file is the record; this table makes tickets searchable next to generations, jobs and chats. Re-runnable.
CREATE TABLE IF NOT EXISTS tickets (
  id            text PRIMARY KEY,
  source        text NOT NULL,                 -- report | crash | job | telegram
  at            timestamptz NOT NULL,
  last_at       timestamptz NOT NULL,
  user_id       text,
  status        text NOT NULL,                 -- open | answered | fixed | wont_fix
  issue         text NOT NULL,
  summary       text NOT NULL DEFAULT '',
  what_happened text NOT NULL DEFAULT '',
  intent        text NOT NULL DEFAULT '',
  proposed_fix  text NOT NULL DEFAULT '',
  fingerprint   text,
  count         integer NOT NULL DEFAULT 1,
  fixed_by      text,
  body          jsonb NOT NULL                 -- the whole ticket: context, questions, answers, history
);
CREATE INDEX IF NOT EXISTS tickets_status ON tickets (status, last_at DESC);
CREATE INDEX IF NOT EXISTS tickets_fingerprint ON tickets (fingerprint);
