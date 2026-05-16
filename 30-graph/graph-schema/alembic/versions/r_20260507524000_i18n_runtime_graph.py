"""Captured from Kysely migration 20260507524000_i18n_runtime_graph."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507524000_i18n_runtime_graph"
down_revision = 'r_20260507523000_kami_eng_runtime_graph'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_i18n_project" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_i18n_project_record_id" ON "vertex_i18n_project" '
         '(record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_i18n_project_created" ON "vertex_i18n_project" '
         '(created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_project ADD COLUMN IF NOT EXISTS project_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_project ADD COLUMN IF NOT EXISTS project_path TEXT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_project ADD COLUMN IF NOT EXISTS total_keys BIGINT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_i18n_project_translation" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_i18n_project_translation_record_id" ON '
         '"vertex_i18n_project_translation" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_i18n_project_translation_created" ON '
         '"vertex_i18n_project_translation" (created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_project_translation ADD COLUMN IF NOT EXISTS project_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_project_translation ADD COLUMN IF NOT EXISTS lang VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_project_translation ADD COLUMN IF NOT EXISTS message_count '
         'BIGINT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_i18n_translation_memory" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_i18n_translation_memory_record_id" ON '
         '"vertex_i18n_translation_memory" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_i18n_translation_memory_created" ON '
         '"vertex_i18n_translation_memory" (created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_translation_memory ADD COLUMN IF NOT EXISTS source_hash VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_translation_memory ADD COLUMN IF NOT EXISTS source_lang VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_translation_memory ADD COLUMN IF NOT EXISTS target_lang VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_translation_memory ADD COLUMN IF NOT EXISTS quality_score DOUBLE '
         'PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_translation_memory ADD COLUMN IF NOT EXISTS source VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_i18n_text_node" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_i18n_text_node_record_id" ON '
         '"vertex_i18n_text_node" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_i18n_text_node_created" ON '
         '"vertex_i18n_text_node" (created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_text_node ADD COLUMN IF NOT EXISTS node_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_text_node ADD COLUMN IF NOT EXISTS node_kind VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_text_node ADD COLUMN IF NOT EXISTS lang VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_text_node ADD COLUMN IF NOT EXISTS text_value TEXT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_i18n_credit_job" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_i18n_credit_job_record_id" ON '
         '"vertex_i18n_credit_job" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_i18n_credit_job_created" ON '
         '"vertex_i18n_credit_job" (created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_credit_job ADD COLUMN IF NOT EXISTS job_kind VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_credit_job ADD COLUMN IF NOT EXISTS credit_estimate BIGINT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_i18n_credit_job ADD COLUMN IF NOT EXISTS workload_units BIGINT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_i18n_project_translation" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      src_vid VARCHAR NOT NULL,\n'
         '      dst_vid VARCHAR NOT NULL,\n'
         '      relation_kind VARCHAR NOT NULL,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_i18n_project_translation_src" ON '
         '"edge_i18n_project_translation" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_i18n_project_translation_dst" ON '
         '"edge_i18n_project_translation" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_i18n_translation_text" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      src_vid VARCHAR NOT NULL,\n'
         '      dst_vid VARCHAR NOT NULL,\n'
         '      relation_kind VARCHAR NOT NULL,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_i18n_translation_text_src" ON '
         '"edge_i18n_translation_text" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_i18n_translation_text_dst" ON '
         '"edge_i18n_translation_text" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_i18n_text_language" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      src_vid VARCHAR NOT NULL,\n'
         '      dst_vid VARCHAR NOT NULL,\n'
         '      relation_kind VARCHAR NOT NULL,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_i18n_text_language_src" ON '
         '"edge_i18n_text_language" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_i18n_text_language_dst" ON '
         '"edge_i18n_text_language" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_i18n_project_id ON vertex_i18n_project (project_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_i18n_project_translation_project_lang ON '
         'vertex_i18n_project_translation (project_id, lang)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_i18n_tm_lookup ON vertex_i18n_translation_memory '
         '(source_hash, target_lang, updated_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_i18n_text_lang ON vertex_i18n_text_node (lang, node_kind)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_i18n_credit_job_status ON vertex_i18n_credit_job (status, '
         'job_kind)',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_i18n_project_translation_coverage', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_i18n_project_translation_coverage AS\n'
         '    SELECT p.project_id, p.total_keys, t.lang, t.message_count\n'
         '    FROM vertex_i18n_project p\n'
         '    LEFT JOIN vertex_i18n_project_translation t ON t.project_id = p.project_id\n'
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_i18n_tm_quality_by_lang', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_i18n_tm_quality_by_lang AS\n'
         '    SELECT source_lang, target_lang, source, count(*)::BIGINT AS entry_count, '
         'avg(quality_score) AS avg_quality_score\n'
         '    FROM vertex_i18n_translation_memory\n'
         '    GROUP BY source_lang, target_lang, source\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_i18n_tm_quality_by_lang', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_i18n_project_translation_coverage', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_i18n_text_language"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_i18n_translation_text"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_i18n_project_translation"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_i18n_credit_job"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_i18n_text_node"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_i18n_translation_memory"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_i18n_project_translation"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_i18n_project"', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
