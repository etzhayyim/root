"""Captured from Kysely migration 0129_icd10_cpc3_gho_bridges."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0129_icd10_cpc3_gho_bridges"
down_revision = 'r_0128_icd10_extended_chains'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_gho'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_gho'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
