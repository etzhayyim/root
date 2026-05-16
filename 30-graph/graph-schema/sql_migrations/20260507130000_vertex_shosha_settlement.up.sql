CREATE TABLE IF NOT EXISTS vertex_shosha_settlement (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      settlement_id varchar NOT NULL,
      ref_trade_id varchar NOT NULL,
      currency varchar NOT NULL,
      amount double precision,
      amount_usd double precision,
      method varchar,
      bank_ref varchar,
      value_date date,
      counterparty_name varchar,
      counterparty_vid varchar,
      pnl_realized double precision,
      remarks varchar,
      status varchar NOT NULL,
      settled_at varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS edge_shosha_trade_settlement (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shosha_settled_pnl_daily AS
      SELECT
        s.created_date,
        t.commodity,
        t.currency,
        COUNT(*) AS settled_count,
        SUM(COALESCE(s.amount_usd, 0)) AS settled_notional_usd,
        SUM(COALESCE(s.pnl_realized, 0)) AS realized_usd
      FROM vertex_shosha_settlement s
      JOIN vertex_shosha_trade t
        ON t.trade_id = s.ref_trade_id
      WHERE s.status = 'settled'
      GROUP BY s.created_date, t.commodity, t.currency;

GRANT SELECT, INSERT, UPDATE ON vertex_shosha_settlement     TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_shosha_settlement     TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON edge_shosha_trade_settlement TO root;

GRANT SELECT, INSERT, UPDATE ON edge_shosha_trade_settlement TO kaisya_app;
