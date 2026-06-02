"""Captured from Kysely migration 20260422150000_udf_gmail_upsert_contact."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260422150000_udf_gmail_upsert_contact"
down_revision = 'r_20260422140000_phishing_alert_llm_columns'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE FUNCTION gmail_upsert_contact(VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'com.etzhayyim.apps.gmail.upsertContact'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS gmail_upsert_contact(VARCHAR)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
