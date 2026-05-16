"""Captured from Kysely migration 0124_asfis_remaining_atc_sdg_isic4."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_0124_asfis_remaining_atc_sdg_isic4"
down_revision = 'r_0123_asfis_hs_sitc_full_connectivity'
branch_labels = None
depends_on = None

UP = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_hs2017'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2017_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_sitc4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc4_sdg'", 'parameters': []}]

DOWN = [{'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_cpc3'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc3_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'asfis_bec'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'bec_asfis'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'atc_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_atc'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_isic4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic4_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_hs2017'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'hs2017_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_isic5'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'isic5_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_nace'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'nace_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_cpc21'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'cpc21_sdg'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sdg_sitc4'", 'parameters': []},
 {'sql': "DELETE FROM edge_classified_as WHERE system = 'sitc4_sdg'", 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
