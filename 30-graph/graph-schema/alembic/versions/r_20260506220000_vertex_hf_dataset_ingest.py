"""Captured from Kysely migration 20260506220000_vertex_hf_dataset_ingest."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506220000_vertex_hf_dataset_ingest"
down_revision = 'r_20260506210000_vertex_malak_agency_referral_review'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hfhub_dataset (\n'
         "      vertex_id        VARCHAR PRIMARY KEY,   -- 'hf:dataset:{repo_id}'\n"
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '\n'
         '      repo_id          VARCHAR NOT NULL,      -- e.g. "squad", "etzhayyim/etzhayyim-corpus"\n'
         '      author           VARCHAR,               -- org or user handle\n'
         '      sha              VARCHAR,               -- latest commit sha\n'
         '\n'
         '      -- Catalog attrs\n'
         '      license          VARCHAR,\n'
         "      size_category    VARCHAR,               -- 'n<1K' | '1K<n<10K' | ... | '100K<n<1M' "
         "| '1M<n<10M' | 'n>10M'\n"
         '      downloads_month  BIGINT DEFAULT 0,\n'
         '      likes            INTEGER DEFAULT 0,\n'
         '      gated            BOOLEAN DEFAULT FALSE,\n'
         '      disabled         BOOLEAN DEFAULT FALSE,\n'
         '      private          BOOLEAN DEFAULT FALSE,\n'
         '\n'
         '      -- Card content (first 4KB of README)\n'
         '      description      VARCHAR,\n'
         '      card_data        VARCHAR,               -- JSON blob of DatasetCardData fields\n'
         '\n'
         '      -- Ingest lifecycle\n'
         "      status           VARCHAR DEFAULT 'pending',  -- pending | active | error | "
         'archived\n'
         '      last_scanned_at  TIMESTAMP,\n'
         '      error_message    VARCHAR,\n'
         '\n'
         '      -- ADR-0095 canonical columns\n'
         "      actor_did        VARCHAR DEFAULT 'did:web:ingest.etzhayyim.com',\n"
         '      org_did          VARCHAR,\n'
         '      at_did           VARCHAR,\n'
         '      created_at       TIMESTAMP NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_dataset_author ON vertex_hfhub_dataset (author)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_dataset_status ON vertex_hfhub_dataset (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_dataset_downloads ON vertex_hfhub_dataset '
         '(downloads_month DESC)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_dataset_scanned ON vertex_hfhub_dataset '
         '(last_scanned_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hfhub_split (\n'
         "      vertex_id        VARCHAR PRIMARY KEY,   -- 'hf:split:{repo_id}:{config}:{split}'\n"
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '\n'
         '      repo_id          VARCHAR NOT NULL,\n'
         "      config_name      VARCHAR NOT NULL DEFAULT 'default',\n"
         '      split_name       VARCHAR NOT NULL,      -- train | validation | test\n'
         '\n'
         '      num_rows         BIGINT,\n'
         '      num_bytes        BIGINT,\n'
         '      num_files        INTEGER DEFAULT 0,\n'
         '      features_json    VARCHAR,               -- column schema as JSON string\n'
         '\n'
         '      -- ADR-0095\n'
         "      actor_did        VARCHAR DEFAULT 'did:web:ingest.etzhayyim.com',\n"
         '      org_did          VARCHAR,\n'
         '      at_did           VARCHAR,\n'
         '      created_at       TIMESTAMP NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_split_repo ON vertex_hfhub_split (repo_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_split_name ON vertex_hfhub_split (split_name)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hfhub_file (\n'
         "      vertex_id        VARCHAR PRIMARY KEY,   -- 'hf:file:{repo_id}@{sha}:{path}'\n"
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '\n'
         '      repo_id          VARCHAR NOT NULL,\n'
         '      split_vertex_id  VARCHAR,               -- FK vertex_hfhub_split.vertex_id\n'
         '      file_path        VARCHAR NOT NULL,      -- relative path inside repo\n'
         "      file_format      VARCHAR DEFAULT 'parquet',\n"
         '      file_size        BIGINT,\n'
         '      blob_url         VARCHAR,               -- '
         'https://huggingface.co/datasets/{repo_id}/resolve/main/{path}\n'
         '\n'
         '      -- ADR-0095\n'
         "      actor_did        VARCHAR DEFAULT 'did:web:ingest.etzhayyim.com',\n"
         '      org_did          VARCHAR,\n'
         '      at_did           VARCHAR,\n'
         '      created_at       TIMESTAMP NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_file_repo ON vertex_hfhub_file (repo_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_file_split ON vertex_hfhub_file (split_vertex_id)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hfhub_filter (\n'
         "      vertex_id        VARCHAR PRIMARY KEY,   -- 'hf:filter:{slug}'\n"
         '      _seq             BIGINT,\n'
         '      created_date     DATE,\n'
         '\n'
         '      slug             VARCHAR NOT NULL,\n'
         '      display_name     VARCHAR,\n'
         '      description      VARCHAR,\n'
         '\n'
         '      -- Filter criteria (all nullable = "no constraint")\n'
         '      filter_tags      VARCHAR,               -- JSON array of required tags\n'
         '      filter_tasks     VARCHAR,               -- JSON array of task categories\n'
         '      filter_languages VARCHAR,               -- JSON array of BCP-47 lang codes\n'
         '      filter_license   VARCHAR,               -- SPDX id or null\n'
         '      min_downloads    BIGINT,\n'
         '      max_rows         BIGINT,                -- NULL = no limit; otherwise filter_tasks '
         'split with num_rows > max_rows\n'
         '      require_gated    BOOLEAN DEFAULT FALSE,\n'
         '      exclude_private  BOOLEAN DEFAULT TRUE,\n'
         '\n'
         '      -- Scan state\n'
         '      enabled          BOOLEAN DEFAULT TRUE,\n'
         '      last_run_at      TIMESTAMP,\n'
         '      match_count      INTEGER DEFAULT 0,\n'
         '\n'
         '      -- ADR-0095\n'
         "      actor_did        VARCHAR DEFAULT 'did:web:ingest.etzhayyim.com',\n"
         '      org_did          VARCHAR,\n'
         '      at_did           VARCHAR,\n'
         '      created_at       TIMESTAMP NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_filter_enabled ON vertex_hfhub_filter (enabled)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_hfhub_ingest_cursor (\n'
         "      vertex_id         VARCHAR PRIMARY KEY,  -- 'hf:cursor:{repo_id}:{config}:{split}'\n"
         '      repo_id           VARCHAR NOT NULL,\n'
         "      config_name       VARCHAR NOT NULL DEFAULT 'default',\n"
         '      split_name        VARCHAR NOT NULL,\n'
         '      last_offset       BIGINT DEFAULT 0,\n'
         '      total_emitted     BIGINT DEFAULT 0,\n'
         '      last_b2_key       VARCHAR,\n'
         '      updated_at        TIMESTAMP NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_hfhub_dataset_tag (\n'
         '      dataset_id       VARCHAR NOT NULL,      -- FK vertex_hfhub_dataset.vertex_id\n'
         '      tag              VARCHAR NOT NULL,\n'
         '      PRIMARY KEY (dataset_id, tag)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_dtag_tag ON edge_hfhub_dataset_tag (tag)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_hfhub_dataset_task (\n'
         '      dataset_id       VARCHAR NOT NULL,\n'
         '      task_category    VARCHAR NOT NULL,\n'
         '      PRIMARY KEY (dataset_id, task_category)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_dtask_task ON edge_hfhub_dataset_task '
         '(task_category)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_hfhub_dataset_language (\n'
         '      dataset_id       VARCHAR NOT NULL,\n'
         '      lang_code        VARCHAR NOT NULL,\n'
         '      PRIMARY KEY (dataset_id, lang_code)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_dlang_lang ON edge_hfhub_dataset_language '
         '(lang_code)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_hfhub_filter_match (\n'
         '      filter_id        VARCHAR NOT NULL,      -- FK vertex_hfhub_filter.vertex_id\n'
         '      dataset_id       VARCHAR NOT NULL,      -- FK vertex_hfhub_dataset.vertex_id\n'
         '      matched_at       TIMESTAMP NOT NULL,\n'
         '      PRIMARY KEY (filter_id, dataset_id)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_fmatch_filter ON edge_hfhub_filter_match '
         '(filter_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hfhub_fmatch_dataset ON edge_hfhub_filter_match '
         '(dataset_id)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_hfhub_split_file (\n'
         '      split_id         VARCHAR NOT NULL,      -- FK vertex_hfhub_split.vertex_id\n'
         '      file_id          VARCHAR NOT NULL,      -- FK vertex_hfhub_file.vertex_id\n'
         '      PRIMARY KEY (split_id, file_id)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_tag_popularity AS\n'
         '    SELECT\n'
         '      tag,\n'
         '      COUNT(DISTINCT dataset_id)  AS dataset_count\n'
         '    FROM edge_hfhub_dataset_tag\n'
         '    GROUP BY tag\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_task_popularity AS\n'
         '    SELECT\n'
         '      task_category,\n'
         '      COUNT(DISTINCT dataset_id)  AS dataset_count\n'
         '    FROM edge_hfhub_dataset_task\n'
         '    GROUP BY task_category\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_filter_match_count AS\n'
         '    SELECT\n'
         '      filter_id,\n'
         '      COUNT(DISTINCT dataset_id)  AS match_count,\n'
         '      MAX(matched_at)             AS last_match_at\n'
         '    FROM edge_hfhub_filter_match\n'
         '    GROUP BY filter_id\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hfhub_ingest_progress AS\n'
         '    SELECT\n'
         '      c.repo_id,\n'
         '      c.config_name,\n'
         '      c.split_name,\n'
         '      c.last_offset,\n'
         '      c.total_emitted,\n'
         '      s.num_rows,\n'
         '      CASE WHEN s.num_rows > 0\n'
         '           THEN ROUND(100.0 * c.last_offset / s.num_rows, 1)\n'
         '           ELSE 0\n'
         '      END                         AS pct_complete,\n'
         '      c.updated_at\n'
         '    FROM vertex_hfhub_ingest_cursor c\n'
         '    LEFT JOIN vertex_hfhub_split s\n'
         '      ON s.repo_id = c.repo_id\n'
         '     AND s.config_name = c.config_name\n'
         '     AND s.split_name  = c.split_name\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_hfhub_ingest_progress', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_hfhub_filter_match_count', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_hfhub_task_popularity', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_hfhub_tag_popularity', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_hfhub_split_file', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_hfhub_filter_match', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_hfhub_dataset_language', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_hfhub_dataset_task', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_hfhub_dataset_tag', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hfhub_ingest_cursor', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hfhub_filter', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hfhub_file', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hfhub_split', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_hfhub_dataset', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
