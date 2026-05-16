"""Captured from Kysely migration 0123_asfis_hs_sitc_full_connectivity."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0123_asfis_hs_sitc_full_connectivity"
down_revision = 'r_0122_cofog_hs2012_asfis_isic4_bridges'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_hs2017'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2017_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_hs2022'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2022_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_hs2012'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2012_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_hs2007'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2007_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_hs2002'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2002_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_hs1996'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs1996_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_sitc4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc4_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_sitc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc3_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_sitc2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc2_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_sitc1'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc1_asfis'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_hs2017'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2017_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_hs2022'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2022_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_hs2012'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2012_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_hs2007'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2007_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_hs2002'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2002_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_hs1996'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs1996_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_sitc4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc4_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_sitc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc3_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_sitc2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc2_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_sitc1'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc1_asfis'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
