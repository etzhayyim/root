// Phase C of the live.gftd.ai L4 actor migration.
//
// Bumps `live_post_chat` to BPMN version 2: same db.insert into
// vertex_live_chat (Tier 2 Domain) followed by a generic.pds.dispatch
// step that publishes `app.bsky.feed.post` from the actor's DID
// (Tier 1 Social — federates over the AT Protocol firehose) and
// finally generic.audit.emit.
//
// What changed in v2:
//   + Task_Federate inserted between Task_Save and Task_Audit
//   + audit emits federatedUri / federatedStatus alongside the
//     existing roomSlug / actorDid / kind payload
//
// Demo actors that already have actor_registry rows (signing keys
// mintable via _mint_pds_service_auth):
//   yorishiro  — did:web:yorishiro.gftd.ai
//   shinkansen — did:web:shinkansen.gftd.ai
//   oshikatsu  — did:web:oshikatsu.gftd.ai
//   shinshi    — did:web:shinshi.gftd.ai
//   yotei      — did:web:yotei.gftd.ai
//
// The "anime" demo handle should be remapped to
//   did:web:media-anime.gftd.ai
// in the live demo roster (separate change in the live worker).
//
// Federation failure is non-fatal: the chat row already landed in
// vertex_live_chat at Task_Save, the WebSocket fan-out from the DO
// already showed the bubble to viewers, and the audit task captures
// the federation status so unreachable actors are observable.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-29T02:00:00Z";
const ownerDid = "did:web:live.gftd.ai";
const actorTag = "sys.bpmn.seed.live.v2";

const procVertexIdV2 =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/apps-live-post-chat-v2";
const bindingVertexId =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/apps-live-postChat-v1";
const sourcePath = "00-contracts/bpmn/ai/gftd/apps/live/postChat.bpmn";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(path.resolve(repoRoot, sourcePath), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  // 1. Register v2 process_def. Same bpmn_process_id (`live_post_chat`)
  //    as v1 — Zeebe gateway picks the highest version when the
  //    binding is updated below.
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${procVertexIdV2}, ${ownerDid}, 'live_post_chat', 2,
      ${xml}, CAST(${size} AS integer), ${sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${procVertexIdV2}
    )
  `.execute(db);

  // 2. Mark the v1 process_def as superseded so debugging dashboards
  //    show the active version unambiguously. Idempotent.
  await sql`
    UPDATE vertex_bpmn_process_def
    SET status = 'superseded'
    WHERE bpmn_process_id = 'live_post_chat'
      AND version = 1
      AND status = 'active'
  `.execute(db);

  // 3. Update the lexicon binding to point at version 2. The vertex_id
  //    stays the same (one binding row per NSID); only the
  //    bpmn_version field bumps.
  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET bpmn_version = 2,
        result_timeout_ms = CAST(15000 AS integer)
    WHERE vertex_id = ${bindingVertexId}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Roll the binding back to v1 + restore v1 as the active process.
  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET bpmn_version = 1,
        result_timeout_ms = CAST(5000 AS integer)
    WHERE vertex_id = ${bindingVertexId}
  `.execute(db);
  await sql`
    UPDATE vertex_bpmn_process_def
    SET status = 'active'
    WHERE bpmn_process_id = 'live_post_chat'
      AND version = 1
  `.execute(db);
  await sql`
    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${procVertexIdV2}
  `.execute(db);
}
