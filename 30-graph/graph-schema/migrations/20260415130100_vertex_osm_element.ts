import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 0055: Self-hosted OSM planet schema.
 *
 * Single discriminated vertex table + two edge tables + one narrow streaming MV.
 * Design summary:
 *   - `vertex_osm_element` holds nodes/ways/relations discriminated by `osm_type`
 *     ('n' | 'w' | 'r'). 1 AT record = 1 row per P10v2 GraphAr convention.
 *   - `edge_osm_way_node` models way → node ordering via `seq`.
 *   - `edge_osm_relation_member` models relation → (node|way|relation) membership
 *     with `role` + `seq` + `member_type`.
 *   - `mv_osm_tag_lookup` is a narrow streaming MV exploding JSONB `tags` into
 *     (key, value) rows for k=v lookup. Filters `valid_to IS NULL` (current
 *     versions only) so the backfill set stays manageable. Complies with MV
 *     memory-safety guardrail (§MV Memory Safety Guardrails) — only 5 columns,
 *     no GROUP BY, no MAX(varchar).
 *
 * Source provenance: `source_did = 'did:web:maps.gftd.ai:planet'`.
 * Spatial indexing: `s2_cell_id` (S2 level 16 ~150m) + `geohash` (12-char).
 * PostGIS is NOT available on RisingWave — geometry is stored as raw lat/lon
 * plus bbox_* for ways/relations.
 *
 * Versioning: OSM elements are versioned on every edit. `version INT` is the
 * OSM API `version=` attribute. `valid_to IS NULL` means current.
 *
 * Public global data — no per-tenant RLS columns. `owner_did` + `source_did`
 * are sufficient (match 0037 IP-cluster pattern).
 *
 * Tags: OSM tags are genuinely schemaless (free-form k=v, millions of distinct
 * keys). JSONB is the correct shape here — this is explicitly the exception to
 * the "no JSON bag / val" rule because typed columns are infeasible for OSM.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── vertex_osm_element ────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_osm_element (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      owner_did        VARCHAR,
      source_did       VARCHAR,
      sensitivity_ord  BIGINT DEFAULT 0,
      created_date     DATE,
      osm_type         VARCHAR,
      osm_id           BIGINT,
      version          INT,
      changeset_id     BIGINT,
      user_name        VARCHAR,
      uid              BIGINT,
      timestamp        TIMESTAMPTZ,
      valid_from       TIMESTAMPTZ,
      valid_to         TIMESTAMPTZ,
      lat              DOUBLE PRECISION,
      lon              DOUBLE PRECISION,
      s2_cell_id       BIGINT,
      geohash          VARCHAR,
      tags             JSONB,
      bbox_min_lng     DOUBLE PRECISION,
      bbox_min_lat     DOUBLE PRECISION,
      bbox_max_lng     DOUBLE PRECISION,
      bbox_max_lat     DOUBLE PRECISION
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_osm_element_s2 ON vertex_osm_element (s2_cell_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_element_type_id_version ON vertex_osm_element (osm_type, osm_id, version)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_element_valid_to ON vertex_osm_element (valid_to)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_element_source_seq ON vertex_osm_element (source_did, _seq)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_element_type_s2 ON vertex_osm_element (osm_type, s2_cell_id)`.execute(db);

  // ── edge_osm_way_node ─────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_osm_way_node (
      edge_id          VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      owner_did        VARCHAR,
      source_did       VARCHAR,
      created_date     DATE,
      way_vertex_id    VARCHAR,
      node_vertex_id   VARCHAR,
      seq              INT,
      valid_from       TIMESTAMPTZ,
      valid_to         TIMESTAMPTZ
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_osm_way_node_way_seq ON edge_osm_way_node (way_vertex_id, seq)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_way_node_node ON edge_osm_way_node (node_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_way_node_source_seq ON edge_osm_way_node (source_did, _seq)`.execute(db);

  // ── edge_osm_relation_member ──────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_osm_relation_member (
      edge_id             VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      owner_did           VARCHAR,
      source_did          VARCHAR,
      created_date        DATE,
      relation_vertex_id  VARCHAR,
      member_vertex_id    VARCHAR,
      member_type         VARCHAR,
      role                VARCHAR,
      seq                 INT,
      valid_from          TIMESTAMPTZ,
      valid_to            TIMESTAMPTZ
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_osm_rel_member_rel_seq ON edge_osm_relation_member (relation_vertex_id, seq)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_rel_member_member ON edge_osm_relation_member (member_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_rel_member_source_seq ON edge_osm_relation_member (source_did, _seq)`.execute(db);

  // ── *_stage tables for ingest idempotent merge ────────────────────────
  // RisingWave lacks ON CONFLICT, so 70-tools/maps-osm-ingest writes COPY
  // batches to *_stage tables, then atomically:
  //   DELETE FROM <main> WHERE pk IN (SELECT pk FROM <stage>);
  //   INSERT INTO <main> SELECT * FROM <stage>;
  //   DELETE FROM <stage>;
  // Stage shape mirrors the main table 1:1. No indexes (transient batches only).
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_osm_element_stage (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      owner_did        VARCHAR,
      source_did       VARCHAR,
      sensitivity_ord  BIGINT DEFAULT 0,
      created_date     DATE,
      osm_type         VARCHAR,
      osm_id           BIGINT,
      version          INT,
      changeset_id     BIGINT,
      user_name        VARCHAR,
      uid              BIGINT,
      timestamp        TIMESTAMPTZ,
      valid_from       TIMESTAMPTZ,
      valid_to         TIMESTAMPTZ,
      lat              DOUBLE PRECISION,
      lon              DOUBLE PRECISION,
      s2_cell_id       BIGINT,
      geohash          VARCHAR,
      tags             JSONB,
      bbox_min_lng     DOUBLE PRECISION,
      bbox_min_lat     DOUBLE PRECISION,
      bbox_max_lng     DOUBLE PRECISION,
      bbox_max_lat     DOUBLE PRECISION
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_osm_way_node_stage (
      edge_id          VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      owner_did        VARCHAR,
      source_did       VARCHAR,
      created_date     DATE,
      way_vertex_id    VARCHAR,
      node_vertex_id   VARCHAR,
      seq              INT,
      valid_from       TIMESTAMPTZ,
      valid_to         TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_osm_relation_member_stage (
      edge_id             VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      owner_did           VARCHAR,
      source_did          VARCHAR,
      created_date        DATE,
      relation_vertex_id  VARCHAR,
      member_vertex_id    VARCHAR,
      member_type         VARCHAR,
      role                VARCHAR,
      seq                 INT,
      valid_from          TIMESTAMPTZ,
      valid_to            TIMESTAMPTZ
    )
  `.execute(db);

  // ── mv_osm_tag_lookup (narrow streaming MV) ───────────────────────────
  // jsonb_each_text(tags) lateral-unnests current-version element tags into
  // (key, value) pairs. 5 columns only, no GROUP BY, no wide MAX — safe per
  // MV memory guardrail.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_osm_tag_lookup AS
    SELECT
      v.vertex_id,
      v.osm_type,
      t.key,
      t.value,
      v.s2_cell_id
    FROM vertex_osm_element AS v,
         jsonb_each_text(v.tags) AS t(key, value)
    WHERE v.valid_to IS NULL
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_osm_tag_lookup`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_osm_relation_member_stage`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_osm_way_node_stage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_osm_element_stage`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_osm_relation_member`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_osm_way_node`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_osm_element`.execute(db);
}
