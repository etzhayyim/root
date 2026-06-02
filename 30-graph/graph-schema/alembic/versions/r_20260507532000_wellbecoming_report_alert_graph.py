"""Captured from Kysely migration 20260507532000_wellbecoming_report_alert_graph."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507532000_wellbecoming_report_alert_graph"
down_revision = 'r_20260507531000_murakumo_fleet_health_graph'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_wellbecoming_proactive_message (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR NOT NULL,\n'
         '      text TEXT NOT NULL,\n'
         '      caller_did VARCHAR,\n'
         '      bottleneck_axis VARCHAR,\n'
         '      avg_separation_delta DOUBLE PRECISION,\n'
         '      value_json TEXT NOT NULL,\n'
         '      indexed_at VARCHAR NOT NULL,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      updated_at VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 2\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_wellbecoming_floor_alert (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR NOT NULL,\n'
         '      text TEXT NOT NULL,\n'
         '      violation_count INTEGER NOT NULL DEFAULT 0,\n'
         '      violation_ids_json TEXT,\n'
         '      value_json TEXT NOT NULL,\n'
         '      indexed_at VARCHAR NOT NULL,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      updated_at VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 2\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_wellbecoming_process_mining_report (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      record_key VARCHAR NOT NULL,\n'
         '      text TEXT NOT NULL,\n'
         '      scored_count INTEGER NOT NULL DEFAULT 0,\n'
         '      floor_violations INTEGER NOT NULL DEFAULT 0,\n'
         '      avg_spirit DOUBLE PRECISION,\n'
         '      avg_separation_delta DOUBLE PRECISION,\n'
         '      value_json TEXT NOT NULL,\n'
         '      indexed_at VARCHAR NOT NULL,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      updated_at VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      owner_did VARCHAR NOT NULL,\n'
         '      sensitivity_ord INTEGER NOT NULL DEFAULT 2\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    SELECT EXISTS (\n'
         '      SELECT 1 FROM information_schema.tables\n'
         '      WHERE table_schema = current_schema()\n'
         "        AND table_name = 'vertex_wellbecoming_record'\n"
         '    ) AS exists\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_wb_proactive_message_caller_time\n'
         '      ON vertex_wellbecoming_proactive_message (caller_did, indexed_at DESC)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_wb_floor_alert_count_time\n'
         '      ON vertex_wellbecoming_floor_alert (violation_count, indexed_at DESC)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_wb_process_mining_report_time\n'
         '      ON vertex_wellbecoming_process_mining_report (indexed_at DESC)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_wellbecoming_report_health AS\n'
         '    SELECT\n'
         '      COUNT(*) AS report_count,\n'
         '      SUM(scored_count) AS scored_count,\n'
         '      SUM(floor_violations) AS floor_violations,\n'
         '      AVG(avg_spirit) AS avg_spirit,\n'
         '      AVG(avg_separation_delta) AS avg_separation_delta,\n'
         '      MAX(indexed_at) AS latest_indexed_at\n'
         '    FROM vertex_wellbecoming_process_mining_report\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS '
         'mv_wellbecoming_proactive_message_caller_counts AS\n'
         '    SELECT caller_did, COUNT(*) AS message_count, MAX(indexed_at) AS latest_indexed_at\n'
         '    FROM vertex_wellbecoming_proactive_message\n'
         '    GROUP BY caller_did\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET write_table_allowlist = $1\n'
         '    WHERE nsid IN (\n'
         "      'com.etzhayyim.apps.wellbecoming.agentLoop',\n"
         "      'com.etzhayyim.apps.wellbecoming.proactiveConnect',\n"
         "      'com.etzhayyim.apps.wellbecoming.floorViolationAlert',\n"
         "      'com.etzhayyim.apps.wellbecoming.processMining'\n"
         '    )\n'
         '  ',
  'parameters': ['vertex_wellbecoming_event,vertex_actor_wellbecoming_profile,vertex_wellbecoming_proactive_message,vertex_wellbecoming_floor_alert,vertex_wellbecoming_process_mining_report']}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_wellbecoming_proactive_message_caller_counts',
  'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_wellbecoming_report_health', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_wellbecoming_process_mining_report', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_wellbecoming_floor_alert', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_wellbecoming_proactive_message', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
