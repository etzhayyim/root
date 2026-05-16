"""Captured from Kysely migration 0110_naics_reverses_cpc3_sitc4_repair_iso639."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0110_naics_reverses_cpc3_sitc4_repair_iso639"
down_revision = 'r_0109_bidirectional_coverage_repair'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_naics'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_naics'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_naics'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'macro_iso639_3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_sitc4'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_naics'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_naics'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_naics'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'macro_iso639_3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_sitc4'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
