"""Captured from Kysely migration 20260422180000_udf_mangaka_storyboard."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260422180000_udf_mangaka_storyboard"
down_revision = 'r_20260422170000_udf_news_translate'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE FUNCTION mangaka_storyboard_from_prompt(VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'com.etzhayyim.apps.mangaka.storyboardFromPrompt'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS mangaka_storyboard_from_prompt(VARCHAR)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
