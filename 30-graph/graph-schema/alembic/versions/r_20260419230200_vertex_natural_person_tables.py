"""Captured from Kysely migration 20260419230200_vertex_natural_person_tables."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260419230200_vertex_natural_person_tables"
down_revision = 'r_20260419230100_vertex_collector_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_natural_person_cohort_person (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      cohort_hash VARCHAR, cohort_did VARCHAR,\n'
         '      country VARCHAR, region VARCHAR, municipality VARCHAR,\n'
         '      age VARCHAR, gender VARCHAR,\n'
         '      income_decile VARCHAR, education_isced VARCHAR, occupation_isco VARCHAR,\n'
         '      employment_status VARCHAR, marital_status VARCHAR,\n'
         '      household_size VARCHAR, housing_tenure VARCHAR, urban_rural VARCHAR,\n'
         '      health_icd10 VARCHAR, disability_type VARCHAR, migration_status VARCHAR,\n'
         '      ethnicity VARCHAR, religion VARCHAR, language_primary VARCHAR,\n'
         '      entity_did VARCHAR, community_id VARCHAR,\n'
         '      vital_status VARCHAR, birth_year VARCHAR, death_year VARCHAR,\n'
         '      death_cause_icd10 VARCHAR, era VARCHAR,\n'
         '      data_classification VARCHAR, rationale VARCHAR,\n'
         '      intel_chain_id VARCHAR, intel_estimated_count BIGINT,\n'
         '      intel_confidence VARCHAR, intel_entity_type VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_natural_person_identified_person (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      person_hash VARCHAR, cohort_did VARCHAR,\n'
         '      name VARCHAR, country VARCHAR, role VARCHAR, organization VARCHAR,\n'
         '      source_app VARCHAR, source_record_id VARCHAR,\n'
         '      enrichment_status VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_natural_person_person_enrichment (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      person_hash VARCHAR, enrichment_method VARCHAR, source_url VARCHAR,\n'
         '      extracted_data VARCHAR, confidence VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_natural_person_census_source (\n'
         '      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord '
         'BIGINT,\n'
         '      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,\n'
         '      source_name VARCHAR, source_org VARCHAR, source_url VARCHAR,\n'
         '      data_year VARCHAR, dimensions VARCHAR, status VARCHAR,\n'
         '      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS vertex_natural_person_census_source', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_natural_person_person_enrichment', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_natural_person_identified_person', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_natural_person_cohort_person', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
