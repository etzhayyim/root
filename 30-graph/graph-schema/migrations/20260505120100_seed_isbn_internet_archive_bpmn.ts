import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * isbn.etzhayyim.com Phase 2 — Internet Archive timer-start BPMN seed.
 * Adds a 6th source covering body text + cover + (optional) per-page
 * IIIF scan images.
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-05T12:01:00Z";
const ownerDid = "did:web:isbn.etzhayyim.com";
const actorTag = "sys.bpmn.seed.isbn-internet-archive";

const seeds: P[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/isbn-ingest-internet-archive-v1",
    bpmnProcessId: "isbn_ingest_internet_archive",
    sourcePath: "00-contracts/bpmn/ai/gftd/isbn/ingestInternetArchive.bpmn", ownerDid },
];

async function insertProcessDef(db: Kysely<unknown>, s: P): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) await insertProcessDef(db, s);
}
export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
}
