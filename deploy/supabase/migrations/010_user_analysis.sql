-- Hosted only. What a signed-in person did and from where. READ plan.md section 10 BEFORE writing a row: an IP address is personal data (UAE PDPL, and GDPR for any EU person).
--   * ip_full only for abuse handling, set to NULL by the retention job after `ip_retention_days` (decide: 7 / 30 / 90); ip_hash (salted per deployment) counts uniques without locating anyone;
--   * country comes from the platform's CDN header, never from a geo-IP service;
--   * detail holds ids, counts, durations, model names and error codes: NEVER a prompt, a caption, a file name, a path or media (the CHECK below refuses forbidden keys);
--   * every person can export and delete their rows (GET /api/me/export, DELETE /api/me): ON DELETE CASCADE does the delete.
-- Re-runnable.

CREATE TABLE IF NOT EXISTS user_analysis (
  id          bigserial PRIMARY KEY,
  u_id        text NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ts          timestamptz NOT NULL DEFAULT now(),
  ip_hash     text,
  ip_full     text,
  user_agent  text,
  country     text,
  device      text CHECK (device IS NULL OR device IN ('phone', 'tablet', 'desktop')),
  event       text NOT NULL CHECK (event IN ('sign_in', 'sign_out', 'batch_created', 'gate_approved', 'pack_exported', 'sticker_sent', 'creator_run', 'error', 'credits_spent')),
  detail      jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (
                jsonb_typeof(detail) = 'object'
                AND NOT (detail ?| ARRAY['prompt', 'caption', 'text', 'message', 'file', 'filename', 'path', 'name', 'title', 'sheet_prompt', 'video_prompt']))
);
CREATE INDEX IF NOT EXISTS user_analysis_u_ts ON user_analysis (u_id, ts DESC);
CREATE INDEX IF NOT EXISTS user_analysis_ts ON user_analysis (ts DESC);

ALTER TABLE user_analysis ENABLE ROW LEVEL SECURITY;     -- no policy: only the service role (the API) can read or write

-- the retention job (run it daily from a scheduler; the number of days is the decision of plan.md section 16 question 7)
CREATE OR REPLACE FUNCTION purge_old_ip(days integer) RETURNS integer LANGUAGE sql AS $$
  WITH x AS (UPDATE user_analysis SET ip_full = NULL WHERE ip_full IS NOT NULL AND ts < now() - make_interval(days => days) RETURNING 1)
  SELECT count(*)::integer FROM x;
$$;
