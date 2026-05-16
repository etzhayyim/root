"""Captured from Kysely migration 20260429213000_gworkspace_lite_zeebe_support."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429213000_gworkspace_lite_zeebe_support"
down_revision = 'r_20260429212000_seed_animeka_appview_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "vertex_gtasks_oauth_token" (\n'
         '        vertex_id VARCHAR PRIMARY KEY,\n'
         '        account_did VARCHAR,\n'
         '        email VARCHAR,\n'
         '        encrypted_refresh_token VARCHAR,\n'
         '        wrapped_data_key VARCHAR,\n'
         '        iv VARCHAR,\n'
         '        scope VARCHAR,\n'
         '        access_token_cache VARCHAR,\n'
         '        access_expires_at BIGINT,\n'
         '        status VARCHAR,\n'
         '        cursor VARCHAR,\n'
         '        history_id VARCHAR,\n'
         '        last_sync_at VARCHAR,\n'
         '        created_at VARCHAR,\n'
         '        updated_at VARCHAR,\n'
         '        actor_did VARCHAR,\n'
         '        org_did VARCHAR,\n'
         '        at_did VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gtasks_oauth_token" ADD COLUMN IF NOT EXISTS history_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gtasks_oauth_token" ADD COLUMN IF NOT EXISTS at_did VARCHAR',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gtasks_oauth_token_email_status ON '
         '"vertex_gtasks_oauth_token" (email, status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gtasks_oauth_token_sync ON '
         '"vertex_gtasks_oauth_token" (status, last_sync_at)',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "vertex_gsheets_oauth_token" (\n'
         '        vertex_id VARCHAR PRIMARY KEY,\n'
         '        account_did VARCHAR,\n'
         '        email VARCHAR,\n'
         '        encrypted_refresh_token VARCHAR,\n'
         '        wrapped_data_key VARCHAR,\n'
         '        iv VARCHAR,\n'
         '        scope VARCHAR,\n'
         '        access_token_cache VARCHAR,\n'
         '        access_expires_at BIGINT,\n'
         '        status VARCHAR,\n'
         '        cursor VARCHAR,\n'
         '        history_id VARCHAR,\n'
         '        last_sync_at VARCHAR,\n'
         '        created_at VARCHAR,\n'
         '        updated_at VARCHAR,\n'
         '        actor_did VARCHAR,\n'
         '        org_did VARCHAR,\n'
         '        at_did VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gsheets_oauth_token" ADD COLUMN IF NOT EXISTS history_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gsheets_oauth_token" ADD COLUMN IF NOT EXISTS at_did VARCHAR',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gsheets_oauth_token_email_status ON '
         '"vertex_gsheets_oauth_token" (email, status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gsheets_oauth_token_sync ON '
         '"vertex_gsheets_oauth_token" (status, last_sync_at)',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "vertex_gdrive_oauth_token" (\n'
         '        vertex_id VARCHAR PRIMARY KEY,\n'
         '        account_did VARCHAR,\n'
         '        email VARCHAR,\n'
         '        encrypted_refresh_token VARCHAR,\n'
         '        wrapped_data_key VARCHAR,\n'
         '        iv VARCHAR,\n'
         '        scope VARCHAR,\n'
         '        access_token_cache VARCHAR,\n'
         '        access_expires_at BIGINT,\n'
         '        status VARCHAR,\n'
         '        cursor VARCHAR,\n'
         '        history_id VARCHAR,\n'
         '        last_sync_at VARCHAR,\n'
         '        created_at VARCHAR,\n'
         '        updated_at VARCHAR,\n'
         '        actor_did VARCHAR,\n'
         '        org_did VARCHAR,\n'
         '        at_did VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gdrive_oauth_token" ADD COLUMN IF NOT EXISTS history_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gdrive_oauth_token" ADD COLUMN IF NOT EXISTS at_did VARCHAR',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gdrive_oauth_token_email_status ON '
         '"vertex_gdrive_oauth_token" (email, status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gdrive_oauth_token_sync ON '
         '"vertex_gdrive_oauth_token" (status, last_sync_at)',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "vertex_gcontacts_oauth_token" (\n'
         '        vertex_id VARCHAR PRIMARY KEY,\n'
         '        account_did VARCHAR,\n'
         '        email VARCHAR,\n'
         '        encrypted_refresh_token VARCHAR,\n'
         '        wrapped_data_key VARCHAR,\n'
         '        iv VARCHAR,\n'
         '        scope VARCHAR,\n'
         '        access_token_cache VARCHAR,\n'
         '        access_expires_at BIGINT,\n'
         '        status VARCHAR,\n'
         '        cursor VARCHAR,\n'
         '        history_id VARCHAR,\n'
         '        last_sync_at VARCHAR,\n'
         '        created_at VARCHAR,\n'
         '        updated_at VARCHAR,\n'
         '        actor_did VARCHAR,\n'
         '        org_did VARCHAR,\n'
         '        at_did VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gcontacts_oauth_token" ADD COLUMN IF NOT EXISTS history_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gcontacts_oauth_token" ADD COLUMN IF NOT EXISTS at_did VARCHAR',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gcontacts_oauth_token_email_status ON '
         '"vertex_gcontacts_oauth_token" (email, status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gcontacts_oauth_token_sync ON '
         '"vertex_gcontacts_oauth_token" (status, last_sync_at)',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "vertex_gmeet_oauth_token" (\n'
         '        vertex_id VARCHAR PRIMARY KEY,\n'
         '        account_did VARCHAR,\n'
         '        email VARCHAR,\n'
         '        encrypted_refresh_token VARCHAR,\n'
         '        wrapped_data_key VARCHAR,\n'
         '        iv VARCHAR,\n'
         '        scope VARCHAR,\n'
         '        access_token_cache VARCHAR,\n'
         '        access_expires_at BIGINT,\n'
         '        status VARCHAR,\n'
         '        cursor VARCHAR,\n'
         '        history_id VARCHAR,\n'
         '        last_sync_at VARCHAR,\n'
         '        created_at VARCHAR,\n'
         '        updated_at VARCHAR,\n'
         '        actor_did VARCHAR,\n'
         '        org_did VARCHAR,\n'
         '        at_did VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gmeet_oauth_token" ADD COLUMN IF NOT EXISTS history_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gmeet_oauth_token" ADD COLUMN IF NOT EXISTS at_did VARCHAR',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmeet_oauth_token_email_status ON '
         '"vertex_gmeet_oauth_token" (email, status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmeet_oauth_token_sync ON '
         '"vertex_gmeet_oauth_token" (status, last_sync_at)',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "vertex_gdocs_oauth_token" (\n'
         '        vertex_id VARCHAR PRIMARY KEY,\n'
         '        account_did VARCHAR,\n'
         '        email VARCHAR,\n'
         '        encrypted_refresh_token VARCHAR,\n'
         '        wrapped_data_key VARCHAR,\n'
         '        iv VARCHAR,\n'
         '        scope VARCHAR,\n'
         '        access_token_cache VARCHAR,\n'
         '        access_expires_at BIGINT,\n'
         '        status VARCHAR,\n'
         '        cursor VARCHAR,\n'
         '        history_id VARCHAR,\n'
         '        last_sync_at VARCHAR,\n'
         '        created_at VARCHAR,\n'
         '        updated_at VARCHAR,\n'
         '        actor_did VARCHAR,\n'
         '        org_did VARCHAR,\n'
         '        at_did VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gdocs_oauth_token" ADD COLUMN IF NOT EXISTS history_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gdocs_oauth_token" ADD COLUMN IF NOT EXISTS at_did VARCHAR',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gdocs_oauth_token_email_status ON '
         '"vertex_gdocs_oauth_token" (email, status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gdocs_oauth_token_sync ON '
         '"vertex_gdocs_oauth_token" (status, last_sync_at)',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "vertex_gslides_oauth_token" (\n'
         '        vertex_id VARCHAR PRIMARY KEY,\n'
         '        account_did VARCHAR,\n'
         '        email VARCHAR,\n'
         '        encrypted_refresh_token VARCHAR,\n'
         '        wrapped_data_key VARCHAR,\n'
         '        iv VARCHAR,\n'
         '        scope VARCHAR,\n'
         '        access_token_cache VARCHAR,\n'
         '        access_expires_at BIGINT,\n'
         '        status VARCHAR,\n'
         '        cursor VARCHAR,\n'
         '        history_id VARCHAR,\n'
         '        last_sync_at VARCHAR,\n'
         '        created_at VARCHAR,\n'
         '        updated_at VARCHAR,\n'
         '        actor_did VARCHAR,\n'
         '        org_did VARCHAR,\n'
         '        at_did VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gslides_oauth_token" ADD COLUMN IF NOT EXISTS history_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gslides_oauth_token" ADD COLUMN IF NOT EXISTS at_did VARCHAR',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gslides_oauth_token_email_status ON '
         '"vertex_gslides_oauth_token" (email, status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gslides_oauth_token_sync ON '
         '"vertex_gslides_oauth_token" (status, last_sync_at)',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS "vertex_gmail_oauth_token" (\n'
         '        vertex_id VARCHAR PRIMARY KEY,\n'
         '        account_did VARCHAR,\n'
         '        email VARCHAR,\n'
         '        encrypted_refresh_token VARCHAR,\n'
         '        wrapped_data_key VARCHAR,\n'
         '        iv VARCHAR,\n'
         '        scope VARCHAR,\n'
         '        access_token_cache VARCHAR,\n'
         '        access_expires_at BIGINT,\n'
         '        status VARCHAR,\n'
         '        cursor VARCHAR,\n'
         '        history_id VARCHAR,\n'
         '        last_sync_at VARCHAR,\n'
         '        created_at VARCHAR,\n'
         '        updated_at VARCHAR,\n'
         '        actor_did VARCHAR,\n'
         '        org_did VARCHAR,\n'
         '        at_did VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gmail_oauth_token" ADD COLUMN IF NOT EXISTS history_id VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE "vertex_gmail_oauth_token" ADD COLUMN IF NOT EXISTS at_did VARCHAR',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmail_oauth_token_email_status ON '
         '"vertex_gmail_oauth_token" (email, status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_vertex_gmail_oauth_token_sync ON '
         '"vertex_gmail_oauth_token" (status, last_sync_at)',
  'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS "vertex_gmail_oauth_token"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_gslides_oauth_token"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_gdocs_oauth_token"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_gmeet_oauth_token"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_gcontacts_oauth_token"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_gdrive_oauth_token"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_gsheets_oauth_token"', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS "vertex_gtasks_oauth_token"', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
