"""Captured from Kysely migration 0126_ndc_isic4_bridge."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0126_ndc_isic4_bridge"
down_revision = 'r_0125_sdg_atc_extended_chains'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_ndc'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_ndc'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
