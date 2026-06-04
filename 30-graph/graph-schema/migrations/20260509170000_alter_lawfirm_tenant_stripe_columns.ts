import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ALTER vertex_lawfirm_tenant ADD Stripe billing columns + add
 * vertex_lawfirm_payment companion if missing + mv_lawfirm_billing_reconciliation.
 *
 * Backs the W11-W12 conversion path defined in
 * `_working/etzhayyim-revenue/stripe-connect-onboarding-runbook.md`:
 *   stripe_customer_id          — Mode A flat tier (firm = direct customer)
 *   stripe_connect_account_id   — Mode B rev-share (firm = Express connected account)
 *   billing_mode                — flat | rev_share_y1 | rev_share_y2 | rev_share_y3 | free
 *   platform_fee_pct            — etzhayyim retention % (85 Y1 / 90 Y2 / 95 Y3 / 100 flat)
 *
 * Reconciliation MV runs daily (CEO dashboard); rate-limit check via
 * downstream cron `lawfirm.billing.alertStaleTenant`.
 *
 * ADR-0036 Hyperdrive direct.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // RW does not honor "ADD COLUMN IF NOT EXISTS"; check first.
  const addCol = async (table: string, name: string, type: string) => {
    const existing = await sql<{ column_name: string }>`
      SELECT column_name FROM information_schema.columns WHERE table_name = ${table}
    `.execute(db);
    const have = new Set(existing.rows.map((r: any) => r.column_name));
    if (!have.has(name)) {
      await sql.raw(`ALTER TABLE ${table} ADD COLUMN ${name} ${type}`).execute(db);
    }
  };

  // ── ALTER vertex_lawfirm_tenant — Stripe billing columns ─────────────────────
  await addCol('vertex_lawfirm_tenant', 'stripe_customer_id', 'varchar');
  await addCol('vertex_lawfirm_tenant', 'stripe_connect_account_id', 'varchar');
  await addCol('vertex_lawfirm_tenant', 'billing_mode', "varchar DEFAULT 'flat'");
  await addCol('vertex_lawfirm_tenant', 'platform_fee_pct', 'int DEFAULT 0');

  // ── ALTER vertex_lawfirm_payment — link back to tenant ──────────────────────
  await addCol('vertex_lawfirm_payment', 'stripe_payment_intent_id', 'varchar');
  await addCol('vertex_lawfirm_payment', 'stripe_charge_id', 'varchar');
  await addCol('vertex_lawfirm_payment', 'platform_fee_minor', 'bigint DEFAULT 0');
  await addCol('vertex_lawfirm_payment', 'currency', "varchar DEFAULT 'usd'");

  // ── ALTER vertex_lawfirm_invoice — Stripe invoice id link ───────────────────
  await addCol('vertex_lawfirm_invoice', 'stripe_invoice_id', 'varchar');
  await addCol('vertex_lawfirm_invoice', 'stripe_subscription_id', 'varchar');
  await addCol('vertex_lawfirm_invoice', 'currency', "varchar DEFAULT 'usd'");

  // ── Index for webhook reverse lookups (Stripe event -> tenant) ──────────────
  await sql`CREATE INDEX IF NOT EXISTS idx_lawfirm_tenant_stripe_customer
              ON vertex_lawfirm_tenant (stripe_customer_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_lawfirm_tenant_stripe_connect
              ON vertex_lawfirm_tenant (stripe_connect_account_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_lawfirm_payment_stripe_pi
              ON vertex_lawfirm_payment (stripe_payment_intent_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_lawfirm_invoice_stripe_invoice
              ON vertex_lawfirm_invoice (stripe_invoice_id)`.execute(db);

  // ── Reconciliation MV — daily payment health per tenant ─────────────────────
  // Plain VIEW (not MV) because amount_minor windowed by now() — RW MV restriction.
  await sql`
    CREATE VIEW IF NOT EXISTS view_lawfirm_billing_reconciliation AS
    SELECT
      t.tenant_id,
      t.slug,
      t.tier,
      t.billing_mode,
      t.platform_fee_pct,
      t.stripe_customer_id,
      t.stripe_connect_account_id,
      COUNT(p.vertex_id) FILTER (
        WHERE CAST(p.paid_at AS timestamptz) > now() - INTERVAL '30 days'
      ) AS payments_30d,
      COALESCE(SUM(p.amount_minor) FILTER (
        WHERE CAST(p.paid_at AS timestamptz) > now() - INTERVAL '30 days'
      ), 0) AS gross_minor_30d,
      COALESCE(SUM(p.platform_fee_minor) FILTER (
        WHERE CAST(p.paid_at AS timestamptz) > now() - INTERVAL '30 days'
      ), 0) AS platform_fee_minor_30d,
      MAX(p.paid_at) AS last_paid_at
    FROM vertex_lawfirm_tenant t
    LEFT JOIN vertex_lawfirm_payment p ON p.tenant_id = t.tenant_id
    WHERE t.status IN ('active', 'promoted', 'pending_kickoff')
    GROUP BY
      t.tenant_id, t.slug, t.tier, t.billing_mode, t.platform_fee_pct,
      t.stripe_customer_id, t.stripe_connect_account_id
  `.execute(db);

  // ── Stale-billing detection MV (active tenants with no payment in 35d) ──────
  await sql`
    CREATE VIEW IF NOT EXISTS view_lawfirm_billing_stale AS
    SELECT tenant_id, slug, tier, billing_mode, last_paid_at,
           CAST(now() - CAST(last_paid_at AS timestamptz) AS varchar) AS days_since_last
    FROM view_lawfirm_billing_reconciliation
    WHERE billing_mode != 'free'
      AND tier = 'saas-prod'
      AND (last_paid_at IS NULL
           OR CAST(last_paid_at AS timestamptz) < now() - INTERVAL '35 days')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_lawfirm_billing_stale`.execute(db);
  await sql`DROP VIEW IF EXISTS view_lawfirm_billing_reconciliation`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_lawfirm_invoice_stripe_invoice`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_lawfirm_payment_stripe_pi`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_lawfirm_tenant_stripe_connect`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_lawfirm_tenant_stripe_customer`.execute(db);

  await sql`ALTER TABLE vertex_lawfirm_invoice DROP COLUMN currency`.execute(db);
  await sql`ALTER TABLE vertex_lawfirm_invoice DROP COLUMN stripe_subscription_id`.execute(db);
  await sql`ALTER TABLE vertex_lawfirm_invoice DROP COLUMN stripe_invoice_id`.execute(db);

  await sql`ALTER TABLE vertex_lawfirm_payment DROP COLUMN currency`.execute(db);
  await sql`ALTER TABLE vertex_lawfirm_payment DROP COLUMN platform_fee_minor`.execute(db);
  await sql`ALTER TABLE vertex_lawfirm_payment DROP COLUMN stripe_charge_id`.execute(db);
  await sql`ALTER TABLE vertex_lawfirm_payment DROP COLUMN stripe_payment_intent_id`.execute(db);

  await sql`ALTER TABLE vertex_lawfirm_tenant DROP COLUMN platform_fee_pct`.execute(db);
  await sql`ALTER TABLE vertex_lawfirm_tenant DROP COLUMN billing_mode`.execute(db);
  await sql`ALTER TABLE vertex_lawfirm_tenant DROP COLUMN stripe_connect_account_id`.execute(db);
  await sql`ALTER TABLE vertex_lawfirm_tenant DROP COLUMN stripe_customer_id`.execute(db);
}
