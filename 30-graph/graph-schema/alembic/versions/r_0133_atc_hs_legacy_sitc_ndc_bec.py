"""Captured from Kysely migration 0133_atc_hs_legacy_sitc_ndc_bec."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0133_atc_hs_legacy_sitc_ndc_bec"
down_revision = 'r_0132_ndc_icd10_asfis_sdg_bridges'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_hs2012'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2012_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_hs2007'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2007_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_hs2002'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2002_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_hs1996'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs1996_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_sitc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc3_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_sitc2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc2_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_sitc1'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc1_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_ndc'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_hs2012'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2012_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_hs2007'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2007_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_hs2002'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2002_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_hs1996'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs1996_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_sitc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc3_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_sitc2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc2_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_sitc1'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc1_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'ndc_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_ndc'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
