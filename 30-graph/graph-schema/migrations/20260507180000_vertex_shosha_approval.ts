import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (approval audit trail — approver_did + role are sensitive
//          but not Tier-3 PII; full RACI split deferred to Phase 3.)

/**
 * shosha.etzhayyim.com Phase 2d (simplified) — approval audit trail.
 *
 * Phase 1 set `approval_state='pending'` on trades >= $1M but had no
 * way to flip pending → approved (or rejected). Phase 2c settleTrade
 * auto-promotes pending → approved as a side-effect of settlement,
 * which is wrong governance: settlement should presuppose approval,
 * not bypass it.
 *
 * Phase 2d adds explicit approveTrade / rejectTrade XRPCs backed by
 * this audit table. Each decision lands a row capturing approver,
 * role, rationale, and amount-at-decision.
 *
 * Multi-day message-event BPMN (deferred to Phase 3) would couple
 * submitTrade.bpmn to wait on an approval event; this simplified
 * Phase 2d is human-in-the-loop via independent XRPC.
 *
 * Tables (1 vertex + 1 streaming MV):
 *   vertex_shosha_approval        per-decision audit row
 *   mv_shosha_approval_summary    per-trade approval count + decision history
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shosha_approval (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      approval_id varchar NOT NULL,
      ref_trade_id varchar NOT NULL,
      decision varchar NOT NULL,
      approver_did varchar,
      approver_role varchar,
      amount_usd_at_decision double precision,
      rationale varchar,
      decided_at varchar NOT NULL,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shosha_approval_summary AS
      SELECT
        ref_trade_id,
        decision,
        COUNT(*) AS decision_count,
        MAX(decided_at) AS last_decided_at,
        SUM(COALESCE(amount_usd_at_decision, 0)) AS total_amount_usd
      FROM vertex_shosha_approval
      WHERE status = 'active'
      GROUP BY ref_trade_id, decision;
  `.execute(db);

  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_approval TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_shosha_approval TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`REVOKE ALL ON vertex_shosha_approval FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON vertex_shosha_approval FROM root`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shosha_approval_summary`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shosha_approval`.execute(db);
}
