-- mv_mailer_gewp_pending — GEWP inbound message processing queue
-- ADR-2605141900 Phase 2: downstream GEWP routing for pregel_triage bridge

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mailer_gewp_pending AS
SELECT
    vertex_id,
    message_id,
    gewp_thread_id,
    gewp_step,
    gewp_type,
    gewp_performative,
    received_at_ms,
    status
FROM vertex_mailer_inbound_email
WHERE gewp_thread_id IS NOT NULL
  AND gewp_step       IS NOT NULL;
