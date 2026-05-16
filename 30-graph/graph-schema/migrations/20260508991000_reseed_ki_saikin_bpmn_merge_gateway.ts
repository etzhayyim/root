/**
 * Fix ki + saikin BPMNs: Zeebe 8.5 rejects ServiceTasks with multiple
 * incoming sequence flows.  Add explicit exclusive merge gateways:
 *   ki:     GW_MergeToRing before Task_Ring  (merges Flow_AfterBloom + Flow_SkipBloom)
 *   saikin: GW_MergeToAudit before Task_Audit (merges Flow_AfterKi + Flow_AfterLyse)
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const OWNER_DID = "did:web:bpmn.gftd.ai";
const CREATED_AT = "2026-05-08T10:00:00Z";
const ACTOR_TAG = "sys.bpmn.reseed.merge-gateway-fix";

const ENTRIES = [
  {
    vertexId:
      "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/ki-vascular-synthesis-cycle-v1",
    processId: "ki_vascular_synthesis_cycle",
    bpmnPath: "00-contracts/bpmn/ai/gftd/ki/vascular-synthesis-cycle.bpmn",
  },
  {
    vertexId:
      "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/saikin-horizontal-transfer-cycle-v1",
    processId: "saikin_horizontal_transfer_cycle",
    bpmnPath: "00-contracts/bpmn/ai/gftd/saikin/horizontal-transfer-cycle.bpmn",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const e of ENTRIES) {
    const xml = readFileSync(path.resolve(repoRoot, e.bpmnPath), "utf-8");
    const byteSize = Buffer.byteLength(xml, "utf-8");

    await sql`
      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${e.vertexId}
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_process_def
        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      VALUES (
        ${e.vertexId}, ${OWNER_DID}, ${e.processId}, 3,
        ${xml}, CAST(${byteSize} AS integer),
        ${e.bpmnPath}, 'active', ${CREATED_AT},
        1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const e of ENTRIES) {
    await sql`
      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${e.vertexId}
    `.execute(db);
  }
}
