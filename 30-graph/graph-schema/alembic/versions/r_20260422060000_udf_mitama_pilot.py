"""Captured from Kysely migration 20260422060000_udf_mitama_pilot."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260422060000_udf_mitama_pilot"
down_revision = 'r_20260422030000_vertex_langgraph_checkpoint'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE FUNCTION bpmn_compile_json_to_xml(VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'ai.gftd.apps.bpmn.compileJsonToXml'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE FUNCTION bpmn_validate_xml(VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'ai.gftd.apps.bpmn.validateXml'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE FUNCTION playwright_session_open(VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'ai.gftd.apps.playwright.sessionOpen'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE FUNCTION playwright_session_close(VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'ai.gftd.apps.playwright.sessionClose'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS playwright_session_close(VARCHAR)', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS playwright_session_open(VARCHAR)', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS bpmn_validate_xml(VARCHAR)', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS bpmn_compile_json_to_xml(VARCHAR)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
