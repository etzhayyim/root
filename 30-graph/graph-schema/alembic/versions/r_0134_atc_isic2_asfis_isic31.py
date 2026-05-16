"""Captured from Kysely migration 0134_atc_isic2_asfis_isic31."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0134_atc_isic2_asfis_isic31"
down_revision = 'r_0133_atc_hs_legacy_sitc_ndc_bec'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_isic2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic2_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_asfis'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_isic2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic2_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_asfis'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
