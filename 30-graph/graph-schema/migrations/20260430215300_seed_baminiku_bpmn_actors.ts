import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:baminiku.etzhayyim.com";
const createdAt = "2026-04-30T21:53:00+09:00";
const actorId = "sys.bpmn.seed.baminiku";
const writeTableAllowlist = [
  "vertex_baminiku_agent_profile",
  "vertex_baminiku_stream",
  "vertex_baminiku_stage_patch",
  "vertex_baminiku_chat",
  "vertex_baminiku_tip",
  "vertex_baminiku_track",
  "vertex_baminiku_track_event",
  "edge_baminiku_stream_agent",
  "edge_baminiku_stream_stage_patch",
  "edge_baminiku_stream_chat",
  "edge_baminiku_stream_tip",
  "edge_baminiku_stream_track",
  "edge_baminiku_stream_track_event",
].join(",");

const seeds: Seed[] = [
  { slug: "set-agent-profile", op: "setAgentProfile", processId: "baminiku_set_agent_profile", writeTableAllowlist },
  { slug: "create-stream", op: "createStream", processId: "baminiku_create_stream", writeTableAllowlist },
  { slug: "update-stage", op: "updateStage", processId: "baminiku_update_stage", writeTableAllowlist },
  { slug: "record-chat", op: "recordChat", processId: "baminiku_record_chat", writeTableAllowlist },
  { slug: "record-tip", op: "recordTip", processId: "baminiku_record_tip", writeTableAllowlist },
  { slug: "enqueue-track", op: "enqueueTrack", processId: "baminiku_enqueue_track", writeTableAllowlist },
  { slug: "skip-track", op: "skipTrack", processId: "baminiku_skip_track", writeTableAllowlist },
  { slug: "get-stream-state", op: "getStreamState", processId: "baminiku_get_stream_state", writeTableAllowlist: "" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/baminiku/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/baminiku-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/baminiku-${s.slug}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${sourcePath(s)}, 'active',
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVertexId(s)}, ${ownerDid}, ${`ai.gftd.apps.baminiku.${s.op}`}, ${s.processId}, 1,
        30000, ${s.writeTableAllowlist}, 'active', ${createdAt},
        100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
