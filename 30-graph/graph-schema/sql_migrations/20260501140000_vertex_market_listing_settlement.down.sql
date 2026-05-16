DROP MATERIALIZED VIEW IF EXISTS mv_market_vacuum_score;

DROP INDEX IF EXISTS idx_market_demand_lane_kind_date;

DROP TABLE IF EXISTS vertex_market_demand_signal;

DROP INDEX IF EXISTS idx_market_settlement_tx;

DROP INDEX IF EXISTS idx_market_settlement_bundle;

DROP INDEX IF EXISTS idx_market_settlement_lane_status;

DROP TABLE IF EXISTS vertex_market_settlement;

DROP INDEX IF EXISTS idx_market_listing_issuer;

DROP INDEX IF EXISTS idx_market_listing_lane_status;

DROP TABLE IF EXISTS vertex_market_listing;
