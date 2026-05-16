"""Captured from Kysely migration 20260429214500_udf_topology_dependency_hint."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429214500_udf_topology_dependency_hint"
down_revision = 'r_20260429214000_seed_gworkspace_lite_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE FUNCTION topology_dependency_hint(VARCHAR, VARCHAR, VARCHAR, VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'topology_dependency_hint'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS topology_dependency_hint(VARCHAR, VARCHAR, VARCHAR, VARCHAR)',
  'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
