import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * etzhayyim.etzhayyim.com Company Ops schema
 * Principal: etzhayyim. Vendor: etzhayyim Japan株式会社.
 *
 * Tables (5 domain event tables + 1 streaming MV):
 *   vertex_etzhayyim_hr_event          HR domain events
 *   vertex_etzhayyim_finance_event     Finance events
 *   vertex_etzhayyim_legal_event       Legal events
 *   vertex_etzhayyim_sales_event       Sales events
 *   vertex_etzhayyim_governance_event  Governance events
 *
 * Streaming MVs:
 *   mv_etzhayyim_omega_daily           daily Ω(t) trend
 *
 * BPMN process_def + lexicon_binding seeds use canonical schema
 * matching production vertex_bpmn_process_def + vertex_bpmn_lexicon_binding
 * (bpmn_process_id / xml / xml_byte_size / source_path / RLS columns).
 *
 * ADR-0036: Worker-direct Hyperdrive.
 * ADR-2605080600: LangGraph Server L3 Runtime (etzhayyim-company-ops graph).
 */

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T00:00:00Z";
const ownerDid = "did:web:etzhayyim.etzhayyim.com";
const actorTag = "sys.bpmn.seed.etzhayyim";

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; resultTimeoutMs: number };

const processSeeds: P[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/etzhayyim-governance-daily-check-v1",
    bpmnProcessId: "etzhayyim_governance_daily_check",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/etzhayyim/governanceDailyCheck.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/etzhayyim-company-ops-dispatch-v1",
    bpmnProcessId: "etzhayyim_company_ops_dispatch",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/etzhayyim/companyOpsDispatch.bpmn",
  },
];

const bindingSeeds: B[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-company-ops-dispatch-xrpc-v1",
    nsid: "com.etzhayyim.apps.etzhayyim.companyOpsDispatch",
    bpmnProcessId: "etzhayyim_company_ops_dispatch",
    resultTimeoutMs: 180_000,
  },
];

async function insertProcessDef(db: Kysely<unknown>, s: P): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: B): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1, CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_hr_event (
      vertex_id varchar PRIMARY KEY,
      task_type varchar NOT NULL,
      action varchar,
      summary varchar,
      employee_did varchar,
      department varchar,
      status varchar DEFAULT 'open',
      action_items_json varchar,
      llm_model varchar,
      created_at varchar,
      sensitivity_ord int DEFAULT 200,
      owner_did varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_finance_event (
      vertex_id varchar PRIMARY KEY,
      task_type varchar NOT NULL,
      action varchar,
      journal_debit varchar,
      journal_credit varchar,
      amount_jpy double precision,
      description varchar,
      summary varchar,
      status varchar DEFAULT 'open',
      action_items_json varchar,
      llm_model varchar,
      created_at varchar,
      sensitivity_ord int DEFAULT 200,
      owner_did varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_legal_event (
      vertex_id varchar PRIMARY KEY,
      task_type varchar NOT NULL,
      action varchar,
      risk_level varchar DEFAULT 'low',
      summary varchar,
      case_id varchar,
      status varchar DEFAULT 'open',
      action_items_json varchar,
      llm_model varchar,
      created_at varchar,
      sensitivity_ord int DEFAULT 300,
      owner_did varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_sales_event (
      vertex_id varchar PRIMARY KEY,
      task_type varchar NOT NULL,
      action varchar,
      customer_name varchar,
      pipeline_stage varchar,
      amount_jpy double precision,
      summary varchar,
      status varchar DEFAULT 'open',
      action_items_json varchar,
      llm_model varchar,
      created_at varchar,
      sensitivity_ord int DEFAULT 100,
      owner_did varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_governance_event (
      vertex_id varchar PRIMARY KEY,
      task_type varchar NOT NULL,
      omega_score double precision,
      floor_violated boolean DEFAULT false,
      decisions_json varchar,
      summary varchar,
      status varchar DEFAULT 'open',
      created_at varchar,
      sensitivity_ord int DEFAULT 100,
      owner_did varchar)
  `.execute(db);

  for (const s of processSeeds) await insertProcessDef(db, s);
  for (const s of bindingSeeds) await insertBinding(db, s);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_omega_daily AS
    SELECT
      SUBSTRING(created_at, 1, 10) AS day,
      AVG(omega_score)            AS avg_omega,
      MIN(omega_score)            AS min_omega,
      MAX(omega_score)            AS max_omega,
      COUNT(*)                    AS check_count,
      BOOL_OR(floor_violated)     AS any_floor_violated
    FROM vertex_etzhayyim_governance_event
    WHERE omega_score IS NOT NULL
    GROUP BY SUBSTRING(created_at, 1, 10)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_omega_daily`.execute(db);
  for (const s of bindingSeeds)
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId}`.execute(db);
  for (const s of processSeeds)
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_governance_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_sales_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_legal_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_finance_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_hr_event`.execute(db);
}
