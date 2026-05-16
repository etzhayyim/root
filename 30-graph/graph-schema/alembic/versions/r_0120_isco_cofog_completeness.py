"""Captured from Kysely migration 0120_isco_cofog_completeness."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0120_isco_cofog_completeness"
down_revision = 'r_0119_isco_cofog_hs_sitc_cpc21_chains'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_hs2022'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2022_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_hs2012'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2012_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_hs2007'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2007_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_hs2002'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2002_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_hs1996'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs1996_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_hs2022'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2022_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_sitc4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc4_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_sitc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc3_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_isic2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic2_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_isco'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_hs2022'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2022_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_hs2012'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2012_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_hs2007'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2007_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_hs2002'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2002_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_hs1996'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs1996_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_hs2022'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2022_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_sitc4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc4_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_sitc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc3_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_isic2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic2_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_isco'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
