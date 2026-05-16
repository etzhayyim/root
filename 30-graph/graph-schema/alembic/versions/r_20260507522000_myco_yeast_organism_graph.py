"""Captured from Kysely migration 20260507522000_myco_yeast_organism_graph."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507522000_myco_yeast_organism_graph"
down_revision = 'r_20260507521000_baminiku_runtime_graph'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_kobo_agent" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      stream_id VARCHAR,\n'
         '      agent_did VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kobo_agent_record_id" ON "vertex_kobo_agent" '
         '(record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kobo_agent_stream" ON "vertex_kobo_agent" '
         '(stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kobo_agent_agent" ON "vertex_kobo_agent" '
         '(agent_did)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kobo_agent ADD COLUMN IF NOT EXISTS parent_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kobo_agent ADD COLUMN IF NOT EXISTS role VARCHAR', 'parameters': []},
 {'sql': 'ALTER TABLE vertex_kobo_agent ADD COLUMN IF NOT EXISTS eta DOUBLE PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kobo_agent ADD COLUMN IF NOT EXISTS stress_score DOUBLE PRECISION',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_kobo_prion" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      stream_id VARCHAR,\n'
         '      agent_did VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kobo_prion_record_id" ON "vertex_kobo_prion" '
         '(record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kobo_prion_stream" ON "vertex_kobo_prion" '
         '(stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kobo_prion_agent" ON "vertex_kobo_prion" '
         '(agent_did)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kobo_prion ADD COLUMN IF NOT EXISTS pattern_hash VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kobo_prion ADD COLUMN IF NOT EXISTS heritable BOOLEAN',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kobo_prion ADD COLUMN IF NOT EXISTS malignant_score DOUBLE PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kobo_prion ADD COLUMN IF NOT EXISTS content TEXT', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_kobo_budding" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kobo_budding_src" ON "edge_kobo_budding" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kobo_budding_dst" ON "edge_kobo_budding" (dst_vid)',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kobo_budding ADD COLUMN IF NOT EXISTS parent_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kobo_budding ADD COLUMN IF NOT EXISTS child_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kobo_budding ADD COLUMN IF NOT EXISTS budded_at VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kobo_budding ADD COLUMN IF NOT EXISTS prion_count BIGINT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_kabi_hypha" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kabi_hypha_src" ON "edge_kabi_hypha" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kabi_hypha_dst" ON "edge_kabi_hypha" (dst_vid)',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kabi_hypha ADD COLUMN IF NOT EXISTS src_agent_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kabi_hypha ADD COLUMN IF NOT EXISTS dst_agent_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kabi_hypha ADD COLUMN IF NOT EXISTS eta DOUBLE PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kabi_hypha ADD COLUMN IF NOT EXISTS flow DOUBLE PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kabi_hypha ADD COLUMN IF NOT EXISTS pruned_at VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_kabi_anastomosis" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kabi_anastomosis_src" ON "edge_kabi_anastomosis" '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_kabi_anastomosis_dst" ON "edge_kabi_anastomosis" '
         '(dst_vid)',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kabi_anastomosis ADD COLUMN IF NOT EXISTS network_a_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kabi_anastomosis ADD COLUMN IF NOT EXISTS network_b_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kabi_anastomosis ADD COLUMN IF NOT EXISTS compatibility_score DOUBLE '
         'PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kabi_anastomosis ADD COLUMN IF NOT EXISTS result VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_kabi_anastomosis ADD COLUMN IF NOT EXISTS reason TEXT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_kabi_network" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      stream_id VARCHAR,\n'
         '      agent_did VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kabi_network_record_id" ON "vertex_kabi_network" '
         '(record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kabi_network_stream" ON "vertex_kabi_network" '
         '(stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kabi_network_agent" ON "vertex_kabi_network" '
         '(agent_did)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kabi_network ADD COLUMN IF NOT EXISTS root_agent_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kabi_network ADD COLUMN IF NOT EXISTS hypha_count BIGINT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kabi_network ADD COLUMN IF NOT EXISTS total_flow DOUBLE PRECISION',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_kinoko_block" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      stream_id VARCHAR,\n'
         '      agent_did VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kinoko_block_record_id" ON "vertex_kinoko_block" '
         '(record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kinoko_block_stream" ON "vertex_kinoko_block" '
         '(stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_kinoko_block_agent" ON "vertex_kinoko_block" '
         '(agent_did)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kinoko_block ADD COLUMN IF NOT EXISTS prev_block_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kinoko_block ADD COLUMN IF NOT EXISTS block_hash VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kinoko_block ADD COLUMN IF NOT EXISTS total_flow DOUBLE PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kinoko_block ADD COLUMN IF NOT EXISTS participant_count BIGINT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kinoko_block ADD COLUMN IF NOT EXISTS eta_min_used DOUBLE PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_kinoko_block ADD COLUMN IF NOT EXISTS block_status VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_houshi_spore" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      stream_id VARCHAR,\n'
         '      agent_did VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_houshi_spore_record_id" ON "vertex_houshi_spore" '
         '(record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_houshi_spore_stream" ON "vertex_houshi_spore" '
         '(stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_houshi_spore_agent" ON "vertex_houshi_spore" '
         '(agent_did)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_houshi_spore ADD COLUMN IF NOT EXISTS origin_agent_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_houshi_spore ADD COLUMN IF NOT EXISTS blob_cbor TEXT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_houshi_spore ADD COLUMN IF NOT EXISTS revival_key_hint VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_houshi_spore ADD COLUMN IF NOT EXISTS quorum_n BIGINT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_houshi_spore ADD COLUMN IF NOT EXISTS germinated_at VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_houshi_custody" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_houshi_custody_src" ON "edge_houshi_custody" '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_houshi_custody_dst" ON "edge_houshi_custody" '
         '(dst_vid)',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_houshi_custody ADD COLUMN IF NOT EXISTS custodian_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE edge_houshi_custody ADD COLUMN IF NOT EXISTS custody_confirmed BOOLEAN',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_hakkou_ferment" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      stream_id VARCHAR,\n'
         '      agent_did VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_hakkou_ferment_record_id" ON '
         '"vertex_hakkou_ferment" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_hakkou_ferment_stream" ON "vertex_hakkou_ferment" '
         '(stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_hakkou_ferment_agent" ON "vertex_hakkou_ferment" '
         '(agent_did)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_hakkou_ferment ADD COLUMN IF NOT EXISTS input_kind VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_hakkou_ferment ADD COLUMN IF NOT EXISTS input_ref TEXT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_hakkou_ferment ADD COLUMN IF NOT EXISTS output_vertex_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_hakkou_ferment ADD COLUMN IF NOT EXISTS output_kind VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_hakkou_ferment ADD COLUMN IF NOT EXISTS ethanol_hash VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_hakkou_ferment ADD COLUMN IF NOT EXISTS co2_audit_ref TEXT',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_kobo_agent_parent ON vertex_kobo_agent (parent_did, '
         'created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_kobo_agent_eta ON vertex_kobo_agent (eta, status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_kobo_prion_pattern ON vertex_kobo_prion (pattern_hash, '
         'heritable)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_kabi_hypha_flow ON edge_kabi_hypha (src_agent_did, '
         'dst_agent_did, pruned_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_kabi_anastomosis_result ON edge_kabi_anastomosis (result, '
         'created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_kinoko_block_chain ON vertex_kinoko_block (prev_block_id, '
         'block_status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_houshi_spore_origin ON vertex_houshi_spore '
         '(origin_agent_did, germinated_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_hakkou_ferment_input ON vertex_hakkou_ferment (agent_did, '
         'input_kind, created_at)',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kabi_nutrient_flow', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_kabi_nutrient_flow AS\n'
         '    SELECT\n'
         '      src_agent_did,\n'
         '      dst_agent_did,\n'
         '      COUNT(*)::BIGINT AS hypha_count,\n'
         '      SUM(flow) AS total_flow,\n'
         '      AVG(eta) AS avg_eta\n'
         '    FROM edge_kabi_hypha\n'
         '    WHERE pruned_at IS NULL\n'
         '    GROUP BY src_agent_did, dst_agent_did\n'
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kabi_eta_gradient', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_kabi_eta_gradient AS\n'
         '    SELECT\n'
         '      dst_agent_did AS agent_did,\n'
         '      COUNT(*)::BIGINT AS inbound_count,\n'
         '      SUM(flow) AS inbound_flow,\n'
         '      AVG(eta) AS inbound_eta_avg,\n'
         '      MAX(eta) AS inbound_eta_max\n'
         '    FROM edge_kabi_hypha\n'
         '    WHERE pruned_at IS NULL\n'
         '    GROUP BY dst_agent_did\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kabi_eta_gradient', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_kabi_nutrient_flow', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_hakkou_ferment"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_houshi_custody"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_houshi_spore"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_kinoko_block"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_kabi_network"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_kabi_anastomosis"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_kabi_hypha"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_kobo_budding"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_kobo_prion"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_kobo_agent"', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
