import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Migration 0073: drive core graph spine.
 *
 * Adds typed drive vertices/edges and two narrow rollup MVs.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_drive_file (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      file_id           VARCHAR,
      name              VARCHAR,
      mime_type         VARCHAR,
      size_bytes        BIGINT,
      checksum          VARCHAR,
      blob_cid          VARCHAR,
      folder_id         VARCHAR,
      parent_folder_id  VARCHAR,
      status            VARCHAR,
      location          VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_drive_file_file_id ON vertex_drive_file (file_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_drive_file_folder_id ON vertex_drive_file (folder_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_drive_folder (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      folder_id         VARCHAR,
      name              VARCHAR,
      parent_folder_id  VARCHAR,
      status            VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_drive_folder_folder_id ON vertex_drive_folder (folder_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_drive_folder_parent ON vertex_drive_folder (parent_folder_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_drive_share (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      share_id          VARCHAR,
      file_id           VARCHAR,
      folder_id         VARCHAR,
      shared_with_did   VARCHAR,
      permission        VARCHAR,
      expires_at        VARCHAR,
      status            VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_drive_share_file_id ON vertex_drive_share (file_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_drive_share_shared_with ON vertex_drive_share (shared_with_did)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_drive_contains (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      relation_kind     VARCHAR,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_drive_contains_src ON edge_drive_contains (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_drive_contains_dst ON edge_drive_contains (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_drive_shared_with (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      permission        VARCHAR,
      share_id          VARCHAR,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_drive_shared_with_src ON edge_drive_shared_with (src_vid)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_drive_folder_size_rollup AS
    SELECT
      COALESCE(folder_id, '') AS folder_id,
      COUNT(*) AS file_count,
      COALESCE(SUM(size_bytes), 0) AS total_size_bytes,
      MAX(_seq) AS last_seq
    FROM vertex_drive_file
    GROUP BY COALESCE(folder_id, '')
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_drive_recent_activity AS
    SELECT
      owner_did,
      SUBSTRING(COALESCE(updated_at, created_at, ''), 1, 10) AS activity_day,
      COUNT(*) AS activity_count,
      MAX(_seq) AS last_seq
    FROM vertex_drive_file
    WHERE owner_did IS NOT NULL
    GROUP BY owner_did, SUBSTRING(COALESCE(updated_at, created_at, ''), 1, 10)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_drive_recent_activity`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_drive_folder_size_rollup`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_drive_shared_with`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_drive_contains`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_drive_share`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_drive_folder`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_drive_file`.execute(db);
}
