"""Captured from Kysely migration 20260416100000_vertex_onion_tables."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260416100000_vertex_onion_tables"
down_revision = 'r_20260416090000_world_collection_coverage_and_keiyaku_quality'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_onion_site (\n'
         '      vertex_id     VARCHAR PRIMARY KEY,\n'
         '      onion_host    VARCHAR NOT NULL,\n'
         '      node_id       VARCHAR,\n'
         '      title         VARCHAR,\n'
         '      category      VARCHAR,\n'
         '      risk_score    INTEGER,\n'
         '      reachable     BOOLEAN,\n'
         '      page_count    INTEGER,\n'
         '      first_seen    VARCHAR,\n'
         '      last_seen     VARCHAR,\n'
         '      site_did      VARCHAR,\n'
         '      mirror_clearnet VARCHAR,\n'
         '      threat_actor_ref VARCHAR,\n'
         '      owner_did     VARCHAR,\n'
         '      created_date  VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_onion_page (\n'
         '      vertex_id         VARCHAR PRIMARY KEY,\n'
         '      onion_url         VARCHAR NOT NULL,\n'
         '      onion_host        VARCHAR NOT NULL,\n'
         '      title             VARCHAR,\n'
         '      content_hash      VARCHAR,\n'
         '      content_blob_cid  VARCHAR,\n'
         '      screenshot_blob_cid VARCHAR,\n'
         '      status_code       INTEGER,\n'
         '      language          VARCHAR,\n'
         '      text_snippet      VARCHAR,\n'
         '      outbound_links    VARCHAR,\n'
         '      threat_indicators VARCHAR,\n'
         '      risk_score        INTEGER,\n'
         '      category          VARCHAR,\n'
         '      crawled_at        VARCHAR,\n'
         '      site_node_id      VARCHAR,\n'
         '      owner_did         VARCHAR,\n'
         '      created_date      VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_onion_crawl (\n'
         '      vertex_id    VARCHAR PRIMARY KEY,\n'
         '      onion_host   VARCHAR NOT NULL,\n'
         '      session_id   VARCHAR,\n'
         '      started_at   VARCHAR,\n'
         '      finished_at  VARCHAR,\n'
         '      page_count   INTEGER,\n'
         '      error_count  INTEGER,\n'
         '      reachable    BOOLEAN,\n'
         '      error_msg    VARCHAR,\n'
         '      owner_did    VARCHAR,\n'
         '      created_date VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_onion_hosted_on (\n'
         '      edge_id      VARCHAR PRIMARY KEY,\n'
         '      src_vid      VARCHAR NOT NULL,\n'
         '      dst_vid      VARCHAR NOT NULL,\n'
         '      owner_did    VARCHAR,\n'
         '      created_date VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_onion_links_to (\n'
         '      edge_id      VARCHAR PRIMARY KEY,\n'
         '      src_vid      VARCHAR NOT NULL,\n'
         '      dst_vid      VARCHAR NOT NULL,\n'
         '      owner_did    VARCHAR,\n'
         '      created_date VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS edge_onion_links_to', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_onion_hosted_on', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_onion_crawl', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_onion_page', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_onion_site', 'parameters': []},
 {'sql': 'FLUSH', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
