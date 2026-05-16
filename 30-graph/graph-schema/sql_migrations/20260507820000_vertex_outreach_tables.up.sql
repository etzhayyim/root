ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS email VARCHAR;

ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS prospect_name VARCHAR;

ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS title VARCHAR;

ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS company VARCHAR;

ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS cohort_name VARCHAR;

ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR;

ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS company_website VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_outreach_prospect_email ON vertex_outreach_prospect (email);

CREATE INDEX IF NOT EXISTS idx_vertex_outreach_prospect_cohort ON vertex_outreach_prospect (cohort_name);

ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS sequence_id VARCHAR;

ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS prospect_id VARCHAR;

ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS sequence_name VARCHAR;

ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS goal TEXT;

ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS current_step BIGINT;

ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS max_steps BIGINT;

ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS reply_detected BOOLEAN;

ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS include_sponsor_slot BOOLEAN;

ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS ad_campaign_id VARCHAR;

ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS zeebe_process_instance_key VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_outreach_sequence_id ON vertex_outreach_sequence (sequence_id);

CREATE INDEX IF NOT EXISTS idx_vertex_outreach_sequence_prospect ON vertex_outreach_sequence (prospect_id);

CREATE INDEX IF NOT EXISTS idx_vertex_outreach_sequence_status ON vertex_outreach_sequence (status);

ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS sequence_id VARCHAR;

ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS step_number BIGINT;

ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS subject_line VARCHAR;

ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS body_text TEXT;

ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION;

ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS resend_email_id VARCHAR;

ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS sent_at VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_outreach_step_sequence ON vertex_outreach_step (sequence_id);

CREATE INDEX IF NOT EXISTS idx_vertex_outreach_step_number ON vertex_outreach_step (sequence_id, step_number);

ALTER TABLE vertex_outreach_dnc ADD COLUMN IF NOT EXISTS email VARCHAR;

ALTER TABLE vertex_outreach_dnc ADD COLUMN IF NOT EXISTS reason VARCHAR;

CREATE UNIQUE INDEX IF NOT EXISTS idx_vertex_outreach_dnc_email ON vertex_outreach_dnc (email);

ALTER TABLE edge_outreach_sent ADD COLUMN IF NOT EXISTS sequence_id VARCHAR;

ALTER TABLE edge_outreach_sent ADD COLUMN IF NOT EXISTS prospect_id VARCHAR;

ALTER TABLE edge_outreach_sent ADD COLUMN IF NOT EXISTS step_number BIGINT;

ALTER TABLE edge_outreach_sent ADD COLUMN IF NOT EXISTS resend_email_id VARCHAR;

CREATE INDEX IF NOT EXISTS idx_edge_outreach_sent_sequence ON edge_outreach_sent (sequence_id);
