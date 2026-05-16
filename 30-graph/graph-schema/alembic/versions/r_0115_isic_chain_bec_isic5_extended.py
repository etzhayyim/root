"""Captured from Kysely migration 0115_isic_chain_bec_isic5_extended."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0115_isic_chain_bec_isic5_extended"
down_revision = 'r_0114_bec_extended_chains'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic2_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_isic2'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic31_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_isic31'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic2_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_isic2'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
