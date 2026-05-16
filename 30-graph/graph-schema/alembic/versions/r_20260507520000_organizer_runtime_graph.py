"""Captured from Kysely migration 20260507520000_organizer_runtime_graph."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507520000_organizer_runtime_graph"
down_revision = 'r_20260507519000_kenkyusha_runtime_graph'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_item" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_item_key" ON "vertex_organizer_item" '
         '(record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_item_status" ON "vertex_organizer_item" '
         '(status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_item_org" ON "vertex_organizer_item" '
         '(org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_item_indexed_at" ON '
         '"vertex_organizer_item" (indexed_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS item_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS filename TEXT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS content_type VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS size_bytes DOUBLE PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS blake3 VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS blob_ref TEXT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS vault_did VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_classification" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_classification_key" ON '
         '"vertex_organizer_classification" (record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_classification_status" ON '
         '"vertex_organizer_classification" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_classification_org" ON '
         '"vertex_organizer_classification" (org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_classification_indexed_at" ON '
         '"vertex_organizer_classification" (indexed_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_classification ADD COLUMN IF NOT EXISTS classification_id '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_classification ADD COLUMN IF NOT EXISTS item_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_classification ADD COLUMN IF NOT EXISTS category VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_classification ADD COLUMN IF NOT EXISTS subcategory VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_classification ADD COLUMN IF NOT EXISTS model VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_classification ADD COLUMN IF NOT EXISTS confidence DOUBLE '
         'PRECISION',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_tag" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_tag_key" ON "vertex_organizer_tag" '
         '(record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_tag_status" ON "vertex_organizer_tag" '
         '(status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_tag_org" ON "vertex_organizer_tag" '
         '(org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_tag_indexed_at" ON '
         '"vertex_organizer_tag" (indexed_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_tag ADD COLUMN IF NOT EXISTS tag_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_tag ADD COLUMN IF NOT EXISTS item_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_tag ADD COLUMN IF NOT EXISTS name VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_tag ADD COLUMN IF NOT EXISTS source VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_collection" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_collection_key" ON '
         '"vertex_organizer_collection" (record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_collection_status" ON '
         '"vertex_organizer_collection" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_collection_org" ON '
         '"vertex_organizer_collection" (org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_collection_indexed_at" ON '
         '"vertex_organizer_collection" (indexed_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_collection ADD COLUMN IF NOT EXISTS collection_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_collection ADD COLUMN IF NOT EXISTS name VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_collection ADD COLUMN IF NOT EXISTS description TEXT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_collection ADD COLUMN IF NOT EXISTS visibility VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_rule" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_rule_key" ON "vertex_organizer_rule" '
         '(record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_rule_status" ON "vertex_organizer_rule" '
         '(status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_rule_org" ON "vertex_organizer_rule" '
         '(org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_rule_indexed_at" ON '
         '"vertex_organizer_rule" (indexed_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_rule ADD COLUMN IF NOT EXISTS rule_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_rule ADD COLUMN IF NOT EXISTS condition TEXT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_rule ADD COLUMN IF NOT EXISTS action VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_rule ADD COLUMN IF NOT EXISTS priority DOUBLE PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_rule ADD COLUMN IF NOT EXISTS target_collection_id VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_subscription_item" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_item_key" ON '
         '"vertex_organizer_subscription_item" (record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_item_status" ON '
         '"vertex_organizer_subscription_item" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_item_org" ON '
         '"vertex_organizer_subscription_item" (org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_item_indexed_at" ON '
         '"vertex_organizer_subscription_item" (indexed_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS subscription_id '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS sender VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS service_name '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS amount DOUBLE '
         'PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS currency VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS billing_cycle '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS first_seen_at '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS last_seen_at '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS email_count '
         'BIGINT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_subscription_analysis" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_analysis_key" ON '
         '"vertex_organizer_subscription_analysis" (record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_analysis_status" ON '
         '"vertex_organizer_subscription_analysis" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_analysis_org" ON '
         '"vertex_organizer_subscription_analysis" (org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_analysis_indexed_at" ON '
         '"vertex_organizer_subscription_analysis" (indexed_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS analysis_id '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS '
         'subscription_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS service_name '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS usage_score '
         'DOUBLE PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS '
         'cost_per_month DOUBLE PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS currency '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS '
         'recommendation VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS analyzed_at '
         'VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_item_deletion" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_item_deletion_key" ON '
         '"vertex_organizer_item_deletion" (record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_item_deletion_status" ON '
         '"vertex_organizer_item_deletion" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_item_deletion_org" ON '
         '"vertex_organizer_item_deletion" (org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_item_deletion_indexed_at" ON '
         '"vertex_organizer_item_deletion" (indexed_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_tag_deletion" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_tag_deletion_key" ON '
         '"vertex_organizer_tag_deletion" (record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_tag_deletion_status" ON '
         '"vertex_organizer_tag_deletion" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_tag_deletion_org" ON '
         '"vertex_organizer_tag_deletion" (org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_tag_deletion_indexed_at" ON '
         '"vertex_organizer_tag_deletion" (indexed_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_collection_item_deletion" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_collection_item_deletion_key" ON '
         '"vertex_organizer_collection_item_deletion" (record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_collection_item_deletion_status" ON '
         '"vertex_organizer_collection_item_deletion" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_collection_item_deletion_org" ON '
         '"vertex_organizer_collection_item_deletion" (org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_collection_item_deletion_indexed_at" ON '
         '"vertex_organizer_collection_item_deletion" (indexed_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_rule_deletion" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_rule_deletion_key" ON '
         '"vertex_organizer_rule_deletion" (record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_rule_deletion_status" ON '
         '"vertex_organizer_rule_deletion" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_rule_deletion_org" ON '
         '"vertex_organizer_rule_deletion" (org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_rule_deletion_indexed_at" ON '
         '"vertex_organizer_rule_deletion" (indexed_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_subscription_review_job" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_review_job_key" ON '
         '"vertex_organizer_subscription_review_job" (record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_review_job_status" ON '
         '"vertex_organizer_subscription_review_job" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_review_job_org" ON '
         '"vertex_organizer_subscription_review_job" (org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_review_job_indexed_at" ON '
         '"vertex_organizer_subscription_review_job" (indexed_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_organizer_subscription_item_update" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      indexed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_item_update_key" ON '
         '"vertex_organizer_subscription_item_update" (record_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_item_update_status" ON '
         '"vertex_organizer_subscription_item_update" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_item_update_org" ON '
         '"vertex_organizer_subscription_item_update" (org_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_organizer_subscription_item_update_indexed_at" ON '
         '"vertex_organizer_subscription_item_update" (indexed_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_organizer_item_classification" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_organizer_item_classification_src" ON '
         '"edge_organizer_item_classification" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_organizer_item_classification_dst" ON '
         '"edge_organizer_item_classification" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_organizer_item_tag" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_organizer_item_tag_src" ON '
         '"edge_organizer_item_tag" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_organizer_item_tag_dst" ON '
         '"edge_organizer_item_tag" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_organizer_collection_item" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_organizer_collection_item_src" ON '
         '"edge_organizer_collection_item" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_organizer_collection_item_dst" ON '
         '"edge_organizer_collection_item" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_organizer_rule_collection" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_organizer_rule_collection_src" ON '
         '"edge_organizer_rule_collection" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_organizer_rule_collection_dst" ON '
         '"edge_organizer_rule_collection" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_organizer_subscription_analysis" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_organizer_subscription_analysis_src" ON '
         '"edge_organizer_subscription_analysis" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_organizer_subscription_analysis_dst" ON '
         '"edge_organizer_subscription_analysis" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_organizer_subscription_review_job" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_organizer_subscription_review_job_src" ON '
         '"edge_organizer_subscription_review_job" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_organizer_subscription_review_job_dst" ON '
         '"edge_organizer_subscription_review_job" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_organizer_item_vault ON vertex_organizer_item (org_id, '
         'vault_did, status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_organizer_item_blake3 ON vertex_organizer_item (blake3)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_organizer_classification_category ON '
         'vertex_organizer_classification (org_id, category)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_organizer_tag_item ON vertex_organizer_tag (item_id, '
         'name)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_organizer_collection_visibility ON '
         'vertex_organizer_collection (org_id, visibility)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_organizer_subscription_status ON '
         'vertex_organizer_subscription_item (org_id, status, billing_cycle)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_organizer_subscription_analysis_rec ON '
         'vertex_organizer_subscription_analysis (org_id, recommendation)',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_organizer_item_status_counts', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_organizer_item_status_counts AS\n'
         '    SELECT org_id, vault_did, status, count(*)::BIGINT AS item_count, sum(size_bytes) AS '
         'total_bytes\n'
         '    FROM vertex_organizer_item\n'
         '    GROUP BY org_id, vault_did, status\n'
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_organizer_classification_category_counts',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_organizer_classification_category_counts AS\n'
         '    SELECT org_id, category, subcategory, count(*)::BIGINT AS item_count, '
         'avg(confidence) AS avg_confidence\n'
         '    FROM vertex_organizer_classification\n'
         '    GROUP BY org_id, category, subcategory\n'
         '  ',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_organizer_subscription_monthly_cost',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_organizer_subscription_monthly_cost AS\n'
         '    SELECT org_id, currency, status, count(*)::BIGINT AS subscription_count,\n'
         "      sum(CASE billing_cycle WHEN 'yearly' THEN amount / 12 WHEN 'weekly' THEN amount * "
         '4.33 ELSE amount END) AS monthly_cost\n'
         '    FROM vertex_organizer_subscription_item\n'
         '    GROUP BY org_id, currency, status\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_organizer_subscription_monthly_cost',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_organizer_classification_category_counts',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_organizer_item_status_counts', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_organizer_subscription_review_job"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_organizer_subscription_analysis"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_organizer_rule_collection"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_organizer_collection_item"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_organizer_item_tag"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_organizer_item_classification"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_subscription_item_update"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_subscription_review_job"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_rule_deletion"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_collection_item_deletion"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_tag_deletion"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_item_deletion"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_subscription_analysis"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_subscription_item"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_rule"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_collection"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_tag"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_classification"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_organizer_item"', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
