"""Captured from Kysely migration 0117_isco_cofog_extended_chains."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0117_isco_cofog_extended_chains"
down_revision = 'r_0116_isco_cofog_isic4_bridges'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_cofog'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_cofog'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
