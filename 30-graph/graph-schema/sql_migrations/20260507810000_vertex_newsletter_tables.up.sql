ALTER TABLE vertex_newsletter_subscriber ADD COLUMN IF NOT EXISTS email VARCHAR;

ALTER TABLE vertex_newsletter_subscriber ADD COLUMN IF NOT EXISTS subscriber_name VARCHAR;

ALTER TABLE vertex_newsletter_subscriber ADD COLUMN IF NOT EXISTS cohort_name VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_newsletter_subscriber_email ON vertex_newsletter_subscriber (email);

CREATE INDEX IF NOT EXISTS idx_vertex_newsletter_subscriber_cohort ON vertex_newsletter_subscriber (cohort_name);

ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS campaign_id VARCHAR;

ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS campaign_name VARCHAR;

ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS topic TEXT;

ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS cohort_name VARCHAR;

ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS subject_line VARCHAR;

ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS body_html TEXT;

ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION;

ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS recipient_count BIGINT;

ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS include_ad_slot BOOLEAN;

ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS ad_campaign_id VARCHAR;

ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS sent_at VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_newsletter_campaign_id ON vertex_newsletter_campaign (campaign_id);

CREATE INDEX IF NOT EXISTS idx_vertex_newsletter_campaign_status ON vertex_newsletter_campaign (status);

ALTER TABLE vertex_newsletter_engagement ADD COLUMN IF NOT EXISTS campaign_id VARCHAR;

ALTER TABLE vertex_newsletter_engagement ADD COLUMN IF NOT EXISTS event_type VARCHAR;

ALTER TABLE vertex_newsletter_engagement ADD COLUMN IF NOT EXISTS resend_email_id VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_newsletter_engagement_campaign ON vertex_newsletter_engagement (campaign_id);

CREATE INDEX IF NOT EXISTS idx_vertex_newsletter_engagement_type ON vertex_newsletter_engagement (event_type);

ALTER TABLE edge_newsletter_sent ADD COLUMN IF NOT EXISTS campaign_id VARCHAR;

ALTER TABLE edge_newsletter_sent ADD COLUMN IF NOT EXISTS subscriber_id VARCHAR;

ALTER TABLE edge_newsletter_sent ADD COLUMN IF NOT EXISTS resend_email_id VARCHAR;

CREATE INDEX IF NOT EXISTS idx_edge_newsletter_sent_campaign ON edge_newsletter_sent (campaign_id);
