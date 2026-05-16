-- Rollback GEWP columns from mailer tables

ALTER TABLE vertex_mailer_inbound_email
  DROP COLUMN IF EXISTS gewp_thread_id,
  DROP COLUMN IF EXISTS gewp_step,
  DROP COLUMN IF EXISTS gewp_type,
  DROP COLUMN IF EXISTS gewp_performative;

ALTER TABLE vertex_mailer_outbound_email
  DROP COLUMN IF EXISTS gewp_thread_id,
  DROP COLUMN IF EXISTS gewp_step;
