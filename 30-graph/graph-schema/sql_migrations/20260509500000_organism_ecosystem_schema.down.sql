-- Reverse of 20260509500000_organism_ecosystem_schema.up.sql

DROP MATERIALIZED VIEW IF EXISTS mv_gradient_flow_rollup;
DROP MATERIALIZED VIEW IF EXISTS mv_bonsai_water_inflow;
DROP MATERIALIZED VIEW IF EXISTS mv_bonsai_pruning_rate;

DROP TABLE IF EXISTS edge_gradient_flow;
DROP TABLE IF EXISTS vertex_router_weight;
-- vertex_model_checkpoint kept (pre-existing); revert only added columns
ALTER TABLE vertex_model_checkpoint DROP COLUMN IF EXISTS ipfs_pinned_layers;
ALTER TABLE vertex_model_checkpoint DROP COLUMN IF EXISTS lean_verified;
ALTER TABLE vertex_model_checkpoint DROP COLUMN IF EXISTS mutation_acceptance_rate;
ALTER TABLE vertex_model_checkpoint DROP COLUMN IF EXISTS karma_safety;
ALTER TABLE vertex_model_checkpoint DROP COLUMN IF EXISTS fruit_accept_rate;
ALTER TABLE vertex_model_checkpoint DROP COLUMN IF EXISTS pruning_rate;
ALTER TABLE vertex_model_checkpoint DROP COLUMN IF EXISTS cohort_did;
ALTER TABLE vertex_model_checkpoint DROP COLUMN IF EXISTS param_count;
ALTER TABLE vertex_model_checkpoint DROP COLUMN IF EXISTS fp8_format;
ALTER TABLE vertex_model_checkpoint DROP COLUMN IF EXISTS parent_cid;
ALTER TABLE vertex_model_checkpoint DROP COLUMN IF EXISTS checkpoint_cid;
DROP TABLE IF EXISTS vertex_organism_embedding;

DROP TABLE IF EXISTS edge_yoro_graft;
DROP TABLE IF EXISTS edge_kobo_plasmid_carry;
DROP TABLE IF EXISTS vertex_kobo_plasmid;

DROP TABLE IF EXISTS vertex_water_consent_grant;
DROP TABLE IF EXISTS edge_bonsai_water;

DROP TABLE IF EXISTS edge_yoro_prune;

DROP TABLE IF EXISTS edge_yoro_pollinate;
DROP TABLE IF EXISTS vertex_yoro_fruit;
DROP TABLE IF EXISTS vertex_yoro_flower;
