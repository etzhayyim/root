"""Captured from Kysely migration 20260422120000_udf_vultr_chat_completions."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260422120000_udf_vultr_chat_completions"
down_revision = 'r_20260422110000_vertex_houbun'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE FUNCTION vultr_chat_completions(VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'com.etzhayyim.apps.vultrInference.chatCompletions'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS vultr_chat_completions(VARCHAR)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
