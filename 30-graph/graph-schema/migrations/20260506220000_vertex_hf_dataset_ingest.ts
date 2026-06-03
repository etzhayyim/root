import type { Kysely } from "kysely";
import { sql } from "kysely";

// HuggingFace Hub dataset catalog ingest schema.
//
// Scope: catalog layer only (metadata + split stats + parquet file pointers).
// Row-level sample ingest writes to B2 shards (see training_export.py pattern).
//
// Tables:
//   vertex_hfhub_dataset      — dataset card per repo_id
//   vertex_hfhub_split        — split-level row/byte stats
//   vertex_hfhub_file         — parquet file pointers (B2-copyable URLs)
//   vertex_hfhub_filter       — first-class filter specs (tags / tasks / langs / license)
//   vertex_hfhub_ingest_cursor — per-split offset cursor for sample export
//   edge_hfhub_dataset_tag    — dataset → tag (avoids IN-on-array anti-pattern)
//   edge_hfhub_dataset_task   — dataset → task_category
//   edge_hfhub_dataset_language — dataset → BCP-47 lang code
//   edge_hfhub_filter_match   — filter → dataset (populated by hf.dataset.scan task)
//   edge_hfhub_split_file     — split → parquet file
//   mv_hfhub_tag_popularity   — streaming MV, bounded ~10k rows
//   mv_hfhub_task_popularity  — streaming MV, bounded ~50 rows
//   mv_hfhub_filter_match_count — streaming MV, bounded by filter count
//   mv_hfhub_ingest_progress  — streaming MV, per-split cursor stats

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_hfhub_dataset ─────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hfhub_dataset (
      vertex_id        VARCHAR PRIMARY KEY,   -- 'hf:dataset:{repo_id}'
      _seq             BIGINT,
      created_date     DATE,

      repo_id          VARCHAR NOT NULL,      -- e.g. "squad", "etzhayyim/etzhayyim-corpus"
      author           VARCHAR,               -- org or user handle
      sha              VARCHAR,               -- latest commit sha

      -- Catalog attrs
      license          VARCHAR,
      size_category    VARCHAR,               -- 'n<1K' | '1K<n<10K' | ... | '100K<n<1M' | '1M<n<10M' | 'n>10M'
      downloads_month  BIGINT DEFAULT 0,
      likes            INTEGER DEFAULT 0,
      gated            BOOLEAN DEFAULT FALSE,
      disabled         BOOLEAN DEFAULT FALSE,
      private          BOOLEAN DEFAULT FALSE,

      -- Card content (first 4KB of README)
      description      VARCHAR,
      card_data        VARCHAR,               -- JSON blob of DatasetCardData fields

      -- Ingest lifecycle
      status           VARCHAR DEFAULT 'pending',  -- pending | active | error | archived
      last_scanned_at  TIMESTAMP,
      error_message    VARCHAR,

      -- ADR-0095 canonical columns
      actor_did        VARCHAR DEFAULT 'did:web:ingest.etzhayyim.com',
      org_did          VARCHAR,
      at_did           VARCHAR,
      created_at       TIMESTAMP NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_dataset_author ON vertex_hfhub_dataset (author)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_dataset_status ON vertex_hfhub_dataset (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_dataset_downloads ON vertex_hfhub_dataset (downloads_month DESC)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_dataset_scanned ON vertex_hfhub_dataset (last_scanned_at)`.execute(db);

  // ── vertex_hfhub_split ───────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hfhub_split (
      vertex_id        VARCHAR PRIMARY KEY,   -- 'hf:split:{repo_id}:{config}:{split}'
      _seq             BIGINT,
      created_date     DATE,

      repo_id          VARCHAR NOT NULL,
      config_name      VARCHAR NOT NULL DEFAULT 'default',
      split_name       VARCHAR NOT NULL,      -- train | validation | test

      num_rows         BIGINT,
      num_bytes        BIGINT,
      num_files        INTEGER DEFAULT 0,
      features_json    VARCHAR,               -- column schema as JSON string

      -- ADR-0095
      actor_did        VARCHAR DEFAULT 'did:web:ingest.etzhayyim.com',
      org_did          VARCHAR,
      at_did           VARCHAR,
      created_at       TIMESTAMP NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_split_repo ON vertex_hfhub_split (repo_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_split_name ON vertex_hfhub_split (split_name)`.execute(db);

  // ── vertex_hfhub_file ────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hfhub_file (
      vertex_id        VARCHAR PRIMARY KEY,   -- 'hf:file:{repo_id}@{sha}:{path}'
      _seq             BIGINT,
      created_date     DATE,

      repo_id          VARCHAR NOT NULL,
      split_vertex_id  VARCHAR,               -- FK vertex_hfhub_split.vertex_id
      file_path        VARCHAR NOT NULL,      -- relative path inside repo
      file_format      VARCHAR DEFAULT 'parquet',
      file_size        BIGINT,
      blob_url         VARCHAR,               -- https://huggingface.co/datasets/{repo_id}/resolve/main/{path}

      -- ADR-0095
      actor_did        VARCHAR DEFAULT 'did:web:ingest.etzhayyim.com',
      org_did          VARCHAR,
      at_did           VARCHAR,
      created_at       TIMESTAMP NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_file_repo ON vertex_hfhub_file (repo_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_file_split ON vertex_hfhub_file (split_vertex_id)`.execute(db);

  // ── vertex_hfhub_filter ──────────────────────────────────────────────────────
  // First-class filter spec entity. Each row defines a reusable filter
  // that the hf.dataset.scan BPMN task applies to populate edge_hfhub_filter_match.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hfhub_filter (
      vertex_id        VARCHAR PRIMARY KEY,   -- 'hf:filter:{slug}'
      _seq             BIGINT,
      created_date     DATE,

      slug             VARCHAR NOT NULL,
      display_name     VARCHAR,
      description      VARCHAR,

      -- Filter criteria (all nullable = "no constraint")
      filter_tags      VARCHAR,               -- JSON array of required tags
      filter_tasks     VARCHAR,               -- JSON array of task categories
      filter_languages VARCHAR,               -- JSON array of BCP-47 lang codes
      filter_license   VARCHAR,               -- SPDX id or null
      min_downloads    BIGINT,
      max_rows         BIGINT,                -- NULL = no limit; otherwise filter_tasks split with num_rows > max_rows
      require_gated    BOOLEAN DEFAULT FALSE,
      exclude_private  BOOLEAN DEFAULT TRUE,

      -- Scan state
      enabled          BOOLEAN DEFAULT TRUE,
      last_run_at      TIMESTAMP,
      match_count      INTEGER DEFAULT 0,

      -- ADR-0095
      actor_did        VARCHAR DEFAULT 'did:web:ingest.etzhayyim.com',
      org_did          VARCHAR,
      at_did           VARCHAR,
      created_at       TIMESTAMP NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_filter_enabled ON vertex_hfhub_filter (enabled)`.execute(db);

  // ── vertex_hfhub_ingest_cursor ───────────────────────────────────────────────
  // Per-split sample export cursor (for future row-level B2 shard export).
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hfhub_ingest_cursor (
      vertex_id         VARCHAR PRIMARY KEY,  -- 'hf:cursor:{repo_id}:{config}:{split}'
      repo_id           VARCHAR NOT NULL,
      config_name       VARCHAR NOT NULL DEFAULT 'default',
      split_name        VARCHAR NOT NULL,
      last_offset       BIGINT DEFAULT 0,
      total_emitted     BIGINT DEFAULT 0,
      last_b2_key       VARCHAR,
      updated_at        TIMESTAMP NOT NULL
    )
  `.execute(db);

  // ── edge_hfhub_dataset_tag ───────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_hfhub_dataset_tag (
      dataset_id       VARCHAR NOT NULL,      -- FK vertex_hfhub_dataset.vertex_id
      tag              VARCHAR NOT NULL,
      PRIMARY KEY (dataset_id, tag)
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_dtag_tag ON edge_hfhub_dataset_tag (tag)`.execute(db);

  // ── edge_hfhub_dataset_task ──────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_hfhub_dataset_task (
      dataset_id       VARCHAR NOT NULL,
      task_category    VARCHAR NOT NULL,
      PRIMARY KEY (dataset_id, task_category)
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_dtask_task ON edge_hfhub_dataset_task (task_category)`.execute(db);

  // ── edge_hfhub_dataset_language ──────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_hfhub_dataset_language (
      dataset_id       VARCHAR NOT NULL,
      lang_code        VARCHAR NOT NULL,
      PRIMARY KEY (dataset_id, lang_code)
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_dlang_lang ON edge_hfhub_dataset_language (lang_code)`.execute(db);

  // ── edge_hfhub_filter_match ──────────────────────────────────────────────────
  // Populated by hf.dataset.scan task when dataset satisfies a filter's criteria.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_hfhub_filter_match (
      filter_id        VARCHAR NOT NULL,      -- FK vertex_hfhub_filter.vertex_id
      dataset_id       VARCHAR NOT NULL,      -- FK vertex_hfhub_dataset.vertex_id
      matched_at       TIMESTAMP NOT NULL,
      PRIMARY KEY (filter_id, dataset_id)
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_fmatch_filter ON edge_hfhub_filter_match (filter_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hfhub_fmatch_dataset ON edge_hfhub_filter_match (dataset_id)`.execute(db);

  // ── edge_hfhub_split_file ────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_hfhub_split_file (
      split_id         VARCHAR NOT NULL,      -- FK vertex_hfhub_split.vertex_id
      file_id          VARCHAR NOT NULL,      -- FK vertex_hfhub_file.vertex_id
      PRIMARY KEY (split_id, file_id)
    )
  `.execute(db);

  // ── Streaming MVs (bounded cardinality only) ──────────────────────────────

  // mv_hfhub_tag_popularity — ~10k rows, bounded by tag diversity on HF Hub
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_tag_popularity AS
    SELECT
      tag,
      COUNT(DISTINCT dataset_id)  AS dataset_count
    FROM edge_hfhub_dataset_tag
    GROUP BY tag
  `.execute(db);

  // mv_hfhub_task_popularity — ~50 rows (HF has ~30-50 task categories)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_task_popularity AS
    SELECT
      task_category,
      COUNT(DISTINCT dataset_id)  AS dataset_count
    FROM edge_hfhub_dataset_task
    GROUP BY task_category
  `.execute(db);

  // mv_hfhub_filter_match_count — bounded by number of vertex_hfhub_filter rows (~100)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_filter_match_count AS
    SELECT
      filter_id,
      COUNT(DISTINCT dataset_id)  AS match_count,
      MAX(matched_at)             AS last_match_at
    FROM edge_hfhub_filter_match
    GROUP BY filter_id
  `.execute(db);

  // mv_hfhub_ingest_progress — bounded by number of cursors (~100s of tracked splits)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_ingest_progress AS
    SELECT
      c.repo_id,
      c.config_name,
      c.split_name,
      c.last_offset,
      c.total_emitted,
      s.num_rows,
      CASE WHEN s.num_rows > 0
           THEN ROUND(100.0 * c.last_offset / s.num_rows, 1)
           ELSE 0
      END                         AS pct_complete,
      c.updated_at
    FROM vertex_hfhub_ingest_cursor c
    LEFT JOIN vertex_hfhub_split s
      ON s.repo_id = c.repo_id
     AND s.config_name = c.config_name
     AND s.split_name  = c.split_name
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const mv of [
    "mv_hfhub_ingest_progress",
    "mv_hfhub_filter_match_count",
    "mv_hfhub_task_popularity",
    "mv_hfhub_tag_popularity",
  ]) {
    await sql`DROP MATERIALIZED VIEW IF EXISTS ${sql.raw(mv)}`.execute(db);
  }
  for (const tbl of [
    "edge_hfhub_split_file",
    "edge_hfhub_filter_match",
    "edge_hfhub_dataset_language",
    "edge_hfhub_dataset_task",
    "edge_hfhub_dataset_tag",
    "vertex_hfhub_ingest_cursor",
    "vertex_hfhub_filter",
    "vertex_hfhub_file",
    "vertex_hfhub_split",
    "vertex_hfhub_dataset",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(tbl)}`.execute(db);
  }
}
