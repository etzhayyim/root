import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Fix coverageReport.bpmn Task_UpdateState INSERT: add missing owner_did column.
// Prior version omitted owner_did (NOT NULL), causing db.insert task failure after
// pds.dispatch succeeded — posts were created but state row was never written.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const sourcePath = "00-contracts/bpmn/com/etzhayyim/copyright/coverageReport.bpmn";
const vid = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/copyright-coverage-report-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(path.resolve(repoRoot, sourcePath), "utf8");
  const size = Buffer.byteLength(xml, "utf8");
  await sql`UPDATE vertex_bpmn_process_def
            SET "xml" = ${xml}, xml_byte_size = ${size}::integer, "version" = 3, status = 'active'
            WHERE vertex_id = ${vid}`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No-op: restoring the broken INSERT would re-break the deploy.
}
