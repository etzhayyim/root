"""Captured from Kysely migration 20260422130000_udf_classify_t3_phishing."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260422130000_udf_classify_t3_phishing"
down_revision = 'r_20260422120000_udf_vultr_chat_completions'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE FUNCTION classify_t3_phishing(VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'app.etzhayyim.apps.yabaiClassifier.phishingT3'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS classify_t3_phishing(VARCHAR)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
