DROP MATERIALIZED VIEW IF EXISTS "mv_infer_cluster_summary";

DROP INDEX IF EXISTS "idx_vertex_infer_match_cohort";

DROP TABLE IF EXISTS "vertex_infer_match";

DROP INDEX IF EXISTS "idx_vertex_infer_cluster_batch";

DROP TABLE IF EXISTS "vertex_infer_cluster";

DROP INDEX IF EXISTS "idx_vertex_infer_input_batch";

DROP TABLE IF EXISTS "vertex_infer_input";
