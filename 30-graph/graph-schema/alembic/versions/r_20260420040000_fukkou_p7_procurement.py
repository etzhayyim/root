"""Captured from Kysely migration 20260420040000_fukkou_p7_procurement."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260420040000_fukkou_p7_procurement"
down_revision = 'r_20260420030708_scraper_dsl_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_fukkou_procurement (\n'
         '      vertex_id         VARCHAR PRIMARY KEY,\n'
         '      _seq              BIGINT,\n'
         '      owner_did         VARCHAR,\n'
         '      procurement_id    VARCHAR,\n'
         '      authority_did     VARCHAR,\n'
         '      project_title     VARCHAR,\n'
         '      procurement_type  VARCHAR,\n'
         '      bid_method        VARCHAR,\n'
         '      announcement_date DATE,\n'
         '      award_date        DATE,\n'
         '      award_amount_yen  NUMERIC,\n'
         '      predicted_price   NUMERIC,\n'
         '      bid_ratio_pct     NUMERIC,\n'
         '      fiscal_year       VARCHAR,\n'
         '      budget_category   VARCHAR,\n'
         '      source_url        VARCHAR,\n'
         '      source_doc        VARCHAR,\n'
         '      created_at        TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_fukkou_vendor (\n'
         '      vertex_id         VARCHAR PRIMARY KEY,\n'
         '      _seq              BIGINT,\n'
         '      owner_did         VARCHAR,\n'
         '      vendor_id         VARCHAR,\n'
         '      corporate_number  VARCHAR,\n'
         '      org_name          VARCHAR,\n'
         '      org_name_kana     VARCHAR,\n'
         '      address           VARCHAR,\n'
         '      org_type          VARCHAR,\n'
         '      capital_yen       NUMERIC,\n'
         '      employees         INTEGER,\n'
         '      founded_year      INTEGER,\n'
         '      industry_code     VARCHAR,\n'
         '      total_awards_yen  NUMERIC,\n'
         '      award_count       INTEGER,\n'
         '      linked_recipient_vertex_id VARCHAR,\n'
         '      created_at        TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_fukkou_officer (\n'
         '      vertex_id         VARCHAR PRIMARY KEY,\n'
         '      _seq              BIGINT,\n'
         '      owner_did         VARCHAR,\n'
         '      officer_id        VARCHAR,\n'
         '      officer_name      VARCHAR,\n'
         '      officer_role      VARCHAR,\n'
         '      officer_type      VARCHAR,\n'
         '      authority_did     VARCHAR,\n'
         '      ministry          VARCHAR,\n'
         '      bureau            VARCHAR,\n'
         '      department        VARCHAR,\n'
         '      tenure_start      DATE,\n'
         '      tenure_end        DATE,\n'
         '      linked_bureaucrat_vertex_id VARCHAR,\n'
         '      created_at        TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_fukkou_org_affiliation (\n'
         '      vertex_id         VARCHAR PRIMARY KEY,\n'
         '      _seq              BIGINT,\n'
         '      owner_did         VARCHAR,\n'
         '      affiliation_id    VARCHAR,\n'
         '      relation_type     VARCHAR,\n'
         '      parent_vertex_id  VARCHAR,\n'
         '      child_vertex_id   VARCHAR,\n'
         '      ownership_pct     NUMERIC,\n'
         '      evidence_source   VARCHAR,\n'
         '      evidence_url      VARCHAR,\n'
         '      as_of_date        DATE,\n'
         '      confidence        NUMERIC,\n'
         '      notes             VARCHAR,\n'
         '      created_at        TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_fukkou_org_parent (\n'
         '      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,\n'
         '      parent_vertex_id VARCHAR, child_vertex_id VARCHAR,\n'
         '      ownership_pct NUMERIC, relation_type VARCHAR,\n'
         '      evidence_source VARCHAR, as_of_date DATE, created_at TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_fukkou_org_affiliate (\n'
         '      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,\n'
         '      from_vertex_id VARCHAR, to_vertex_id VARCHAR,\n'
         '      relation_type VARCHAR, evidence_source VARCHAR,\n'
         '      as_of_date DATE, created_at TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_fukkou_procurement_awarded_to (\n'
         '      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,\n'
         '      procurement_vertex_id VARCHAR, vendor_vertex_id VARCHAR,\n'
         '      award_amount_yen NUMERIC, award_share_pct NUMERIC,\n'
         '      joint_bid_flag BOOLEAN, created_at TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_fukkou_procurement_handled_by (\n'
         '      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,\n'
         '      procurement_vertex_id VARCHAR, officer_vertex_id VARCHAR,\n'
         '      role VARCHAR, created_at TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_fukkou_vendor_employs_officer (\n'
         '      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,\n'
         '      vendor_vertex_id VARCHAR, officer_vertex_id VARCHAR,\n'
         '      role VARCHAR, tenure_start DATE, tenure_end DATE, created_at TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS edge_fukkou_vendor_employs_officer', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_fukkou_procurement_handled_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_fukkou_procurement_awarded_to', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_fukkou_org_affiliate', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_fukkou_org_parent', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_fukkou_org_affiliation', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_fukkou_officer', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_fukkou_vendor', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_fukkou_procurement', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
