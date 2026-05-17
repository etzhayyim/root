import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const seedCreatedAt = "2026-05-08T00:00:00Z";
const seedOwnerDid = "did:web:lawfirm.etzhayyim.com";
const seedActorTag = "sys.bpmn.seed.lawfirm";

const PROCESSES = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/lawfirm-payment-intake-v1",
    bpmnProcessId: "lawfirm_payment_intake",
    sourcePath: "00-contracts/bpmn/ai/gftd/lawfirm/paymentIntake.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/lawfirm-marketing-tick-v1",
    bpmnProcessId: "lawfirm_marketing_tick",
    sourcePath: "00-contracts/bpmn/ai/gftd/lawfirm/marketingTick.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/lawfirm-marketing-ad-hoc-v1",
    bpmnProcessId: "lawfirm_marketing_ad_hoc",
    sourcePath: "00-contracts/bpmn/ai/gftd/lawfirm/marketingAdHoc.bpmn",
  },
];
const BINDINGS = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/lawfirm-stripe-webhook-v1",
    nsid: "ai.gftd.apps.lawfirm.stripeWebhook",
    bpmnProcessId: "lawfirm_payment_intake",
    resultTimeoutMs: 60_000,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/lawfirm-marketing-ad-hoc-xrpc-v1",
    nsid: "ai.gftd.apps.lawfirm.marketingDispatch",
    bpmnProcessId: "lawfirm_marketing_ad_hoc",
    resultTimeoutMs: 180_000,
  },
];

/**
 * lawfirm.etzhayyim.com payment + marketing schema (Day-0 individual practice).
 *
 * Tables:
 *   vertex_lawfirm_invoice         Stripe invoice mirror (matter-linked)
 *   vertex_lawfirm_payment         Stripe charge mirror (paid_at + amount)
 *   vertex_lawfirm_marketing_asset Drafted marketing asset (blog/post/mail/etc)
 *   vertex_lawfirm_marketing_run   Marketing graph run log (LangGraph trace)
 *
 * Streaming MVs:
 *   mv_lawfirm_revenue_monthly        ARR per month per stream
 *   mv_lawfirm_outstanding_invoices   Unpaid > 30 days
 *   mv_lawfirm_marketing_publish_calendar  Scheduled vs published assets
 *
 * BCI Rule 36 compliance: marketing_asset.compliance_check + brand axis
 * (advocate vs platform); advocate-brand assets MUST pass compliance gate.
 *
 * ADR-0036 Hyperdrive direct.
 * ADR-2605080600 LangGraph Server L3 Runtime.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Stripe invoice mirror ───────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_invoice (
      vertex_id          varchar PRIMARY KEY,
      stripe_invoice_id  varchar NOT NULL,
      matter_uri         varchar,
      client_did         varchar,
      stream             varchar,
      amount_minor       bigint,
      currency           varchar DEFAULT 'USD',
      tax_minor          bigint DEFAULT 0,
      total_minor        bigint,
      status             varchar DEFAULT 'open',
      due_date           varchar,
      issued_at          varchar,
      paid_at            varchar,
      hosted_invoice_url varchar,
      raw_json           varchar,
      created_at         varchar,
      sensitivity_ord    int DEFAULT 200,
      owner_did          varchar)
  `.execute(db);

  // ── Stripe payment mirror ───────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_payment (
      vertex_id          varchar PRIMARY KEY,
      stripe_charge_id   varchar NOT NULL,
      stripe_invoice_id  varchar,
      matter_uri         varchar,
      client_did         varchar,
      stream             varchar,
      amount_minor       bigint,
      currency           varchar DEFAULT 'USD',
      paid_at            varchar,
      receipt_url        varchar,
      payment_method     varchar,
      raw_json           varchar,
      created_at         varchar,
      sensitivity_ord    int DEFAULT 200,
      owner_did          varchar)
  `.execute(db);

  // ── Marketing asset (blog/post/mail/event) ──────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_marketing_asset (
      vertex_id          varchar PRIMARY KEY,
      asset_kind         varchar NOT NULL,
      brand              varchar NOT NULL,
      audience           varchar,
      title              varchar,
      body_md            varchar,
      target_url         varchar,
      compliance_check   varchar DEFAULT 'pending',
      compliance_notes   varchar,
      compliance_score   double precision,
      reviewer_did       varchar,
      scheduled_at       varchar,
      published_at       varchar,
      published_url      varchar,
      llm_model          varchar,
      created_at         varchar,
      sensitivity_ord    int DEFAULT 100,
      owner_did          varchar)
  `.execute(db);

  // ── Marketing graph run log ─────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_marketing_run (
      vertex_id        varchar PRIMARY KEY,
      run_id           varchar NOT NULL,
      task_type        varchar NOT NULL,
      brand            varchar,
      requester_did    varchar,
      result_summary   varchar,
      asset_count      int DEFAULT 0,
      ok               boolean,
      error            varchar,
      started_at       varchar,
      finished_at      varchar,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 100,
      owner_did        varchar)
  `.execute(db);

  // ── Streaming MVs ───────────────────────────────────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lawfirm_revenue_monthly AS
    SELECT
      SUBSTRING(paid_at, 1, 7) AS month,
      currency,
      COALESCE(stream, 'unknown') AS stream,
      SUM(amount_minor) AS amount_minor_total,
      COUNT(*)          AS payment_count
    FROM vertex_lawfirm_payment
    WHERE paid_at IS NOT NULL
    GROUP BY SUBSTRING(paid_at, 1, 7), currency, COALESCE(stream, 'unknown')
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lawfirm_outstanding_invoices AS
    SELECT
      stripe_invoice_id,
      matter_uri,
      client_did,
      currency,
      total_minor,
      due_date,
      issued_at,
      hosted_invoice_url
    FROM vertex_lawfirm_invoice
    WHERE status = 'open'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lawfirm_marketing_publish_calendar AS
    SELECT
      asset_kind,
      brand,
      compliance_check,
      scheduled_at,
      published_at,
      title,
      target_url,
      published_url
    FROM vertex_lawfirm_marketing_asset
    WHERE compliance_check IN ('approved', 'pending')
  `.execute(db);

  // ── BPMN seeds (canonical schema) ──────────────────────────────────────────
  for (const p of PROCESSES) {
    const xml = readContract(p.sourcePath);
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT ${p.vertexId}, ${seedOwnerDid}, ${p.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${p.sourcePath}, 'active', ${seedCreatedAt}, 1, ${seedOwnerDid}, ${seedOwnerDid}, ${seedActorTag}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${p.vertexId})
    `.execute(db);
  }

  for (const b of BINDINGS) {
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT ${b.vertexId}, ${seedOwnerDid}, ${b.nsid}, ${b.bpmnProcessId}, 1, CAST(${b.resultTimeoutMs} AS integer), 'active', ${seedCreatedAt}, 1, ${seedOwnerDid}, ${seedOwnerDid}, ${seedActorTag}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${b.vertexId})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const b of BINDINGS)
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${b.vertexId}`.execute(db);
  for (const p of PROCESSES)
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${p.vertexId}`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_marketing_publish_calendar`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_outstanding_invoices`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_revenue_monthly`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_marketing_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_marketing_asset`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_payment`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_invoice`.execute(db);
}
