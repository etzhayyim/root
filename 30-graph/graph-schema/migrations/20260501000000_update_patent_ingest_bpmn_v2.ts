import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Re-seed ingestUsptoWeekly.bpmn v2:
//   - Remove Task_Manifest (S3 manifest.json returns HTTP 403)
//   - Hardcode g_patent.tsv.zip + g_us_patent_citation.tsv.zip URLs directly
//   - Remove manifestVersion reference from audit payload
// The F5 watcher picks up the status='active' change on the next 30s tick
// and redeploys to Zeebe.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const BPMN_PROCESS_ID = "patent_ingest_uspto_weekly";
const BPMN_FILE = path.resolve(
  repoRoot,
  "00-contracts/bpmn/ai/gftd/patent/ingestUsptoWeekly.bpmn",
);

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(BPMN_FILE, "utf8");
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml"          = ${xml},
        xml_byte_size  = CAST(${size} AS integer),
        status         = 'active'
    WHERE bpmn_process_id = ${BPMN_PROCESS_ID}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_process_def
    SET status = 'inactive'
    WHERE bpmn_process_id = ${BPMN_PROCESS_ID}
  `.execute(db);
}
