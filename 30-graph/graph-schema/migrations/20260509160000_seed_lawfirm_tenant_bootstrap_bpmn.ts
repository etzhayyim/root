import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const SEED_CREATED_AT = "2026-05-08T00:00:00Z";
const SEED_OWNER_DID = "did:web:lawfirm.etzhayyim.com";
const SEED_ACTOR_TAG = "sys.bpmn.seed.lawfirm";

const PROCESS = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/lawfirm-tenant-bootstrap-v1",
  bpmnProcessId: "lawfirm_tenant_bootstrap",
  sourcePath: "00-contracts/bpmn/com/etzhayyim/lawfirm/tenantBootstrap.bpmn",
};

const BINDING = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/lawfirm-tenant-bootstrap-xrpc-v1",
  nsid: "com.etzhayyim.apps.lawfirm.tenantBootstrap",
  bpmnProcessId: "lawfirm_tenant_bootstrap",
  resultTimeoutMs: 30_000,
};

/**
 * Seed: tenantBootstrap BPMN process_def + lexicon binding.
 *
 * Closes the lexicon → BPMN → primitive chain:
 *   com.etzhayyim.apps.lawfirm.tenantBootstrap (lexicon)
 *     → vertex_bpmn_lexicon_binding (this seed)
 *       → vertex_bpmn_process_def: lawfirm_tenant_bootstrap (this seed)
 *         → BPMN serviceTask type: lawfirm.tenant.bootstrap
 *           → pyzeebe primitive task_lawfirm_tenant_bootstrap (lawfirm_tenant.py)
 *             → vertex_lawfirm_tenant + tenant_event + edge_tenant_lead
 *
 * F5 watcher auto-deploys process_def to BPMN engine on insert.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(PROCESS.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord,
       org_id, user_id, actor_id)
    SELECT
      ${PROCESS.vertexId}, ${SEED_OWNER_DID}, ${PROCESS.bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${PROCESS.sourcePath}, 'active',
      ${SEED_CREATED_AT}, 1, ${SEED_OWNER_DID}, ${SEED_OWNER_DID}, ${SEED_ACTOR_TAG}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS.vertexId})
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
       result_timeout_ms, status, created_at, sensitivity_ord,
       org_id, user_id, actor_id)
    SELECT
      ${BINDING.vertexId}, ${SEED_OWNER_DID}, ${BINDING.nsid}, ${BINDING.bpmnProcessId}, 1,
      CAST(${BINDING.resultTimeoutMs} AS integer), 'active',
      ${SEED_CREATED_AT}, 1, ${SEED_OWNER_DID}, ${SEED_OWNER_DID}, ${SEED_ACTOR_TAG}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING.vertexId})
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING.vertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS.vertexId}`.execute(db);
}
