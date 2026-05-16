"""Captured from Kysely migration 0122_cofog_hs2012_asfis_isic4_bridges."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0122_cofog_hs2012_asfis_isic4_bridges"
down_revision = 'r_0121_cofog_hs_legacy_isco_sitc'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_hs2012'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2012_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_asfis'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_hs2012'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2012_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_asfis'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
