import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * billing.gftd.ai — Stripe wiring + 適格請求書 PDF schema (ADR-2605080000
 * §D7 + Roadmap P7).  Builds on `billing-foundation-p1`.
 *
 * Adds:
 *   vertex_billing_stripe_customer    Stripe Customer mapping per org
 *   vertex_billing_stripe_event       inbound webhook event log (idempotent)
 *   ALTER vertex_billing_invoice
 *     + qualified_invoice_pdf_b2_key  B2 object key for the rendered 適格請求書 PDF
 *     + qualified_invoice_pdf_url     short-lived presigned URL (regenerated on read)
 *     + stripe_invoice_id (already present on the row, no-op)
 *
 * Stripe webhook flow:
 *   POST https://atproto.gftd.ai/xrpc/ai.gftd.apps.billing.stripeWebhook
 *     headers: stripe-signature: ...
 *     body: full Stripe event JSON
 *   →  PDS verifies signature against vertex_billing_stripe_customer
 *      .stripe_webhook_secret
 *   →  bpmn-dispatcher → billing.stripe.handleEvent pyzeebe primitive
 *   →  INSERT vertex_billing_stripe_event (idempotent on stripe_event_id)
 *   →  branch on event.type:
 *        invoice.paid              → UPDATE vertex_billing_invoice SET status='paid', paid_at=…
 *        invoice.payment_failed    → UPDATE … SET status='overdue'
 *        customer.subscription.*   → upsert vertex_billing_org_plan
 *        charge.refunded           → INSERT vertex_billing_credit (kind='refund')
 *
 * Issue invoice flow:
 *   billing_issue_invoice BPMN (cron 0 0 5 1 * ?)
 *   →  SELECT vertex_billing_invoice WHERE status='draft' AND issued_at IS NULL
 *   →  for each row:
 *        1. billing.invoice.renderPdf  → 適格請求書 (T9007028460042) HTML → PDF
 *        2. yata.storage.put           → B2 archive bucket (per-org private)
 *        3. UPDATE vertex_billing_invoice SET qualified_invoice_pdf_b2_key=…,
 *                                            status='issued', issued_at=now
 *        4. (optional, future) Stripe.invoices.create + .send
 *        5. generic.audit.emit         OCEL trail
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_billing_stripe_customer (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      org_did varchar NOT NULL,
      stripe_customer_id varchar NOT NULL,
      stripe_account_id varchar NOT NULL,
      stripe_webhook_secret varchar,
      email varchar,
      tax_id varchar,
      currency varchar NOT NULL,
      default_payment_method varchar,
      created_at varchar NOT NULL,
      status varchar NOT NULL,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_billing_stripe_customer_org    ON vertex_billing_stripe_customer (org_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_billing_stripe_customer_stripe ON vertex_billing_stripe_customer (stripe_customer_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_billing_stripe_event (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      stripe_event_id varchar NOT NULL,
      stripe_event_type varchar NOT NULL,
      stripe_account_id varchar NOT NULL,
      org_did varchar,
      ref_invoice_id varchar,
      ref_subscription_id varchar,
      received_at varchar NOT NULL,
      processed_at varchar,
      status varchar NOT NULL,
      raw_event_json varchar,
      error varchar,
      created_at varchar NOT NULL,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_billing_stripe_event_id     ON vertex_billing_stripe_event (stripe_event_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_billing_stripe_event_org    ON vertex_billing_stripe_event (org_did, received_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_billing_stripe_event_status ON vertex_billing_stripe_event (status, received_at)`.execute(db);

  // Add 適格請求書 PDF columns to existing vertex_billing_invoice.
  await sql`ALTER TABLE vertex_billing_invoice ADD COLUMN IF NOT EXISTS qualified_invoice_pdf_b2_key VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_billing_invoice ADD COLUMN IF NOT EXISTS qualified_invoice_pdf_sha256 VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_billing_invoice ADD COLUMN IF NOT EXISTS rendered_at VARCHAR`.execute(db);

  // Streaming MV for unprocessed Stripe events (drives an alert pipeline).
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_billing_stripe_event_pending AS
      SELECT stripe_event_type, stripe_account_id, COUNT(*) AS n,
             MAX(received_at) AS latest_received_at
      FROM vertex_billing_stripe_event
      WHERE status = 'pending' OR status = 'failed'
      GROUP BY stripe_event_type, stripe_account_id;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_billing_stripe_event_pending`.execute(db);
  await sql`ALTER TABLE vertex_billing_invoice DROP COLUMN IF EXISTS rendered_at`.execute(db);
  await sql`ALTER TABLE vertex_billing_invoice DROP COLUMN IF EXISTS qualified_invoice_pdf_sha256`.execute(db);
  await sql`ALTER TABLE vertex_billing_invoice DROP COLUMN IF EXISTS qualified_invoice_pdf_b2_key`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_billing_stripe_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_billing_stripe_customer`.execute(db);
}
