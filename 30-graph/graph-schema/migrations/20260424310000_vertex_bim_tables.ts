import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR 2604241500 — BIM persistence (Worker-direct Hyperdrive per ADR-0036).
 *
 * Feeds `com.etzhayyim.apps.bim.*` XRPC surface at `bim.etzhayyim.com`:
 *   - importIfc / getStoreyScene / listSpaces / annotateElement / requestExport
 *
 * IFC-native hierarchy (mirrors `kami_bim::*` Rust types):
 *   vertex_bim_project       — IfcProject equivalent (1 per model)
 *   vertex_bim_revision      — versioned snapshot (IFC blob + tessellation cache)
 *   vertex_bim_building      — IfcBuilding
 *   vertex_bim_storey        — IfcBuildingStorey (primary LOD unit)
 *   vertex_bim_space         — IfcSpace (room)
 *   vertex_bim_element       — IfcWall / IfcSlab / IfcColumn / IfcBeam / ...
 *   vertex_bim_pset          — IFC Pset_* / Qto_* property sets
 *   vertex_bim_annotation    — BCF-style review annotation (comment / issue / RFI / approval)
 *   vertex_bim_job           — async IFC import/export job
 *   edge_bim_has_revision    — project → revision
 *   edge_bim_has_building    — project → building
 *   edge_bim_has_storey      — building → storey
 *   edge_bim_has_space       — storey → space
 *   edge_bim_has_element     — storey → element
 *   edge_bim_bounded_by      — space → element (wall / slab)
 *   edge_bim_has_pset        — element / space → pset
 *   edge_bim_annotated_by    — element → annotation
 *
 * Heavy geometry (IFC STEP originals, tessellation caches, BCF zips,
 * export artefacts) lives in B2 (Backblaze B2 S3-compatible, ADR-0048)
 * content-addressed under `bim/blobs/{sha256}` / `bim/meshes/{sha256}`
 * / `bim/exports/{sha256}` in bucket `etzhayyim-bim`. Only `blob_key` +
 * metadata is stored here (ADR-0036 invariant: no large binaries in
 * Hyperdrive).
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── vertex_bim_project ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bim_project (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      name             VARCHAR,
      description      VARCHAR,
      units_length     VARCHAR,
      units_angle      VARCHAR,
      units_time       VARCHAR,
      true_north_rad   DOUBLE PRECISION,
      world_origin_x   DOUBLE PRECISION,
      world_origin_y   DOUBLE PRECISION,
      world_origin_z   DOUBLE PRECISION,
      head_revision_id VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  // ── vertex_bim_revision ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bim_revision (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      project_id         VARCHAR,
      parent_revision_id VARCHAR,
      source_format      VARCHAR,
      schema_version     VARCHAR,
      source_blob_key    VARCHAR,
      tessellation_key   VARCHAR,
      tessellation_tol   DOUBLE PRECISION,
      bbox_min_x         DOUBLE PRECISION,
      bbox_min_y         DOUBLE PRECISION,
      bbox_min_z         DOUBLE PRECISION,
      bbox_max_x         DOUBLE PRECISION,
      bbox_max_y         DOUBLE PRECISION,
      bbox_max_z         DOUBLE PRECISION,
      status             VARCHAR,
      message            VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_revision_project ON vertex_bim_revision (project_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_revision_status ON vertex_bim_revision (status)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── vertex_bim_building ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bim_building (
      vertex_id           VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      rkey                VARCHAR,
      repo                VARCHAR,
      revision_id         VARCHAR,
      project_id          VARCHAR,
      global_id           VARCHAR,
      name                VARCHAR,
      reference_elevation DOUBLE PRECISION,
      latitude_deg        DOUBLE PRECISION,
      longitude_deg       DOUBLE PRECISION,
      elevation_m         DOUBLE PRECISION,
      created_at          VARCHAR,
      org_id              VARCHAR,
      user_id             VARCHAR,
      actor_id            VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_building_revision ON vertex_bim_building (revision_id)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── vertex_bim_storey ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bim_storey (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      revision_id      VARCHAR,
      building_id      VARCHAR,
      global_id        VARCHAR,
      name             VARCHAR,
      elevation        DOUBLE PRECISION,
      height           DOUBLE PRECISION,
      bbox_min_x       DOUBLE PRECISION,
      bbox_min_y       DOUBLE PRECISION,
      bbox_min_z       DOUBLE PRECISION,
      bbox_max_x       DOUBLE PRECISION,
      bbox_max_y       DOUBLE PRECISION,
      bbox_max_z       DOUBLE PRECISION,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_storey_building ON vertex_bim_storey (building_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_storey_revision ON vertex_bim_storey (revision_id)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── vertex_bim_space ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bim_space (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      revision_id      VARCHAR,
      storey_id        VARCHAR,
      building_id      VARCHAR,
      global_id        VARCHAR,
      name             VARCHAR,
      long_name        VARCHAR,
      label            VARCHAR,
      category         VARCHAR,
      height           DOUBLE PRECISION,
      gross_area_m2    DOUBLE PRECISION,
      net_area_m2      DOUBLE PRECISION,
      gross_volume_m3  DOUBLE PRECISION,
      net_volume_m3    DOUBLE PRECISION,
      boundary_json    VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_space_storey ON vertex_bim_space (storey_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_space_category ON vertex_bim_space (category)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── vertex_bim_element ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bim_element (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      revision_id       VARCHAR,
      storey_id         VARCHAR,
      building_id       VARCHAR,
      global_id         VARCHAR,
      name              VARCHAR,
      kind              VARCHAR,
      geometry_kind     VARCHAR,
      mesh_blob_key     VARCHAR,
      triangle_count    BIGINT,
      base_color_hex    VARCHAR,
      placement_json    VARCHAR,
      classification_src VARCHAR,
      classification_code VARCHAR,
      material_json     VARCHAR,
      gross_area_m2     DOUBLE PRECISION,
      net_area_m2       DOUBLE PRECISION,
      gross_volume_m3   DOUBLE PRECISION,
      weight_kg         DOUBLE PRECISION,
      length_m          DOUBLE PRECISION,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_element_storey ON vertex_bim_element (storey_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_element_kind ON vertex_bim_element (kind)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_element_revision ON vertex_bim_element (revision_id)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── vertex_bim_pset ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bim_pset (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      parent_vertex_id VARCHAR,
      parent_kind      VARCHAR,
      pset_name        VARCHAR,
      props_json       VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_pset_parent ON vertex_bim_pset (parent_vertex_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_pset_name ON vertex_bim_pset (pset_name)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── vertex_bim_annotation ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bim_annotation (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      element_id       VARCHAR,
      storey_id        VARCHAR,
      kind             VARCHAR,
      severity         VARCHAR,
      text             VARCHAR,
      viewpoint_json   VARCHAR,
      assigned_to      VARCHAR,
      reply_to         VARCHAR,
      status           VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_annotation_element ON vertex_bim_annotation (element_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_annotation_status ON vertex_bim_annotation (status)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── vertex_bim_job ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bim_job (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      job_kind         VARCHAR,
      project_id       VARCHAR,
      revision_id      VARCHAR,
      target           VARCHAR,
      source_blob_key  VARCHAR,
      output_blob_key  VARCHAR,
      status           VARCHAR,
      error_message    VARCHAR,
      estimated_secs   BIGINT,
      started_at       VARCHAR,
      finished_at      VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_job_revision ON vertex_bim_job (revision_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_job_status ON vertex_bim_job (status)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_bim_job_kind ON vertex_bim_job (job_kind)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── edges (all share the standard src_vid/dst_vid + RLS/owner shape) ──
  const edgeDdl = (table: string) => sql`
    CREATE TABLE IF NOT EXISTS ${sql.raw(table)} (
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
  `;
  const edgeIdx = (table: string, col: 'src' | 'dst') => sql`
    CREATE INDEX IF NOT EXISTS ${sql.raw(`idx_${table}_${col}`)} ON ${sql.raw(table)} (${sql.raw(`${col}_vid`)})
  `;

  const edges = [
    'edge_bim_has_revision',
    'edge_bim_has_building',
    'edge_bim_has_storey',
    'edge_bim_has_space',
    'edge_bim_has_element',
    'edge_bim_bounded_by',
    'edge_bim_has_pset',
    'edge_bim_annotated_by',
  ];
  for (const t of edges) {
    await edgeDdl(t).execute(db);
  await sql`FLUSH`.execute(db);
    await edgeIdx(t, 'src').execute(db);
  await sql`FLUSH`.execute(db);
    await edgeIdx(t, 'dst').execute(db);
  await sql`FLUSH`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const edges = [
    'edge_bim_has_revision',
    'edge_bim_has_building',
    'edge_bim_has_storey',
    'edge_bim_has_space',
    'edge_bim_has_element',
    'edge_bim_bounded_by',
    'edge_bim_has_pset',
    'edge_bim_annotated_by',
  ];
  for (const t of edges) {
    await sql`${sql.raw(`DROP INDEX IF EXISTS idx_${t}_dst`)}`.execute(db);
  await sql`FLUSH`.execute(db);
    await sql`${sql.raw(`DROP INDEX IF EXISTS idx_${t}_src`)}`.execute(db);
  await sql`FLUSH`.execute(db);
    await sql`${sql.raw(`DROP TABLE IF EXISTS ${t}`)}`.execute(db);
  await sql`FLUSH`.execute(db);
  }

  await sql`DROP INDEX IF EXISTS idx_vertex_bim_job_kind`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_bim_job_status`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_bim_job_revision`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bim_job`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_bim_annotation_status`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_bim_annotation_element`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bim_annotation`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_bim_pset_name`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_bim_pset_parent`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bim_pset`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_bim_element_revision`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_bim_element_kind`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_bim_element_storey`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bim_element`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_bim_space_category`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_bim_space_storey`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bim_space`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_bim_storey_revision`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_bim_storey_building`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bim_storey`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_bim_building_revision`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bim_building`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_bim_revision_status`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_bim_revision_project`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bim_revision`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP TABLE IF EXISTS vertex_bim_project`.execute(db);
  await sql`FLUSH`.execute(db);
}
