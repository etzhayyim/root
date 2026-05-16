DROP MATERIALIZED VIEW IF EXISTS mv_shosha_at_risk_trades;

DROP MATERIALIZED VIEW IF EXISTS mv_shosha_pnl_daily;

DROP MATERIALIZED VIEW IF EXISTS mv_shosha_exposure_by_counterparty;

DROP MATERIALIZED VIEW IF EXISTS mv_shosha_exposure_by_commodity;

DROP TABLE IF EXISTS edge_shosha_trade_hedge;

DROP TABLE IF EXISTS edge_shosha_trade_counterparty;

DROP TABLE IF EXISTS vertex_shosha_hedge;

DROP TABLE IF EXISTS vertex_shosha_exposure_snapshot;

DROP TABLE IF EXISTS vertex_shosha_trade;

DROP TABLE IF EXISTS vertex_shosha_counterparty;

DROP TABLE IF EXISTS vertex_shosha_market_view;

DROP TABLE IF EXISTS vertex_shosha_intel;
