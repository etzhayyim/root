"""Captured from Kysely migration 0130_gho_fixes_icd10_sdg_ndc_extended."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0130_gho_fixes_icd10_sdg_ndc_extended"
down_revision = 'r_0129_icd10_cpc3_gho_bridges'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_ndc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_ndc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_ndc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_ndc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_ndc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_gho'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_gho'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_ndc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_ndc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_ndc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_ndc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_ndc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'gho_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_gho'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
