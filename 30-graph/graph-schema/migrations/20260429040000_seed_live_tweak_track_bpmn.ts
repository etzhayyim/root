// Phase D2a — register the per-track edit BPMN flow.
//
// `dispatcher.etzhayyim.com/xrpc/com.etzhayyim.apps.live.tweakTrack` becomes the
// performer's per-track edit surface: change one track's BPM / dance
// / audio preset / cue list without re-publishing the whole setlist.
// Targets the `vertex_live_track` table introduced in 20260429030000
// (phase D1); the legacy `vertex_live_room.setlist_json` blob is left
// untouched (caller's responsibility to keep them in sync if both
// matter).
//
// PK convention:
//   at://<callerDid>/com.etzhayyim.apps.live.track/<roomSlug>-<position>
// Same PK on re-insert → RisingWave overwrites (canonical RW upsert).

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-29T04:00:00Z";
const ownerDid = "did:web:live.etzhayyim.com";
const actorTag = "sys.bpmn.seed.live.tweakTrack";

const procVertexId =
  "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-live-tweak-track-v1";
const bindingVertexId =
  "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-live-tweakTrack-v1";
const sourcePath = "00-contracts/bpmn/com/etzhayyim/apps/live/tweakTrack.bpmn";
const bpmnProcessId = "live_tweak_track";
const nsid = "com.etzhayyim.apps.live.tweakTrack";
const resultTimeoutMs = 8_000;

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(path.resolve(repoRoot, sourcePath), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${procVertexId}, ${ownerDid}, ${bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${procVertexId}
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${bindingVertexId}, ${ownerDid}, ${nsid}, ${bpmnProcessId}, 1,
      CAST(${resultTimeoutMs} AS integer), 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${procVertexId}`.execute(db);
}
