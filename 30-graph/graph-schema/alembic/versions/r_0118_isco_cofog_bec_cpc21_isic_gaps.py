"""Captured from Kysely migration 0118_isco_cofog_bec_cpc21_isic_gaps."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0118_isco_cofog_bec_cpc21_isic_gaps"
down_revision = 'r_0117_isco_cofog_extended_chains'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_naics'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'naics_isic31'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_naics'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'naics_isic31'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
