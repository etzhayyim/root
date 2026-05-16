"""Captured from Kysely migration 20260422170000_udf_news_translate."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260422170000_udf_news_translate"
down_revision = 'r_20260422160000_udf_yabai_sender_reputation'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE FUNCTION news_translate(VARCHAR, VARCHAR, VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'ai.gftd.apps.news.translate'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS news_translate(VARCHAR, VARCHAR, VARCHAR)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
