import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Add tenant_id column to all lawfirm tables for D3 demo-tenant scoping
 * (sandbox path: lawfirm.etzhayyim.com/?tenant=nishith → tenant_id='demo-nishith').
 *
 * Production rows default to 'production'. Demo tenants use 'demo-{slug}'.
 * Single-Worker, single-RW-namespace, query-time filter.
 *
 * Tables affected:
 *   vertex_lawfirm_lead
 *   vertex_lawfirm_outreach_event
 *   vertex_lawfirm_pipeline_stage
 *   vertex_lawfirm_invoice
 *   vertex_lawfirm_payment
 *   vertex_lawfirm_marketing_asset
 *   vertex_lawfirm_marketing_run
 *   vertex_lawfirm_esign_request
 *   vertex_lawfirm_pwc_clearance
 *   vertex_lawfirm_msgraph_subscription
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const tables = [
    "vertex_lawfirm_lead",
    "vertex_lawfirm_outreach_event",
    "vertex_lawfirm_pipeline_stage",
    "vertex_lawfirm_invoice",
    "vertex_lawfirm_payment",
    "vertex_lawfirm_marketing_asset",
    "vertex_lawfirm_marketing_run",
    "vertex_lawfirm_esign_request",
    "vertex_lawfirm_pwc_clearance",
    "vertex_lawfirm_msgraph_subscription",
  ];
  for (const tbl of tables) {
    await sql`ALTER TABLE ${sql.id(tbl)} ADD COLUMN tenant_id varchar DEFAULT 'production'`.execute(db);
  }

  // Convenience MV: per-tenant lead count (helps D3 demo isolation verify)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lawfirm_tenant_lead_count AS
    SELECT
      COALESCE(tenant_id, 'production') AS tenant_id,
      COUNT(*) AS lead_count,
      COUNT(*) FILTER (WHERE stage = 'paid') AS paid_count
    FROM vertex_lawfirm_lead
    GROUP BY COALESCE(tenant_id, 'production')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_tenant_lead_count`.execute(db);
  const tables = [
    "vertex_lawfirm_lead",
    "vertex_lawfirm_outreach_event",
    "vertex_lawfirm_pipeline_stage",
    "vertex_lawfirm_invoice",
    "vertex_lawfirm_payment",
    "vertex_lawfirm_marketing_asset",
    "vertex_lawfirm_marketing_run",
    "vertex_lawfirm_esign_request",
    "vertex_lawfirm_pwc_clearance",
    "vertex_lawfirm_msgraph_subscription",
  ];
  for (const tbl of tables) {
    await sql`ALTER TABLE ${sql.id(tbl)} DROP COLUMN tenant_id`.execute(db);
  }
}
