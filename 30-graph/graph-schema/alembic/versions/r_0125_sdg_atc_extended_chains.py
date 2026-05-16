"""Captured from Kysely migration 0125_sdg_atc_extended_chains."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0125_sdg_atc_extended_chains"
down_revision = 'r_0124_asfis_remaining_atc_sdg_isic4'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_hs2022'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2022_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_hs2012'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2012_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_hs2007'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2007_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_hs2002'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2002_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_hs1996'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs1996_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_sitc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc3_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_sitc2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc2_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_sitc1'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc1_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_hs2017'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2017_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_hs2022'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2022_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_sitc4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc4_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_atc'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_hs2022'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2022_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_hs2012'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2012_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_hs2007'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2007_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_hs2002'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2002_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_hs1996'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs1996_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_sitc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc3_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_sitc2'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc2_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_sitc1'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc1_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_cofog'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cofog_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_isco'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isco_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_hs2017'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2017_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_hs2022'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2022_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_sitc4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc4_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_atc'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
