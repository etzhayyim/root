// tier: B
// live.etzhayyim.com — virtual concert room state + actor chat log.
//
// Two new vertex_* tables that fold into `view_actor_universal` so the
// actor-resolver Worker (actor.etzhayyim.com/{kind}/{rkey}) returns DID docs
// for every live room and chat utterance. Replaces the in-memory
// RoomLiveDO + recentChat ring buffer as the federation source of truth;
// the DO continues to own the WebSocket fan-out path but mirrors writes
// here for durability + AT Protocol federation.
//
// Naming alignment:
//   vertex_live_room              → did:web:actor.etzhayyim.com:liveRoom:<slug>
//                                  → actor.etzhayyim.com/liveRoom/<slug>/did.json
//   vertex_live_chat              → did:web:actor.etzhayyim.com:liveChat:<rkey>
//                                  → actor.etzhayyim.com/liveChat/<rkey>/did.json
//
// RLS shape: ADR-0095 canonical 4-column scheme
//   actor_did  — issuer (= performer / speaker DID)
//   org_did    — tenant boundary (= room operator)
//   at_did     — federation alias (did:web:* or did:plc:*) for cross-PDS
//   created_at — ISO 8601
//
// After this migration runs:
//   1. python3 70-tools/scripts/contract/gen-view-actor-universal.mjs
//      regenerates the universal view to fold these two new branches in
//   2. live worker mirrors RoomLiveDO writes here via Kysely (Tier 2
//      Domain write per ADR-0036)

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_live_room ─────────────────────────────────────────────
  // One row per concert room (== one BPMN show flow instance).
  // PK = vertex_id of form `at://<perf_did>/ai.gftd.apps.live.room/<slug>`.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_live_room (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      slug VARCHAR NOT NULL,
      bpm DOUBLE PRECISION NOT NULL,
      start_at DOUBLE PRECISION NOT NULL,
      stage_preset VARCHAR NOT NULL,
      performer_handle VARCHAR,
      setlist_json TEXT,
      lighting_json TEXT,
      crowd_seed BIGINT,
      fans_target BIGINT,
      name VARCHAR,
      description VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      at_did VARCHAR,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  // ── vertex_live_chat ─────────────────────────────────────────────
  // Append-only utterance log. PK = vertex_id of form
  // `at://<actor_did>/ai.gftd.apps.live.chat/<ts>-<nanoid>`.
  // text_excerpt is the utterance itself; `name` is a 1-line caption
  // (== "{handle}: {text}") so the universal-view name column is
  // populated without joining.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_live_chat (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      room_slug VARCHAR NOT NULL,
      actor_handle VARCHAR NOT NULL,
      text VARCHAR NOT NULL,
      kind VARCHAR,
      tint_r DOUBLE PRECISION,
      tint_g DOUBLE PRECISION,
      tint_b DOUBLE PRECISION,
      posted_at DOUBLE PRECISION NOT NULL,
      name VARCHAR,
      description VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      at_did VARCHAR,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  // Seed the demo room so the actor-resolver returns something the
  // moment routing-gateway sends an `actor.etzhayyim.com/liveRoom/demo` hit.
  // RLS: actor_did = the performer DID (here = the room itself, since
  // demo is anchored at live.etzhayyim.com); org_did stays "anon" until a
  // performer wallet binds to the room.
  await sql`
    INSERT INTO vertex_live_room (
      vertex_id, slug, bpm, start_at, stage_preset, performer_handle,
      setlist_json, lighting_json, crowd_seed, fans_target,
      name, description, actor_did, org_did, at_did, created_at
    )
    VALUES (
      'at://did:web:live.etzhayyim.com/ai.gftd.apps.live.room/demo',
      'demo',
      128.0,
      1777380000.0,
      'hall',
      'Mitama',
      '[]',
      '[]',
      7,
      600,
      'live demo room',
      'Open virtual concert room — mitama actors join, dance, converse via the BPMN show flow at apps/live/showFlow.bpmn.',
      'did:web:live.etzhayyim.com',
      'anon',
      'did:web:live.etzhayyim.com',
      '2026-04-29T00:00:00Z'
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_live_chat`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_live_room`.execute(db);
}
