import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const sourcePath = "00-contracts/bpmn/ai/gftd/ingest/houbunEgovJpnDelta.bpmn";
const xml = () => readFileSync(path.resolve(repoRoot, sourcePath), "utf8");

const processVertexId =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/ingest-houbun-egov-jpn-delta-v1";
const bindingVertexId =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/ingest-start-houbun-egov-jpn-delta-v1";
const ownerDid = "did:web:ingest.gftd.ai";
const createdAt = "2026-04-25T16:10:00Z";
const actorTag = "sys.bpmn.seed.ingest-houbun";

export async function up(db: Kysely<unknown>): Promise<void> {
  const body = xml();
  const size = Buffer.byteLength(body, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT ${processVertexId}, ${ownerDid}, 'ingest_houbun_egov_jpn_delta',
           1, ${body}, CAST(${size} AS integer), ${sourcePath}, 'active',
           ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId})
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT ${bindingVertexId}, ${ownerDid}, 'ai.gftd.apps.ingest.start',
           'ingest_houbun_egov_jpn_delta', 1, CAST(0 AS integer), 'active',
           ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId})
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}`.execute(db);
}
