DROP INDEX IF EXISTS idx_mv_cpc_patent_coverage_cpc;

DROP INDEX IF EXISTS idx_mv_cpc_patent_prefix_match_patent;

DROP INDEX IF EXISTS idx_mv_cpc_patent_prefix_match_cpc;

DROP MATERIALIZED VIEW IF EXISTS mv_cpc_patent_coverage;

DROP MATERIALIZED VIEW IF EXISTS mv_cpc_patent_prefix_match;

DROP VIEW IF EXISTS view_cpc_product_live;
