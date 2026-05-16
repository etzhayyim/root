"""Captured from Kysely migration 20260429193000_udf_bpmn_analyze_process."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429193000_udf_bpmn_analyze_process"
down_revision = 'r_20260429162000_jp_corp_finance_process_mining'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE FUNCTION bpmn_analyze_process(VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'ai.gftd.apps.bpmn.analyzeProcess'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS bpmn_analyze_process(VARCHAR)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
