DROP INDEX IF EXISTS idx_projector_flow_run_claimable;

ALTER TABLE vertex_projector_flow_run DROP COLUMN IF EXISTS owner_token_expires_at;

ALTER TABLE vertex_projector_flow_run DROP COLUMN IF EXISTS owner_token;
