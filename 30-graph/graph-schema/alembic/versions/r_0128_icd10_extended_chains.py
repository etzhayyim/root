"""Captured from Kysely migration 0128_icd10_extended_chains."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0128_icd10_extended_chains"
down_revision = 'r_0127_icd10_healthcare_bridges'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_icd10'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_icd10'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'icd10_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_icd10'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
