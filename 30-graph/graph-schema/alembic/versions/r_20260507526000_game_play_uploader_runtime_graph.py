"""Captured from Kysely migration 20260507526000_game_play_uploader_runtime_graph."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507526000_game_play_uploader_runtime_graph"
down_revision = 'r_20260507526000_agent_development_document_graph'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_game_play_participant" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      participant_did VARCHAR,\n'
         '      session_id VARCHAR,\n'
         '      upload_id VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_participant_record_id" ON '
         '"vertex_game_play_participant" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_participant_participant" ON '
         '"vertex_game_play_participant" (participant_did, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_participant_session" ON '
         '"vertex_game_play_participant" (session_id, created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_participant ADD COLUMN IF NOT EXISTS participant_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_participant ADD COLUMN IF NOT EXISTS display_name VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_participant ADD COLUMN IF NOT EXISTS age_band VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_participant ADD COLUMN IF NOT EXISTS payout_handle VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_game_play_upload_session" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      participant_did VARCHAR,\n'
         '      session_id VARCHAR,\n'
         '      upload_id VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_upload_session_record_id" ON '
         '"vertex_game_play_upload_session" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_upload_session_participant" ON '
         '"vertex_game_play_upload_session" (participant_did, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_upload_session_session" ON '
         '"vertex_game_play_upload_session" (session_id, created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_upload_session ADD COLUMN IF NOT EXISTS game_title VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_upload_session ADD COLUMN IF NOT EXISTS platform VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_upload_session ADD COLUMN IF NOT EXISTS duration_sec BIGINT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_upload_session ADD COLUMN IF NOT EXISTS capture_started_at '
         'VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_game_play_upload" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      participant_did VARCHAR,\n'
         '      session_id VARCHAR,\n'
         '      upload_id VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_upload_record_id" ON '
         '"vertex_game_play_upload" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_upload_participant" ON '
         '"vertex_game_play_upload" (participant_did, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_upload_session" ON '
         '"vertex_game_play_upload" (session_id, created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_upload ADD COLUMN IF NOT EXISTS object_uri TEXT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_upload ADD COLUMN IF NOT EXISTS duration_sec BIGINT',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_upload ADD COLUMN IF NOT EXISTS sha256 VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_game_play_review" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      participant_did VARCHAR,\n'
         '      session_id VARCHAR,\n'
         '      upload_id VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_review_record_id" ON '
         '"vertex_game_play_review" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_review_participant" ON '
         '"vertex_game_play_review" (participant_did, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_review_session" ON '
         '"vertex_game_play_review" (session_id, created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_review ADD COLUMN IF NOT EXISTS review_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_review ADD COLUMN IF NOT EXISTS decision VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_review ADD COLUMN IF NOT EXISTS reviewer_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_review ADD COLUMN IF NOT EXISTS quality_score DOUBLE '
         'PRECISION',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_review ADD COLUMN IF NOT EXISTS reward_estimate_jpy BIGINT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "vertex_game_play_reward" (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      participant_did VARCHAR,\n'
         '      session_id VARCHAR,\n'
         '      upload_id VARCHAR,\n'
         '      label VARCHAR,\n'
         '      status VARCHAR,\n'
         '      value_json TEXT,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR,\n'
         '      sensitivity_ord BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_reward_record_id" ON '
         '"vertex_game_play_reward" (record_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_reward_participant" ON '
         '"vertex_game_play_reward" (participant_did, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_vertex_game_play_reward_session" ON '
         '"vertex_game_play_reward" (session_id, created_at)',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_game_play_reward ADD COLUMN IF NOT EXISTS reward_jpy BIGINT',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_game_play_participant_session" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_game_play_participant_session_src" ON '
         '"edge_game_play_participant_session" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_game_play_participant_session_dst" ON '
         '"edge_game_play_participant_session" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_game_play_session_upload" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_game_play_session_upload_src" ON '
         '"edge_game_play_session_upload" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_game_play_session_upload_dst" ON '
         '"edge_game_play_session_upload" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_game_play_upload_review" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_game_play_upload_review_src" ON '
         '"edge_game_play_upload_review" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_game_play_upload_review_dst" ON '
         '"edge_game_play_upload_review" (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS "edge_game_play_upload_reward" (\n'
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
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_game_play_upload_reward_src" ON '
         '"edge_game_play_upload_reward" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_game_play_upload_reward_dst" ON '
         '"edge_game_play_upload_reward" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_game_play_participant_did ON vertex_game_play_participant '
         '(participant_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_game_play_upload_status ON vertex_game_play_upload '
         '(status, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_game_play_review_upload_decision ON '
         'vertex_game_play_review (upload_id, decision)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_game_play_reward_upload ON vertex_game_play_reward '
         '(upload_id, status)',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_game_play_campaign_status', 'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW mv_game_play_campaign_status AS\n'
         '    SELECT\n'
         '      count(DISTINCT p.vertex_id)::BIGINT AS participant_count,\n'
         '      count(DISTINCT u.vertex_id)::BIGINT AS upload_count,\n'
         "      coalesce(sum(CASE WHEN r.decision = 'approved' THEN u.duration_sec ELSE 0 END), "
         '0)::BIGINT AS approved_duration_sec,\n'
         '      coalesce(sum(rew.reward_jpy), 0)::BIGINT AS reward_jpy\n'
         '    FROM vertex_game_play_participant p\n'
         '    LEFT JOIN vertex_game_play_upload_session s ON s.participant_did = '
         'p.participant_did\n'
         '    LEFT JOIN vertex_game_play_upload u ON u.session_id = s.session_id\n'
         '    LEFT JOIN vertex_game_play_review r ON r.upload_id = u.upload_id\n'
         '    LEFT JOIN vertex_game_play_reward rew ON rew.upload_id = u.upload_id\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_game_play_campaign_status', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_game_play_upload_reward"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_game_play_upload_review"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_game_play_session_upload"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "edge_game_play_participant_session"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_game_play_reward"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_game_play_review"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_game_play_upload"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_game_play_upload_session"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_game_play_participant"', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
