import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Re-apply copyright BPMN XMLs with xmlns:xsi moved to the definitions root.
// The prior migration (600300) stored inline xmlns:xsi inside <timeCycle>,
// which Zeebe 8.5 rejects as ProcessInvalidError.
// Also resets status='active' so the F5 watcher retries the deploy.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const processes = [
  { file: "crossrefIngest", processId: "copyright_crossref_ingest" },
  { file: "dataciteIngest", processId: "copyright_datacite_ingest" },
] as const;

const sourcePath = (file: string) => `00-contracts/bpmn/ai/gftd/copyright/${file}.bpmn`;
const slug = (file: string) => file.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`);
const processVertexId = (file: string) =>
  `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/copyright-${slug(file)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const p of processes) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(p.file)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    const vid = processVertexId(p.file);
    await sql`UPDATE vertex_bpmn_process_def
              SET "xml" = ${xml}, xml_byte_size = ${size}::integer, "version" = 3, status = 'active'
              WHERE vertex_id = ${vid}`.execute(db);
  }
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No-op: restoring the broken XML would re-break the deploy.
}
