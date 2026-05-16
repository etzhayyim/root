DROP VIEW IF EXISTS view_profile_page_stats;

DROP INDEX IF EXISTS idx_mv_page_count_by_owner_canonical_did;

DROP INDEX IF EXISTS idx_mv_profile_core_stats_canonical_actor_did;

DROP INDEX IF EXISTS idx_mv_profile_core_stats_actor_did;

DROP MATERIALIZED VIEW IF EXISTS mv_page_count_by_owner_canonical_did;

DROP MATERIALIZED VIEW IF EXISTS mv_profile_core_stats;
