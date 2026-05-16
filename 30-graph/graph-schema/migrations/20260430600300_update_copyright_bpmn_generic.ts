import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Update copyright BPMNs from v1 (custom Python handlers) to v2 (generic primitives only).
// Rewrites: crossrefIngest, dataciteIngest, coverageReport
// After this migration, copyright_ingest.py handlers are no longer needed.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const processes = [
  { file: "crossrefIngest",   processId: "copyright_crossref_ingest"   },
  { file: "dataciteIngest",   processId: "copyright_datacite_ingest"   },
  { file: "coverageReport",   processId: "copyright_coverage_report"   },
] as const;

const sourcePath = (file: string) => `00-contracts/bpmn/ai/gftd/copyright/${file}.bpmn`;
const slug      = (file: string) => file.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`);
const processVertexId = (file: string) =>
  `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/copyright-${slug(file)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const p of processes) {
    const xml  = readFileSync(path.resolve(repoRoot, sourcePath(p.file)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    const vid  = processVertexId(p.file);
    await sql`UPDATE vertex_bpmn_process_def
              SET "xml" = ${xml}, xml_byte_size = ${size}::integer, "version" = 2
              WHERE vertex_id = ${vid}`.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Re-read would require the v1 XML; since it's deleted from disk, down() is a no-op.
  // To roll back: restore the BPMN files from git and re-run the update.
}
