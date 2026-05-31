"""Captured from Kysely migration 20260507530000_magatama_organizer_run_graph."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507530000_magatama_organizer_run_graph"
down_revision = 'r_20260507529000_bunken_bibliographic_item_graph'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_magatama_organizer_run (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR NOT NULL,\n'
         '      status VARCHAR NOT NULL,\n'
         '      value_json TEXT NOT NULL,\n'
         '      indexed_at VARCHAR NOT NULL,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      updated_at VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 2,\n'
         '      http_status INTEGER NOT NULL DEFAULT 0,\n'
         '      runs_total_24h INTEGER NOT NULL DEFAULT 0,\n'
         '      summary_hot INTEGER NOT NULL DEFAULT 0,\n'
         '      summary_normal INTEGER NOT NULL DEFAULT 0,\n'
         '      summary_stale INTEGER NOT NULL DEFAULT 0,\n'
         '      summary_silent INTEGER NOT NULL DEFAULT 0,\n'
         '      summary_archived INTEGER NOT NULL DEFAULT 0,\n'
         '      fleet_saturation DOUBLE PRECISION NOT NULL DEFAULT 0,\n'
         '      plan_ts VARCHAR,\n'
         '      latency_ms INTEGER NOT NULL DEFAULT 0,\n'
         '      error TEXT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    SELECT EXISTS (\n'
         '      SELECT 1 FROM information_schema.tables\n'
         '      WHERE table_schema = current_schema()\n'
         "        AND table_name = 'vertex_magatama_record'\n"
         '    ) AS exists\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_magatama_organizer_run_status_time\n'
         '      ON vertex_magatama_organizer_run (status, indexed_at DESC)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_magatama_organizer_run_http_time\n'
         '      ON vertex_magatama_organizer_run (http_status, indexed_at DESC)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_magatama_organizer_run_health AS\n'
         '    SELECT\n'
         '      status,\n'
         '      COUNT(*) AS run_count,\n'
         '      MAX(indexed_at) AS latest_indexed_at,\n'
         '      AVG(fleet_saturation) AS avg_fleet_saturation,\n'
         '      AVG(latency_ms) AS avg_latency_ms\n'
         '    FROM vertex_magatama_organizer_run\n'
         '    GROUP BY status\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         "    SET write_table_allowlist = 'vertex_magatama_organizer_run'\n"
         '    WHERE owner_did = $1\n'
         '      AND nsid = $2\n'
         '  ',
  'parameters': ['did:web:magatama.etzhayyim.com', 'app.etzhayyim.apps.magatama.organizerRun']}]

DOWN = [{'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         "    SET write_table_allowlist = ''\n"
         '    WHERE owner_did = $1\n'
         '      AND nsid = $2\n'
         '  ',
  'parameters': ['did:web:magatama.etzhayyim.com', 'app.etzhayyim.apps.magatama.organizerRun']},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_magatama_organizer_run_health', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_magatama_organizer_run', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
