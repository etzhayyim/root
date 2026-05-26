"""Captured from Kysely migration 20260428350000_seed_deceased_cohort_persons."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428350000_seed_deceased_cohort_persons"
down_revision = 'r_20260428340000_vertex_whois_record_netintel_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-prehistoric-infectious_disease',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-prehistoric-infectious_disease',
                 'at://did:web:natural-person.etzhayyim.com',
                 '707265686973746f',
                 'did:web:natural-person.etzhayyim.com:deceased:prehistoric:infectious_disease',
                 '-100000',
                 '-10000',
                 'A00-B99',
                 'prehistoric',
                 'pop-chain:prehistoric:infectious_disease',
                 875000000,
                 'low',
                 'public',
                 'ADR-0018 §historical: era=prehistoric → public; estimate McEvedy-Jones 1978',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-prehistoric-infectious_disease',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-prehistoric-infectious_disease',
                 'did:web:natural-person.etzhayyim.com',
                 '0001-01-01']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-prehistoric-infectious_disease',
                 'did:web:natural-person.etzhayyim.com:deceased:prehistoric:infectious_disease',
                 'prehistoric.infectious_disease',
                 '707265686973746f',
                 875,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-prehistoric-trauma_injury',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-prehistoric-trauma_injury',
                 'at://did:web:natural-person.etzhayyim.com',
                 '707265686973746f',
                 'did:web:natural-person.etzhayyim.com:deceased:prehistoric:trauma_injury',
                 '-100000',
                 '-10000',
                 'S00-T98',
                 'prehistoric',
                 'pop-chain:prehistoric:trauma_injury',
                 750000000,
                 'low',
                 'public',
                 'ADR-0018 §historical: era=prehistoric → public; fossil record evidence',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-prehistoric-trauma_injury',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-prehistoric-trauma_injury',
                 'did:web:natural-person.etzhayyim.com',
                 '0001-01-01']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-prehistoric-trauma_injury',
                 'did:web:natural-person.etzhayyim.com:deceased:prehistoric:trauma_injury',
                 'prehistoric.trauma_injury',
                 '707265686973746f',
                 750,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-prehistoric-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-prehistoric-nutritional_deficiency',
                 'at://did:web:natural-person.etzhayyim.com',
                 '707265686973746f',
                 'did:web:natural-person.etzhayyim.com:deceased:prehistoric:nutritional_deficiency',
                 '-100000',
                 '-10000',
                 'E40-E46',
                 'prehistoric',
                 'pop-chain:prehistoric:nutritional_deficiency',
                 500000000,
                 'low',
                 'public',
                 'ADR-0018 §historical: era=prehistoric → public; climate/famine cycles',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-prehistoric-nutritional_deficiency',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-prehistoric-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com',
                 '0001-01-01']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-prehistoric-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com:deceased:prehistoric:nutritional_deficiency',
                 'prehistoric.nutritional_deficiency',
                 '707265686973746f',
                 500,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-prehistoric-maternal_perinatal',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-prehistoric-maternal_perinatal',
                 'at://did:web:natural-person.etzhayyim.com',
                 '707265686973746f',
                 'did:web:natural-person.etzhayyim.com:deceased:prehistoric:maternal_perinatal',
                 '-100000',
                 '-10000',
                 'O00-O99',
                 'prehistoric',
                 'pop-chain:prehistoric:maternal_perinatal',
                 250000000,
                 'low',
                 'public',
                 'ADR-0018 §historical: era=prehistoric → public; MMR >2000/100k births',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-prehistoric-maternal_perinatal',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-prehistoric-maternal_perinatal',
                 'did:web:natural-person.etzhayyim.com',
                 '0001-01-01']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-prehistoric-maternal_perinatal',
                 'did:web:natural-person.etzhayyim.com:deceased:prehistoric:maternal_perinatal',
                 'prehistoric.maternal_perinatal',
                 '707265686973746f',
                 250,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-prehistoric-cardiovascular',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-prehistoric-cardiovascular',
                 'at://did:web:natural-person.etzhayyim.com',
                 '707265686973746f',
                 'did:web:natural-person.etzhayyim.com:deceased:prehistoric:cardiovascular',
                 '-100000',
                 '-10000',
                 'I00-I99',
                 'prehistoric',
                 'pop-chain:prehistoric:cardiovascular',
                 125000000,
                 'low',
                 'public',
                 'ADR-0018 §historical: era=prehistoric → public; low incidence short life',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-prehistoric-cardiovascular',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-prehistoric-cardiovascular',
                 'did:web:natural-person.etzhayyim.com',
                 '0001-01-01']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-prehistoric-cardiovascular',
                 'did:web:natural-person.etzhayyim.com:deceased:prehistoric:cardiovascular',
                 'prehistoric.cardiovascular',
                 '707265686973746f',
                 125,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-ancient-infectious_disease',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-ancient-infectious_disease',
                 'at://did:web:natural-person.etzhayyim.com',
                 '616e6369656e747c',
                 'did:web:natural-person.etzhayyim.com:deceased:ancient:infectious_disease',
                 '-10000',
                 '500',
                 'A00-B99',
                 'ancient',
                 'pop-chain:ancient:infectious_disease',
                 3200000000,
                 'medium',
                 'public',
                 'ADR-0018 §historical: era=ancient → public; Antonine Plague, Athenian Plague',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-ancient-infectious_disease',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-ancient-infectious_disease',
                 'did:web:natural-person.etzhayyim.com',
                 '500-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-ancient-infectious_disease',
                 'did:web:natural-person.etzhayyim.com:deceased:ancient:infectious_disease',
                 'ancient.infectious_disease',
                 '616e6369656e747c',
                 3200,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-ancient-trauma_injury',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-ancient-trauma_injury',
                 'at://did:web:natural-person.etzhayyim.com',
                 '616e6369656e747c',
                 'did:web:natural-person.etzhayyim.com:deceased:ancient:trauma_injury',
                 '-10000',
                 '500',
                 'S00-T98',
                 'ancient',
                 'pop-chain:ancient:trauma_injury',
                 1600000000,
                 'medium',
                 'public',
                 'ADR-0018 §historical: era=ancient → public; Mongol conquests, Roman wars',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-ancient-trauma_injury',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-ancient-trauma_injury',
                 'did:web:natural-person.etzhayyim.com',
                 '500-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-ancient-trauma_injury',
                 'did:web:natural-person.etzhayyim.com:deceased:ancient:trauma_injury',
                 'ancient.trauma_injury',
                 '616e6369656e747c',
                 1600,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-ancient-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-ancient-nutritional_deficiency',
                 'at://did:web:natural-person.etzhayyim.com',
                 '616e6369656e747c',
                 'did:web:natural-person.etzhayyim.com:deceased:ancient:nutritional_deficiency',
                 '-10000',
                 '500',
                 'E40-E46',
                 'ancient',
                 'pop-chain:ancient:nutritional_deficiency',
                 1600000000,
                 'medium',
                 'public',
                 'ADR-0018 §historical: era=ancient → public; agricultural failure cycles',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-ancient-nutritional_deficiency',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-ancient-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com',
                 '500-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-ancient-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com:deceased:ancient:nutritional_deficiency',
                 'ancient.nutritional_deficiency',
                 '616e6369656e747c',
                 1600,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-ancient-maternal_perinatal',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-ancient-maternal_perinatal',
                 'at://did:web:natural-person.etzhayyim.com',
                 '616e6369656e747c',
                 'did:web:natural-person.etzhayyim.com:deceased:ancient:maternal_perinatal',
                 '-10000',
                 '500',
                 'O00-O99',
                 'ancient',
                 'pop-chain:ancient:maternal_perinatal',
                 800000000,
                 'medium',
                 'public',
                 'ADR-0018 §historical: era=ancient → public; MMR ~1500/100k births',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-ancient-maternal_perinatal',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-ancient-maternal_perinatal',
                 'did:web:natural-person.etzhayyim.com',
                 '500-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-ancient-maternal_perinatal',
                 'did:web:natural-person.etzhayyim.com:deceased:ancient:maternal_perinatal',
                 'ancient.maternal_perinatal',
                 '616e6369656e747c',
                 800,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-ancient-cardiovascular',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-ancient-cardiovascular',
                 'at://did:web:natural-person.etzhayyim.com',
                 '616e6369656e747c',
                 'did:web:natural-person.etzhayyim.com:deceased:ancient:cardiovascular',
                 '-10000',
                 '500',
                 'I00-I99',
                 'ancient',
                 'pop-chain:ancient:cardiovascular',
                 800000000,
                 'medium',
                 'public',
                 'ADR-0018 §historical: era=ancient → public; Galen era cardiac descriptions',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-ancient-cardiovascular',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-ancient-cardiovascular',
                 'did:web:natural-person.etzhayyim.com',
                 '500-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-ancient-cardiovascular',
                 'did:web:natural-person.etzhayyim.com:deceased:ancient:cardiovascular',
                 'ancient.cardiovascular',
                 '616e6369656e747c',
                 800,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-medieval-infectious_disease',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-medieval-infectious_disease',
                 'at://did:web:natural-person.etzhayyim.com',
                 '6d6564696576616c',
                 'did:web:natural-person.etzhayyim.com:deceased:medieval:infectious_disease',
                 '500',
                 '1500',
                 'A00-B99',
                 'medieval',
                 'pop-chain:medieval:infectious_disease',
                 2700000000,
                 'medium',
                 'public',
                 'ADR-0018 §historical: era=medieval → public; Black Death 75-200M deaths',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-medieval-infectious_disease',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/medieval-001-1000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-medieval-infectious_disease',
                 'did:web:natural-person.etzhayyim.com',
                 '1500-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-medieval-infectious_disease',
                 'did:web:natural-person.etzhayyim.com:deceased:medieval:infectious_disease',
                 'medieval.infectious_disease',
                 '6d6564696576616c',
                 2700,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/medieval-001-1000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-medieval-trauma_injury',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-medieval-trauma_injury',
                 'at://did:web:natural-person.etzhayyim.com',
                 '6d6564696576616c',
                 'did:web:natural-person.etzhayyim.com:deceased:medieval:trauma_injury',
                 '500',
                 '1500',
                 'S00-T98',
                 'medieval',
                 'pop-chain:medieval:trauma_injury',
                 1200000000,
                 'medium',
                 'public',
                 'ADR-0018 §historical: era=medieval → public; Mongol conquest est. 40M deaths',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-medieval-trauma_injury',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/medieval-001-1000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-medieval-trauma_injury',
                 'did:web:natural-person.etzhayyim.com',
                 '1500-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-medieval-trauma_injury',
                 'did:web:natural-person.etzhayyim.com:deceased:medieval:trauma_injury',
                 'medieval.trauma_injury',
                 '6d6564696576616c',
                 1200,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/medieval-001-1000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-medieval-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-medieval-nutritional_deficiency',
                 'at://did:web:natural-person.etzhayyim.com',
                 '6d6564696576616c',
                 'did:web:natural-person.etzhayyim.com:deceased:medieval:nutritional_deficiency',
                 '500',
                 '1500',
                 'E40-E46',
                 'medieval',
                 'pop-chain:medieval:nutritional_deficiency',
                 1200000000,
                 'medium',
                 'public',
                 'ADR-0018 §historical: era=medieval → public; Great Famine 1315-22, drought',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-medieval-nutritional_deficiency',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/medieval-001-1000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-medieval-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com',
                 '1500-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-medieval-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com:deceased:medieval:nutritional_deficiency',
                 'medieval.nutritional_deficiency',
                 '6d6564696576616c',
                 1200,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/medieval-001-1000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-medieval-maternal_perinatal',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-medieval-maternal_perinatal',
                 'at://did:web:natural-person.etzhayyim.com',
                 '6d6564696576616c',
                 'did:web:natural-person.etzhayyim.com:deceased:medieval:maternal_perinatal',
                 '500',
                 '1500',
                 'O00-O99',
                 'medieval',
                 'pop-chain:medieval:maternal_perinatal',
                 600000000,
                 'medium',
                 'public',
                 'ADR-0018 §historical: era=medieval → public; MMR ~1200/100k births',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-medieval-maternal_perinatal',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/medieval-001-1000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-medieval-maternal_perinatal',
                 'did:web:natural-person.etzhayyim.com',
                 '1500-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-medieval-maternal_perinatal',
                 'did:web:natural-person.etzhayyim.com:deceased:medieval:maternal_perinatal',
                 'medieval.maternal_perinatal',
                 '6d6564696576616c',
                 600,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/medieval-001-1000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-medieval-cardiovascular',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-medieval-cardiovascular',
                 'at://did:web:natural-person.etzhayyim.com',
                 '6d6564696576616c',
                 'did:web:natural-person.etzhayyim.com:deceased:medieval:cardiovascular',
                 '500',
                 '1500',
                 'I00-I99',
                 'medieval',
                 'pop-chain:medieval:cardiovascular',
                 300000000,
                 'medium',
                 'public',
                 'ADR-0018 §historical: era=medieval → public; low due to short life span',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-medieval-cardiovascular',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/medieval-001-1000',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-medieval-cardiovascular',
                 'did:web:natural-person.etzhayyim.com',
                 '1500-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-medieval-cardiovascular',
                 'did:web:natural-person.etzhayyim.com:deceased:medieval:cardiovascular',
                 'medieval.cardiovascular',
                 '6d6564696576616c',
                 300,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/medieval-001-1000',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-industrial-infectious_disease',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-industrial-infectious_disease',
                 'at://did:web:natural-person.etzhayyim.com',
                 '696e647573747269',
                 'did:web:natural-person.etzhayyim.com:deceased:industrial:infectious_disease',
                 '1500',
                 '1900',
                 'A00-B99',
                 'industrial',
                 'pop-chain:industrial:infectious_disease',
                 4200000000,
                 'high',
                 'public',
                 'ADR-0018 §historical: era=industrial → public; cholera pandemics, TB White '
                 'Plague',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-industrial-infectious_disease',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-industrial-infectious_disease',
                 'did:web:natural-person.etzhayyim.com',
                 '1900-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-industrial-infectious_disease',
                 'did:web:natural-person.etzhayyim.com:deceased:industrial:infectious_disease',
                 'industrial.infectious_disease',
                 '696e647573747269',
                 4200,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-industrial-cardiovascular',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-industrial-cardiovascular',
                 'at://did:web:natural-person.etzhayyim.com',
                 '696e647573747269',
                 'did:web:natural-person.etzhayyim.com:deceased:industrial:cardiovascular',
                 '1500',
                 '1900',
                 'I00-I99',
                 'industrial',
                 'pop-chain:industrial:cardiovascular',
                 2400000000,
                 'high',
                 'public',
                 'ADR-0018 §historical: era=industrial → public; rising with improved life '
                 'expectancy',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-industrial-cardiovascular',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-industrial-cardiovascular',
                 'did:web:natural-person.etzhayyim.com',
                 '1900-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-industrial-cardiovascular',
                 'did:web:natural-person.etzhayyim.com:deceased:industrial:cardiovascular',
                 'industrial.cardiovascular',
                 '696e647573747269',
                 2400,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-industrial-trauma_injury',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-industrial-trauma_injury',
                 'at://did:web:natural-person.etzhayyim.com',
                 '696e647573747269',
                 'did:web:natural-person.etzhayyim.com:deceased:industrial:trauma_injury',
                 '1500',
                 '1900',
                 'S00-T98',
                 'industrial',
                 'pop-chain:industrial:trauma_injury',
                 1800000000,
                 'high',
                 'public',
                 'ADR-0018 §historical: era=industrial → public; Americas collapse 50-80M',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-industrial-trauma_injury',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-industrial-trauma_injury',
                 'did:web:natural-person.etzhayyim.com',
                 '1900-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-industrial-trauma_injury',
                 'did:web:natural-person.etzhayyim.com:deceased:industrial:trauma_injury',
                 'industrial.trauma_injury',
                 '696e647573747269',
                 1800,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-industrial-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-industrial-nutritional_deficiency',
                 'at://did:web:natural-person.etzhayyim.com',
                 '696e647573747269',
                 'did:web:natural-person.etzhayyim.com:deceased:industrial:nutritional_deficiency',
                 '1500',
                 '1900',
                 'E40-E46',
                 'industrial',
                 'pop-chain:industrial:nutritional_deficiency',
                 1800000000,
                 'high',
                 'public',
                 'ADR-0018 §historical: era=industrial → public; Bengal, Irish famines',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-industrial-nutritional_deficiency',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-industrial-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com',
                 '1900-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-industrial-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com:deceased:industrial:nutritional_deficiency',
                 'industrial.nutritional_deficiency',
                 '696e647573747269',
                 1800,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-industrial-maternal_perinatal',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-industrial-maternal_perinatal',
                 'at://did:web:natural-person.etzhayyim.com',
                 '696e647573747269',
                 'did:web:natural-person.etzhayyim.com:deceased:industrial:maternal_perinatal',
                 '1500',
                 '1900',
                 'O00-O99',
                 'industrial',
                 'pop-chain:industrial:maternal_perinatal',
                 1800000000,
                 'high',
                 'public',
                 'ADR-0018 §historical: era=industrial → public; MMR ~600/100k births '
                 'pre-Semmelweis',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-industrial-maternal_perinatal',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-industrial-maternal_perinatal',
                 'did:web:natural-person.etzhayyim.com',
                 '1900-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-industrial-maternal_perinatal',
                 'did:web:natural-person.etzhayyim.com:deceased:industrial:maternal_perinatal',
                 'industrial.maternal_perinatal',
                 '696e647573747269',
                 1800,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-modern-cardiovascular',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-modern-cardiovascular',
                 'at://did:web:natural-person.etzhayyim.com',
                 '6d6f6465726e7c63',
                 'did:web:natural-person.etzhayyim.com:deceased:modern:cardiovascular',
                 '1900',
                 '2025',
                 'I00-I99',
                 'modern',
                 'pop-chain:modern:cardiovascular',
                 1750000000,
                 'high',
                 'internal',
                 'ADR-0018 §deceased_no_protect: JPN/GBR/IND/USA no perpetual protection → '
                 'internal',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-modern-cardiovascular',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-modern-cardiovascular',
                 'did:web:natural-person.etzhayyim.com',
                 '2025-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-modern-cardiovascular',
                 'did:web:natural-person.etzhayyim.com:deceased:modern:cardiovascular',
                 'modern.cardiovascular',
                 '6d6f6465726e7c63',
                 1750,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-modern-infectious_disease',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-modern-infectious_disease',
                 'at://did:web:natural-person.etzhayyim.com',
                 '6d6f6465726e7c69',
                 'did:web:natural-person.etzhayyim.com:deceased:modern:infectious_disease',
                 '1900',
                 '2025',
                 'A00-B99',
                 'modern',
                 'pop-chain:modern:infectious_disease',
                 1000000000,
                 'high',
                 'internal',
                 'ADR-0018: Spanish flu 50M, COVID 7M, HIV/AIDS 40M, TB ongoing 1.5M/yr',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-modern-infectious_disease',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-modern-infectious_disease',
                 'did:web:natural-person.etzhayyim.com',
                 '2025-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-modern-infectious_disease',
                 'did:web:natural-person.etzhayyim.com:deceased:modern:infectious_disease',
                 'modern.infectious_disease',
                 '6d6f6465726e7c69',
                 1000,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-modern-neoplasms',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-modern-neoplasms',
                 'at://did:web:natural-person.etzhayyim.com',
                 '6d6f6465726e7c6e',
                 'did:web:natural-person.etzhayyim.com:deceased:modern:neoplasms',
                 '1900',
                 '2025',
                 'C00-D48',
                 'modern',
                 'pop-chain:modern:neoplasms',
                 750000000,
                 'high',
                 'internal',
                 'ADR-0018: modern cancer burden 10M deaths/yr; WHO 2023 leading cause',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-modern-neoplasms',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-modern-neoplasms',
                 'did:web:natural-person.etzhayyim.com',
                 '2025-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-modern-neoplasms',
                 'did:web:natural-person.etzhayyim.com:deceased:modern:neoplasms',
                 'modern.neoplasms',
                 '6d6f6465726e7c6e',
                 750,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-modern-trauma_injury',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-modern-trauma_injury',
                 'at://did:web:natural-person.etzhayyim.com',
                 '6d6f6465726e7c74',
                 'did:web:natural-person.etzhayyim.com:deceased:modern:trauma_injury',
                 '1900',
                 '2025',
                 'S00-T98',
                 'modern',
                 'pop-chain:modern:trauma_injury',
                 750000000,
                 'high',
                 'internal',
                 'ADR-0018: WWI 20M, WWII 70-85M, road traffic 1.35M/yr (WHO 2023)',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-modern-trauma_injury',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-modern-trauma_injury',
                 'did:web:natural-person.etzhayyim.com',
                 '2025-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-modern-trauma_injury',
                 'did:web:natural-person.etzhayyim.com:deceased:modern:trauma_injury',
                 'modern.trauma_injury',
                 '6d6f6465726e7c74',
                 750,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '      INSERT INTO vertex_natural_person_cohort_person (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        cohort_hash, cohort_did,\n'
         '        country, vital_status,\n'
         '        birth_year, death_year, death_cause_icd10, era,\n'
         '        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,\n'
         '        data_classification, rationale,\n'
         '        actor_did, org_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 300,\n"
         '        $2, $3, $4,\n'
         '        $5, $6,\n'
         "        'WORLD', 'deceased',\n"
         '        $7, $8, $9, $10,\n'
         '        $11,\n'
         "        $12, $13, 'PopulationCohort',\n"
         '        $14, $15,\n'
         '        $16, $17, $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-modern-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com',
                 'deceased-modern-nutritional_deficiency',
                 'at://did:web:natural-person.etzhayyim.com',
                 '6d6f6465726e7c6e',
                 'did:web:natural-person.etzhayyim.com:deceased:modern:nutritional_deficiency',
                 '1900',
                 '2025',
                 'E40-E46',
                 'modern',
                 'pop-chain:modern:nutritional_deficiency',
                 750000000,
                 'high',
                 'internal',
                 'ADR-0018: Chinese famine 15-55M, Bengal 1943 3M, Great Leap 15-55M',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_derived (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, owner_did,\n'
         '        posterior, fission_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', $4,\n"
         '        0.85, $5\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortDerived/derv-modern-nutritional_deficiency',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortPerson/deceased-modern-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com',
                 '2025-12-31']},
 {'sql': '\n'
         '      INSERT INTO vertex_cohort_actor (\n'
         '        vertex_id, cohort_did, handle,\n'
         '        kind, segment_hash, k_anonymity,\n'
         '        fission_enabled, derived_from, status,\n'
         '        genesis_at, owner_did, _seq, created_date,\n'
         '        actor_did, org_did\n'
         '      ) VALUES (\n'
         '        $1, $2,\n'
         '        $3,\n'
         "        'deceased_population_cohort',\n"
         '        $4,\n'
         '        $5,\n'
         '        false,\n'
         '        $6,\n'
         "        'active',\n"
         "        $7, $8, 1, '2026-04-28',\n"
         '        $9, $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.cohortActor/deceased-modern-nutritional_deficiency',
                 'did:web:natural-person.etzhayyim.com:deceased:modern:nutritional_deficiency',
                 'modern.nutritional_deficiency',
                 '6d6f6465726e7c6e',
                 750,
                 'at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 '2026-04-28T00:00:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com']},
 {'sql': '\n'
         '    UPDATE dim_world_domain\n'
         "    SET unit = 'humans ever lived (100k BCE–2025 CE: 108B total, $1 deceased cohort "
         "classes)'\n"
         "    WHERE app_host = 'natural-person'\n"
         '  ',
  'parameters': [25]}]

DOWN = [{'sql': '\n'
         '    DELETE FROM vertex_natural_person_cohort_person\n'
         "    WHERE rkey LIKE 'deceased-%'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    DELETE FROM edge_cohort_derived\n'
         "    WHERE edge_id LIKE '%/cohortDerived/derv-%'\n"
         '  ',
  'parameters': []},
 {'sql': "\n    DELETE FROM vertex_cohort_actor\n    WHERE kind = 'deceased_population_cohort'\n  ",
  'parameters': []},
 {'sql': '\n'
         '    UPDATE dim_world_domain\n'
         "    SET unit = 'humans ever lived (100k-year historical scope)'\n"
         "    WHERE app_host = 'natural-person'\n"
         '  ',
  'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
