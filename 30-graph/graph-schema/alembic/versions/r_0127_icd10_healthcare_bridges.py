"""Captured from Kysely migration 0127_icd10_healthcare_bridges."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0127_icd10_healthcare_bridges"
down_revision = 'r_0126_ndc_isic4_bridge'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_icd10'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_icd10'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
