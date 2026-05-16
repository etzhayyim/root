"""Captured from Kysely migration 0121_cofog_hs_legacy_isco_sitc."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0121_cofog_hs_legacy_isco_sitc"
down_revision = 'r_0120_isco_cofog_completeness'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_hs2007'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2007_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_hs2002'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2002_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_hs1996'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs1996_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_sitc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc3_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_sitc2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc2_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_sitc1'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc1_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_sitc2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc2_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_sitc1'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc1_cofog'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_hs2007'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2007_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_hs2002'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2002_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_hs1996'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs1996_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_sitc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc3_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_sitc2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc2_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_sitc1'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc1_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_sitc2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc2_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_sitc1'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc1_cofog'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
