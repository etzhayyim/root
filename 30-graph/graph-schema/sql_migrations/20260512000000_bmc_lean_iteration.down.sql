DROP MATERIALIZED VIEW IF EXISTS mv_bmc_block_health;
DROP MATERIALIZED VIEW IF EXISTS mv_bmc_iteration_latest;
DROP MATERIALIZED VIEW IF EXISTS mv_bmc_hypothesis_status;
DROP MATERIALIZED VIEW IF EXISTS mv_bmc_state_head;

DROP INDEX IF EXISTS idx_edge_bmc_pivot_applied_src;
DROP TABLE IF EXISTS edge_bmc_pivot_applied_to_state;

DROP INDEX IF EXISTS idx_edge_bmc_dec_of_iter_src;
DROP TABLE IF EXISTS edge_bmc_decision_of_iteration;

DROP INDEX IF EXISTS idx_edge_bmc_iter_of_hyp_src;
DROP TABLE IF EXISTS edge_bmc_iteration_of_hypothesis;

DROP INDEX IF EXISTS idx_edge_bmc_hyp_in_block_src;
DROP TABLE IF EXISTS edge_bmc_hypothesis_in_block;

DROP INDEX IF EXISTS idx_edge_bmc_supersedes_src;
DROP TABLE IF EXISTS edge_bmc_state_supersedes;

DROP INDEX IF EXISTS idx_bmc_sample_window;
DROP INDEX IF EXISTS idx_bmc_sample_hyp_time;
DROP INDEX IF EXISTS idx_bmc_sample_iter;
DROP TABLE IF EXISTS vertex_bmc_metric_sample;

DROP INDEX IF EXISTS idx_bmc_dec_org_time;
DROP INDEX IF EXISTS idx_bmc_dec_iter;
DROP TABLE IF EXISTS vertex_bmc_decision;

DROP INDEX IF EXISTS idx_bmc_iter_org_time;
DROP INDEX IF EXISTS idx_bmc_iter_slug_time;
DROP TABLE IF EXISTS vertex_bmc_iteration;

DROP INDEX IF EXISTS idx_bmc_hyp_evt_org_time;
DROP INDEX IF EXISTS idx_bmc_hyp_evt_slug_time;
DROP TABLE IF EXISTS vertex_bmc_hypothesis_event;

DROP INDEX IF EXISTS idx_bmc_hyp_org_block;
DROP INDEX IF EXISTS idx_bmc_hyp_block;
DROP INDEX IF EXISTS idx_bmc_hyp_slug;
DROP TABLE IF EXISTS vertex_bmc_hypothesis;

DROP INDEX IF EXISTS idx_bmc_state_org_version;
DROP INDEX IF EXISTS idx_bmc_state_version;
DROP TABLE IF EXISTS vertex_bmc_state;
