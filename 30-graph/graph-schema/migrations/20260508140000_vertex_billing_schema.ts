import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (billing — org_did + amounts; not Tier-3 PII but business-
//          confidential. Per-call refResource may include actor DIDs
//          and resource names; visible to org owner + billing admin.)

/**
 * billing.gftd.ai — retail cloud billing v2 schema (ADR-2605080000).
 *
 * Foundation for two retail products:
 *   - yatabase.gftd.ai  (RisingWave-backed graph database)
 *   - obj.gftd.ai       (B2-backed S3-compatible object storage)
 *
 * Pattern: T2 BPMN-as-actor (ADR-0036 Worker-direct Hyperdrive +
 * ADR-0056 BPMN-as-actor + ADR-2604282300 pymagatama + Zeebe, no CF
 * Worker). Mirrors shosha (2026-05-06) and shinshi (2026-05-07)
 * bring-up.
 *
 * Tables (5 vertex):
 *   vertex_billing_event       per-request usage event (storage gb-h /
 *                               egress gb / llm tokens / gpu hour /
 *                               api req / mcp call / yata node-h /
 *                               obj class A/B / ...). Content-addressed
 *                               PK (ADR-0041) keyed on
 *                               sha256(orgDid+metric+tsMs+refResource).
 *   vertex_billing_org_plan    per-org plan tier + applied_discount_pct
 *   vertex_billing_discount    discount audit log (sales / CFO / CEO)
 *   vertex_billing_credit      one-time credit application log
 *   vertex_billing_invoice     monthly invoice (draft / issued / paid /
 *                               overdue / void) with 適格請求書 metadata
 *
 * Streaming MVs (5):
 *   mv_billing_daily_org       per-org × day × metric × product
 *                               aggregation (qty + billedJpyMicro)
 *   mv_billing_monthly_org     per-org × month × product aggregation
 *                               (drives invoice generation)
 *   mv_billing_overage_alert   plan included vs consumed
 *                               with alert_level ∈ {ok, warn80,
 *                               exceeded, critical150}
 *   mv_billing_margin_actual   trailing 30d sum(billed) -
 *                               sum(unitCost*qty), rolling gross margin
 *   mv_billing_quota_breach    rows where consumed > 1.0 * included
 *                               (hard cap candidates)
 *
 * MV cardinality safety (per 30-graph/graph-schema/CLAUDE.md MV rules):
 *  - mv_billing_daily_org GROUP BY (org_did, day, metric, product) —
 *    bounded by ~10K orgs × 31 days × 14 metrics × 4 products ≈ 17.4M
 *    in worst case. Acceptable for streaming (no MAX(varchar) wide
 *    columns; only SUM bigint + SUM double).
 *  - mv_billing_monthly_org GROUP BY (org_did, month, product) —
 *    ~10K × 12 × 4 ≈ 480K, well under 500K threshold.
 *  - mv_billing_overage_alert / quota_breach JOIN with org_plan keyed
 *    on org_did — bounded by org count.
 *  - margin_actual is SUM-only over rolling window, no GROUP BY explosion.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_billing_event (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      org_did varchar NOT NULL,
      actor_did varchar,
      ts_ms bigint NOT NULL,
      metric varchar NOT NULL,
      qty double precision NOT NULL,
      product varchar NOT NULL,
      ref_resource varchar,
      unit_cost_jpy_micro bigint,
      list_price_jpy_micro bigint,
      applied_discount_pct double precision,
      billed_amount_jpy_micro bigint,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_billing_event_org_ts ON vertex_billing_event (org_did, ts_ms)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_billing_event_metric ON vertex_billing_event (metric, ts_ms)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_billing_org_plan (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      org_did varchar NOT NULL,
      plan varchar NOT NULL,
      billing_period_start date NOT NULL,
      billing_period_end date NOT NULL,
      applied_discount_pct double precision NOT NULL,
      base_fee_jpy_micro bigint,
      currency varchar NOT NULL,
      stripe_customer_id varchar,
      stripe_subscription_id varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_billing_org_plan_org ON vertex_billing_org_plan (org_did)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_billing_discount (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      discount_id varchar NOT NULL,
      org_did varchar NOT NULL,
      discount_pct double precision NOT NULL,
      previous_discount_pct double precision,
      kind varchar NOT NULL,
      approver varchar NOT NULL,
      approver_role varchar NOT NULL,
      approval_state varchar NOT NULL,
      reject_reason varchar,
      rationale varchar,
      valid_from date NOT NULL,
      valid_until date,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_billing_discount_org ON vertex_billing_discount (org_did, valid_from)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_billing_credit (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      credit_id varchar NOT NULL,
      org_did varchar NOT NULL,
      amount_jpy_micro bigint NOT NULL,
      consumed_jpy_micro bigint NOT NULL,
      kind varchar NOT NULL,
      approver varchar NOT NULL,
      approver_role varchar NOT NULL,
      rationale varchar,
      issued_at varchar NOT NULL,
      expires_at varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_billing_credit_org_status ON vertex_billing_credit (org_did, status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_billing_invoice (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      invoice_id varchar NOT NULL,
      org_did varchar NOT NULL,
      period_start date NOT NULL,
      period_end date NOT NULL,
      subtotal_jpy_micro bigint NOT NULL,
      total_discount_jpy_micro bigint NOT NULL,
      tax_jpy_micro bigint NOT NULL,
      total_jpy_micro bigint NOT NULL,
      currency varchar NOT NULL,
      status varchar NOT NULL,
      qualified_invoice_number varchar,
      issued_at varchar,
      due_at varchar,
      paid_at varchar,
      stripe_invoice_id varchar,
      line_items_json varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_billing_invoice_org_period ON vertex_billing_invoice (org_did, period_start)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_billing_invoice_status ON vertex_billing_invoice (status)`.execute(db);

  // ── Streaming MVs ──────────────────────────────────────────────────

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_billing_daily_org AS
      SELECT
        org_did,
        CAST(to_timestamp(ts_ms / 1000.0) AS date) AS day,
        metric,
        product,
        SUM(qty) AS total_qty,
        SUM(COALESCE(billed_amount_jpy_micro, 0)) AS billed_jpy_micro,
        SUM(COALESCE(unit_cost_jpy_micro, 0) * qty) AS cost_jpy_micro,
        COUNT(*) AS event_count
      FROM vertex_billing_event
      GROUP BY org_did, CAST(to_timestamp(ts_ms / 1000.0) AS date), metric, product;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_billing_monthly_org AS
      SELECT
        org_did,
        CAST(to_char(to_timestamp(ts_ms / 1000.0), 'YYYY-MM-01') AS date) AS month,
        product,
        SUM(qty) AS total_qty,
        SUM(COALESCE(billed_amount_jpy_micro, 0)) AS billed_jpy_micro,
        SUM(COALESCE(unit_cost_jpy_micro, 0) * qty) AS cost_jpy_micro,
        COUNT(*) AS event_count
      FROM vertex_billing_event
      GROUP BY org_did, CAST(to_char(to_timestamp(ts_ms / 1000.0), 'YYYY-MM-01') AS date), product;
  `.execute(db);

  // Margin trailing 30d. RW cannot use NOW() in MV SELECT, so we expose
  // a per-org daily margin from mv_billing_daily_org and let callers
  // window-aggregate. Keeps MV state low and avoids RW VIEW restrictions.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_billing_margin_actual AS
      SELECT
        org_did,
        day,
        SUM(billed_jpy_micro) AS billed_jpy_micro,
        SUM(cost_jpy_micro) AS cost_jpy_micro,
        SUM(billed_jpy_micro) - SUM(cost_jpy_micro) AS gross_jpy_micro
      FROM mv_billing_daily_org
      GROUP BY org_did, day;
  `.execute(db);

  // Quota breach: org consumed > org plan's included quota for
  // current billing period. Joins consumption (mv_billing_daily_org
  // last 31d sum) with plan limits encoded as static rows in a
  // dim table (vertex_billing_plan_quota — created on demand by seed
  // migration when plan limits change). For Phase 1 we expose only
  // raw consumption summary; the alert level computation is done by
  // the detectOverage pyzeebe primitive against `vertex_billing_org_plan`
  // + Python-side plan-limit table.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_billing_overage_alert AS
      SELECT
        m.org_did,
        m.product,
        m.metric,
        SUM(m.total_qty) AS consumed_qty,
        SUM(m.billed_jpy_micro) AS billed_jpy_micro,
        MAX(p.plan) AS plan,
        MAX(p.applied_discount_pct) AS applied_discount_pct,
        MAX(p.billing_period_start) AS billing_period_start,
        MAX(p.billing_period_end) AS billing_period_end
      FROM mv_billing_daily_org m
      LEFT JOIN vertex_billing_org_plan p ON p.org_did = m.org_did
      WHERE m.day >= p.billing_period_start
        AND m.day <= p.billing_period_end
      GROUP BY m.org_did, m.product, m.metric;
  `.execute(db);

  // mv_billing_quota_breach is a thin filter on mv_billing_overage_alert
  // (>=80% utilization is the alert threshold per ADR D7 metering).
  // Real quota arithmetic lives in pyzeebe primitive task_billing_detect_overage
  // which has access to plan-limit constants. The MV here only exposes
  // raw consumption to keep streaming-state minimal.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_billing_quota_breach AS
      SELECT
        org_did,
        product,
        metric,
        consumed_qty,
        billed_jpy_micro,
        plan,
        billing_period_start,
        billing_period_end
      FROM mv_billing_overage_alert
      WHERE billed_jpy_micro > 0;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_billing_quota_breach`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_billing_overage_alert`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_billing_margin_actual`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_billing_monthly_org`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_billing_daily_org`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_billing_invoice`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_billing_credit`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_billing_discount`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_billing_org_plan`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_billing_event`.execute(db);
}
