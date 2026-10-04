-- What the chat knows about a person (agent/profile.py, docs/agent-and-chat.md "The person's profile"): the Postgres copy of out/profile/<user>.json `facts`.
-- The file is the record (it wins when the database is down); one row per user id, rewritten on every change. Re-runnable.
CREATE TABLE IF NOT EXISTS user_profiles (
  user_id     text PRIMARY KEY,
  facts       jsonb NOT NULL,                -- {name, place, age, likes, dislikes, extra}: each {value, at}
  updated_at  timestamptz NOT NULL DEFAULT now()
);
