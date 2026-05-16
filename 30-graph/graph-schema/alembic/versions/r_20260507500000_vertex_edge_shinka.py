"""Captured from Kysely migration 20260507500000_vertex_edge_shinka."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507500000_vertex_edge_shinka"
down_revision = 'r_20260507491000_vertex_yorishiro_enaiyo_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_shinka_timeline" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_timeline_key" ON "vertex_shinka_timeline" '
         '(vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_timeline_status" ON '
         '"vertex_shinka_timeline" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_timeline_indexed_at" ON '
         '"vertex_shinka_timeline" (indexed_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_timeline_actor" ON '
         '"vertex_shinka_timeline" (actor_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_shinka_historical_event" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_historical_event_key" ON '
         '"vertex_shinka_historical_event" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_historical_event_status" ON '
         '"vertex_shinka_historical_event" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_historical_event_indexed_at" ON '
         '"vertex_shinka_historical_event" (indexed_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_historical_event_actor" ON '
         '"vertex_shinka_historical_event" (actor_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_shinka_propagation_event" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_propagation_event_key" ON '
         '"vertex_shinka_propagation_event" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_propagation_event_status" ON '
         '"vertex_shinka_propagation_event" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_propagation_event_indexed_at" ON '
         '"vertex_shinka_propagation_event" (indexed_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_propagation_event_actor" ON '
         '"vertex_shinka_propagation_event" (actor_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_shinka_propagation_job" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_propagation_job_key" ON '
         '"vertex_shinka_propagation_job" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_propagation_job_status" ON '
         '"vertex_shinka_propagation_job" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_propagation_job_indexed_at" ON '
         '"vertex_shinka_propagation_job" (indexed_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_propagation_job_actor" ON '
         '"vertex_shinka_propagation_job" (actor_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_shinka_evolution_run" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_evolution_run_key" ON '
         '"vertex_shinka_evolution_run" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_evolution_run_status" ON '
         '"vertex_shinka_evolution_run" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_evolution_run_indexed_at" ON '
         '"vertex_shinka_evolution_run" (indexed_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_evolution_run_actor" ON '
         '"vertex_shinka_evolution_run" (actor_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_shinka_kyumei_result" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_kyumei_result_key" ON '
         '"vertex_shinka_kyumei_result" (vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_kyumei_result_status" ON '
         '"vertex_shinka_kyumei_result" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_kyumei_result_indexed_at" ON '
         '"vertex_shinka_kyumei_result" (indexed_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_kyumei_result_actor" ON '
         '"vertex_shinka_kyumei_result" (actor_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_shinka_coverage" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      vertex_key VARCHAR,\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_coverage_key" ON "vertex_shinka_coverage" '
         '(vertex_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_coverage_status" ON '
         '"vertex_shinka_coverage" (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_coverage_indexed_at" ON '
         '"vertex_shinka_coverage" (indexed_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_shinka_coverage_actor" ON '
         '"vertex_shinka_coverage" (actor_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_shinka_heard_from" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      edge_key VARCHAR,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      relation VARCHAR,\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_heard_from_key" ON "edge_shinka_heard_from" '
         '(edge_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_heard_from_src" ON "edge_shinka_heard_from" '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_heard_from_dst" ON "edge_shinka_heard_from" '
         '(dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_heard_from_relation" ON '
         '"edge_shinka_heard_from" (relation)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_heard_from_indexed_at" ON '
         '"edge_shinka_heard_from" (indexed_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_shinka_mention" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      edge_key VARCHAR,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      relation VARCHAR,\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_mention_key" ON "edge_shinka_mention" '
         '(edge_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_mention_src" ON "edge_shinka_mention" '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_mention_dst" ON "edge_shinka_mention" '
         '(dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_mention_relation" ON "edge_shinka_mention" '
         '(relation)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_mention_indexed_at" ON "edge_shinka_mention" '
         '(indexed_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_shinka_knowledge" (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      edge_key VARCHAR,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      relation VARCHAR,\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_knowledge_key" ON "edge_shinka_knowledge" '
         '(edge_key)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_knowledge_src" ON "edge_shinka_knowledge" '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_knowledge_dst" ON "edge_shinka_knowledge" '
         '(dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_knowledge_relation" ON '
         '"edge_shinka_knowledge" (relation)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinka_knowledge_indexed_at" ON '
         '"edge_shinka_knowledge" (indexed_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_vertex_shinka_job_status_schedule\n'
         '      ON vertex_shinka_propagation_job (status, indexed_at)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_vertex_shinka_event_time\n'
         '      ON vertex_shinka_propagation_event (created_at)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shinka_propagation_queue_stats AS\n'
         '    SELECT status, count(*) AS cnt\n'
         '    FROM vertex_shinka_propagation_job\n'
         '    GROUP BY status\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shinka_knowledge_degree AS\n'
         '    SELECT src_vid AS actor_did, count(*) AS out_degree\n'
         '    FROM edge_shinka_knowledge\n'
         '    GROUP BY src_vid\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_shinka_knowledge_degree', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_shinka_propagation_queue_stats', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_shinka_knowledge"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_shinka_mention"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_shinka_heard_from"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_shinka_coverage"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_shinka_kyumei_result"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_shinka_evolution_run"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_shinka_propagation_job"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_shinka_propagation_event"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_shinka_historical_event"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_shinka_timeline"', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
