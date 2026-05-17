import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (settlement record — bank refs are sensitive but not Tier-3 PII;
//          full Tier-3 split deferred to a future PII tightening pass)

/**
 * shosha.etzhayyim.com Phase 2c — settlement workflow.
 *
 * Restores the table that was deferred from Phase 1 (originally listed in
 * the Phase 1 ADR but cut for scope). Closes the trade lifecycle:
 *   submitTrade (open/pending) → settleTrade (closed/settled)
 * (Phase 2d will add the standalone approveTrade flow between these.)
 *
 * Tables (1 vertex + 1 edge + 1 streaming MV):
 *   vertex_shosha_settlement       per-trade settlement record
 *   edge_shosha_trade_settlement   trade → settlement
 *   mv_shosha_settled_pnl_daily    realized P&L on settled trades only
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
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
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_shosha_trade_settlement (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
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
  `.execute(db);

  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_settlement     TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_settlement     TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_shosha_trade_settlement TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON edge_shosha_trade_settlement TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`REVOKE ALL ON edge_shosha_trade_settlement FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON edge_shosha_trade_settlement FROM root`.execute(db);
  await sql`REVOKE ALL ON vertex_shosha_settlement     FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON vertex_shosha_settlement     FROM root`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shosha_settled_pnl_daily`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_shosha_trade_settlement`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shosha_settlement`.execute(db);
}
