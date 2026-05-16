import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * isbn.gftd.ai BPMN v2 — pure autonomous timer-start, no CF Worker.
 *
 * Phase 1 (20260505100100) wired 5 manual-start ingest BPMNs + 5 XRPC
 * lexicon bindings + 1 refreshDaily orchestrator. The XRPC bindings
 * required a CF Worker (atproto.gftd.ai) entry point.
 *
 * v2 redesign:
 *  - Each of the 5 ingest BPMNs becomes timer-start (cron schedule)
 *  - refreshDaily.bpmn is dropped (per-source timers replace it)
 *  - All XRPC lexicon bindings are dropped (no XRPC entry needed)
 *  - process_def version bumped 1 → 2 so the bpmn-dispatcher F5
 *    watcher re-deploys the new XML to Zeebe
 *
 * Manual / on-demand triggers (operator only):
 *   kubectl exec -n mitama-udf deploy/zeebe-worker -- python -c \
 *     "import asyncio; from pymagatama.primitives.isbn import \
 *      task_isbn_aozora_ingest as f; print(asyncio.run(f(fulltext=True, limit=200)))"
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-05T11:00:00Z";
const ownerDid = "did:web:isbn.gftd.ai";
const actorTag = "sys.bpmn.seed.isbn-no-cf-worker";

// Bindings to remove (XRPC entry points retired).
const bindingVertexIds = [
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/isbn-ingestOpenLibrary-v1",
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/isbn-ingestAozora-v1",
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/isbn-ingestGutenberg-v1",
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/isbn-ingestNdl-v1",
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/isbn-ingestHathiTrust-v1",
];

// refreshDaily process_def to drop (subsumed by per-source timers).
const refreshDailyVertexId =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/isbn-refresh-daily-v1";

// v1 process_def rows to drop (replaced by v2 timer-start XML below).
const v1ProcessVertexIds = [
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/isbn-ingest-open-library-v1",
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/isbn-ingest-aozora-v1",
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/isbn-ingest-gutenberg-v1",
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/isbn-ingest-ndl-v1",
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/isbn-ingest-hathitrust-v1",
];

// v2 process_def rows (timer-start, autonomous).
const v2ProcessSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/isbn-ingest-open-library-v2",
    bpmnProcessId: "isbn_ingest_open_library",
    sourcePath: "00-contracts/bpmn/ai/gftd/isbn/ingestOpenLibrary.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/isbn-ingest-aozora-v2",
    bpmnProcessId: "isbn_ingest_aozora",
    sourcePath: "00-contracts/bpmn/ai/gftd/isbn/ingestAozora.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/isbn-ingest-gutenberg-v2",
    bpmnProcessId: "isbn_ingest_gutenberg",
    sourcePath: "00-contracts/bpmn/ai/gftd/isbn/ingestGutenberg.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/isbn-ingest-ndl-v2",
    bpmnProcessId: "isbn_ingest_ndl",
    sourcePath: "00-contracts/bpmn/ai/gftd/isbn/ingestNdl.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/isbn-ingest-hathitrust-v2",
    bpmnProcessId: "isbn_ingest_hathitrust",
    sourcePath: "00-contracts/bpmn/ai/gftd/isbn/ingestHathiTrust.bpmn", ownerDid },
];

async function insertProcessDef(db: Kysely<unknown>, s: P): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.bpmnProcessId}, 2, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  // 1. Drop the 5 XRPC lexicon bindings (retire CF Worker entry).
  for (const vid of bindingVertexIds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${vid}`.execute(db);
  }
  // 2. Drop refreshDaily process_def (subsumed by per-source timers).
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${refreshDailyVertexId}`.execute(db);
  // 3. Drop v1 process_def rows (replaced by v2 below).
  for (const vid of v1ProcessVertexIds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${vid}`.execute(db);
  }
  // 4. Insert v2 process_def rows with timer-start XML.
  for (const s of v2ProcessSeeds) await insertProcessDef(db, s);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // Forward-only.  Re-running 20260505100100 plus a manual restore of
  // refreshDaily would recover v1, but the topology is permanently
  // moving to autonomous timer-start (no CF Worker entry).
}
