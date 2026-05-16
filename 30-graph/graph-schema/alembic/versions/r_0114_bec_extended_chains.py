"""Captured from Kysely migration 0114_bec_extended_chains."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0114_bec_extended_chains"
down_revision = 'r_0113_cpc21_fanout_repair'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'naics_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_naics'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'naics_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_naics'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
