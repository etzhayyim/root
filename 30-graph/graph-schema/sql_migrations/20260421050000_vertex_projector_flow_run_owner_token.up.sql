ALTER TABLE vertex_projector_flow_run
    ADD COLUMN IF NOT EXISTS owner_token VARCHAR;

ALTER TABLE vertex_projector_flow_run
    ADD COLUMN IF NOT EXISTS owner_token_expires_at VARCHAR;

CREATE INDEX IF NOT EXISTS idx_projector_flow_run_claimable
    ON vertex_projector_flow_run (status, owner_token_expires_at);
