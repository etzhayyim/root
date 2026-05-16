-- Rollback attachment_json column
ALTER TABLE vertex_mailer_inbound_email
  DROP COLUMN IF EXISTS attachment_json;
