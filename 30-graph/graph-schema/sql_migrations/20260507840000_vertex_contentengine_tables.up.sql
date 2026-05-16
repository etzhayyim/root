ALTER TABLE vertex_contentengine_cohort_profile ADD COLUMN IF NOT EXISTS cohort_name VARCHAR;

ALTER TABLE vertex_contentengine_cohort_profile ADD COLUMN IF NOT EXISTS interests TEXT;

ALTER TABLE vertex_contentengine_cohort_profile ADD COLUMN IF NOT EXISTS reading_level VARCHAR;

ALTER TABLE vertex_contentengine_cohort_profile ADD COLUMN IF NOT EXISTS preferred_formats TEXT;

ALTER TABLE vertex_contentengine_cohort_profile ADD COLUMN IF NOT EXISTS industry_context VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_cten_cohort_name ON vertex_contentengine_cohort_profile (cohort_name);

ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS content_id VARCHAR;

ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS cohort_name VARCHAR;

ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS content_type VARCHAR;

ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS topic VARCHAR;

ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS tone VARCHAR;

ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS title VARCHAR;

ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS body TEXT;

ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION;

ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS relevance_score DOUBLE PRECISION;

ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS include_sponsor_slot BOOLEAN;

ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS ad_campaign_id VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_cten_content_id ON vertex_contentengine_content (content_id);

CREATE INDEX IF NOT EXISTS idx_vertex_cten_content_cohort ON vertex_contentengine_content (cohort_name);

CREATE INDEX IF NOT EXISTS idx_vertex_cten_content_type ON vertex_contentengine_content (content_type);

CREATE INDEX IF NOT EXISTS idx_vertex_cten_content_status ON vertex_contentengine_content (status);

CREATE INDEX IF NOT EXISTS idx_vertex_cten_content_score ON vertex_contentengine_content (quality_score);
