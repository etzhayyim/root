import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * adsk.etzhayyim.com BPMN v3 — strip XML-illegal `--` from header comment.
 *
 * Zeebe broker rejected v2 deploy:
 *   `Fatal Error: URI=null Line=11: The string "--" is not permitted
 *    within comments.`
 *
 * Root cause: the v2 BPMN header documented `kubectl exec ... -- python -c`
 * (the `--` is kubectl's argument separator) inside an XML comment.
 * XML spec disallows the `--` substring anywhere inside `<!-- ... -->`.
 * v3 rewrites the comment to remove the offending substring.
 *
 * v2 row was marked status='inactive' by `_mark_invalid_sync`. We
 * delete it and re-insert at v3/status=active so the F5 watcher
 * picks it up on the next 30s tick.
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-06T00:01:00Z";
const ownerDid = "did:web:adsk.etzhayyim.com";
const actorTag = "sys.bpmn.seed.adsk-comment-fix";

const v2VertexId = "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/adsk-ingest-dataset-v2";
const v3Seed: P = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/adsk-ingest-dataset-v3",
  bpmnProcessId: "adsk_ingest_dataset",
  sourcePath: "00-contracts/bpmn/ai/gftd/adsk/ingestAdskDataset.bpmn",
  ownerDid,
};

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${v2VertexId}`.execute(db);

  const xml = readContract(v3Seed.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${v3Seed.vertexId}, ${v3Seed.ownerDid}, ${v3Seed.bpmnProcessId}, CAST(3 AS int), ${xml}, CAST(${size} AS integer), ${v3Seed.sourcePath}, 'active', ${createdAt}, CAST(1 AS int), ${v3Seed.ownerDid}, ${v3Seed.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${v3Seed.vertexId})
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${v3Seed.vertexId}`.execute(db);
}
