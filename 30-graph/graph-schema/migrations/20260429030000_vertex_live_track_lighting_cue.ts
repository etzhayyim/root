// tier: B
// Phase D1 of the live.etzhayyim.com L4 migration.
//
// Splits the JSON-blob fields of `vertex_live_room` (setlist_json /
// lighting_json) into first-class vertex tables so each track and
// each lighting cue resolves at the actor-resolver:
//
//   did:web:actor.etzhayyim.com:liveTrack:<rkey>          (per track)
//   did:web:actor.etzhayyim.com:liveLightingCue:<rkey>    (per cue)
//
// The blob columns on `vertex_live_room` stay for backwards-compat
// (the L3 worker still mirrors writes there for the demo flow), but
// new authoring should write per-track / per-cue rows so:
//   - federation can target one track at a time (replace just the
//     drop position without re-publishing the whole setlist)
//   - actor-resolver returns useful DID docs for individual tracks
//   - graph queries can join tracks ↔ chat utterances ↔ cheers via
//     room_slug + (optionally) at_beat
//
// RLS shape per ADR-0095: actor_did / org_did / at_did / created_at.

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_live_track ────────────────────────────────────────────
  // One row per setlist position. PK = `at://<perf_did>/com.etzhayyim.apps.live.track/<room>-<pos>`.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_live_track (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      room_slug VARCHAR NOT NULL,
      position BIGINT NOT NULL,
      title VARCHAR NOT NULL,
      bpm DOUBLE PRECISION NOT NULL,
      length_beats BIGINT NOT NULL,
      dance VARCHAR,
      audio VARCHAR,
      cues_json TEXT,
      name VARCHAR,
      description VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      at_did VARCHAR,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  // ── vertex_live_lighting_cue ─────────────────────────────────────
  // PK = `at://<perf_did>/com.etzhayyim.apps.live.lightingCue/<room>-<seq>`.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_live_lighting_cue (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      room_slug VARCHAR NOT NULL,
      fixture VARCHAR NOT NULL,
      color_r DOUBLE PRECISION NOT NULL,
      color_g DOUBLE PRECISION NOT NULL,
      color_b DOUBLE PRECISION NOT NULL,
      intensity DOUBLE PRECISION NOT NULL,
      envelope VARCHAR NOT NULL,
      envelope_param DOUBLE PRECISION,
      bars BIGINT NOT NULL,
      start_bar BIGINT NOT NULL,
      name VARCHAR,
      description VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      at_did VARCHAR,
      created_at VARCHAR NOT NULL
    )
  `.execute(db);

  // ── edges: room → track + room → cue ─────────────────────────────
  // Folds into the per-room navigation MV via `mv_actor_room_navigation`
  // (out of scope here; declared so the relationship is queryable).
  await sql`
    CREATE TABLE IF NOT EXISTS edge_live_room_track (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      position BIGINT NOT NULL,
      created_at VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      at_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_live_room_lighting_cue (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      start_bar BIGINT NOT NULL,
      created_at VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      at_did VARCHAR
    )
  `.execute(db);

  // ── seed: project the demo room's three default tracks ───────────
  // Mirrors the canned setlist that lives in the live worker's
  // demoSet() so actor-resolver returns something coherent the moment
  // routing-gateway 4c hits actor.etzhayyim.com/liveTrack/demo-1/did.json.
  const tracks = [
    {
      pos: 1,
      title: "Opener (Wota Call)",
      bpm: 128,
      lengthBeats: 128,
      dance: "wota",
      audio: "opener",
      cuesJson:
        '[{"atBeat":32,"kind":"drop","tag":"first-drop"},{"atBeat":96,"kind":"drop","tag":"second-drop"}]',
    },
    {
      pos: 2,
      title: "Ballad Breakdown",
      bpm: 92,
      lengthBeats: 96,
      dance: "hold",
      audio: "ballad",
      cuesJson: '[{"atBeat":16,"kind":"breakdown","tag":"sway"}]',
    },
    {
      pos: 3,
      title: "K-Pop Encore",
      bpm: 140,
      lengthBeats: 128,
      dance: "kpop-point",
      audio: "encore",
      cuesJson:
        '[{"atBeat":16,"kind":"callout","tag":"hello-tokyo"},{"atBeat":64,"kind":"drop","tag":"encore-drop"}]',
    },
  ];
  for (const t of tracks) {
    const vid = `at://did:web:live.etzhayyim.com/com.etzhayyim.apps.live.track/demo-${t.pos}`;
    await sql`
      INSERT INTO vertex_live_track (
        vertex_id, room_slug, position, title, bpm, length_beats,
        dance, audio, cues_json, name, description,
        actor_did, org_did, at_did, created_at
      )
      VALUES (
        ${vid}, 'demo', ${t.pos}, ${t.title}, ${t.bpm}, ${t.lengthBeats},
        ${t.dance}, ${t.audio}, ${t.cuesJson},
        ${t.title + " (track #" + t.pos + ")"},
        ${"Live track " + t.pos + " of room demo — " + t.dance},
        'did:web:live.etzhayyim.com', 'anon', 'did:web:live.etzhayyim.com',
        '2026-04-29T03:00:00Z'
      )
    `.execute(db);
    await sql`
      INSERT INTO edge_live_room_track (
        edge_id, src_vid, dst_vid, position, created_at,
        actor_did, org_did, at_did
      )
      VALUES (
        ${"at://did:web:live.etzhayyim.com/com.etzhayyim.apps.live.roomTrack/demo-" + t.pos},
        'at://did:web:live.etzhayyim.com/com.etzhayyim.apps.live.room/demo',
        ${vid},
        ${t.pos},
        '2026-04-29T03:00:00Z',
        'did:web:live.etzhayyim.com', 'anon', 'did:web:live.etzhayyim.com'
      )
    `.execute(db);
  }

  // ── seed: 3 default lighting cues from the live worker's demoSet ─
  const cues = [
    { idx: 1, fixture: "frontPar", r: 1.0, g: 0.55, b: 0.35, intensity: 0.85, envelope: "breathe", param: null, bars: 16, startBar: 0 },
    { idx: 2, fixture: "laser", r: 0.2, g: 0.7, b: 1.0, intensity: 0.9, envelope: "hold", param: null, bars: 24, startBar: 0 },
    { idx: 3, fixture: "strobe", r: 1.0, g: 1.0, b: 1.0, intensity: 1.0, envelope: "strobe", param: 0.25, bars: 4, startBar: 2 },
  ];
  for (const c of cues) {
    const vid = `at://did:web:live.etzhayyim.com/com.etzhayyim.apps.live.lightingCue/demo-${c.idx}`;
    await sql`
      INSERT INTO vertex_live_lighting_cue (
        vertex_id, room_slug, fixture, color_r, color_g, color_b,
        intensity, envelope, envelope_param, bars, start_bar,
        name, description, actor_did, org_did, at_did, created_at
      )
      VALUES (
        ${vid}, 'demo', ${c.fixture}, ${c.r}, ${c.g}, ${c.b},
        ${c.intensity}, ${c.envelope}, ${c.param}, ${c.bars}, ${c.startBar},
        ${c.fixture + " " + c.envelope + " #" + c.idx},
        ${"Lighting cue #" + c.idx + " for room demo — " + c.fixture + " " + c.envelope},
        'did:web:live.etzhayyim.com', 'anon', 'did:web:live.etzhayyim.com',
        '2026-04-29T03:00:00Z'
      )
    `.execute(db);
    await sql`
      INSERT INTO edge_live_room_lighting_cue (
        edge_id, src_vid, dst_vid, start_bar, created_at,
        actor_did, org_did, at_did
      )
      VALUES (
        ${"at://did:web:live.etzhayyim.com/com.etzhayyim.apps.live.roomLightingCue/demo-" + c.idx},
        'at://did:web:live.etzhayyim.com/com.etzhayyim.apps.live.room/demo',
        ${vid},
        ${c.startBar},
        '2026-04-29T03:00:00Z',
        'did:web:live.etzhayyim.com', 'anon', 'did:web:live.etzhayyim.com'
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_live_room_lighting_cue`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_live_room_track`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_live_lighting_cue`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_live_track`.execute(db);
}
