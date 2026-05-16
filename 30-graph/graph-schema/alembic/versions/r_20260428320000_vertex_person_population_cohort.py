"""Captured from Kysely migration 20260428320000_vertex_person_population_cohort."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428320000_vertex_person_population_cohort"
down_revision = 'r_20260428310000_seed_actor_registry'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_person_population_cohort (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      _seq BIGINT,\n'
         '      created_date DATE,\n'
         '      sensitivity_ord BIGINT DEFAULT 0,\n'
         '      owner_did VARCHAR,\n'
         '      rkey VARCHAR,\n'
         '      repo VARCHAR,\n'
         '      -- Era temporal bounds (negative = BCE, e.g. -100000 = 100,000 BCE)\n'
         '      era_label VARCHAR,\n'
         '      era_start_year INTEGER,\n'
         '      era_end_year INTEGER,\n'
         '      -- Geographic scope (UN M49 codes)\n'
         '      region_m49 VARCHAR,\n'
         '      region_name VARCHAR,\n'
         '      subregion_m49 VARCHAR,\n'
         '      -- Population estimates (central + uncertainty bounds)\n'
         '      estimated_population BIGINT,\n'
         '      population_low BIGINT,\n'
         '      population_high BIGINT,\n'
         '      -- Vital statistics\n'
         '      birth_rate DOUBLE PRECISION,\n'
         '      death_rate DOUBLE PRECISION,\n'
         '      life_expectancy DOUBLE PRECISION,\n'
         '      infant_mortality_rate DOUBLE PRECISION,\n'
         '      -- Data provenance\n'
         '      data_source VARCHAR,\n'
         '      confidence_level VARCHAR,\n'
         '      -- Cohort identity (ADR-0026)\n'
         '      cohort_did VARCHAR,\n'
         '      -- ADR-0095 RLS columns\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      at_did VARCHAR,\n'
         '      created_at VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_cohort_ancestor_of (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      src_vid VARCHAR,\n'
         '      dst_vid VARCHAR,\n'
         '      _seq BIGINT,\n'
         '      created_date DATE,\n'
         '      sensitivity_ord BIGINT DEFAULT 0,\n'
         '      owner_did VARCHAR,\n'
         '      -- Ancestry relationship\n'
         '      generation_offset INTEGER,\n'
         '      temporal_gap_years INTEGER,\n'
         '      confidence DOUBLE PRECISION,\n'
         '      lineage_type VARCHAR,\n'
         '      -- ADR-0095 RLS columns\n'
         '      actor_did VARCHAR,\n'
         '      org_did VARCHAR,\n'
         '      at_did VARCHAR,\n'
         '      created_at VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_person_pop_cohort_era\n'
         '    ON vertex_person_population_cohort (era_label)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_person_pop_cohort_region\n'
         '    ON vertex_person_population_cohort (region_m49)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_person_pop_cohort_year_range\n'
         '    ON vertex_person_population_cohort (era_start_year, era_end_year)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_cohort_ancestor_src\n'
         '    ON edge_cohort_ancestor_of (src_vid)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE INDEX IF NOT EXISTS idx_edge_cohort_ancestor_dst\n'
         '    ON edge_cohort_ancestor_of (dst_vid)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_person_cohort_era_summary AS\n'
         '    SELECT\n'
         '      era_label,\n'
         '      MIN(era_start_year) AS era_start_year,\n'
         '      MAX(era_end_year)   AS era_end_year,\n'
         '      COUNT(*)            AS cohort_count,\n'
         '      SUM(estimated_population) AS total_population,\n'
         '      SUM(population_low)       AS total_population_low,\n'
         '      SUM(population_high)      AS total_population_high,\n'
         '      AVG(life_expectancy)      AS avg_life_expectancy\n'
         '    FROM vertex_person_population_cohort\n'
         "    WHERE region_m49 = '001'\n"
         '    GROUP BY era_label\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/early_paleolithic-001-100000',
                 'did:web:natural-person.gftd.ai',
                 'early_paleolithic-001-100000',
                 'at://did:web:natural-person.gftd.ai',
                 'early_paleolithic',
                 -100000,
                 -74000,
                 100000,
                 50000,
                 500000,
                 25,
                 80,
                 78,
                 400,
                 'haub_2011_prb',
                 'speculative',
                 'did:web:natural-person.gftd.ai:pop:early_paleolithic-001-100000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/toba_bottleneck-001-74000',
                 'did:web:natural-person.gftd.ai',
                 'toba_bottleneck-001-74000',
                 'at://did:web:natural-person.gftd.ai',
                 'toba_bottleneck',
                 -74000,
                 -70000,
                 5000,
                 2000,
                 10000,
                 22,
                 80,
                 79,
                 450,
                 'ambrose_1998_toba',
                 'speculative',
                 'did:web:natural-person.gftd.ai:pop:toba_bottleneck-001-74000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 'did:web:natural-person.gftd.ai',
                 'upper_paleolithic-001-70000',
                 'at://did:web:natural-person.gftd.ai',
                 'upper_paleolithic',
                 -70000,
                 -10000,
                 1000000,
                 500000,
                 3000000,
                 27,
                 75,
                 73,
                 350,
                 'mcevedy_jones_1978',
                 'low',
                 'did:web:natural-person.gftd.ai:pop:upper_paleolithic-001-70000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 'did:web:natural-person.gftd.ai',
                 'neolithic-001-10000',
                 'at://did:web:natural-person.gftd.ai',
                 'neolithic',
                 -10000,
                 -3000,
                 7000000,
                 5000000,
                 14000000,
                 30,
                 60,
                 57,
                 300,
                 'hyde_3_3',
                 'low',
                 'did:web:natural-person.gftd.ai:pop:neolithic-001-10000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/bronze_age-001-3000',
                 'did:web:natural-person.gftd.ai',
                 'bronze_age-001-3000',
                 'at://did:web:natural-person.gftd.ai',
                 'bronze_age',
                 -3000,
                 -1200,
                 50000000,
                 40000000,
                 70000000,
                 32,
                 55,
                 52,
                 250,
                 'hyde_3_3',
                 'medium',
                 'did:web:natural-person.gftd.ai:pop:bronze_age-001-3000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/iron_age-001-1200',
                 'did:web:natural-person.gftd.ai',
                 'iron_age-001-1200',
                 'at://did:web:natural-person.gftd.ai',
                 'iron_age',
                 -1200,
                 -500,
                 100000000,
                 80000000,
                 130000000,
                 33,
                 50,
                 47,
                 220,
                 'hyde_3_3',
                 'medium',
                 'did:web:natural-person.gftd.ai:pop:iron_age-001-1200',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/classical-001-500',
                 'did:web:natural-person.gftd.ai',
                 'classical-001-500',
                 'at://did:web:natural-person.gftd.ai',
                 'classical',
                 -500,
                 500,
                 260000000,
                 200000000,
                 350000000,
                 35,
                 45,
                 42,
                 200,
                 'hyde_3_3',
                 'medium',
                 'did:web:natural-person.gftd.ai:pop:classical-001-500',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/early_medieval-001-500',
                 'did:web:natural-person.gftd.ai',
                 'early_medieval-001-500',
                 'at://did:web:natural-person.gftd.ai',
                 'early_medieval',
                 500,
                 1000,
                 310000000,
                 270000000,
                 360000000,
                 33,
                 48,
                 45,
                 220,
                 'mcevedy_jones_1978',
                 'medium',
                 'did:web:natural-person.gftd.ai:pop:early_medieval-001-500',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/medieval-001-1000',
                 'did:web:natural-person.gftd.ai',
                 'medieval-001-1000',
                 'at://did:web:natural-person.gftd.ai',
                 'medieval',
                 1000,
                 1500,
                 390000000,
                 350000000,
                 440000000,
                 35,
                 45,
                 43,
                 200,
                 'mcevedy_jones_1978',
                 'medium',
                 'did:web:natural-person.gftd.ai:pop:medieval-001-1000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 'did:web:natural-person.gftd.ai',
                 'early_modern-001-1500',
                 'at://did:web:natural-person.gftd.ai',
                 'early_modern',
                 1500,
                 1700,
                 580000000,
                 500000000,
                 680000000,
                 38,
                 40,
                 37,
                 170,
                 'hyde_3_3',
                 'high',
                 'did:web:natural-person.gftd.ai:pop:early_modern-001-1500',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/pre_industrial-001-1700',
                 'did:web:natural-person.gftd.ai',
                 'pre_industrial-001-1700',
                 'at://did:web:natural-person.gftd.ai',
                 'pre_industrial',
                 1700,
                 1800,
                 890000000,
                 820000000,
                 960000000,
                 40,
                 38,
                 35,
                 150,
                 'hyde_3_3',
                 'high',
                 'did:web:natural-person.gftd.ai:pop:pre_industrial-001-1700',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/industrial-001-1800',
                 'did:web:natural-person.gftd.ai',
                 'industrial-001-1800',
                 'at://did:web:natural-person.gftd.ai',
                 'industrial',
                 1800,
                 1900,
                 1600000000,
                 1500000000,
                 1700000000,
                 45,
                 35,
                 30,
                 120,
                 'hyde_3_3',
                 'high',
                 'did:web:natural-person.gftd.ai:pop:industrial-001-1800',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 'did:web:natural-person.gftd.ai',
                 'modern_early-001-1900',
                 'at://did:web:natural-person.gftd.ai',
                 'modern_early',
                 1900,
                 1950,
                 2536000000,
                 2400000000,
                 2600000000,
                 48,
                 36,
                 25,
                 100,
                 'un_wpp_2024',
                 'high',
                 'did:web:natural-person.gftd.ai:pop:modern_early-001-1900',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_boom-001-1950',
                 'did:web:natural-person.gftd.ai',
                 'modern_boom-001-1950',
                 'at://did:web:natural-person.gftd.ai',
                 'modern_boom',
                 1950,
                 1975,
                 4000000000,
                 3900000000,
                 4100000000,
                 56,
                 32,
                 14,
                 75,
                 'un_wpp_2024',
                 'high',
                 'did:web:natural-person.gftd.ai:pop:modern_boom-001-1950',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_transition-001-1975',
                 'did:web:natural-person.gftd.ai',
                 'modern_transition-001-1975',
                 'at://did:web:natural-person.gftd.ai',
                 'modern_transition',
                 1975,
                 2000,
                 6100000000,
                 6050000000,
                 6150000000,
                 65,
                 24,
                 9,
                 55,
                 'un_wpp_2024',
                 'high',
                 'did:web:natural-person.gftd.ai:pop:modern_transition-001-1975',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_person_population_cohort (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, rkey, repo,\n'
         '        era_label, era_start_year, era_end_year,\n'
         '        region_m49, region_name,\n'
         '        estimated_population, population_low, population_high,\n'
         '        life_expectancy, birth_rate, death_rate, infant_mortality_rate,\n'
         '        data_source, confidence_level,\n'
         '        cohort_did,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         "        $1, 1, '2026-04-28', 0,\n"
         '        $2, $3, $4,\n'
         '        $5, $6, $7,\n'
         "        '001', 'World',\n"
         '        $8, $9, $10,\n'
         '        $11, $12, $13, $14,\n'
         '        $15, $16,\n'
         '        $17,\n'
         '        $18, $19, null, $20\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
                 'did:web:natural-person.gftd.ai',
                 'contemporary-001-2000',
                 'at://did:web:natural-person.gftd.ai',
                 'contemporary',
                 2000,
                 2025,
                 8200000000,
                 8100000000,
                 8300000000,
                 73,
                 18,
                 8,
                 28,
                 'un_wpp_2024',
                 'high',
                 'did:web:natural-person.gftd.ai:pop:contemporary-001-2000',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-early_paleolithic-toba_bottleneck',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/early_paleolithic-001-100000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/toba_bottleneck-001-74000',
                 'did:web:natural-person.gftd.ai',
                 1040,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-toba_bottleneck-upper_paleolithic',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/toba_bottleneck-001-74000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 'did:web:natural-person.gftd.ai',
                 160,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-upper_paleolithic-neolithic',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/upper_paleolithic-001-70000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 'did:web:natural-person.gftd.ai',
                 2400,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-neolithic-bronze_age',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/neolithic-001-10000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/bronze_age-001-3000',
                 'did:web:natural-person.gftd.ai',
                 280,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-bronze_age-iron_age',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/bronze_age-001-3000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/iron_age-001-1200',
                 'did:web:natural-person.gftd.ai',
                 72,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-iron_age-classical',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/iron_age-001-1200',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/classical-001-500',
                 'did:web:natural-person.gftd.ai',
                 28,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-classical-early_medieval',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/classical-001-500',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/early_medieval-001-500',
                 'did:web:natural-person.gftd.ai',
                 40,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-early_medieval-medieval',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/early_medieval-001-500',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/medieval-001-1000',
                 'did:web:natural-person.gftd.ai',
                 20,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-medieval-early_modern',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/medieval-001-1000',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 'did:web:natural-person.gftd.ai',
                 20,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-early_modern-pre_industrial',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/early_modern-001-1500',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/pre_industrial-001-1700',
                 'did:web:natural-person.gftd.ai',
                 8,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-pre_industrial-industrial',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/pre_industrial-001-1700',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/industrial-001-1800',
                 'did:web:natural-person.gftd.ai',
                 4,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-industrial-modern_early',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/industrial-001-1800',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 'did:web:natural-person.gftd.ai',
                 4,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-modern_early-modern_boom',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_early-001-1900',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_boom-001-1950',
                 'did:web:natural-person.gftd.ai',
                 2,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-modern_boom-modern_transition',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_boom-001-1950',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_transition-001-1975',
                 'did:web:natural-person.gftd.ai',
                 1,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO edge_cohort_ancestor_of (\n'
         '        edge_id, src_vid, dst_vid,\n'
         '        _seq, created_date, sensitivity_ord, owner_did,\n'
         '        generation_offset, temporal_gap_years, confidence, lineage_type,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, '2026-04-28', 0, $4,\n"
         "        $5, $6, 0.9, 'direct',\n"
         '        $7, $8, null, $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/anc-modern_transition-contemporary',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/modern_transition-001-1975',
                 'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
                 'did:web:natural-person.gftd.ai',
                 1,
                 0,
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 '2026-04-28T00:00:00Z']},
 {'sql': '\n'
         '    UPDATE dim_world_domain\n'
         '    SET world_total = 108000000000,\n'
         "        unit = 'humans ever lived (100k-year historical scope)'\n"
         "    WHERE app_host = 'natural-person'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    INSERT INTO dim_world_domain_collection (\n'
         '      app_host, collection, domain, world_total, unit\n'
         '    ) VALUES (\n'
         "      'natural-person',\n"
         "      'ai.gftd.apps.naturalPerson.populationCohort',\n"
         "      'natural_person',\n"
         '      108000000000,\n'
         "      'humans ever lived'\n"
         '    )\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_person_cohort_era_summary', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_person_pop_cohort_era', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_person_pop_cohort_region', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_person_pop_cohort_year_range', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_cohort_ancestor_src', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_edge_cohort_ancestor_dst', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_cohort_ancestor_of', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_person_population_cohort', 'parameters': []},
 {'sql': '\n'
         '    UPDATE dim_world_domain\n'
         '    SET world_total = 8100000000,\n'
         "        unit = 'natural persons'\n"
         "    WHERE app_host = 'natural-person'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    DELETE FROM dim_world_domain_collection\n'
         "    WHERE collection = 'ai.gftd.apps.naturalPerson.populationCohort'\n"
         '  ',
  'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
