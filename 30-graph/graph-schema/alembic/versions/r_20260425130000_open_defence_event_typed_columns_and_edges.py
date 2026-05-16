"""Captured from Kysely migration 20260425130000_open_defence_event_typed_columns_and_edges."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425130000_open_defence_event_typed_columns_and_edges"
down_revision = 'r_20260425123000_rename_contracts_social_contract'
branch_labels = None
depends_on = None

UP = [{'sql': 'ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS subject_lei varchar',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS subject_imo varchar',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS subject_cve_id varchar',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS subject_country varchar',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS treaty_code varchar',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS commodity_code varchar',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS aircraft_did varchar',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS satellite_norad_id '
         'varchar',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS evidence_uri varchar',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS fiscal_year varchar',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS amount_usd double '
         'precision',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_open_defence_event ADD COLUMN IF NOT EXISTS confidence double '
         'precision',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_open_defence_event_lei      ON vertex_open_defence_event '
         '(subject_lei)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_open_defence_event_imo      ON vertex_open_defence_event '
         '(subject_imo)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_open_defence_event_cve      ON vertex_open_defence_event '
         '(subject_cve_id)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_open_defence_event_country  ON vertex_open_defence_event '
         '(subject_country)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_open_defence_event_treaty   ON vertex_open_defence_event '
         '(treaty_code)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_open_defence_event_commodity ON vertex_open_defence_event '
         '(commodity_code)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_defence_subject_to_lei (\n'
         '      edge_id         varchar PRIMARY KEY,\n'
         '      src_vid         varchar NOT NULL,\n'
         '      dst_vid         varchar NOT NULL,\n'
         '      role            varchar NOT NULL,\n'
         '      created_at      varchar NOT NULL,\n'
         '      sensitivity_ord integer NOT NULL,\n'
         '      org_id          varchar NOT NULL,\n'
         '      user_id         varchar NOT NULL,\n'
         '      actor_id        varchar NOT NULL,\n'
         '      owner_did       varchar NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_defence_lei_src ON edge_defence_subject_to_lei '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_defence_lei_dst ON edge_defence_subject_to_lei '
         '(dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_defence_subject_to_vessel (\n'
         '      edge_id         varchar PRIMARY KEY,\n'
         '      src_vid         varchar NOT NULL,\n'
         '      dst_vid         varchar NOT NULL,\n'
         '      role            varchar NOT NULL,\n'
         '      created_at      varchar NOT NULL,\n'
         '      sensitivity_ord integer NOT NULL,\n'
         '      org_id          varchar NOT NULL,\n'
         '      user_id         varchar NOT NULL,\n'
         '      actor_id        varchar NOT NULL,\n'
         '      owner_did       varchar NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_defence_vessel_src ON edge_defence_subject_to_vessel '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_defence_vessel_dst ON edge_defence_subject_to_vessel '
         '(dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_defence_event_to_cve (\n'
         '      edge_id         varchar PRIMARY KEY,\n'
         '      src_vid         varchar NOT NULL,\n'
         '      dst_vid         varchar NOT NULL,\n'
         '      role            varchar NOT NULL,\n'
         '      created_at      varchar NOT NULL,\n'
         '      sensitivity_ord integer NOT NULL,\n'
         '      org_id          varchar NOT NULL,\n'
         '      user_id         varchar NOT NULL,\n'
         '      actor_id        varchar NOT NULL,\n'
         '      owner_did       varchar NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_defence_cve_src ON edge_defence_event_to_cve '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_defence_cve_dst ON edge_defence_event_to_cve '
         '(dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_defence_event_to_treaty (\n'
         '      edge_id         varchar PRIMARY KEY,\n'
         '      src_vid         varchar NOT NULL,\n'
         '      dst_vid         varchar NOT NULL,\n'
         '      role            varchar NOT NULL,\n'
         '      created_at      varchar NOT NULL,\n'
         '      sensitivity_ord integer NOT NULL,\n'
         '      org_id          varchar NOT NULL,\n'
         '      user_id         varchar NOT NULL,\n'
         '      actor_id        varchar NOT NULL,\n'
         '      owner_did       varchar NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_defence_treaty_src ON edge_defence_event_to_treaty '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_defence_treaty_dst ON edge_defence_event_to_treaty '
         '(dst_vid)',
  'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS edge_defence_event_to_treaty', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_defence_event_to_cve', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_defence_subject_to_vessel', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_defence_subject_to_lei', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
