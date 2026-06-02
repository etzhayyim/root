import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

export async function up(db: Kysely<unknown>): Promise<void> {
  const vertexId = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/saikin-horizontal-transfer-cycle-v1";
  const bpmnPath = "00-contracts/bpmn/com/etzhayyim/saikin/horizontal-transfer-cycle.bpmn";
  const xml = readFileSync(path.resolve(repoRoot, bpmnPath), "utf-8");
  const byteSize = Buffer.byteLength(xml, "utf-8");

  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${vertexId}`.execute(db);
  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    VALUES (
      ${vertexId}, 'did:web:bpmn.etzhayyim.com', 'saikin_horizontal_transfer_cycle', 5,
      ${xml}, CAST(${byteSize} AS integer),
      ${bpmnPath}, 'active', ${new Date().toISOString()},
      1, 'did:web:bpmn.etzhayyim.com', 'did:web:bpmn.etzhayyim.com', 'sys.bpmn.reseed.timer-retrigger'
    )
  `.execute(db);
}

export async function down(): Promise<void> {}
