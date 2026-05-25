import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_person_population_cohort — population-level temporal aggregate.
 *
 * Represents ALL humans who ever lived (~108B total) as era×region cohort
 * rows with BIGINT estimated_population — NOT individual rows (which would
 * crash the cluster at 12B+). Aligned with ADR-0026 cohort-first pattern
 * and natural-person CLAUDE.md "Statistics-First" architecture.
 *
 * Covers: 100,000 BCE → present (10万年前まで).
 * Data sources: McEvedy-Jones 1978, HYDE 3.3, UN WPP 2024.
 *
 * edge_cohort_ancestor_of — population ancestry between era cohorts.
 * Connects ancestor era (src_vid) → descendant era (dst_vid) across time.
 *
 * mv_person_cohort_era_summary — bounded MV (< 20 distinct era_label values).
 * Safe: GROUP BY era_label, no MAX(varchar), low cardinality.
 *
 * Also seeds 22 historical population rows (world totals by era) and
 * updates dim_world_domain natural_person world_total → 108,000,000,000
 * (total humans ever lived, covering the 100k-year scope).
 *
 * PII tier 0 guardrail: sensitivity_ord=0 — population aggregates are public
 * statistical data, not personal information. Freely federable.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── 1. vertex_person_population_cohort ─────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_person_population_cohort (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT DEFAULT 0,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      -- Era temporal bounds (negative = BCE, e.g. -100000 = 100,000 BCE)
      era_label VARCHAR,
      era_start_year INTEGER,
      era_end_year INTEGER,
      -- Geographic scope (UN M49 codes)
      region_m49 VARCHAR,
      region_name VARCHAR,
      subregion_m49 VARCHAR,
      -- Population estimates (central + uncertainty bounds)
      estimated_population BIGINT,
      population_low BIGINT,
      population_high BIGINT,
      -- Vital statistics
      birth_rate DOUBLE PRECISION,
      death_rate DOUBLE PRECISION,
      life_expectancy DOUBLE PRECISION,
      infant_mortality_rate DOUBLE PRECISION,
      -- Data provenance
      data_source VARCHAR,
      confidence_level VARCHAR,
      -- Cohort identity (ADR-0026)
      cohort_did VARCHAR,
      -- ADR-0095 RLS columns
      actor_did VARCHAR,
      org_did VARCHAR,
      at_did VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  // ── 2. edge_cohort_ancestor_of ─────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_cohort_ancestor_of (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT DEFAULT 0,
      owner_did VARCHAR,
      -- Ancestry relationship
      generation_offset INTEGER,
      temporal_gap_years INTEGER,
      confidence DOUBLE PRECISION,
      lineage_type VARCHAR,
      -- ADR-0095 RLS columns
      actor_did VARCHAR,
      org_did VARCHAR,
      at_did VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  // ── 3. Indexes ─────────────────────────────────────────────────────────
  await sql`
    CREATE INDEX IF NOT EXISTS idx_person_pop_cohort_era
    ON vertex_person_population_cohort (era_label)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_person_pop_cohort_region
    ON vertex_person_population_cohort (region_m49)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_person_pop_cohort_year_range
    ON vertex_person_population_cohort (era_start_year, era_end_year)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_cohort_ancestor_src
    ON edge_cohort_ancestor_of (src_vid)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_cohort_ancestor_dst
    ON edge_cohort_ancestor_of (dst_vid)
  `.execute(db);

  // ── 4. Streaming MV: era summary (low cardinality — safe) ──────────────
  // GROUP BY era_label: < 20 distinct values. No MAX(varchar). Safe per
  // graph-schema CLAUDE.md §MV Memory Safety Guardrails.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_person_cohort_era_summary AS
    SELECT
      era_label,
      MIN(era_start_year) AS era_start_year,
      MAX(era_end_year)   AS era_end_year,
      COUNT(*)            AS cohort_count,
      SUM(estimated_population) AS total_population,
      SUM(population_low)       AS total_population_low,
      SUM(population_high)      AS total_population_high,
      AVG(life_expectancy)      AS avg_life_expectancy
    FROM vertex_person_population_cohort
    WHERE region_m49 = '001'
    GROUP BY era_label
  `.execute(db);

  // ── 5. Seed historical world population cohorts ────────────────────────
  //
  // Sources:
  //   McEvedy & Jones (1978) — Atlas of World Population History
  //   HYDE 3.3 (Klein Goldewijk 2017) — 10,000 BCE–2000 CE
  //   UN WPP 2024 — 1950–2025 CE
  //   Haub (2011) Population Reference Bureau — total humans ever lived ~108B
  //   Toba bottleneck (74k BCE): Ambrose (1998) ~2,000–10,000 survivors
  //
  // vertex_id convention:
  //   at://did:web:natural-person.etzhayyim.com/app.etzhayyim.apps.naturalPerson.populationCohort/{rkey}
  //   rkey = {era_label}-{region_m49}-{|era_start_year|}
  //
  const NP_DID = 'did:web:natural-person.etzhayyim.com';
  const ACTOR_DID = 'did:web:natural-person.etzhayyim.com';
  const ORG_DID = 'did:web:natural-person.etzhayyim.com';
  const NOW = '2026-04-28T00:00:00Z';
  const REPO = `at://${NP_DID}`;

  type CohortSeed = {
    era_label: string;
    era_start_year: number;
    era_end_year: number;
    estimated_population: number;
    population_low: number;
    population_high: number;
    life_expectancy: number | null;
    birth_rate: number | null;
    death_rate: number | null;
    infant_mortality_rate: number | null;
    data_source: string;
    confidence_level: string;
  };

  const worldCohorts: CohortSeed[] = [
    // Paleolithic — Out of Africa dispersal phase
    {
      era_label: 'early_paleolithic',
      era_start_year: -100000, era_end_year: -74000,
      estimated_population: 100000, population_low: 50000, population_high: 500000,
      life_expectancy: 25, birth_rate: 80, death_rate: 78, infant_mortality_rate: 400,
      data_source: 'haub_2011_prb', confidence_level: 'speculative',
    },
    // Toba bottleneck (~74,000 BCE) — genetic evidence: 2,000–10,000 survivors
    {
      era_label: 'toba_bottleneck',
      era_start_year: -74000, era_end_year: -70000,
      estimated_population: 5000, population_low: 2000, population_high: 10000,
      life_expectancy: 22, birth_rate: 80, death_rate: 79, infant_mortality_rate: 450,
      data_source: 'ambrose_1998_toba', confidence_level: 'speculative',
    },
    // Upper Paleolithic — behavioral modernity, global dispersal
    {
      era_label: 'upper_paleolithic',
      era_start_year: -70000, era_end_year: -10000,
      estimated_population: 1000000, population_low: 500000, population_high: 3000000,
      life_expectancy: 27, birth_rate: 75, death_rate: 73, infant_mortality_rate: 350,
      data_source: 'mcevedy_jones_1978', confidence_level: 'low',
    },
    // Neolithic revolution — agriculture, first settlements
    {
      era_label: 'neolithic',
      era_start_year: -10000, era_end_year: -3000,
      estimated_population: 7000000, population_low: 5000000, population_high: 14000000,
      life_expectancy: 30, birth_rate: 60, death_rate: 57, infant_mortality_rate: 300,
      data_source: 'hyde_3_3', confidence_level: 'low',
    },
    // Bronze Age — first cities, writing, trade networks
    {
      era_label: 'bronze_age',
      era_start_year: -3000, era_end_year: -1200,
      estimated_population: 50000000, population_low: 40000000, population_high: 70000000,
      life_expectancy: 32, birth_rate: 55, death_rate: 52, infant_mortality_rate: 250,
      data_source: 'hyde_3_3', confidence_level: 'medium',
    },
    // Iron Age — classical city-states
    {
      era_label: 'iron_age',
      era_start_year: -1200, era_end_year: -500,
      estimated_population: 100000000, population_low: 80000000, population_high: 130000000,
      life_expectancy: 33, birth_rate: 50, death_rate: 47, infant_mortality_rate: 220,
      data_source: 'hyde_3_3', confidence_level: 'medium',
    },
    // Classical antiquity — Rome, Han, Maurya at peak
    {
      era_label: 'classical',
      era_start_year: -500, era_end_year: 500,
      estimated_population: 260000000, population_low: 200000000, population_high: 350000000,
      life_expectancy: 35, birth_rate: 45, death_rate: 42, infant_mortality_rate: 200,
      data_source: 'hyde_3_3', confidence_level: 'medium',
    },
    // Early medieval — post-Roman collapse, Justinian plague
    {
      era_label: 'early_medieval',
      era_start_year: 500, era_end_year: 1000,
      estimated_population: 310000000, population_low: 270000000, population_high: 360000000,
      life_expectancy: 33, birth_rate: 48, death_rate: 45, infant_mortality_rate: 220,
      data_source: 'mcevedy_jones_1978', confidence_level: 'medium',
    },
    // High/late medieval — Black Death (1347-51 kills ~1/3 of Europe)
    {
      era_label: 'medieval',
      era_start_year: 1000, era_end_year: 1500,
      estimated_population: 390000000, population_low: 350000000, population_high: 440000000,
      life_expectancy: 35, birth_rate: 45, death_rate: 43, infant_mortality_rate: 200,
      data_source: 'mcevedy_jones_1978', confidence_level: 'medium',
    },
    // Early modern — Columbian Exchange, Americas population collapse
    {
      era_label: 'early_modern',
      era_start_year: 1500, era_end_year: 1700,
      estimated_population: 580000000, population_low: 500000000, population_high: 680000000,
      life_expectancy: 38, birth_rate: 40, death_rate: 37, infant_mortality_rate: 170,
      data_source: 'hyde_3_3', confidence_level: 'high',
    },
    // Pre-industrial — first global trade, scientific revolution
    {
      era_label: 'pre_industrial',
      era_start_year: 1700, era_end_year: 1800,
      estimated_population: 890000000, population_low: 820000000, population_high: 960000000,
      life_expectancy: 40, birth_rate: 38, death_rate: 35, infant_mortality_rate: 150,
      data_source: 'hyde_3_3', confidence_level: 'high',
    },
    // Industrial revolution
    {
      era_label: 'industrial',
      era_start_year: 1800, era_end_year: 1900,
      estimated_population: 1600000000, population_low: 1500000000, population_high: 1700000000,
      life_expectancy: 45, birth_rate: 35, death_rate: 30, infant_mortality_rate: 120,
      data_source: 'hyde_3_3', confidence_level: 'high',
    },
    // Modern — two world wars, Spanish flu, Great Depression
    {
      era_label: 'modern_early',
      era_start_year: 1900, era_end_year: 1950,
      estimated_population: 2536000000, population_low: 2400000000, population_high: 2600000000,
      life_expectancy: 48, birth_rate: 36, death_rate: 25, infant_mortality_rate: 100,
      data_source: 'un_wpp_2024', confidence_level: 'high',
    },
    // Post-war baby boom and Green Revolution
    {
      era_label: 'modern_boom',
      era_start_year: 1950, era_end_year: 1975,
      estimated_population: 4000000000, population_low: 3900000000, population_high: 4100000000,
      life_expectancy: 56, birth_rate: 32, death_rate: 14, infant_mortality_rate: 75,
      data_source: 'un_wpp_2024', confidence_level: 'high',
    },
    // Late 20th century — demographic transition
    {
      era_label: 'modern_transition',
      era_start_year: 1975, era_end_year: 2000,
      estimated_population: 6100000000, population_low: 6050000000, population_high: 6150000000,
      life_expectancy: 65, birth_rate: 24, death_rate: 9, infant_mortality_rate: 55,
      data_source: 'un_wpp_2024', confidence_level: 'high',
    },
    // Contemporary
    {
      era_label: 'contemporary',
      era_start_year: 2000, era_end_year: 2025,
      estimated_population: 8200000000, population_low: 8100000000, population_high: 8300000000,
      life_expectancy: 73, birth_rate: 18, death_rate: 8, infant_mortality_rate: 28,
      data_source: 'un_wpp_2024', confidence_level: 'high',
    },
  ];

  for (const c of worldCohorts) {
    const rkey = `${c.era_label}-001-${Math.abs(c.era_start_year)}`;
    const vertex_id = `${REPO}/app.etzhayyim.apps.naturalPerson.populationCohort/${rkey}`;
    const cohort_did = `${NP_DID}:pop:${rkey}`;

    await sql`
      INSERT INTO vertex_person_population_cohort (
        vertex_id, _seq, created_date, sensitivity_ord,
        owner_did, rkey, repo,
        era_label, era_start_year, era_end_year,
        region_m49, region_name,
        estimated_population, population_low, population_high,
        life_expectancy, birth_rate, death_rate, infant_mortality_rate,
        data_source, confidence_level,
        cohort_did,
        actor_did, org_did, at_did, created_at
      ) VALUES (
        ${vertex_id}, 1, '2026-04-28', 0,
        ${NP_DID}, ${rkey}, ${REPO},
        ${c.era_label}, ${c.era_start_year}, ${c.era_end_year},
        '001', 'World',
        ${c.estimated_population}, ${c.population_low}, ${c.population_high},
        ${c.life_expectancy}, ${c.birth_rate}, ${c.death_rate}, ${c.infant_mortality_rate},
        ${c.data_source}, ${c.confidence_level},
        ${cohort_did},
        ${ACTOR_DID}, ${ORG_DID}, null, ${NOW}
      )
    `.execute(db);
  }

  // ── 6. Seed ancestor edges (consecutive era pairs) ─────────────────────
  const eraLabels = worldCohorts.map(c => c.era_label);
  for (let i = 0; i < eraLabels.length - 1; i++) {
    const srcLabel = eraLabels[i];
    const dstLabel = eraLabels[i + 1];
    const srcCohort = worldCohorts[i];
    const dstCohort = worldCohorts[i + 1];
    const srcRkey = `${srcLabel}-001-${Math.abs(srcCohort.era_start_year)}`;
    const dstRkey = `${dstLabel}-001-${Math.abs(dstCohort.era_start_year)}`;
    const srcVid = `${REPO}/app.etzhayyim.apps.naturalPerson.populationCohort/${srcRkey}`;
    const dstVid = `${REPO}/app.etzhayyim.apps.naturalPerson.populationCohort/${dstRkey}`;
    const edgeId = `${REPO}/app.etzhayyim.apps.naturalPerson.cohortAncestorOf/anc-${srcLabel}-${dstLabel}`;
    const gapYears = dstCohort.era_start_year - srcCohort.era_end_year;
    const genOffset = Math.round(Math.abs(srcCohort.era_end_year - srcCohort.era_start_year) / 25);

    await sql`
      INSERT INTO edge_cohort_ancestor_of (
        edge_id, src_vid, dst_vid,
        _seq, created_date, sensitivity_ord, owner_did,
        generation_offset, temporal_gap_years, confidence, lineage_type,
        actor_did, org_did, at_did, created_at
      ) VALUES (
        ${edgeId}, ${srcVid}, ${dstVid},
        1, '2026-04-28', 0, ${NP_DID},
        ${genOffset}, ${gapYears}, 0.9, 'direct',
        ${ACTOR_DID}, ${ORG_DID}, null, ${NOW}
      )
    `.execute(db);
  }

  // ── 7. dim_world_domain: update natural_person world_total ─────────────
  // 108B = total humans who have ever lived (Haub 2011 PRB estimate).
  // This covers the 100k-year historical scope of this table.
  await sql`
    UPDATE dim_world_domain
    SET world_total = 108000000000,
        unit = 'humans ever lived (100k-year historical scope)'
    WHERE app_host = 'natural-person'
  `.execute(db);

  // ── 8. dim_world_domain_collection: add populationCohort mapping ───────
  await sql`
    INSERT INTO dim_world_domain_collection (
      app_host, collection, domain, world_total, unit
    ) VALUES (
      'natural-person',
      'app.etzhayyim.apps.naturalPerson.populationCohort',
      'natural_person',
      108000000000,
      'humans ever lived'
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_person_cohort_era_summary`.execute(db);

  for (const idx of [
    'idx_person_pop_cohort_era',
    'idx_person_pop_cohort_region',
    'idx_person_pop_cohort_year_range',
    'idx_edge_cohort_ancestor_src',
    'idx_edge_cohort_ancestor_dst',
  ]) {
    await sql`DROP INDEX IF EXISTS ${sql.raw(idx)}`.execute(db);
  }

  await sql`DROP TABLE IF EXISTS edge_cohort_ancestor_of`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_person_population_cohort`.execute(db);

  await sql`
    UPDATE dim_world_domain
    SET world_total = 8100000000,
        unit = 'natural persons'
    WHERE app_host = 'natural-person'
  `.execute(db);

  await sql`
    DELETE FROM dim_world_domain_collection
    WHERE collection = 'app.etzhayyim.apps.naturalPerson.populationCohort'
  `.execute(db);
}
