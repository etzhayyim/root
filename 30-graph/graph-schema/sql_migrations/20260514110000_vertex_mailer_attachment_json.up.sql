-- Add attachment_json column to vertex_mailer_inbound_email
-- ADR-2605141900 Phase 2: store GEWP Layer-1 attachment payload from email-relay Worker

ALTER TABLE vertex_mailer_inbound_email
  ADD COLUMN IF NOT EXISTS attachment_json VARCHAR;
