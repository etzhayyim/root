import { Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Billing Tenant ───────────────────────────────────────────────────────
  // One row per kyber tenant. plan_id maps to ADR-2605072300 tier names.

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_billing_tenant (
      vertex_id VARCHAR PRIMARY KEY,
      tenant_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      plan_id VARCHAR NOT NULL DEFAULT 'free',
      stripe_customer_id VARCHAR,
      stripe_subscription_id VARCHAR,
      plan_activated_at VARCHAR NOT NULL,
      trial_ends_at VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      max_users INTEGER NOT NULL DEFAULT 1,
      max_monthly_txns INTEGER NOT NULL DEFAULT 100,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Usage Meter ──────────────────────────────────────────────────────────
  // Append-only counter rows. meter_type values per ADR-2605072300 §3.

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_usage_meter (
      vertex_id VARCHAR PRIMARY KEY,
      tenant_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      meter_type VARCHAR NOT NULL,
      period_month VARCHAR NOT NULL,
      delta_count BIGINT NOT NULL DEFAULT 0,
      reported_to_stripe BOOLEAN NOT NULL DEFAULT FALSE,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Stripe Report Log ────────────────────────────────────────────────────
  // Idempotency record for monthly Stripe Meter API submissions.

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kyber_stripe_report (
      vertex_id VARCHAR PRIMARY KEY,
      tenant_id VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      period_month VARCHAR NOT NULL,
      meter_type VARCHAR NOT NULL,
      total_count BIGINT NOT NULL DEFAULT 0,
      stripe_event_id VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'pending',
      reported_at VARCHAR,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Monthly Usage Aggregation MV ─────────────────────────────────────────

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kyber_monthly_usage AS
    SELECT
      tenant_id,
      org_did,
      meter_type,
      period_month,
      sum(delta_count) AS total_count
    FROM vertex_kyber_usage_meter
    GROUP BY tenant_id, org_did, meter_type, period_month
  `.execute(db);

  // ── Plan Limits View ─────────────────────────────────────────────────────

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kyber_tenant_usage_summary AS
    SELECT
      t.tenant_id,
      t.org_did,
      t.plan_id,
      t.status AS tenant_status,
      t.max_users,
      t.max_monthly_txns,
      coalesce(sum(u.delta_count) FILTER (WHERE u.meter_type = 'xrpc_request'), 0) AS xrpc_requests_total,
      coalesce(sum(u.delta_count) FILTER (WHERE u.meter_type = 'rw_row'), 0) AS rw_rows_total,
      coalesce(sum(u.delta_count) FILTER (WHERE u.meter_type = 'llm_token'), 0) AS llm_tokens_total,
      coalesce(sum(u.delta_count) FILTER (WHERE u.meter_type = 'zeebe_instance'), 0) AS zeebe_instances_total,
      coalesce(sum(u.delta_count) FILTER (WHERE u.meter_type = 'pds_byte'), 0) AS pds_bytes_total
    FROM vertex_kyber_billing_tenant t
    LEFT JOIN vertex_kyber_usage_meter u ON t.tenant_id = u.tenant_id
    GROUP BY t.tenant_id, t.org_did, t.plan_id, t.status, t.max_users, t.max_monthly_txns
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const mv of [
    "mv_kyber_tenant_usage_summary",
    "mv_kyber_monthly_usage",
  ]) {
    await sql`DROP MATERIALIZED VIEW IF EXISTS ${sql.raw(mv)}`.execute(db);
  }

  for (const t of [
    "vertex_kyber_stripe_report",
    "vertex_kyber_usage_meter",
    "vertex_kyber_billing_tenant",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
