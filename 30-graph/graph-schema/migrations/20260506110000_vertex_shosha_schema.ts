import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (trading book — counterparty + trade + hedge are sensitive but
//          not Tier-3 PII; full PII split deferred to Phase 2)

/**
 * shosha.gftd.ai Phase 1 — sogo-shosha (general trading company) schema
 * (ADR-0036 Worker-direct Hyperdrive + ADR-0056 BPMN-as-actor +
 *  ADR-2604282300 T2 = pymagatama + Zeebe, no CF Worker).
 *
 * Tables (6 vertex + 2 edge):
 *   vertex_shosha_intel              market intel ticks (price/FX/freight/news)
 *   vertex_shosha_market_view        LLM-synthesized per-commodity outlook
 *   vertex_shosha_counterparty       counterparty registry + sanction status
 *   vertex_shosha_trade              trade tickets (procure/trade/hedge desks)
 *   vertex_shosha_exposure_snapshot  point-in-time exposure aggregates
 *   vertex_shosha_hedge              hedge instruments (futures/forward/swap)
 *   edge_shosha_trade_counterparty   trade → counterparty
 *   edge_shosha_trade_hedge          trade → hedge instrument
 *
 * Streaming MVs (4):
 *   mv_shosha_exposure_by_commodity     net long/short per commodity
 *   mv_shosha_exposure_by_counterparty  concentration per counterparty
 *   mv_shosha_pnl_daily                 daily realized + unrealized P&L
 *   mv_shosha_at_risk_trades            trades flagged by sanction match,
 *                                        counterparty downgrade, or
 *                                        unhedged > 0 USD
 *
 * Settlement table + approval-state vertex are deferred to Phase 2.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shosha_intel (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      source varchar NOT NULL,
      symbol varchar NOT NULL,
      category varchar NOT NULL,
      value double precision,
      unit varchar,
      ts_ms bigint NOT NULL,
      raw_json varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shosha_market_view (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      commodity varchar NOT NULL,
      as_of_date date NOT NULL,
      direction varchar NOT NULL,
      confidence double precision,
      price_target double precision,
      price_currency varchar,
      price_unit varchar,
      rationale varchar,
      intel_count_used int,
      llm_model varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shosha_counterparty (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      name varchar NOT NULL,
      name_normalized varchar NOT NULL,
      country varchar,
      legal_entity_id varchar,
      risk_band varchar,
      credit_limit_usd double precision,
      sanction_status varchar NOT NULL,
      sanction_flags varchar,
      last_reviewed_at varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shosha_trade (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      trade_id varchar NOT NULL,
      side varchar NOT NULL,
      commodity varchar NOT NULL,
      quantity double precision NOT NULL,
      unit varchar NOT NULL,
      price double precision NOT NULL,
      currency varchar NOT NULL,
      amount_usd double precision,
      counterparty_name varchar NOT NULL,
      counterparty_vid varchar,
      desk varchar NOT NULL,
      delivery_date date,
      delivery_location varchar,
      rationale varchar,
      comply_ok boolean NOT NULL,
      comply_flags varchar,
      approval_state varchar NOT NULL,
      approver varchar,
      approved_at varchar,
      status varchar NOT NULL,
      pnl_realized double precision,
      pnl_unrealized double precision,
      pnl_marked_at varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shosha_exposure_snapshot (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      as_of_ts_ms bigint NOT NULL,
      group_by varchar NOT NULL,
      group_key varchar NOT NULL,
      gross_long double precision,
      gross_short double precision,
      net double precision,
      hedged double precision,
      unhedged double precision,
      currency varchar,
      counterparty_top1 varchar,
      counterparty_top1_pct double precision,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shosha_hedge (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      hedge_id varchar NOT NULL,
      instrument varchar NOT NULL,
      commodity varchar NOT NULL,
      ref_trade_id varchar,
      direction varchar NOT NULL,
      notional double precision NOT NULL,
      currency varchar,
      strike double precision,
      expiry_date date,
      broker varchar,
      target_hedge_ratio double precision,
      current_exposure double precision,
      rationale varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_shosha_trade_counterparty (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_shosha_trade_hedge (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Streaming MVs ──────────────────────────────────────────────────

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shosha_exposure_by_commodity AS
      SELECT
        commodity,
        currency,
        COUNT(*) FILTER (WHERE status='open') AS open_count,
        SUM(CASE WHEN side='buy'  AND status='open' THEN amount_usd ELSE 0 END) AS gross_long_usd,
        SUM(CASE WHEN side='sell' AND status='open' THEN amount_usd ELSE 0 END) AS gross_short_usd,
        SUM(CASE WHEN side='buy'  AND status='open' THEN amount_usd
                 WHEN side='sell' AND status='open' THEN -amount_usd ELSE 0 END) AS net_usd
      FROM vertex_shosha_trade
      WHERE comply_ok = true
      GROUP BY commodity, currency;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shosha_exposure_by_counterparty AS
      SELECT
        counterparty_name,
        COUNT(*) FILTER (WHERE status='open') AS open_count,
        SUM(CASE WHEN status='open' THEN amount_usd ELSE 0 END) AS open_notional_usd,
        SUM(CASE WHEN side='buy'  AND status='open' THEN amount_usd ELSE 0 END) AS long_usd,
        SUM(CASE WHEN side='sell' AND status='open' THEN amount_usd ELSE 0 END) AS short_usd
      FROM vertex_shosha_trade
      WHERE comply_ok = true
      GROUP BY counterparty_name;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shosha_pnl_daily AS
      SELECT
        created_date,
        commodity,
        SUM(COALESCE(pnl_realized, 0))   AS realized_usd,
        SUM(COALESCE(pnl_unrealized, 0)) AS unrealized_usd,
        SUM(COALESCE(pnl_realized, 0) + COALESCE(pnl_unrealized, 0)) AS total_usd,
        COUNT(*) AS trade_count
      FROM vertex_shosha_trade
      WHERE comply_ok = true
      GROUP BY created_date, commodity;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shosha_at_risk_trades AS
      SELECT
        t.vertex_id,
        t.trade_id,
        t.commodity,
        t.side,
        t.amount_usd,
        t.counterparty_name,
        t.approval_state,
        t.status,
        CASE
          WHEN t.comply_ok = false                                  THEN 'comply-blocked'
          WHEN c.sanction_status IN ('flagged','blocked')           THEN 'counterparty-sanctioned'
          WHEN t.approval_state = 'pending' AND t.amount_usd > 1000000 THEN 'large-pending'
          WHEN t.status = 'open' AND COALESCE(t.pnl_unrealized, 0) < -100000 THEN 'mtm-loss'
          ELSE 'unhedged'
        END AS risk_class,
        t.created_at
      FROM vertex_shosha_trade t
      LEFT JOIN vertex_shosha_counterparty c
        ON c.name = t.counterparty_name AND c.status = 'active'
      WHERE t.status IN ('open','pending')
        AND (
          t.comply_ok = false
          OR c.sanction_status IN ('flagged','blocked')
          OR (t.approval_state = 'pending' AND t.amount_usd > 1000000)
          OR (t.status = 'open' AND COALESCE(t.pnl_unrealized, 0) < -100000)
        );
  `.execute(db);

  // ── Grants ─────────────────────────────────────────────────────────
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_intel              TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_intel              TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_market_view        TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_market_view        TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_counterparty       TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_counterparty       TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_trade              TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_trade              TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_exposure_snapshot  TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_exposure_snapshot  TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_hedge              TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_hedge              TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_shosha_trade_counterparty   TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_shosha_trade_counterparty   TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_shosha_trade_hedge          TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_shosha_trade_hedge          TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shosha_at_risk_trades`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shosha_pnl_daily`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shosha_exposure_by_counterparty`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shosha_exposure_by_commodity`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_shosha_trade_hedge`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_shosha_trade_counterparty`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shosha_hedge`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shosha_exposure_snapshot`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shosha_trade`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shosha_counterparty`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shosha_market_view`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shosha_intel`.execute(db);
}
