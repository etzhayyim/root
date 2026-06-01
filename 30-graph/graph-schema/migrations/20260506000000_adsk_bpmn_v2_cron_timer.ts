import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * adsk.etzhayyim.com BPMN v2 — replace ISO 8601 `R/P30D` timeCycle with
 * Zeebe-supported cron expression `0 0 0 6 * ?` (monthly day 6, 00:00 UTC).
 *
 * v1 was rejected by Zeebe with `ProcessInvalidError` (empty message,
 * "permanently invalid"). Same shape as the isbn open-library /
 * hathitrust monthly cron BPMNs.
 *
 * v2 process_def uses bumped version=2 so the F5 watcher re-deploys
 * the new XML to Zeebe (the v1 row was marked status='inactive' by
 * _mark_invalid_sync; we drop it and re-insert at v2/status=active).
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-06T00:00:00Z";
const ownerDid = "did:web:adsk.etzhayyim.com";
const actorTag = "sys.bpmn.seed.adsk-cron";

const v1VertexId = "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/adsk-ingest-dataset-v1";
const v2Seed: P = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/adsk-ingest-dataset-v2",
  bpmnProcessId: "adsk_ingest_dataset",
  sourcePath: "00-contracts/bpmn/ai/gftd/adsk/ingestAdskDataset.bpmn",
  ownerDid,
};

export async function up(db: Kysely<unknown>): Promise<void> {
  // Drop the rejected v1 row so the F5 watcher's deployed_in_flight
  // set doesn't keep skipping the bpmn_process_id.
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${v1VertexId}`.execute(db);

  const xml = readContract(v2Seed.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${v2Seed.vertexId}, ${v2Seed.ownerDid}, ${v2Seed.bpmnProcessId}, CAST(2 AS int), ${xml}, CAST(${size} AS integer), ${v2Seed.sourcePath}, 'active', ${createdAt}, CAST(1 AS int), ${v2Seed.ownerDid}, ${v2Seed.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${v2Seed.vertexId})
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${v2Seed.vertexId}`.execute(db);
}
