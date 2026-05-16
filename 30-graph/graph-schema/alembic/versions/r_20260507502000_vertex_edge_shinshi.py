"""Captured from Kysely migration 20260507502000_vertex_edge_shinshi."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507502000_vertex_edge_shinshi"
down_revision = 'r_20260507501000_vertex_edge_tsukuru'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_shinshi_model_profile (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did VARCHAR,\n'
         '      model_did VARCHAR,\n'
         '      char_name VARCHAR,\n'
         '      series VARCHAR,\n'
         '      age_look BIGINT,\n'
         '      body_type VARCHAR,\n'
         '      ethnicity_look VARCHAR,\n'
         '      language TEXT,\n'
         '      relationship_role VARCHAR,\n'
         '      occupation VARCHAR,\n'
         '      hobbies TEXT,\n'
         '      personality TEXT,\n'
         '      prompt_style TEXT,\n'
         '      external_uri TEXT,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      created_at VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_shinshi_chat_message (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did VARCHAR,\n'
         '      convo_id VARCHAR,\n'
         '      model_did VARCHAR,\n'
         '      user_did VARCHAR,\n'
         '      role VARCHAR,\n'
         '      content TEXT,\n'
         '      in_reply_to VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      created_at VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_shinshi_token_ledger (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did VARCHAR,\n'
         '      user_did VARCHAR,\n'
         '      balance BIGINT,\n'
         '      granted BIGINT,\n'
         '      purchased BIGINT,\n'
         '      spent BIGINT,\n'
         '      free_quota_used BIGINT,\n'
         '      free_quota_reset_at VARCHAR,\n'
         '      tier VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      updated_at VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_shinshi_scene (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      scene_id VARCHAR,\n'
         '      model_did VARCHAR,\n'
         '      user_did VARCHAR,\n'
         '      scene_type VARCHAR,\n'
         '      prompt TEXT,\n'
         '      blob_key TEXT,\n'
         '      post_uri TEXT,\n'
         '      post_cid TEXT,\n'
         '      tokens_spent BIGINT,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR,\n'
         '      owner_did VARCHAR,\n'
         '      sensitivity_ord BIGINT,\n'
         '      created_at VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "edge_shinshi_model_profile" (\n'
         '        edge_id VARCHAR PRIMARY KEY,\n'
         '        edge_key VARCHAR,\n'
         '        src_vid VARCHAR,\n'
         '        dst_vid VARCHAR,\n'
         '        relation VARCHAR,\n'
         '        value_json TEXT,\n'
         '        created_at VARCHAR,\n'
         '        updated_at VARCHAR,\n'
         '        owner_did VARCHAR,\n'
         '        sensitivity_ord BIGINT\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinshi_model_profile_src" ON '
         '"edge_shinshi_model_profile" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinshi_model_profile_dst" ON '
         '"edge_shinshi_model_profile" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinshi_model_profile_relation" ON '
         '"edge_shinshi_model_profile" (relation)',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "edge_shinshi_conversation" (\n'
         '        edge_id VARCHAR PRIMARY KEY,\n'
         '        edge_key VARCHAR,\n'
         '        src_vid VARCHAR,\n'
         '        dst_vid VARCHAR,\n'
         '        relation VARCHAR,\n'
         '        value_json TEXT,\n'
         '        created_at VARCHAR,\n'
         '        updated_at VARCHAR,\n'
         '        owner_did VARCHAR,\n'
         '        sensitivity_ord BIGINT\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinshi_conversation_src" ON '
         '"edge_shinshi_conversation" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinshi_conversation_dst" ON '
         '"edge_shinshi_conversation" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinshi_conversation_relation" ON '
         '"edge_shinshi_conversation" (relation)',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "edge_shinshi_scene_post" (\n'
         '        edge_id VARCHAR PRIMARY KEY,\n'
         '        edge_key VARCHAR,\n'
         '        src_vid VARCHAR,\n'
         '        dst_vid VARCHAR,\n'
         '        relation VARCHAR,\n'
         '        value_json TEXT,\n'
         '        created_at VARCHAR,\n'
         '        updated_at VARCHAR,\n'
         '        owner_did VARCHAR,\n'
         '        sensitivity_ord BIGINT\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinshi_scene_post_src" ON '
         '"edge_shinshi_scene_post" (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinshi_scene_post_dst" ON '
         '"edge_shinshi_scene_post" (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS "idx_edge_shinshi_scene_post_relation" ON '
         '"edge_shinshi_scene_post" (relation)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_shinshi_model_profile_model ON '
         'vertex_shinshi_model_profile (model_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_shinshi_model_profile_series ON '
         'vertex_shinshi_model_profile (series)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_shinshi_chat_convo_created ON vertex_shinshi_chat_message '
         '(convo_id, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_shinshi_chat_model_user ON vertex_shinshi_chat_message '
         '(model_did, user_did)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_shinshi_token_user ON vertex_shinshi_token_ledger '
         '(user_did, updated_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_shinshi_scene_model_created ON vertex_shinshi_scene '
         '(model_did, created_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_shinshi_scene_user_created ON vertex_shinshi_scene '
         '(user_did, created_at)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shinshi_model_activity AS\n'
         '    SELECT\n'
         '      p.model_did,\n'
         '      max(p.char_name) AS char_name,\n'
         '      max(p.series) AS series,\n'
         '      count(DISTINCT c.vertex_id) AS chat_messages,\n'
         '      count(DISTINCT s.vertex_id) AS scenes\n'
         '    FROM vertex_shinshi_model_profile p\n'
         '    LEFT JOIN vertex_shinshi_chat_message c ON c.model_did = p.model_did\n'
         '    LEFT JOIN vertex_shinshi_scene s ON s.model_did = p.model_did\n'
         '    GROUP BY p.model_did\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shinshi_token_liability AS\n'
         '    SELECT\n'
         '      count(*) AS ledger_count,\n'
         '      sum(balance) AS outstanding_balance,\n'
         '      sum(spent) AS total_spent\n'
         '    FROM vertex_shinshi_token_ledger\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_shinshi_token_liability', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_shinshi_model_activity', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_shinshi_scene_post', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_shinshi_conversation', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_shinshi_model_profile', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_shinshi_scene', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_shinshi_token_ledger', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_shinshi_chat_message', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_shinshi_model_profile', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
