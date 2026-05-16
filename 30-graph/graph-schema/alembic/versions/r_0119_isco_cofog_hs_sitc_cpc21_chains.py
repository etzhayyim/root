"""Captured from Kysely migration 0119_isco_cofog_hs_sitc_cpc21_chains."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0119_isco_cofog_hs_sitc_cpc21_chains"
down_revision = 'r_0118_isco_cofog_bec_cpc21_isic_gaps'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_hs2017'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2017_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_hs2017'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2017_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_sitc4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc4_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_cofog'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_hs2017'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2017_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_hs2017'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2017_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_sitc4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc4_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_cofog'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
