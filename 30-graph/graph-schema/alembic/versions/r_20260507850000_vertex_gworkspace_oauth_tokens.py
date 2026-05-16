"""Captured from Kysely migration 20260507850000_vertex_gworkspace_oauth_tokens."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507850000_vertex_gworkspace_oauth_tokens"
down_revision = 'r_20260507850000_coverage_recipe_business_person_lei'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS vertex_gdrive_oauth_token (\n'
         '        vertex_id                VARCHAR PRIMARY KEY,\n'
         '        account_did              VARCHAR,\n'
         '        email                    VARCHAR,\n'
         '        encrypted_refresh_token  VARCHAR,\n'
         '        wrapped_data_key         VARCHAR,\n'
         '        iv                       VARCHAR,\n'
         '        scope                    VARCHAR,\n'
         '        access_token_cache       VARCHAR,\n'
         '        access_expires_at        BIGINT,\n'
         '        status                   VARCHAR,\n'
         '        cursor                   VARCHAR,\n'
         '        history_id               VARCHAR,\n'
         '        last_sync_at             VARCHAR,\n'
         '        created_at               VARCHAR,\n'
         '        updated_at               VARCHAR,\n'
         '        actor_did                VARCHAR,\n'
         '        org_did                  VARCHAR,\n'
         '        at_did                   VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE INDEX IF NOT EXISTS idx_gdrive_oauth_token_email\n'
         '        ON vertex_gdrive_oauth_token (email)\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE INDEX IF NOT EXISTS idx_gdrive_oauth_token_status\n'
         '        ON vertex_gdrive_oauth_token (status)\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS vertex_gcontacts_oauth_token (\n'
         '        vertex_id                VARCHAR PRIMARY KEY,\n'
         '        account_did              VARCHAR,\n'
         '        email                    VARCHAR,\n'
         '        encrypted_refresh_token  VARCHAR,\n'
         '        wrapped_data_key         VARCHAR,\n'
         '        iv                       VARCHAR,\n'
         '        scope                    VARCHAR,\n'
         '        access_token_cache       VARCHAR,\n'
         '        access_expires_at        BIGINT,\n'
         '        status                   VARCHAR,\n'
         '        cursor                   VARCHAR,\n'
         '        history_id               VARCHAR,\n'
         '        last_sync_at             VARCHAR,\n'
         '        created_at               VARCHAR,\n'
         '        updated_at               VARCHAR,\n'
         '        actor_did                VARCHAR,\n'
         '        org_did                  VARCHAR,\n'
         '        at_did                   VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE INDEX IF NOT EXISTS idx_gcontacts_oauth_token_email\n'
         '        ON vertex_gcontacts_oauth_token (email)\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE INDEX IF NOT EXISTS idx_gcontacts_oauth_token_status\n'
         '        ON vertex_gcontacts_oauth_token (status)\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS vertex_gdocs_oauth_token (\n'
         '        vertex_id                VARCHAR PRIMARY KEY,\n'
         '        account_did              VARCHAR,\n'
         '        email                    VARCHAR,\n'
         '        encrypted_refresh_token  VARCHAR,\n'
         '        wrapped_data_key         VARCHAR,\n'
         '        iv                       VARCHAR,\n'
         '        scope                    VARCHAR,\n'
         '        access_token_cache       VARCHAR,\n'
         '        access_expires_at        BIGINT,\n'
         '        status                   VARCHAR,\n'
         '        cursor                   VARCHAR,\n'
         '        history_id               VARCHAR,\n'
         '        last_sync_at             VARCHAR,\n'
         '        created_at               VARCHAR,\n'
         '        updated_at               VARCHAR,\n'
         '        actor_did                VARCHAR,\n'
         '        org_did                  VARCHAR,\n'
         '        at_did                   VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE INDEX IF NOT EXISTS idx_gdocs_oauth_token_email\n'
         '        ON vertex_gdocs_oauth_token (email)\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE INDEX IF NOT EXISTS idx_gdocs_oauth_token_status\n'
         '        ON vertex_gdocs_oauth_token (status)\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS vertex_gmeet_oauth_token (\n'
         '        vertex_id                VARCHAR PRIMARY KEY,\n'
         '        account_did              VARCHAR,\n'
         '        email                    VARCHAR,\n'
         '        encrypted_refresh_token  VARCHAR,\n'
         '        wrapped_data_key         VARCHAR,\n'
         '        iv                       VARCHAR,\n'
         '        scope                    VARCHAR,\n'
         '        access_token_cache       VARCHAR,\n'
         '        access_expires_at        BIGINT,\n'
         '        status                   VARCHAR,\n'
         '        cursor                   VARCHAR,\n'
         '        history_id               VARCHAR,\n'
         '        last_sync_at             VARCHAR,\n'
         '        created_at               VARCHAR,\n'
         '        updated_at               VARCHAR,\n'
         '        actor_did                VARCHAR,\n'
         '        org_did                  VARCHAR,\n'
         '        at_did                   VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE INDEX IF NOT EXISTS idx_gmeet_oauth_token_email\n'
         '        ON vertex_gmeet_oauth_token (email)\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE INDEX IF NOT EXISTS idx_gmeet_oauth_token_status\n'
         '        ON vertex_gmeet_oauth_token (status)\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS vertex_gsheets_oauth_token (\n'
         '        vertex_id                VARCHAR PRIMARY KEY,\n'
         '        account_did              VARCHAR,\n'
         '        email                    VARCHAR,\n'
         '        encrypted_refresh_token  VARCHAR,\n'
         '        wrapped_data_key         VARCHAR,\n'
         '        iv                       VARCHAR,\n'
         '        scope                    VARCHAR,\n'
         '        access_token_cache       VARCHAR,\n'
         '        access_expires_at        BIGINT,\n'
         '        status                   VARCHAR,\n'
         '        cursor                   VARCHAR,\n'
         '        history_id               VARCHAR,\n'
         '        last_sync_at             VARCHAR,\n'
         '        created_at               VARCHAR,\n'
         '        updated_at               VARCHAR,\n'
         '        actor_did                VARCHAR,\n'
         '        org_did                  VARCHAR,\n'
         '        at_did                   VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE INDEX IF NOT EXISTS idx_gsheets_oauth_token_email\n'
         '        ON vertex_gsheets_oauth_token (email)\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE INDEX IF NOT EXISTS idx_gsheets_oauth_token_status\n'
         '        ON vertex_gsheets_oauth_token (status)\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE TABLE IF NOT EXISTS vertex_gslides_oauth_token (\n'
         '        vertex_id                VARCHAR PRIMARY KEY,\n'
         '        account_did              VARCHAR,\n'
         '        email                    VARCHAR,\n'
         '        encrypted_refresh_token  VARCHAR,\n'
         '        wrapped_data_key         VARCHAR,\n'
         '        iv                       VARCHAR,\n'
         '        scope                    VARCHAR,\n'
         '        access_token_cache       VARCHAR,\n'
         '        access_expires_at        BIGINT,\n'
         '        status                   VARCHAR,\n'
         '        cursor                   VARCHAR,\n'
         '        history_id               VARCHAR,\n'
         '        last_sync_at             VARCHAR,\n'
         '        created_at               VARCHAR,\n'
         '        updated_at               VARCHAR,\n'
         '        actor_did                VARCHAR,\n'
         '        org_did                  VARCHAR,\n'
         '        at_did                   VARCHAR\n'
         '      )\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE INDEX IF NOT EXISTS idx_gslides_oauth_token_email\n'
         '        ON vertex_gslides_oauth_token (email)\n'
         '    ',
  'parameters': []},
 {'sql': '\n'
         '      CREATE INDEX IF NOT EXISTS idx_gslides_oauth_token_status\n'
         '        ON vertex_gslides_oauth_token (status)\n'
         '    ',
  'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS vertex_gdrive_oauth_token', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_gcontacts_oauth_token', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_gdocs_oauth_token', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_gmeet_oauth_token', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_gsheets_oauth_token', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_gslides_oauth_token', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
