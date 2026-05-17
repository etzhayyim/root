/**
 * Fix ki + saikin BPMNs: BPMN 2.0 XSD requires <outgoing> BEFORE
 * <timerEventDefinition> inside a <startEvent>.  Zeebe 8.5 validates
 * XSD ordering strictly and rejects with INVALID_ARGUMENT when the
 * order is reversed.
 *
 * Both ki and saikin had:
 *   <bpmn:timerEventDefinition>…</bpmn:timerEventDefinition>
 *   <bpmn:outgoing>Flow_S</bpmn:outgoing>
 *
 * Correct order (matching shinshi/seedGapFill.bpmn pattern):
 *   <bpmn:outgoing>Flow_S</bpmn:outgoing>
 *   <bpmn:timerEventDefinition>…</bpmn:timerEventDefinition>
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const CREATED_AT = "2026-05-08T10:30:00Z";
const ACTOR_TAG = "sys.bpmn.reseed.outgoing-order-fix";

const ENTRIES = [
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/ki-vascular-synthesis-cycle-v1",
    processId: "ki_vascular_synthesis_cycle",
    bpmnPath: "00-contracts/bpmn/ai/gftd/ki/vascular-synthesis-cycle.bpmn",
  },
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/saikin-horizontal-transfer-cycle-v1",
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
        ${e.vertexId}, ${OWNER_DID}, ${e.processId}, 4,
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
