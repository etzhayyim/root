"""Captured from Kysely migration 0132_ndc_icd10_asfis_sdg_bridges."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0132_ndc_icd10_asfis_sdg_bridges"
down_revision = 'r_0131_atc_cpc3_naics_isic31_isic2_chains'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_ndc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_isic2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic2_ndc'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_ndc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_isic2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic2_ndc'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
