-- GEWP (Etzhayyim Email Wire Protocol) columns for mailer tables
-- ADR-2605141900 — mailer.etzhayyim.com GEWP implementation

ALTER TABLE vertex_mailer_inbound_email
  ADD COLUMN IF NOT EXISTS gewp_thread_id   VARCHAR,
  ADD COLUMN IF NOT EXISTS gewp_step        BIGINT,
  ADD COLUMN IF NOT EXISTS gewp_type        VARCHAR,
  ADD COLUMN IF NOT EXISTS gewp_performative VARCHAR;

ALTER TABLE vertex_mailer_outbound_email
  ADD COLUMN IF NOT EXISTS gewp_thread_id   VARCHAR,
  ADD COLUMN IF NOT EXISTS gewp_step        BIGINT;
