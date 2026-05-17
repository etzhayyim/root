import type { Kysely } from "kysely";
import { sql } from "kysely";
import { readFileSync } from "fs";
import * as path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const CREATED_AT = "2026-04-29T23:35:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const ACTOR_TAG = "sys.bpmn.seed.kaisya";

function readBpmn(relativePath: string): string {
  return readFileSync(path.resolve(repoRoot, relativePath), "utf-8");
}

const PROCESS_DEFS = [
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/kaisya-master-routine-v1",
    bpmnProcessId: "kaisya_master_routine",
    sourcePath: "00-contracts/bpmn/ai/gftd/kaisya/masterRoutine.bpmn",
  },
] as const;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const def of PROCESS_DEFS) {
    const bpmnXml = readBpmn(def.sourcePath);
    const size = Buffer.byteLength(bpmnXml, "utf-8");

    await sql`
      INSERT INTO vertex_bpmn_process_def
        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT ${def.vertexId}, ${OWNER_DID}, ${def.bpmnProcessId}, 1, ${bpmnXml},
             CAST(${size} AS integer), ${def.sourcePath}, 'active', ${CREATED_AT},
             1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def
        WHERE vertex_id = ${def.vertexId}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const def of PROCESS_DEFS) {
    await sql`
      DELETE FROM vertex_bpmn_process_def
      WHERE vertex_id = ${def.vertexId}
    `.execute(db);
  }
}
