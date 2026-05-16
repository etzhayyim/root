"""Captured from Kysely migration 20260507521000_baminiku_runtime_graph."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507521000_baminiku_runtime_graph"
down_revision = 'r_20260507520000_organizer_runtime_graph'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_baminiku_agent_profile" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_agent_profile_record_id" ON '
         '"vertex_baminiku_agent_profile" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_agent_profile_stream" ON '
         '"vertex_baminiku_agent_profile" (stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_agent_profile_agent" ON '
         '"vertex_baminiku_agent_profile" (agent_did)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_agent_profile ADD COLUMN IF NOT EXISTS display_name VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_agent_profile ADD COLUMN IF NOT EXISTS voice_preset VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_agent_profile ADD COLUMN IF NOT EXISTS personality TEXT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_baminiku_stream" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_stream_record_id" ON '
         '"vertex_baminiku_stream" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_stream_stream" ON '
         '"vertex_baminiku_stream" (stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_stream_agent" ON '
         '"vertex_baminiku_stream" (agent_did)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_stream ADD COLUMN IF NOT EXISTS title VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_stream ADD COLUMN IF NOT EXISTS stage_preset VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_stream ADD COLUMN IF NOT EXISTS visibility VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_stream ADD COLUMN IF NOT EXISTS scheduled_at VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_stream ADD COLUMN IF NOT EXISTS knp_room VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_baminiku_stage_patch" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_stage_patch_record_id" ON '
         '"vertex_baminiku_stage_patch" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_stage_patch_stream" ON '
         '"vertex_baminiku_stage_patch" (stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_stage_patch_agent" ON '
         '"vertex_baminiku_stage_patch" (agent_did)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_baminiku_chat" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_chat_record_id" ON '
         '"vertex_baminiku_chat" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_chat_stream" ON "vertex_baminiku_chat" '
         '(stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_chat_agent" ON "vertex_baminiku_chat" '
         '(agent_did)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_chat ADD COLUMN IF NOT EXISTS viewer_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_chat ADD COLUMN IF NOT EXISTS convo_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_chat ADD COLUMN IF NOT EXISTS text TEXT', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_baminiku_tip" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_tip_record_id" ON "vertex_baminiku_tip" '
         '(record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_tip_stream" ON "vertex_baminiku_tip" '
         '(stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_tip_agent" ON "vertex_baminiku_tip" '
         '(agent_did)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_tip ADD COLUMN IF NOT EXISTS viewer_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_tip ADD COLUMN IF NOT EXISTS amount DOUBLE PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_tip ADD COLUMN IF NOT EXISTS currency VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_tip ADD COLUMN IF NOT EXISTS effect_type VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_baminiku_track" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_track_record_id" ON '
         '"vertex_baminiku_track" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_track_stream" ON "vertex_baminiku_track" '
         '(stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_track_agent" ON "vertex_baminiku_track" '
         '(agent_did)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_track ADD COLUMN IF NOT EXISTS title VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_track ADD COLUMN IF NOT EXISTS artist VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_track ADD COLUMN IF NOT EXISTS audio_uri TEXT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_track ADD COLUMN IF NOT EXISTS requested_by_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_track ADD COLUMN IF NOT EXISTS queue_position BIGINT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_baminiku_track_event" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_track_event_record_id" ON '
         '"vertex_baminiku_track_event" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_track_event_stream" ON '
         '"vertex_baminiku_track_event" (stream_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_baminiku_track_event_agent" ON '
         '"vertex_baminiku_track_event" (agent_did)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_track_event ADD COLUMN IF NOT EXISTS skipped_track_id '
         'VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_baminiku_track_event ADD COLUMN IF NOT EXISTS reason TEXT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_baminiku_stream_agent" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_baminiku_stream_agent_src" ON '
         '"edge_baminiku_stream_agent" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_baminiku_stream_agent_dst" ON '
         '"edge_baminiku_stream_agent" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_baminiku_stream_stage_patch" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_baminiku_stream_stage_patch_src" ON '
         '"edge_baminiku_stream_stage_patch" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_baminiku_stream_stage_patch_dst" ON '
         '"edge_baminiku_stream_stage_patch" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_baminiku_stream_chat" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_baminiku_stream_chat_src" ON '
         '"edge_baminiku_stream_chat" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_baminiku_stream_chat_dst" ON '
         '"edge_baminiku_stream_chat" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_baminiku_stream_tip" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_baminiku_stream_tip_src" ON '
         '"edge_baminiku_stream_tip" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_baminiku_stream_tip_dst" ON '
         '"edge_baminiku_stream_tip" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_baminiku_stream_track" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_baminiku_stream_track_src" ON '
         '"edge_baminiku_stream_track" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_baminiku_stream_track_dst" ON '
         '"edge_baminiku_stream_track" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_baminiku_stream_track_event" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_baminiku_stream_track_event_src" ON '
         '"edge_baminiku_stream_track_event" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_baminiku_stream_track_event_dst" ON '
         '"edge_baminiku_stream_track_event" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_baminiku_stream_status ON vertex_baminiku_stream (status, '
         'visibility, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_baminiku_chat_viewer ON vertex_baminiku_chat (viewer_did, '
         'created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_baminiku_tip_viewer ON vertex_baminiku_tip (viewer_did, '
         'created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_baminiku_track_queue ON vertex_baminiku_track (stream_id, '
         'status, queue_position)',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_baminiku_stream_activity_counts', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_baminiku_stream_activity_counts AS\n'
         '    SELECT s.stream_id, s.agent_did, s.status, s.visibility,\n'
         '      count(DISTINCT c.vertex_id)::BIGINT AS chat_count,\n'
         '      count(DISTINCT t.vertex_id)::BIGINT AS tip_count,\n'
         '      coalesce(sum(t.amount), 0) AS tip_amount_total,\n'
         '      count(DISTINCT tr.vertex_id)::BIGINT AS track_count\n'
         '    FROM vertex_baminiku_stream s\n'
         '    LEFT JOIN vertex_baminiku_chat c ON c.stream_id = s.stream_id\n'
         '    LEFT JOIN vertex_baminiku_tip t ON t.stream_id = s.stream_id\n'
         '    LEFT JOIN vertex_baminiku_track tr ON tr.stream_id = s.stream_id\n'
         '    GROUP BY s.stream_id, s.agent_did, s.status, s.visibility\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_baminiku_stream_activity_counts', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_baminiku_stream_track_event"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_baminiku_stream_track"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_baminiku_stream_tip"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_baminiku_stream_chat"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_baminiku_stream_stage_patch"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_baminiku_stream_agent"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_baminiku_track_event"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_baminiku_track"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_baminiku_tip"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_baminiku_chat"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_baminiku_stage_patch"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_baminiku_stream"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_baminiku_agent_profile"', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
