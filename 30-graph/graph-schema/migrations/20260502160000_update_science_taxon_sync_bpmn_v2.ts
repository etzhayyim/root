import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Update scienceTaxonSync BPMN to add science.taxon.seedBiologicalTaxa step.
// Previously the taxon sync pipeline only called syncNcbi + seedVegetation.
// seedBiologicalTaxa (canonical model organisms: human/mouse/rat/zebrafish/etc.)
// was registered as a pymagatama task type but had no timer-start BPMN driver —
// this migration wires it in as step 3 (between seedVegetation and audit).
// The F5 watcher picks up the status='active' change and redeploys to Zeebe
// within 30s.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const BPMN_PROCESS_ID = "science_taxon_sync";
const BPMN_FILE = path.resolve(
  repoRoot,
  "00-contracts/bpmn/ai/gftd/maps/scienceTaxonSync.bpmn",
);

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(BPMN_FILE, "utf8");
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml"         = ${xml},
        xml_byte_size = CAST(${size} AS integer),
        status        = 'active'
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
