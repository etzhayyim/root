import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * ADR-0040 — ISEKAI World Map + Artboard topology (Phase 1 SSoT).
 *
 * Tables:
 *   vertex_isekai_world_map      — top-level map (seed / dims)
 *   vertex_isekai_world_scene    — scene placement (x/z in decimeters, radius, scene_type)
 *   vertex_isekai_world_portal   — explicit teleport edges
 *   edge_map_contains_scene      — map → scene
 *   edge_scene_adjacent          — scene ↔ scene (distance, coupling_strength)
 *   edge_scene_portal            — from_scene → to_scene
 *
 * Coordinates stored as BIGINT in decimeters (0.1 m units) to satisfy the
 * "AT Lexicon forbids float" guardrail (CLAUDE.md) while keeping 10 cm
 * resolution across a 10 km map.
 *
 * Federation: worldMap / worldScene / worldPortal are public AT Records.
 * Artboard (private WIP, ADR-0036 writePrivate) is deliberately not in
 * this migration — only added when Phase 3 lands.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_isekai_world_map (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      name             VARCHAR,
      width_m          BIGINT,
      height_m         BIGINT,
      seed             BIGINT,
      biome_mask_cid   VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_isekai_world_scene (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      world_map_uri    VARCHAR,
      scene_type       VARCHAR,
      x_dm             BIGINT,
      z_dm             BIGINT,
      radius_dm        BIGINT,
      label            VARCHAR,
      params_json      VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_isekai_world_scene_map ON vertex_isekai_world_scene (world_map_uri)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_isekai_world_scene_type ON vertex_isekai_world_scene (scene_type)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_isekai_world_portal (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      world_map_uri    VARCHAR,
      from_scene_uri   VARCHAR,
      to_scene_uri     VARCHAR,
      fade_ms          BIGINT,
      bidirectional    BOOLEAN,
      label            VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_map_contains_scene (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_map_contains_scene_src ON edge_map_contains_scene (src_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_scene_adjacent (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      distance_dm        BIGINT,
      coupling_strength  DOUBLE PRECISION,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_scene_adjacent_src ON edge_scene_adjacent (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_scene_adjacent_dst ON edge_scene_adjacent (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_scene_portal (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      fade_ms          BIGINT,
      bidirectional    BOOLEAN,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_scene_portal_src ON edge_scene_portal (src_vid)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_edge_scene_portal_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_scene_portal`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_scene_adjacent_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_scene_adjacent_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_scene_adjacent`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_map_contains_scene_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_map_contains_scene`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_isekai_world_portal`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_isekai_world_scene_type`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_isekai_world_scene_map`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_isekai_world_scene`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_isekai_world_map`.execute(db);
}
