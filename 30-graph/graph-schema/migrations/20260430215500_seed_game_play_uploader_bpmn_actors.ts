import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:game-play-uploader.etzhayyim.com";
const createdAt = "2026-04-30T21:55:00+09:00";
const actorId = "sys.bpmn.seed.game-play-uploader";
const writeTableAllowlist = [
  "vertex_game_play_participant",
  "vertex_game_play_upload_session",
  "vertex_game_play_upload",
  "vertex_game_play_review",
  "vertex_game_play_reward",
  "edge_game_play_participant_session",
  "edge_game_play_session_upload",
  "edge_game_play_upload_review",
  "edge_game_play_upload_reward",
].join(",");

const seeds: Seed[] = [
  { slug: "register-participant", op: "registerParticipant", processId: "game_play_uploader_register_participant", writeTableAllowlist },
  { slug: "create-upload-session", op: "createUploadSession", processId: "game_play_uploader_create_upload_session", writeTableAllowlist },
  { slug: "record-gameplay-upload", op: "recordGameplayUpload", processId: "game_play_uploader_record_gameplay_upload", writeTableAllowlist },
  { slug: "review-upload", op: "reviewUpload", processId: "game_play_uploader_review_upload", writeTableAllowlist },
  { slug: "calculate-reward", op: "calculateReward", processId: "game_play_uploader_calculate_reward", writeTableAllowlist: "" },
  { slug: "get-campaign-status", op: "getCampaignStatus", processId: "game_play_uploader_get_campaign_status", writeTableAllowlist: "" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/gamePlayUploader/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/game-play-uploader-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/game-play-uploader-${s.slug}-v1`;

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
        ${bindingVertexId(s)}, ${ownerDid}, ${`ai.gftd.apps.gamePlayUploader.${s.op}`}, ${s.processId}, 1,
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
