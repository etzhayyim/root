REVOKE ALL ON edge_shosha_trade_settlement FROM kaisya_app;

REVOKE ALL ON edge_shosha_trade_settlement FROM root;

REVOKE ALL ON vertex_shosha_settlement     FROM kaisya_app;

REVOKE ALL ON vertex_shosha_settlement     FROM root;

DROP MATERIALIZED VIEW IF EXISTS mv_shosha_settled_pnl_daily;

DROP TABLE IF EXISTS edge_shosha_trade_settlement;

DROP TABLE IF EXISTS vertex_shosha_settlement;
