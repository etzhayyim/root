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
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/lawfirm-intake-funnel-v1",
    bpmnProcessId: "lawfirm_intake_funnel",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/lawfirm/intakeFunnel.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/lawfirm-matter-create-v1",
    bpmnProcessId: "lawfirm_matter_create",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/lawfirm/matterCreate.bpmn",
  },
];
const BINDINGS = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/lawfirm-intake-submit-xrpc-v1",
    nsid: "com.etzhayyim.apps.lawfirm.intakeSubmit",
    bpmnProcessId: "lawfirm_intake_funnel",
    resultTimeoutMs: 60_000,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/lawfirm-matter-create-xrpc-v1",
    nsid: "com.etzhayyim.apps.lawfirm.matterCreate",
    bpmnProcessId: "lawfirm_matter_create",
    resultTimeoutMs: 60_000,
  },
];

/**
 * lawfirm.etzhayyim.com matter + intake schema (CRITICAL — closes intake → matter
 * gap that smoke test + engagementClose BPMN reference).
 *
 * Tables:
 *   vertex_lawfirm_intake  Multilingual public intake form submissions
 *                          (field-encrypted on privileged content)
 *   vertex_lawfirm_matter  Advocate-accepted matter; the canonical record
 *                          referenced by engagementClose / pwcClearance /
 *                          esign / payment / outreach event flows
 *
 * Streaming MVs:
 *   mv_lawfirm_intake_pending      open intakes awaiting advocate triage
 *   mv_lawfirm_matter_active       active matters per tenant_id
 *   mv_lawfirm_intake_lang_dist    intake distribution by language
 *
 * BPMN:
 *   lawfirm_intake_funnel  XRPC com.etzhayyim.apps.lawfirm.intakeSubmit
 *
 * Tier 2 sensitivity (privileged content field-encrypted at app layer
 * with signal:v1 prefix; sensitivity_ord=200).
 *
 * ADR-0036 Hyperdrive direct.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_lawfirm_intake ──────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_intake (
      vertex_id            varchar PRIMARY KEY,
      intake_id            varchar NOT NULL,
      tenant_id            varchar DEFAULT 'production',
      submitted_at         varchar,
      lang                 varchar DEFAULT 'en',
      client_name_cipher   varchar,
      client_email         varchar,
      client_phone_cipher  varchar,
      client_country       varchar DEFAULT 'IN',
      matter_type_hint     varchar,
      jurisdiction_hint    varchar,
      cross_border_flag    boolean DEFAULT false,
      summary_cipher       varchar,
      consent_status       varchar DEFAULT 'pending',
      consent_ts           varchar,
      source_url           varchar,
      ip_country           varchar,
      assigned_to_did      varchar,
      status               varchar DEFAULT 'pending',
      promoted_matter_uri  varchar,
      created_at           varchar,
      sensitivity_ord      int DEFAULT 200,
      owner_did            varchar)
  `.execute(db);

  // ── vertex_lawfirm_matter ──────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_matter (
      vertex_id           varchar PRIMARY KEY,
      matter_id           varchar NOT NULL,
      tenant_id           varchar DEFAULT 'production',
      intake_uri          varchar,
      client_did          varchar,
      client_name_cipher  varchar,
      lead_advocate_did   varchar,
      co_counsel_dids     varchar,
      matter_type         varchar NOT NULL,
      jurisdiction        varchar,
      subject_cipher      varchar,
      fee_structure       varchar,
      fee_amount_minor    bigint,
      currency            varchar DEFAULT 'USD',
      pwc_clearance_uri   varchar,
      engagement_letter_envelope_id varchar,
      stripe_subscription_id varchar,
      status              varchar DEFAULT 'pending_pwc',
      opened_at           varchar,
      closed_at           varchar,
      bci_disclosure      varchar,
      raw_metadata_json   varchar,
      created_at          varchar,
      sensitivity_ord     int DEFAULT 200,
      owner_did           varchar)
  `.execute(db);

  // ── MVs ────────────────────────────────────────────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lawfirm_intake_pending AS
    SELECT
      intake_id, tenant_id, submitted_at, lang, matter_type_hint,
      jurisdiction_hint, cross_border_flag, client_email,
      assigned_to_did, source_url
    FROM vertex_lawfirm_intake
    WHERE status = 'pending'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lawfirm_matter_active AS
    SELECT
      tenant_id,
      COUNT(*) AS matter_count,
      COUNT(*) FILTER (WHERE status = 'active') AS active_count,
      COUNT(*) FILTER (WHERE status = 'pending_pwc') AS pending_pwc_count,
      COUNT(*) FILTER (WHERE status = 'declined_conflict') AS declined_count,
      COUNT(*) FILTER (WHERE status = 'closed') AS closed_count
    FROM vertex_lawfirm_matter
    GROUP BY tenant_id
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lawfirm_intake_lang_dist AS
    SELECT
      tenant_id, lang, COUNT(*) AS intake_count,
      COUNT(*) FILTER (WHERE cross_border_flag = true) AS cross_border_count
    FROM vertex_lawfirm_intake
    GROUP BY tenant_id, lang
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
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_intake_lang_dist`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_matter_active`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_intake_pending`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_matter`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_intake`.execute(db);
}
