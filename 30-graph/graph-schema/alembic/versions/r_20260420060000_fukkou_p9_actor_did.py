"""Captured from Kysely migration 20260420060000_fukkou_p9_actor_did."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260420060000_fukkou_p9_actor_did"
down_revision = 'r_20260420050000_fukkou_p8_subcontractor_evidence'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_fukkou_actor_did (\n'
         '      vertex_id         VARCHAR PRIMARY KEY,\n'
         '      _seq              BIGINT,\n'
         '      owner_did         VARCHAR,\n'
         '      actor_did         VARCHAR,\n'
         '      actor_type        VARCHAR,\n'
         '      display_name      VARCHAR,\n'
         '      display_name_kana VARCHAR,\n'
         '      handle            VARCHAR,\n'
         '      country           VARCHAR,\n'
         '      lei_code          VARCHAR,\n'
         '      corporate_number  VARCHAR,\n'
         '      gender            VARCHAR,\n'
         '      role              VARCHAR,\n'
         '      linked_vertex_id  VARCHAR,\n'
         '      linked_vertex_type VARCHAR,\n'
         '      did_verification_status VARCHAR,\n'
         '      canonical         BOOLEAN,\n'
         '      created_at        TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_fukkou_person_represents_org (\n'
         '      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,\n'
         '      person_actor_did VARCHAR, org_actor_did VARCHAR,\n'
         '      role VARCHAR, start_date DATE, end_date DATE,\n'
         '      confidence NUMERIC, created_at TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_fukkou_actor_succeeds (\n'
         '      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,\n'
         '      from_actor_did VARCHAR, to_actor_did VARCHAR,\n'
         '      relation VARCHAR, effective_date DATE, created_at TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS edge_fukkou_actor_succeeds', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_fukkou_person_represents_org', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_fukkou_actor_did', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
