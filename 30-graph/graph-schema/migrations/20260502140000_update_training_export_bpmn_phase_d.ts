import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Phase D: update trainingExport.bpmn to add training.push.huggingface step
// after the audit task. F5 watcher picks up the xml change and redeploys
// to Zeebe within 30s.
//
// Applied via: psql (ADR-2604241342 out-of-band pattern)

const __filename  = fileURLToPath(import.meta.url);
const __dirname   = path.dirname(__filename);
const repoRoot    = path.resolve(__dirname, "..", "..", "..");

const BPMN_PATH   = "00-contracts/bpmn/ai/gftd/training/trainingExport.bpmn";
const PROCESS_VID = "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/training-export-v1";
const updatedAt   = "2026-05-02T14:00:00+09:00";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml  = readFileSync(path.resolve(repoRoot, BPMN_PATH), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml"         = ${xml},
        xml_byte_size = CAST(${size} AS integer),
        source_path   = ${BPMN_PATH}
    WHERE vertex_id   = ${PROCESS_VID}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // No rollback — the prior XML is in git history.
  // To revert: run this migration pointing at the v1 BPMN file via psql.
}
