import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * isbn.etzhayyim.com BPMN-as-actor seeding (ADR-0056).
 *
 * 6 BPMN process defs + 5 XRPC bindings (refreshDaily is timer-start
 * only, not bound to an XRPC NSID).
 *
 *  Process / NSID                                        Source
 *  ---------------------------------------------------------------------
 *  isbn_ingest_open_library    app.etzhayyim.apps.isbn.ingestOpenLibrary
 *  isbn_ingest_aozora          app.etzhayyim.apps.isbn.ingestAozora
 *  isbn_ingest_gutenberg       app.etzhayyim.apps.isbn.ingestGutenberg
 *  isbn_ingest_ndl             app.etzhayyim.apps.isbn.ingestNdl
 *  isbn_ingest_hathitrust      app.etzhayyim.apps.isbn.ingestHathiTrust
 *  isbn_refresh_daily          (timer R/PT24H, no XRPC binding)
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };
type B = { vertexId: string; nsid: string; bpmnProcessId: string; ownerDid: string; resultTimeoutMs: number };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-05T10:00:00Z";
const ownerDid = "did:web:isbn.etzhayyim.com";
const actorTag = "sys.bpmn.seed.isbn-bulk-ingest";

const processSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isbn-ingest-open-library-v1",
    bpmnProcessId: "isbn_ingest_open_library",
    sourcePath: "00-contracts/bpmn/ai/gftd/isbn/ingestOpenLibrary.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isbn-ingest-aozora-v1",
    bpmnProcessId: "isbn_ingest_aozora",
    sourcePath: "00-contracts/bpmn/ai/gftd/isbn/ingestAozora.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isbn-ingest-gutenberg-v1",
    bpmnProcessId: "isbn_ingest_gutenberg",
    sourcePath: "00-contracts/bpmn/ai/gftd/isbn/ingestGutenberg.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isbn-ingest-ndl-v1",
    bpmnProcessId: "isbn_ingest_ndl",
    sourcePath: "00-contracts/bpmn/ai/gftd/isbn/ingestNdl.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isbn-ingest-hathitrust-v1",
    bpmnProcessId: "isbn_ingest_hathitrust",
    sourcePath: "00-contracts/bpmn/ai/gftd/isbn/ingestHathiTrust.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isbn-refresh-daily-v1",
    bpmnProcessId: "isbn_refresh_daily",
    sourcePath: "00-contracts/bpmn/ai/gftd/isbn/refreshDaily.bpmn", ownerDid },
];

const bindingSeeds: B[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isbn-ingestOpenLibrary-v1",
    nsid: "app.etzhayyim.apps.isbn.ingestOpenLibrary",
    bpmnProcessId: "isbn_ingest_open_library", ownerDid, resultTimeoutMs: 21_600_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isbn-ingestAozora-v1",
    nsid: "app.etzhayyim.apps.isbn.ingestAozora",
    bpmnProcessId: "isbn_ingest_aozora", ownerDid, resultTimeoutMs: 7_200_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isbn-ingestGutenberg-v1",
    nsid: "app.etzhayyim.apps.isbn.ingestGutenberg",
    bpmnProcessId: "isbn_ingest_gutenberg", ownerDid, resultTimeoutMs: 21_600_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isbn-ingestNdl-v1",
    nsid: "app.etzhayyim.apps.isbn.ingestNdl",
    bpmnProcessId: "isbn_ingest_ndl", ownerDid, resultTimeoutMs: 600_000 },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isbn-ingestHathiTrust-v1",
    nsid: "app.etzhayyim.apps.isbn.ingestHathiTrust",
    bpmnProcessId: "isbn_ingest_hathitrust", ownerDid, resultTimeoutMs: 21_600_000 },
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

async function insertBinding(db: Kysely<unknown>, s: B): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1, CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) await insertProcessDef(db, s);
  for (const s of bindingSeeds) await insertBinding(db, s);
}
export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of bindingSeeds) await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId}`.execute(db);
  for (const s of processSeeds) await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
}
