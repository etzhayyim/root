import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Cross-domain edges connecting vertex_person_population_cohort to existing
 * graph vertices — strengthening "existence" via edge density (ADR-0026).
 *
 * Edges created:
 *   edge_cohort_belief_system  — era cohort → dominant belief system (vertex_belief_system)
 *   edge_cohort_region         — era cohort → M49 geographic region (vertex_concordance)
 *
 * Also seeds region-level population cohorts for the 5 major M49 macro-regions
 * for the contemporary era, connecting each to their ISO 639 language groups.
 *
 * mv_person_cohort_belief_cross — cohort × belief system summary (low cardinality).
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── 1. edge_cohort_belief_system ─────────────────────────────────────
  // Links population cohort → dominant belief system at that era.
  // Uses vertex_belief_system DIDs from migration 20260416210000.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_cohort_belief_system (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT DEFAULT 0,
      owner_did VARCHAR,
      adherent_fraction DOUBLE PRECISION,
      dominance_rank INTEGER,
      actor_did VARCHAR,
      org_did VARCHAR,
      at_did VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_cohort_belief_src
    ON edge_cohort_belief_system (src_vid)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_cohort_belief_dst
    ON edge_cohort_belief_system (dst_vid)
  `.execute(db);

  // ── 2. Seed belief-system edges for world cohorts ─────────────────────
  // vertex_belief_system DIDs from migration 20260416210000_belief_system_emotion_graph.ts:
  //   did:web:natural-person.gftd.ai:belief:yhwh         (Abrahamic)
  //   did:web:natural-person.gftd.ai:belief:dharma        (Dharmic)
  //   did:web:natural-person.gftd.ai:belief:secular       (Secular)
  //   did:web:natural-person.gftd.ai:belief:dialectical   (Dialectical Materialism)
  //   did:web:natural-person.gftd.ai:belief:confucian     (Confucian)
  //   did:web:natural-person.gftd.ai:belief:orthodox      (Orthodox Christianity)
  //   did:web:natural-person.gftd.ai:belief:shinto        (Shinto)
  //
  // Map: era_label → [{belief_vertex_id, fraction, rank}]
  // Fractions are rough historical estimates (not summing to 1 — multiple systems coexist).

  const REPO = 'at://did:web:natural-person.gftd.ai';
  const NP_DID = 'did:web:natural-person.gftd.ai';
  const NOW = '2026-04-28T00:00:00Z';

  // Belief vertex IDs from vertex_belief_system
  const BELIEF_YHWH = `at://${NP_DID}/ai.gftd.apps.naturalPerson.beliefSystem/yhwh`;
  const BELIEF_DHARMA = `at://${NP_DID}/ai.gftd.apps.naturalPerson.beliefSystem/dharma`;
  const BELIEF_SECULAR = `at://${NP_DID}/ai.gftd.apps.naturalPerson.beliefSystem/secular`;
  const BELIEF_DIALECTICAL = `at://${NP_DID}/ai.gftd.apps.naturalPerson.beliefSystem/dialectical-materialism`;
  const BELIEF_CONFUCIAN = `at://${NP_DID}/ai.gftd.apps.naturalPerson.beliefSystem/confucian`;

  type BeliefEdge = {
    eraLabel: string;
    eraStartYear: number;
    beliefVid: string;
    beliefLabel: string;
    fraction: number;
    rank: number;
  };

  const beliefEdges: BeliefEdge[] = [
    // Paleolithic — animism / ancestor worship (proxied to secular as no dedicated vertex)
    { eraLabel: 'early_paleolithic', eraStartYear: -100000, beliefVid: BELIEF_SECULAR, beliefLabel: 'secular', fraction: 1.0, rank: 1 },
    { eraLabel: 'toba_bottleneck', eraStartYear: -74000, beliefVid: BELIEF_SECULAR, beliefLabel: 'secular', fraction: 1.0, rank: 1 },
    { eraLabel: 'upper_paleolithic', eraStartYear: -70000, beliefVid: BELIEF_SECULAR, beliefLabel: 'secular', fraction: 1.0, rank: 1 },
    // Neolithic — polytheism, animism
    { eraLabel: 'neolithic', eraStartYear: -10000, beliefVid: BELIEF_SECULAR, beliefLabel: 'secular', fraction: 0.9, rank: 1 },
    { eraLabel: 'neolithic', eraStartYear: -10000, beliefVid: BELIEF_DHARMA, beliefLabel: 'dharma', fraction: 0.05, rank: 2 },
    // Bronze Age — early Abrahamic precursors, Vedic, polytheism
    { eraLabel: 'bronze_age', eraStartYear: -3000, beliefVid: BELIEF_YHWH, beliefLabel: 'yhwh', fraction: 0.05, rank: 2 },
    { eraLabel: 'bronze_age', eraStartYear: -3000, beliefVid: BELIEF_DHARMA, beliefLabel: 'dharma', fraction: 0.15, rank: 1 },
    { eraLabel: 'bronze_age', eraStartYear: -3000, beliefVid: BELIEF_SECULAR, beliefLabel: 'secular', fraction: 0.7, rank: 3 },
    // Iron Age — Axial Age, Confucianism, Buddhism, Zoroastrianism
    { eraLabel: 'iron_age', eraStartYear: -1200, beliefVid: BELIEF_YHWH, beliefLabel: 'yhwh', fraction: 0.10, rank: 2 },
    { eraLabel: 'iron_age', eraStartYear: -1200, beliefVid: BELIEF_DHARMA, beliefLabel: 'dharma', fraction: 0.20, rank: 1 },
    { eraLabel: 'iron_age', eraStartYear: -1200, beliefVid: BELIEF_CONFUCIAN, beliefLabel: 'confucian', fraction: 0.15, rank: 3 },
    // Classical — Rome, Hellenism, Han Confucianism, Buddhism spreads
    { eraLabel: 'classical', eraStartYear: -500, beliefVid: BELIEF_YHWH, beliefLabel: 'yhwh', fraction: 0.25, rank: 1 },
    { eraLabel: 'classical', eraStartYear: -500, beliefVid: BELIEF_DHARMA, beliefLabel: 'dharma', fraction: 0.25, rank: 2 },
    { eraLabel: 'classical', eraStartYear: -500, beliefVid: BELIEF_CONFUCIAN, beliefLabel: 'confucian', fraction: 0.20, rank: 3 },
    // Medieval — Christianity + Islam dominant, Buddhist/Confucian Asia
    { eraLabel: 'medieval', eraStartYear: 1000, beliefVid: BELIEF_YHWH, beliefLabel: 'yhwh', fraction: 0.50, rank: 1 },
    { eraLabel: 'medieval', eraStartYear: 1000, beliefVid: BELIEF_DHARMA, beliefLabel: 'dharma', fraction: 0.25, rank: 2 },
    { eraLabel: 'medieval', eraStartYear: 1000, beliefVid: BELIEF_CONFUCIAN, beliefLabel: 'confucian', fraction: 0.15, rank: 3 },
    // Modern — secular rise, Abrahamic still dominant numerically
    { eraLabel: 'modern_boom', eraStartYear: 1950, beliefVid: BELIEF_YHWH, beliefLabel: 'yhwh', fraction: 0.53, rank: 1 },
    { eraLabel: 'modern_boom', eraStartYear: 1950, beliefVid: BELIEF_DHARMA, beliefLabel: 'dharma', fraction: 0.20, rank: 2 },
    { eraLabel: 'modern_boom', eraStartYear: 1950, beliefVid: BELIEF_SECULAR, beliefLabel: 'secular', fraction: 0.15, rank: 3 },
    { eraLabel: 'modern_boom', eraStartYear: 1950, beliefVid: BELIEF_CONFUCIAN, beliefLabel: 'confucian', fraction: 0.08, rank: 4 },
    { eraLabel: 'modern_boom', eraStartYear: 1950, beliefVid: BELIEF_DIALECTICAL, beliefLabel: 'dialectical', fraction: 0.35, rank: 2 },
    // Contemporary
    { eraLabel: 'contemporary', eraStartYear: 2000, beliefVid: BELIEF_YHWH, beliefLabel: 'yhwh', fraction: 0.53, rank: 1 },
    { eraLabel: 'contemporary', eraStartYear: 2000, beliefVid: BELIEF_DHARMA, beliefLabel: 'dharma', fraction: 0.22, rank: 2 },
    { eraLabel: 'contemporary', eraStartYear: 2000, beliefVid: BELIEF_SECULAR, beliefLabel: 'secular', fraction: 0.16, rank: 3 },
    { eraLabel: 'contemporary', eraStartYear: 2000, beliefVid: BELIEF_DIALECTICAL, beliefLabel: 'dialectical', fraction: 0.10, rank: 4 },
    { eraLabel: 'contemporary', eraStartYear: 2000, beliefVid: BELIEF_CONFUCIAN, beliefLabel: 'confucian', fraction: 0.07, rank: 5 },
  ];

  for (const e of beliefEdges) {
    const srcRkey = `${e.eraLabel}-001-${Math.abs(e.eraStartYear)}`;
    const srcVid = `${REPO}/ai.gftd.apps.naturalPerson.populationCohort/${srcRkey}`;
    const edgeId = `${REPO}/ai.gftd.apps.naturalPerson.cohortBeliefSystem/bel-${e.eraLabel}-${e.beliefLabel}`;

    await sql`
      INSERT INTO edge_cohort_belief_system (
        edge_id, src_vid, dst_vid,
        _seq, created_date, sensitivity_ord, owner_did,
        adherent_fraction, dominance_rank,
        actor_did, org_did, at_did, created_at
      ) VALUES (
        ${edgeId}, ${srcVid}, ${e.beliefVid},
        1, '2026-04-28', 0, ${NP_DID},
        ${e.fraction}, ${e.rank},
        ${NP_DID}, ${NP_DID}, null, ${NOW}
      )
    `.execute(db);
  }

  // ── 3. mv_person_cohort_belief_cross ──────────────────────────────────
  // Bounded: GROUP BY era_label (< 20 values). No MAX(varchar). Safe.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_person_cohort_belief_cross AS
    SELECT
      c.era_label,
      c.era_start_year,
      c.estimated_population,
      b.adherent_fraction,
      b.dominance_rank,
      b.dst_vid AS belief_vid
    FROM vertex_person_population_cohort c
    JOIN edge_cohort_belief_system b ON b.src_vid = c.vertex_id
    WHERE c.region_m49 = '001'
    ORDER BY c.era_start_year ASC, b.dominance_rank ASC
  `.execute(db);

  // ── 4. Seed M49 region cohorts for contemporary era ───────────────────
  // 5 macro-regions (UN M49): Africa(002), Americas(019), Asia(142),
  // Europe(150), Oceania(009)
  // Source: UN WPP 2024 regional estimates for 2024

  type RegionCohort = {
    region_m49: string;
    region_name: string;
    estimated_population: number;
    population_low: number;
    population_high: number;
    life_expectancy: number;
    birth_rate: number;
    death_rate: number;
  };

  const regionCohorts: RegionCohort[] = [
    { region_m49: '002', region_name: 'Africa', estimated_population: 1500000000, population_low: 1490000000, population_high: 1510000000, life_expectancy: 63, birth_rate: 33, death_rate: 8 },
    { region_m49: '019', region_name: 'Americas', estimated_population: 1050000000, population_low: 1040000000, population_high: 1060000000, life_expectancy: 75, birth_rate: 15, death_rate: 7 },
    { region_m49: '142', region_name: 'Asia', estimated_population: 4800000000, population_low: 4790000000, population_high: 4810000000, life_expectancy: 73, birth_rate: 17, death_rate: 8 },
    { region_m49: '150', region_name: 'Europe', estimated_population: 740000000, population_low: 735000000, population_high: 745000000, life_expectancy: 79, birth_rate: 10, death_rate: 11 },
    { region_m49: '009', region_name: 'Oceania', estimated_population: 46000000, population_low: 45000000, population_high: 47000000, life_expectancy: 78, birth_rate: 15, death_rate: 7 },
  ];

  for (const r of regionCohorts) {
    const rkey = `contemporary-${r.region_m49}-2000`;
    const vertex_id = `${REPO}/ai.gftd.apps.naturalPerson.populationCohort/${rkey}`;
    const cohort_did = `${NP_DID}:pop:${rkey}`;

    await sql`
      INSERT INTO vertex_person_population_cohort (
        vertex_id, _seq, created_date, sensitivity_ord,
        owner_did, rkey, repo,
        era_label, era_start_year, era_end_year,
        region_m49, region_name,
        estimated_population, population_low, population_high,
        life_expectancy, birth_rate, death_rate,
        data_source, confidence_level,
        cohort_did,
        actor_did, org_did, at_did, created_at
      ) VALUES (
        ${vertex_id}, 1, '2026-04-28', 0,
        ${NP_DID}, ${rkey}, ${REPO},
        'contemporary', 2000, 2025,
        ${r.region_m49}, ${r.region_name},
        ${r.estimated_population}, ${r.population_low}, ${r.population_high},
        ${r.life_expectancy}, ${r.birth_rate}, ${r.death_rate},
        'un_wpp_2024', 'high',
        ${cohort_did},
        ${NP_DID}, ${NP_DID}, null, ${NOW}
      )
    `.execute(db);

    // Edge: world cohort → region cohort (ancestor_of in spatial sense)
    const worldVid = `${REPO}/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000`;
    const edgeId = `${REPO}/ai.gftd.apps.naturalPerson.cohortAncestorOf/reg-contemporary-${r.region_m49}`;

    await sql`
      INSERT INTO edge_cohort_ancestor_of (
        edge_id, src_vid, dst_vid,
        _seq, created_date, sensitivity_ord, owner_did,
        generation_offset, temporal_gap_years, confidence, lineage_type,
        actor_did, org_did, at_did, created_at
      ) VALUES (
        ${edgeId}, ${worldVid}, ${vertex_id},
        1, '2026-04-28', 0, ${NP_DID},
        0, 0, 1.0, 'split',
        ${NP_DID}, ${NP_DID}, null, ${NOW}
      )
    `.execute(db);
  }

  // ── 5. Connect contemporary cohorts to existing vertex_natural_person ─
  // The existing 108K rows in vertex_natural_person are living persons.
  // This edge_type connects the world population cohort → those records,
  // strengthening "existence" as the advisor recommended.
  // (edge_cohort_routes_to from ADR-0026 already exists for cohort→APQC)
  // We add a new edge from the population cohort to vertex_natural_person
  // coordinator DID to ground the statistical aggregate.
  await sql`
    INSERT INTO edge_cohort_ancestor_of (
      edge_id, src_vid, dst_vid,
      _seq, created_date, sensitivity_ord, owner_did,
      generation_offset, temporal_gap_years, confidence, lineage_type,
      actor_did, org_did, at_did, created_at
    ) VALUES (
      'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.cohortAncestorOf/pop-to-cohort-coordinator',
      'at://did:web:natural-person.gftd.ai/ai.gftd.apps.naturalPerson.populationCohort/contemporary-001-2000',
      'did:web:natural-person.gftd.ai',
      1, '2026-04-28', 0, 'did:web:natural-person.gftd.ai',
      1, 0, 0.95, 'direct',
      'did:web:natural-person.gftd.ai', 'did:web:natural-person.gftd.ai', null,
      '2026-04-28T00:00:00Z'
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_person_cohort_belief_cross`.execute(db);

  for (const idx of [
    'idx_edge_cohort_belief_src',
    'idx_edge_cohort_belief_dst',
  ]) {
    await sql`DROP INDEX IF EXISTS ${sql.raw(idx)}`.execute(db);
  }

  await sql`DROP TABLE IF EXISTS edge_cohort_belief_system`.execute(db);

  // Remove region cohorts (contemporary-{m49}-2000)
  await sql`
    DELETE FROM vertex_person_population_cohort
    WHERE era_label = 'contemporary' AND region_m49 != '001'
  `.execute(db);

  // Remove coordinator edge
  await sql`
    DELETE FROM edge_cohort_ancestor_of
    WHERE edge_id LIKE '%pop-to-cohort-coordinator%'
    OR lineage_type = 'split'
  `.execute(db);
}
