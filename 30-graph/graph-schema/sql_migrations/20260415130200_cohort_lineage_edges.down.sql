DROP MATERIALIZED VIEW IF EXISTS "mv_cohort_lineage_depth";

DROP INDEX IF EXISTS "idx_edge_cohort_routes_pcfl1";

DROP TABLE IF EXISTS "edge_cohort_routes_to";

DROP INDEX IF EXISTS "idx_edge_cohort_evidence_dst";

DROP TABLE IF EXISTS "edge_cohort_evidence_about";

DROP INDEX IF EXISTS "idx_edge_cohort_derived_dst";

DROP INDEX IF EXISTS "idx_edge_cohort_derived_src";

DROP TABLE IF EXISTS "edge_cohort_derived";
