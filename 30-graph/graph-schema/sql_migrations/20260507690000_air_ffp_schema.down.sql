DROP MATERIALIZED VIEW IF EXISTS mv_air_member_tier_summary;

DROP INDEX IF EXISTS idx_air_ffp_member_tier_carrier;

DROP INDEX IF EXISTS idx_air_ffp_accrual_member_date;

DROP INDEX IF EXISTS idx_air_ffp_member_id;

DROP TABLE IF EXISTS edge_air_member_has_accrual;

DROP TABLE IF EXISTS vertex_air_ffp_transaction;

DROP TABLE IF EXISTS vertex_air_ffp_tier_event;

DROP TABLE IF EXISTS vertex_air_ffp_redemption;

DROP TABLE IF EXISTS vertex_air_ffp_miles_accrual;

DROP TABLE IF EXISTS vertex_air_ffp_member;
