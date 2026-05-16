ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS input_kind VARCHAR;

ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS raw_ref TEXT;

ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS signal_hash VARCHAR;

ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS classification VARCHAR;

ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION;

ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS fixed_at VARCHAR;

ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS released_at VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_koke_fixation_hash ON vertex_koke_fixation (signal_hash);

CREATE INDEX IF NOT EXISTS idx_vertex_koke_fixation_status ON vertex_koke_fixation (status);

ALTER TABLE edge_koke_flow ADD COLUMN IF NOT EXISTS fixation_id VARCHAR;

ALTER TABLE edge_koke_flow ADD COLUMN IF NOT EXISTS ferment_id VARCHAR;

ALTER TABLE edge_koke_flow ADD COLUMN IF NOT EXISTS handoff_kind VARCHAR;

ALTER TABLE edge_koke_flow ADD COLUMN IF NOT EXISTS handed_off_at VARCHAR;
