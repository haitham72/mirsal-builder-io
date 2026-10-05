-- Help & Support (flow/support.py, flow/faq.py, flow/support_kb.py, flow/notifications.py; docs/agent-and-chat.md "Support").
-- The files under out/ are the record (out/faq/F###.json, out/support/C###.json, out/notifications/<user>.json, out/support/index.json);
-- these tables mirror them and hold the 768-d vectors (the local nomic model) the support agent searches. Re-runnable.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS faq (
  id         text PRIMARY KEY,
  status     text NOT NULL,                  -- draft | published | archived; only published rows ever answer
  title      text NOT NULL DEFAULT '',
  question   text NOT NULL DEFAULT '',
  answer     text NOT NULL DEFAULT '',
  revision   integer NOT NULL DEFAULT 0,
  updated    timestamptz NOT NULL,
  vec        vector(768),                    -- the published question + answer; NULL until published and embedded
  embed_model text,
  body       jsonb NOT NULL                  -- the whole entry: pending proposal, revisions, provenance
);
CREATE INDEX IF NOT EXISTS faq_status ON faq (status, updated DESC);
CREATE INDEX IF NOT EXISTS faq_vec ON faq USING hnsw (vec vector_cosine_ops);

CREATE TABLE IF NOT EXISTS support_chunks (
  id         text PRIMARY KEY,               -- <kind>:<path>#<n>
  kind       text NOT NULL,                  -- doc (everyone) | code (owner and admins only)
  path       text NOT NULL,                  -- relative to MIRSAL_SUPPORT_REPO
  heading    text NOT NULL DEFAULT '',
  text       text NOT NULL,
  sha        text NOT NULL,                  -- the file's sha256 when it was cut
  vec        vector(768),
  embed_model text
);
CREATE INDEX IF NOT EXISTS support_chunks_path ON support_chunks (path);
CREATE INDEX IF NOT EXISTS support_chunks_vec ON support_chunks USING hnsw (vec vector_cosine_ops);

CREATE TABLE IF NOT EXISTS support_conversations (
  id         text PRIMARY KEY,
  user_id    text NOT NULL,
  status     text NOT NULL,                  -- answered | awaiting_admin | admin_replied | resolved
  ticket     text,
  updated    timestamptz NOT NULL,
  body       jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS support_conversations_user ON support_conversations (user_id, updated DESC);

CREATE TABLE IF NOT EXISTS notifications (
  id         text PRIMARY KEY,               -- <user>:<event key>
  user_id    text NOT NULL,
  at         timestamptz NOT NULL,
  kind       text NOT NULL,                  -- reply | resolved
  read       boolean NOT NULL DEFAULT false,
  body       jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS notifications_user ON notifications (user_id, at DESC);
