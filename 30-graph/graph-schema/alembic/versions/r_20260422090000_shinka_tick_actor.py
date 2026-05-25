"""Captured from Kysely migration 20260422090000_shinka_tick_actor."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260422090000_shinka_tick_actor"
down_revision = 'r_20260422060000_udf_mitama_pilot'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE FUNCTION shinka_tick_actor(VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'app.etzhayyim.apps.shinka.tickActor'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS shinka_tick_actor(VARCHAR)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
