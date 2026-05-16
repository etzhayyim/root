"""Captured from Kysely migration 20260420050000_fukkou_p8_subcontractor_evidence."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260420050000_fukkou_p8_subcontractor_evidence"
down_revision = 'r_20260420040000_fukkou_p7_procurement'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_fukkou_subcontractor (\n'
         '      vertex_id         VARCHAR PRIMARY KEY,\n'
         '      _seq              BIGINT,\n'
         '      owner_did         VARCHAR,\n'
         '      sub_id            VARCHAR,\n'
         '      corporate_number  VARCHAR,\n'
         '      org_name          VARCHAR,\n'
         '      org_name_kana     VARCHAR,\n'
         '      address           VARCHAR,\n'
         '      prefecture        VARCHAR,\n'
         '      org_type          VARCHAR,\n'
         '      typical_tier      INTEGER,\n'
         '      industry_category VARCHAR,\n'
         '      employees         INTEGER,\n'
         '      capital_yen       NUMERIC,\n'
         '      founded_year      INTEGER,\n'
         '      linked_vendor_vertex_id VARCHAR,\n'
         '      first_observed_at DATE,\n'
         '      created_at        TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_fukkou_subcontracted_to (\n'
         '      edge_id           VARCHAR PRIMARY KEY,\n'
         '      _seq              BIGINT,\n'
         '      procurement_vertex_id VARCHAR,\n'
         '      parent_vertex_id  VARCHAR,\n'
         '      child_vertex_id   VARCHAR,\n'
         '      tier_level        INTEGER,\n'
         '      scope             VARCHAR,\n'
         '      amount_yen        NUMERIC,\n'
         '      share_pct         NUMERIC,\n'
         '      evidence_source   VARCHAR,\n'
         '      evidence_blob_id  VARCHAR,\n'
         '      as_of_date        DATE,\n'
         '      disclosure_status VARCHAR,\n'
         '      created_at        TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_fukkou_evidence_blob (\n'
         '      vertex_id         VARCHAR PRIMARY KEY,\n'
         '      _seq              BIGINT,\n'
         '      owner_did         VARCHAR,\n'
         '      blob_id           VARCHAR,\n'
         '      source_type       VARCHAR,\n'
         '      source_url        VARCHAR,\n'
         '      source_title      VARCHAR,\n'
         '      source_issuer     VARCHAR,\n'
         '      source_date       DATE,\n'
         '      captured_at       TIMESTAMPTZ,\n'
         '      sha256            VARCHAR,\n'
         '      bytes             BIGINT,\n'
         '      r2_bucket         VARCHAR,\n'
         '      r2_key_original   VARCHAR,\n'
         '      r2_key_webp       VARCHAR,\n'
         '      r2_key_thumbnail  VARCHAR,\n'
         '      r2_key_dom_html   VARCHAR,\n'
         '      page_count        INTEGER,\n'
         '      webp_width        INTEGER,\n'
         '      webp_height       INTEGER,\n'
         '      ocr_text_snippet  VARCHAR,\n'
         '      related_vertex_ids VARCHAR,\n'
         '      wayback_url       VARCHAR,\n'
         '      status            VARCHAR,\n'
         '      created_at        TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_fukkou_evidenced_by (\n'
         '      edge_id           VARCHAR PRIMARY KEY,\n'
         '      _seq              BIGINT,\n'
         '      target_vertex_id  VARCHAR,\n'
         '      blob_vertex_id    VARCHAR,\n'
         '      relation          VARCHAR,\n'
         '      page_ref          VARCHAR,\n'
         '      created_at        TIMESTAMPTZ\n'
         '    )\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS edge_fukkou_evidenced_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_fukkou_evidence_blob', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_fukkou_subcontracted_to', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_fukkou_subcontractor', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
