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

const PROCESS = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/lawfirm-pwc-clearance-v1",
  bpmnProcessId: "lawfirm_pwc_clearance",
  sourcePath: "00-contracts/bpmn/ai/gftd/lawfirm/pwcClearance.bpmn",
};
const BINDING = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/lawfirm-pwc-clearance-xrpc-v1",
  nsid: "app.etzhayyim.apps.lawfirm.pwcClearanceRequest",
  bpmnProcessId: "lawfirm_pwc_clearance",
  resultTimeoutMs: 86_400_000,
};

/**
 * lawfirm.etzhayyim.com PwC conflict clearance audit table.
 *
 * CEO decision D4 (2026-05-08): conflict screening uses formal PwC India
 * compliance escalation per matter (NOT auto-screen via hash list). This
 * table captures the request/response trail for audit + retrospective.
 *
 * Workflow:
 *   matter intake → CEO requests PwC clearance → PwC India compliance
 *   responds (no_conflict / conflict / need_more_info) → matter unlocked
 *   or declined → audit row persisted here.
 *
 * Tier 2 sensitivity (CEO/COO/CLO read; PwC names + matter subject are
 * sensitive but not personal data per DPDP, sensitivity_ord=200).
 *
 * ADR-0036 Hyperdrive direct.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_pwc_clearance (
      vertex_id          varchar PRIMARY KEY,
      matter_uri         varchar NOT NULL,
      client_name        varchar NOT NULL,
      matter_summary     varchar,
      requested_at       varchar,
      requested_by_did   varchar,
      pwc_contact        varchar,
      pwc_response       varchar,
      pwc_response_text  varchar,
      responded_at       varchar,
      clearance_status   varchar DEFAULT 'pending',
      sla_deadline       varchar,
      escalated          boolean DEFAULT false,
      created_at         varchar,
      sensitivity_ord    int DEFAULT 200,
      owner_did          varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lawfirm_pwc_clearance_pending AS
    SELECT vertex_id, matter_uri, client_name, requested_at, sla_deadline, escalated
    FROM vertex_lawfirm_pwc_clearance
    WHERE clearance_status = 'pending'
  `.execute(db);

  const xml = readContract(PROCESS.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${PROCESS.vertexId}, ${seedOwnerDid}, ${PROCESS.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${PROCESS.sourcePath}, 'active', ${seedCreatedAt}, 1, ${seedOwnerDid}, ${seedOwnerDid}, ${seedActorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS.vertexId})
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${BINDING.vertexId}, ${seedOwnerDid}, ${BINDING.nsid}, ${BINDING.bpmnProcessId}, 1, CAST(${BINDING.resultTimeoutMs} AS integer), 'active', ${seedCreatedAt}, 1, ${seedOwnerDid}, ${seedOwnerDid}, ${seedActorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING.vertexId})
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING.vertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS.vertexId}`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_pwc_clearance_pending`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_pwc_clearance`.execute(db);
}
