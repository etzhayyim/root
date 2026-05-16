"""Captured from Kysely migration 0131_atc_cpc3_naics_isic31_isic2_chains."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0131_atc_cpc3_naics_isic31_isic2_chains"
down_revision = 'r_0130_gho_fixes_icd10_sdg_ndc_extended'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic2_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_isic2'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic2_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_isic2'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
