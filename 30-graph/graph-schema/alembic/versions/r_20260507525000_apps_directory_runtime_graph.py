"""Captured from Kysely migration 20260507525000_apps_directory_runtime_graph."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507525000_apps_directory_runtime_graph"
down_revision = 'r_20260507524000_i18n_runtime_graph'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_apps_directory_listing" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      listing_id VARCHAR,\n'
         '      app_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      category VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_apps_directory_listing_record_id" ON '
         '"vertex_apps_directory_listing" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_apps_directory_listing_listing" ON '
         '"vertex_apps_directory_listing" (listing_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_apps_directory_listing_category" ON '
         '"vertex_apps_directory_listing" (category, created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_listing ADD COLUMN IF NOT EXISTS name VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_listing ADD COLUMN IF NOT EXISTS display_name VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_listing ADD COLUMN IF NOT EXISTS description TEXT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_listing ADD COLUMN IF NOT EXISTS icon VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_listing ADD COLUMN IF NOT EXISTS embed_url TEXT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_apps_directory_feature" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      listing_id VARCHAR,\n'
         '      app_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      category VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_apps_directory_feature_record_id" ON '
         '"vertex_apps_directory_feature" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_apps_directory_feature_listing" ON '
         '"vertex_apps_directory_feature" (listing_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_apps_directory_feature_category" ON '
         '"vertex_apps_directory_feature" (category, created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_feature ADD COLUMN IF NOT EXISTS feature_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_feature ADD COLUMN IF NOT EXISTS rail VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_feature ADD COLUMN IF NOT EXISTS rank BIGINT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_feature ADD COLUMN IF NOT EXISTS approved_by_did '
         'VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_apps_directory_install_intent" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      listing_id VARCHAR,\n'
         '      app_did VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      category VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_apps_directory_install_intent_record_id" ON '
         '"vertex_apps_directory_install_intent" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_apps_directory_install_intent_listing" ON '
         '"vertex_apps_directory_install_intent" (listing_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_apps_directory_install_intent_category" ON '
         '"vertex_apps_directory_install_intent" (category, created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_install_intent ADD COLUMN IF NOT EXISTS intent_id '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_install_intent ADD COLUMN IF NOT EXISTS user_did '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_install_intent ADD COLUMN IF NOT EXISTS source VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_apps_directory_install_intent ADD COLUMN IF NOT EXISTS client VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_apps_directory_listing_feature" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_apps_directory_listing_feature_src" ON '
         '"edge_apps_directory_listing_feature" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_apps_directory_listing_feature_dst" ON '
         '"edge_apps_directory_listing_feature" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_apps_directory_listing_install_intent" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_apps_directory_listing_install_intent_src" ON '
         '"edge_apps_directory_listing_install_intent" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_apps_directory_listing_install_intent_dst" ON '
         '"edge_apps_directory_listing_install_intent" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_apps_directory_listing_app_did ON '
         'vertex_apps_directory_listing (app_did, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_apps_directory_listing_status_category ON '
         'vertex_apps_directory_listing (status, category, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_apps_directory_feature_rail ON '
         'vertex_apps_directory_feature (rail, rank)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_apps_directory_install_user ON '
         'vertex_apps_directory_install_intent (user_did, created_at)',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_apps_directory_category_counts', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_apps_directory_category_counts AS\n'
         '    SELECT category, status, count(*)::BIGINT AS listing_count\n'
         '    FROM vertex_apps_directory_listing\n'
         '    GROUP BY category, status\n'
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_apps_directory_listing_engagement', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_apps_directory_listing_engagement AS\n'
         '    SELECT l.listing_id, l.app_did, l.category,\n'
         '      count(DISTINCT f.vertex_id)::BIGINT AS feature_count,\n'
         '      count(DISTINCT i.vertex_id)::BIGINT AS install_intent_count\n'
         '    FROM vertex_apps_directory_listing l\n'
         '    LEFT JOIN vertex_apps_directory_feature f ON f.listing_id = l.listing_id\n'
         '    LEFT JOIN vertex_apps_directory_install_intent i ON i.listing_id = l.listing_id\n'
         '    GROUP BY l.listing_id, l.app_did, l.category\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_apps_directory_listing_engagement', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_apps_directory_category_counts', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_apps_directory_listing_install_intent"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_apps_directory_listing_feature"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_apps_directory_install_intent"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_apps_directory_feature"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_apps_directory_listing"', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
