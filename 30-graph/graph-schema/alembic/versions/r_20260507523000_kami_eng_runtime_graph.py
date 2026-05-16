"""Captured from Kysely migration 20260507523000_kami_eng_runtime_graph."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507523000_kami_eng_runtime_graph"
down_revision = 'r_20260507522000_vertex_cohort_evidence'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_kami_eng_eda_schematic" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_eda_schematic_record_id" ON '
         '"vertex_kami_eng_eda_schematic" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_eda_schematic_created" ON '
         '"vertex_kami_eng_eda_schematic" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_eda_schematic_status" ON '
         '"vertex_kami_eng_eda_schematic" (status)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_eda_schematic ADD COLUMN IF NOT EXISTS name VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_eda_schematic ADD COLUMN IF NOT EXISTS sheet_size VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_eda_schematic ADD COLUMN IF NOT EXISTS grid_spacing VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_kami_eng_cad_model" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_cad_model_record_id" ON '
         '"vertex_kami_eng_cad_model" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_cad_model_created" ON '
         '"vertex_kami_eng_cad_model" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_cad_model_status" ON '
         '"vertex_kami_eng_cad_model" (status)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_cad_model ADD COLUMN IF NOT EXISTS name VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_cad_model ADD COLUMN IF NOT EXISTS model_type VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_cad_model ADD COLUMN IF NOT EXISTS unit VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_kami_eng_cad_feature" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_cad_feature_record_id" ON '
         '"vertex_kami_eng_cad_feature" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_cad_feature_created" ON '
         '"vertex_kami_eng_cad_feature" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_cad_feature_status" ON '
         '"vertex_kami_eng_cad_feature" (status)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_cad_feature ADD COLUMN IF NOT EXISTS model_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_cad_feature ADD COLUMN IF NOT EXISTS feature_type VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_cad_feature ADD COLUMN IF NOT EXISTS feature_order DOUBLE '
         'PRECISION',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_kami_eng_cam_job" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_cam_job_record_id" ON '
         '"vertex_kami_eng_cam_job" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_cam_job_created" ON '
         '"vertex_kami_eng_cam_job" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_cam_job_status" ON '
         '"vertex_kami_eng_cam_job" (status)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_cam_job ADD COLUMN IF NOT EXISTS model_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_cam_job ADD COLUMN IF NOT EXISTS machine VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_kami_eng_rtl_module_ref" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_rtl_module_ref_record_id" ON '
         '"vertex_kami_eng_rtl_module_ref" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_rtl_module_ref_created" ON '
         '"vertex_kami_eng_rtl_module_ref" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_rtl_module_ref_status" ON '
         '"vertex_kami_eng_rtl_module_ref" (status)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_rtl_module_ref ADD COLUMN IF NOT EXISTS module_id VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_kami_eng_rtl_simulation" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_rtl_simulation_record_id" ON '
         '"vertex_kami_eng_rtl_simulation" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_rtl_simulation_created" ON '
         '"vertex_kami_eng_rtl_simulation" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_rtl_simulation_status" ON '
         '"vertex_kami_eng_rtl_simulation" (status)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_rtl_simulation ADD COLUMN IF NOT EXISTS module_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_rtl_simulation ADD COLUMN IF NOT EXISTS duration VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_kami_eng_cae_analysis" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_cae_analysis_record_id" ON '
         '"vertex_kami_eng_cae_analysis" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_cae_analysis_created" ON '
         '"vertex_kami_eng_cae_analysis" (created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kami_eng_cae_analysis_status" ON '
         '"vertex_kami_eng_cae_analysis" (status)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_cae_analysis ADD COLUMN IF NOT EXISTS model_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kami_eng_cae_analysis ADD COLUMN IF NOT EXISTS analysis_type VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_kami_eng_cad_model_feature" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kami_eng_cad_model_feature_src" ON '
         '"edge_kami_eng_cad_model_feature" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kami_eng_cad_model_feature_dst" ON '
         '"edge_kami_eng_cad_model_feature" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_kami_eng_cad_model_cam_job" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kami_eng_cad_model_cam_job_src" ON '
         '"edge_kami_eng_cad_model_cam_job" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kami_eng_cad_model_cam_job_dst" ON '
         '"edge_kami_eng_cad_model_cam_job" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_kami_eng_rtl_module_simulation" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kami_eng_rtl_module_simulation_src" ON '
         '"edge_kami_eng_rtl_module_simulation" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kami_eng_rtl_module_simulation_dst" ON '
         '"edge_kami_eng_rtl_module_simulation" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_kami_eng_cad_model_cae_analysis" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kami_eng_cad_model_cae_analysis_src" ON '
         '"edge_kami_eng_cad_model_cae_analysis" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kami_eng_cad_model_cae_analysis_dst" ON '
         '"edge_kami_eng_cad_model_cae_analysis" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_kami_eng_feature_model ON vertex_kami_eng_cad_feature '
         '(model_id, feature_order)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_kami_eng_cam_model ON vertex_kami_eng_cam_job (model_id, '
         'status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_kami_eng_rtl_sim_module ON vertex_kami_eng_rtl_simulation '
         '(module_id, status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_kami_eng_cae_model ON vertex_kami_eng_cae_analysis '
         '(model_id, analysis_type, status)',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kami_eng_workbench_counts', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_kami_eng_workbench_counts AS\n'
         "    SELECT 'eda_schematic' AS workbench_kind, status, count(*)::BIGINT AS record_count "
         'FROM vertex_kami_eng_eda_schematic GROUP BY status\n'
         '    UNION ALL\n'
         "    SELECT 'cad_model', status, count(*)::BIGINT FROM vertex_kami_eng_cad_model GROUP BY "
         'status\n'
         '    UNION ALL\n'
         "    SELECT 'cad_feature', status, count(*)::BIGINT FROM vertex_kami_eng_cad_feature "
         'GROUP BY status\n'
         '    UNION ALL\n'
         "    SELECT 'cam_job', status, count(*)::BIGINT FROM vertex_kami_eng_cam_job GROUP BY "
         'status\n'
         '    UNION ALL\n'
         "    SELECT 'rtl_simulation', status, count(*)::BIGINT FROM "
         'vertex_kami_eng_rtl_simulation GROUP BY status\n'
         '    UNION ALL\n'
         "    SELECT 'cae_analysis', status, count(*)::BIGINT FROM vertex_kami_eng_cae_analysis "
         'GROUP BY status\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kami_eng_workbench_counts', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_kami_eng_cad_model_cae_analysis"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_kami_eng_rtl_module_simulation"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_kami_eng_cad_model_cam_job"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_kami_eng_cad_model_feature"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_kami_eng_cae_analysis"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_kami_eng_rtl_simulation"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_kami_eng_rtl_module_ref"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_kami_eng_cam_job"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_kami_eng_cad_feature"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_kami_eng_cad_model"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_kami_eng_eda_schematic"', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
