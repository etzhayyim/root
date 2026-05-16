ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS competitor_id VARCHAR;

ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS competitor_name VARCHAR;

ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS website VARCHAR;

ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS industry VARCHAR;

ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS tracking_dimensions TEXT;

ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS threat_score DOUBLE PRECISION;

ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS last_refreshed_at VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_compintel_competitor_id ON vertex_compintel_competitor (competitor_id);

CREATE INDEX IF NOT EXISTS idx_vertex_compintel_competitor_industry ON vertex_compintel_competitor (industry);

CREATE INDEX IF NOT EXISTS idx_vertex_compintel_competitor_threat ON vertex_compintel_competitor (threat_score);

ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS snapshot_id VARCHAR;

ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS competitor_id VARCHAR;

ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS latest_summary TEXT;

ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS pricing_signals TEXT;

ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS product_signals TEXT;

ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS hiring_signals TEXT;

ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS funding_signals TEXT;

ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS press_signals TEXT;

ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS threat_score DOUBLE PRECISION;

ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS content_hash VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_compintel_snapshot_competitor ON vertex_compintel_snapshot (competitor_id);

CREATE INDEX IF NOT EXISTS idx_vertex_compintel_snapshot_created ON vertex_compintel_snapshot (competitor_id, created_at);

ALTER TABLE vertex_compintel_alert ADD COLUMN IF NOT EXISTS alert_id VARCHAR;

ALTER TABLE vertex_compintel_alert ADD COLUMN IF NOT EXISTS competitor_id VARCHAR;

ALTER TABLE vertex_compintel_alert ADD COLUMN IF NOT EXISTS dimension VARCHAR;

ALTER TABLE vertex_compintel_alert ADD COLUMN IF NOT EXISTS summary TEXT;

ALTER TABLE vertex_compintel_alert ADD COLUMN IF NOT EXISTS severity VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_compintel_alert_competitor ON vertex_compintel_alert (competitor_id);

CREATE INDEX IF NOT EXISTS idx_vertex_compintel_alert_severity ON vertex_compintel_alert (severity);

CREATE INDEX IF NOT EXISTS idx_vertex_compintel_alert_created ON vertex_compintel_alert (created_at);

ALTER TABLE edge_compintel_snapshot ADD COLUMN IF NOT EXISTS competitor_id VARCHAR;

ALTER TABLE edge_compintel_snapshot ADD COLUMN IF NOT EXISTS snapshot_id VARCHAR;

CREATE INDEX IF NOT EXISTS idx_edge_compintel_snapshot_competitor ON edge_compintel_snapshot (competitor_id);
