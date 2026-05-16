-- mv_pregel_step_pending: per-(gewp_thread_id, gewp_step) arrival tracking for ext:pregel barrier.
-- A barrier step is satisfied when arrived_count == expected_count (set by the sender via payload).
-- Phase 3 of ADR-2605141900.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_pregel_step_pending AS
SELECT
    gewp_thread_id,
    gewp_step,
    COUNT(*)                                        AS arrived_count,
    MIN(received_at_ms)                             AS first_arrived_ms,
    MAX(received_at_ms)                             AS last_arrived_ms,
    ARRAY_AGG(vertex_id ORDER BY received_at_ms)    AS vertex_ids,
    ARRAY_AGG(DISTINCT sender_address)              AS sender_addresses
FROM vertex_mailer_inbound_email
WHERE gewp_thread_id IS NOT NULL
  AND gewp_step      IS NOT NULL
  AND gewp_type      = 'pregel.barrier'
GROUP BY gewp_thread_id, gewp_step;
