import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def for aidesk Phase 1 BPMNs.
// F5 watcher deploys each to Zeebe within 30s of INSERT (ADR-0056).
// Both are message-triggered (not timer-start).

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readBpmn = (file: string) =>
  readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/aidesk", file),
    "utf8",
  );

const CREATED_AT = "2026-05-06T13:00:00Z";
const OWNER_DID = "did:web:bpmn.gftd.ai";
const ACTOR_TAG = "sys.bpmn.seed.aidesk";

const ENTRIES = [
  {
    vertexId:
      "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/aidesk-synthesize-cad-from-image-v1",
    bpmnProcessId: "aidesk_synthesize_cad_from_image",
    sourcePath: "00-contracts/bpmn/ai/gftd/aidesk/synthesizeCadFromImage.bpmn",
    file: "synthesizeCadFromImage.bpmn",
  },
  {
    vertexId:
      "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/aidesk-export-to-tsukuru-v1",
    bpmnProcessId: "aidesk_export_to_tsukuru",
    sourcePath: "00-contracts/bpmn/ai/gftd/aidesk/exportToTsukuru.bpmn",
    file: "exportToTsukuru.bpmn",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const e of ENTRIES) {
    const xml = readBpmn(e.file);
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def
        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT ${e.vertexId}, ${OWNER_DID}, ${e.bpmnProcessId}, 1, ${xml},
             CAST(${size} AS integer), ${e.sourcePath}, 'active', ${CREATED_AT},
             1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${e.vertexId}
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
