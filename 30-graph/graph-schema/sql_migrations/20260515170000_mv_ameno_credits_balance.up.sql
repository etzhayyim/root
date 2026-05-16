-- Phase 5j — per-user credit balance for the ameno Tier 2 reward loop.
-- Aggregates vertex_credits_af_event rows written by ameno_handlers
-- (event_type='ameno_browser_inference', amount = base + outputTokens/100).
-- user_id cardinality = unique actor DIDs that ran browser inference,
-- bounded; SUM/COUNT/MAX over BIGINT only — well within MV memory rules
-- (no wide MAX(varchar), no high-cardinality GROUP BY).
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ameno_credits_balance AS
SELECT
  user_id,
  SUM(amount)        AS balance,
  COUNT(*)           AS event_count,
  MAX(ts_ms)         AS last_event_ts_ms,
  MAX(created_at)    AS last_event_created_at
FROM vertex_credits_af_event
WHERE event_type = 'ameno_browser_inference'
GROUP BY user_id;
