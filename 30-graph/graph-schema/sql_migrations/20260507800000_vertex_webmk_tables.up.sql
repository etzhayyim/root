ALTER TABLE vertex_webmk_client ADD COLUMN IF NOT EXISTS client_name VARCHAR;

ALTER TABLE vertex_webmk_client ADD COLUMN IF NOT EXISTS website_url VARCHAR;

ALTER TABLE vertex_webmk_client ADD COLUMN IF NOT EXISTS industry VARCHAR;

ALTER TABLE vertex_webmk_client ADD COLUMN IF NOT EXISTS delivery_email VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_webmk_client_url ON vertex_webmk_client (website_url);

ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS client_vid VARCHAR;

ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS proposal_id VARCHAR;

ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS budget_jpy BIGINT;

ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS strategy_json TEXT;

ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS copy_markdown TEXT;

ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION;

ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS lg_run_id VARCHAR;

ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS delivered_at VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_webmk_proposal_id ON vertex_webmk_proposal (proposal_id);

CREATE INDEX IF NOT EXISTS idx_vertex_webmk_proposal_status ON vertex_webmk_proposal (status);

CREATE INDEX IF NOT EXISTS idx_vertex_webmk_proposal_client ON vertex_webmk_proposal (client_vid);

ALTER TABLE edge_webmk_campaign_link ADD COLUMN IF NOT EXISTS proposal_id VARCHAR;

ALTER TABLE edge_webmk_campaign_link ADD COLUMN IF NOT EXISTS ads_campaign_id VARCHAR;

ALTER TABLE edge_webmk_campaign_link ADD COLUMN IF NOT EXISTS ads_campaign_did VARCHAR;

CREATE INDEX IF NOT EXISTS idx_edge_webmk_campaign_proposal ON edge_webmk_campaign_link (proposal_id);
