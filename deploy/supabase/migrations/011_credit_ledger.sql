-- Hosted only. Per-person credits: a RESERVATION before a paid call, a SETTLE on its real cost, a REFUND when it fails (plan.md section 7).
-- The balance is accounts.test_credits; this table is the book it is computed from, so "who spent what" is answerable per person and per day. Re-runnable.

CREATE TABLE IF NOT EXISTS credit_ledger (
  id          bigserial PRIMARY KEY,
  u_id        text NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ts          timestamptz NOT NULL DEFAULT now(),
  kind        text NOT NULL CHECK (kind IN ('grant', 'reserve', 'settle', 'refund')),
  credits     numeric(10,2) NOT NULL,              -- positive amounts; the sign comes from `kind`
  job_id      text,                                -- J### (out/jobs)
  external_task_id text,                           -- the provider's ticket: the hard truth of rule 10
  note        text
);
CREATE INDEX IF NOT EXISTS credit_ledger_u_ts ON credit_ledger (u_id, ts DESC);
CREATE UNIQUE INDEX IF NOT EXISTS credit_ledger_one_settle ON credit_ledger (job_id, kind) WHERE kind IN ('settle', 'refund') AND job_id IS NOT NULL;   -- a job settles or refunds at most once
ALTER TABLE credit_ledger ENABLE ROW LEVEL SECURITY;

-- reserve: refuses (returns false) when the person cannot afford it; atomic, so two tabs cannot both spend the last credits
CREATE OR REPLACE FUNCTION reserve_credits(p_u text, p_credits numeric, p_job text) RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE ok integer;
BEGIN
  UPDATE accounts SET test_credits = test_credits - p_credits WHERE u_id = p_u AND NOT disabled AND test_credits >= p_credits;
  GET DIAGNOSTICS ok = ROW_COUNT;
  IF ok = 1 THEN
    INSERT INTO credit_ledger (u_id, kind, credits, job_id, note) VALUES (p_u, 'reserve', p_credits, p_job, 'reserved before the provider call');
  END IF;
  RETURN ok = 1;
END $$;

-- settle: the real cost replaces the reservation (the difference goes back or is taken); refund: a failed job gives the whole reservation back
CREATE OR REPLACE FUNCTION settle_credits(p_u text, p_reserved numeric, p_real numeric, p_job text, p_ticket text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  UPDATE accounts SET test_credits = greatest(0, test_credits + p_reserved - p_real) WHERE u_id = p_u;
  INSERT INTO credit_ledger (u_id, kind, credits, job_id, external_task_id) VALUES (p_u, 'settle', p_real, p_job, p_ticket);
END $$;

CREATE OR REPLACE FUNCTION refund_credits(p_u text, p_reserved numeric, p_job text, p_note text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  UPDATE accounts SET test_credits = test_credits + p_reserved WHERE u_id = p_u;
  INSERT INTO credit_ledger (u_id, kind, credits, job_id, note) VALUES (p_u, 'refund', p_reserved, p_job, p_note);
END $$;
