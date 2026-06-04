import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR 2604241500 — CAD persistence (Worker-direct Hyperdrive per ADR-0036).
 *
 * Feeds `com.etzhayyim.apps.cad.*` XRPC surface at `cad.etzhayyim.com`:
 *   - importCadFile / getRevisionScene / addAnchoredComment / listComments / requestExport
 *
 * Tables:
 *   vertex_cad_model        — workspace root (1 model = N revisions)
 *   vertex_cad_revision     — immutable version of a model (blob + tessellation cache refs)
 *   vertex_cad_feature      — parametric feature-tree entry (sketch / extrude / revolve / ...)
 *   vertex_cad_comment      — anchored review comment (part_occurrence_path + topology_ref)
 *   vertex_cad_export_job   — async export job (STEP/IGES/glTF/STL/PDF/DXF)
 *   edge_cad_has_revision   — model → revision
 *   edge_cad_has_feature    — revision → feature
 *   edge_cad_commented_on   — comment → revision
 *   edge_cad_derives_from   — revision → revision (branch / lineage)
 *
 * Heavy geometry (BREP solids, tessellation caches, STEP blobs) lives
 * in B2 (Backblaze B2 S3-compatible, ADR-0048) content-addressed under
 * `cad/blobs/{sha256}` / `cad/meshes/{sha256}` / `cad/exports/{sha256}`
 * in bucket `etzhayyim-cad`. Only the `blob_key` + metadata is stored here.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── vertex_cad_model ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cad_model (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      workspace_id     VARCHAR,
      name             VARCHAR,
      description      VARCHAR,
      units            VARCHAR,
      head_revision_id VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cad_model_workspace ON vertex_cad_model (workspace_id)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── vertex_cad_revision ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cad_revision (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      model_id           VARCHAR,
      parent_revision_id VARCHAR,
      source_format      VARCHAR,
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
      units              VARCHAR,
      message            VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cad_revision_model ON vertex_cad_revision (model_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cad_revision_status ON vertex_cad_revision (status)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── vertex_cad_feature ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cad_feature (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      revision_id      VARCHAR,
      feature_type     VARCHAR,
      feature_index    BIGINT,
      parent_feature_id VARCHAR,
      params_json      VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cad_feature_revision ON vertex_cad_feature (revision_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cad_feature_type ON vertex_cad_feature (feature_type)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── vertex_cad_comment ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cad_comment (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      revision_id          VARCHAR,
      part_occurrence_path VARCHAR,
      topology_kind        VARCHAR,
      topology_id          VARCHAR,
      world_pos_x          DOUBLE PRECISION,
      world_pos_y          DOUBLE PRECISION,
      world_pos_z          DOUBLE PRECISION,
      camera_snapshot_json VARCHAR,
      text                 VARCHAR,
      reply_to             VARCHAR,
      status               VARCHAR,
      created_at           VARCHAR,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cad_comment_revision ON vertex_cad_comment (revision_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cad_comment_part ON vertex_cad_comment (part_occurrence_path)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── vertex_cad_export_job ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cad_export_job (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      revision_id      VARCHAR,
      target           VARCHAR,
      units            VARCHAR,
      tessellation_tol DOUBLE PRECISION,
      status           VARCHAR,
      output_blob_key  VARCHAR,
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
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cad_export_job_revision ON vertex_cad_export_job (revision_id)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cad_export_job_status ON vertex_cad_export_job (status)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── edge_cad_has_revision ── (model → revision)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_cad_has_revision (
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
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_cad_has_revision_src ON edge_cad_has_revision (src_vid)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── edge_cad_has_feature ── (revision → feature)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_cad_has_feature (
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
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_cad_has_feature_src ON edge_cad_has_feature (src_vid)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── edge_cad_commented_on ── (comment → revision)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_cad_commented_on (
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
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_cad_commented_on_src ON edge_cad_commented_on (src_vid)`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_cad_commented_on_dst ON edge_cad_commented_on (dst_vid)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── edge_cad_derives_from ── (revision → parent revision)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_cad_derives_from (
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
  await sql`FLUSH`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_cad_derives_from_src ON edge_cad_derives_from (src_vid)`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_edge_cad_derives_from_src`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_cad_derives_from`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_cad_commented_on_dst`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_cad_commented_on_src`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_cad_commented_on`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_cad_has_feature_src`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_cad_has_feature`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_cad_has_revision_src`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_cad_has_revision`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_cad_export_job_status`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_cad_export_job_revision`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cad_export_job`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_cad_comment_part`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_cad_comment_revision`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cad_comment`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_cad_feature_type`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_cad_feature_revision`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cad_feature`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_cad_revision_status`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_cad_revision_model`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cad_revision`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_cad_model_workspace`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cad_model`.execute(db);
  await sql`FLUSH`.execute(db);
}
