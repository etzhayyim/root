"""Captured from Kysely migration 20260430183500_repair_natural_person_cohort_hashes."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430183500_repair_natural_person_cohort_hashes"
down_revision = 'r_20260430182000_seed_natural_person_reconcile_visibility_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    SELECT vertex_id, cohort_hash,\n'
         '           country, region, municipality, age, gender,\n'
         '           income_decile, education_isced, occupation_isco, employment_status,\n'
         '           marital_status, household_size, housing_tenure, urban_rural,\n'
         '           health_icd10, disability_type, migration_status,\n'
         '           ethnicity, religion, language_primary,\n'
         '           entity_did, community_id,\n'
         '           vital_status, birth_year, death_year,\n'
         '           death_cause_icd10, era\n'
         '      FROM vertex_natural_person_cohort_person\n'
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
