"""Captured from Kysely migration 0112_bec_hs_sitc_bridges."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0112_bec_hs_sitc_bridges"
down_revision = 'r_0111_r_suffix_cleanup_sitc_asym_fix'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2017_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_hs2017'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2022_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_hs2022'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2012_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_hs2012'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2007_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_hs2007'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2002_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_hs2002'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs1996_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_hs1996'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc4_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_sitc4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc3_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_sitc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc2_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_sitc2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc1_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_sitc1'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2017_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_hs2017'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2022_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_hs2022'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2012_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_hs2012'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2007_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_hs2007'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2002_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_hs2002'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs1996_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_hs1996'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc4_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_sitc4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc3_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_sitc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc2_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_sitc2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc1_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_sitc1'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
