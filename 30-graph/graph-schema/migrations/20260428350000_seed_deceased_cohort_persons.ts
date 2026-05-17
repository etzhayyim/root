import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Phase 1C: generateDeceasedCohorts — seed deceased cohort persons
 * from historical population data (natural-person CLAUDE.md §Phase 1C).
 *
 * Generates vertex_natural_person_cohort_person rows for each:
 *   era (5 groups) × ICD-10 death cause cluster (5) = 25 deceased cohort rows.
 *
 * Each row represents a statistical cohort of humans who lived in that era
 * and died from that cause. intel_estimated_count carries the estimated count
 * of individuals (billions for prehistoric, millions for modern specific cause).
 *
 * ADR-0018 compliance: historical eras → data_classification='public'.
 * modern_era deceased → 'internal' (JPN/GBR/IND etc. no longer protect).
 *
 * Also seeds:
 *   edge_cohort_derived (ADR-0026): population cohort → cohort person (25 edges)
 *   vertex_cohort_actor (ADR-0026): cohort actor registry entries (25 rows)
 *
 * ICD-10 cause clusters:
 *   A00-B99  infectious_disease (plague, cholera, smallpox, malaria)
 *   J00-J99  respiratory_infection (TB, pneumonia, influenza)
 *   S00-T98  trauma_injury (war, violence, accident)
 *   E40-E46  nutritional_deficiency (famine, starvation)
 *   I00-I99  cardiovascular (heart disease, stroke — modern dominant)
 *
 * Estimated deaths by era (based on McEvedy-Jones + Haub PRB + UN WPP):
 *   Total humans who ever died: ~108B (mirroring dim_world_domain world_total)
 *   prehistoric: ~2.5B deaths (90K years × tiny population)
 *   ancient:     ~8B deaths  (10K years × growing population)
 *   medieval:    ~6B deaths  (1000 years × Black Death etc.)
 *   industrial:  ~12B deaths (400 years × faster growth)
 *   modern:      ~5B deaths  (125 years, faster still but higher life expectancy)
 */
export async function up(db: Kysely<any>): Promise<void> {
  const NP_DID = 'did:web:natural-person.etzhayyim.com';
  const REPO = `at://${NP_DID}`;
  const NOW = '2026-04-28T00:00:00Z';

  type DeceasedCohort = {
    era: 'prehistoric' | 'ancient' | 'medieval' | 'industrial' | 'modern';
    eraStartYear: number;
    eraEndYear: number;
    icdCluster: string;
    icdLabel: string;
    deathCauseIcd10: string;
    intelEstimatedCount: number;
    birthYear: string;
    deathYear: string;
    lifeExpectancy: string;
    primaryRegion: string;
    primaryLanguage: string;
    dataClassification: 'public' | 'internal' | 'confidential' | 'restricted';
    rationale: string;
    intelConfidence: 'high' | 'medium' | 'low';
  };

  const cohorts: DeceasedCohort[] = [
    // ── PREHISTORIC (100,000 BCE – 10,000 BCE) ──────────────────────────
    {
      era: 'prehistoric', eraStartYear: -100000, eraEndYear: -10000,
      icdCluster: 'infectious_disease', icdLabel: 'Infectious diseases',
      deathCauseIcd10: 'A00-B99',
      intelEstimatedCount: 875000000,  // ~35% of ~2.5B total prehistoric deaths
      birthYear: '-100000', deathYear: '-10000',
      lifeExpectancy: '25', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'low',
      rationale: 'ADR-0018 §historical: era=prehistoric → public; estimate McEvedy-Jones 1978',
    },
    {
      era: 'prehistoric', eraStartYear: -100000, eraEndYear: -10000,
      icdCluster: 'trauma_injury', icdLabel: 'Trauma and injuries',
      deathCauseIcd10: 'S00-T98',
      intelEstimatedCount: 750000000,  // ~30%
      birthYear: '-100000', deathYear: '-10000',
      lifeExpectancy: '25', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'low',
      rationale: 'ADR-0018 §historical: era=prehistoric → public; fossil record evidence',
    },
    {
      era: 'prehistoric', eraStartYear: -100000, eraEndYear: -10000,
      icdCluster: 'nutritional_deficiency', icdLabel: 'Nutritional deficiency / famine',
      deathCauseIcd10: 'E40-E46',
      intelEstimatedCount: 500000000,  // ~20%
      birthYear: '-100000', deathYear: '-10000',
      lifeExpectancy: '25', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'low',
      rationale: 'ADR-0018 §historical: era=prehistoric → public; climate/famine cycles',
    },
    {
      era: 'prehistoric', eraStartYear: -100000, eraEndYear: -10000,
      icdCluster: 'maternal_perinatal', icdLabel: 'Maternal and perinatal',
      deathCauseIcd10: 'O00-O99',
      intelEstimatedCount: 250000000,  // ~10%
      birthYear: '-100000', deathYear: '-10000',
      lifeExpectancy: '25', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'low',
      rationale: 'ADR-0018 §historical: era=prehistoric → public; MMR >2000/100k births',
    },
    {
      era: 'prehistoric', eraStartYear: -100000, eraEndYear: -10000,
      icdCluster: 'cardiovascular', icdLabel: 'Cardiovascular disease',
      deathCauseIcd10: 'I00-I99',
      intelEstimatedCount: 125000000,  // ~5%
      birthYear: '-100000', deathYear: '-10000',
      lifeExpectancy: '25', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'low',
      rationale: 'ADR-0018 §historical: era=prehistoric → public; low incidence short life',
    },

    // ── ANCIENT (10,000 BCE – 500 CE) ─────────────────────────────────
    {
      era: 'ancient', eraStartYear: -10000, eraEndYear: 500,
      icdCluster: 'infectious_disease', icdLabel: 'Infectious diseases',
      deathCauseIcd10: 'A00-B99',
      intelEstimatedCount: 3200000000,  // ~40% of ~8B total ancient deaths
      birthYear: '-10000', deathYear: '500',
      lifeExpectancy: '30', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'medium',
      rationale: 'ADR-0018 §historical: era=ancient → public; Antonine Plague, Athenian Plague',
    },
    {
      era: 'ancient', eraStartYear: -10000, eraEndYear: 500,
      icdCluster: 'trauma_injury', icdLabel: 'Trauma and injuries (incl. war)',
      deathCauseIcd10: 'S00-T98',
      intelEstimatedCount: 1600000000,  // ~20%
      birthYear: '-10000', deathYear: '500',
      lifeExpectancy: '30', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'medium',
      rationale: 'ADR-0018 §historical: era=ancient → public; Mongol conquests, Roman wars',
    },
    {
      era: 'ancient', eraStartYear: -10000, eraEndYear: 500,
      icdCluster: 'nutritional_deficiency', icdLabel: 'Nutritional deficiency / famine',
      deathCauseIcd10: 'E40-E46',
      intelEstimatedCount: 1600000000,  // ~20%
      birthYear: '-10000', deathYear: '500',
      lifeExpectancy: '30', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'medium',
      rationale: 'ADR-0018 §historical: era=ancient → public; agricultural failure cycles',
    },
    {
      era: 'ancient', eraStartYear: -10000, eraEndYear: 500,
      icdCluster: 'maternal_perinatal', icdLabel: 'Maternal and perinatal',
      deathCauseIcd10: 'O00-O99',
      intelEstimatedCount: 800000000,  // ~10%
      birthYear: '-10000', deathYear: '500',
      lifeExpectancy: '30', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'medium',
      rationale: 'ADR-0018 §historical: era=ancient → public; MMR ~1500/100k births',
    },
    {
      era: 'ancient', eraStartYear: -10000, eraEndYear: 500,
      icdCluster: 'cardiovascular', icdLabel: 'Cardiovascular disease',
      deathCauseIcd10: 'I00-I99',
      intelEstimatedCount: 800000000,  // ~10%
      birthYear: '-10000', deathYear: '500',
      lifeExpectancy: '30', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'medium',
      rationale: 'ADR-0018 §historical: era=ancient → public; Galen era cardiac descriptions',
    },

    // ── MEDIEVAL (500 CE – 1500 CE) ───────────────────────────────────
    {
      era: 'medieval', eraStartYear: 500, eraEndYear: 1500,
      icdCluster: 'infectious_disease', icdLabel: 'Infectious diseases (incl. Black Death)',
      deathCauseIcd10: 'A00-B99',
      intelEstimatedCount: 2700000000,  // ~45% of ~6B medieval deaths
      birthYear: '500', deathYear: '1500',
      lifeExpectancy: '33', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'medium',
      rationale: 'ADR-0018 §historical: era=medieval → public; Black Death 75-200M deaths',
    },
    {
      era: 'medieval', eraStartYear: 500, eraEndYear: 1500,
      icdCluster: 'trauma_injury', icdLabel: 'Trauma and injuries (incl. Mongol conquests)',
      deathCauseIcd10: 'S00-T98',
      intelEstimatedCount: 1200000000,  // ~20%
      birthYear: '500', deathYear: '1500',
      lifeExpectancy: '33', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'medium',
      rationale: 'ADR-0018 §historical: era=medieval → public; Mongol conquest est. 40M deaths',
    },
    {
      era: 'medieval', eraStartYear: 500, eraEndYear: 1500,
      icdCluster: 'nutritional_deficiency', icdLabel: 'Nutritional deficiency / famine',
      deathCauseIcd10: 'E40-E46',
      intelEstimatedCount: 1200000000,  // ~20%
      birthYear: '500', deathYear: '1500',
      lifeExpectancy: '33', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'medium',
      rationale: 'ADR-0018 §historical: era=medieval → public; Great Famine 1315-22, drought',
    },
    {
      era: 'medieval', eraStartYear: 500, eraEndYear: 1500,
      icdCluster: 'maternal_perinatal', icdLabel: 'Maternal and perinatal',
      deathCauseIcd10: 'O00-O99',
      intelEstimatedCount: 600000000,  // ~10%
      birthYear: '500', deathYear: '1500',
      lifeExpectancy: '33', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'medium',
      rationale: 'ADR-0018 §historical: era=medieval → public; MMR ~1200/100k births',
    },
    {
      era: 'medieval', eraStartYear: 500, eraEndYear: 1500,
      icdCluster: 'cardiovascular', icdLabel: 'Cardiovascular disease',
      deathCauseIcd10: 'I00-I99',
      intelEstimatedCount: 300000000,  // ~5%
      birthYear: '500', deathYear: '1500',
      lifeExpectancy: '33', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'medium',
      rationale: 'ADR-0018 §historical: era=medieval → public; low due to short life span',
    },

    // ── INDUSTRIAL (1500 CE – 1900 CE) ────────────────────────────────
    {
      era: 'industrial', eraStartYear: 1500, eraEndYear: 1900,
      icdCluster: 'infectious_disease', icdLabel: 'Infectious diseases (TB, cholera, smallpox)',
      deathCauseIcd10: 'A00-B99',
      intelEstimatedCount: 4200000000,  // ~35% of ~12B industrial deaths
      birthYear: '1500', deathYear: '1900',
      lifeExpectancy: '40', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'high',
      rationale: 'ADR-0018 §historical: era=industrial → public; cholera pandemics, TB White Plague',
    },
    {
      era: 'industrial', eraStartYear: 1500, eraEndYear: 1900,
      icdCluster: 'cardiovascular', icdLabel: 'Cardiovascular disease',
      deathCauseIcd10: 'I00-I99',
      intelEstimatedCount: 2400000000,  // ~20%
      birthYear: '1500', deathYear: '1900',
      lifeExpectancy: '40', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'high',
      rationale: 'ADR-0018 §historical: era=industrial → public; rising with improved life expectancy',
    },
    {
      era: 'industrial', eraStartYear: 1500, eraEndYear: 1900,
      icdCluster: 'trauma_injury', icdLabel: 'Trauma (incl. Columbian Exchange, colonial wars)',
      deathCauseIcd10: 'S00-T98',
      intelEstimatedCount: 1800000000,  // ~15%
      birthYear: '1500', deathYear: '1900',
      lifeExpectancy: '40', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'high',
      rationale: 'ADR-0018 §historical: era=industrial → public; Americas collapse 50-80M',
    },
    {
      era: 'industrial', eraStartYear: 1500, eraEndYear: 1900,
      icdCluster: 'nutritional_deficiency', icdLabel: 'Nutritional deficiency / famine',
      deathCauseIcd10: 'E40-E46',
      intelEstimatedCount: 1800000000,  // ~15%
      birthYear: '1500', deathYear: '1900',
      lifeExpectancy: '40', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'high',
      rationale: 'ADR-0018 §historical: era=industrial → public; Bengal, Irish famines',
    },
    {
      era: 'industrial', eraStartYear: 1500, eraEndYear: 1900,
      icdCluster: 'maternal_perinatal', icdLabel: 'Maternal and perinatal',
      deathCauseIcd10: 'O00-O99',
      intelEstimatedCount: 1800000000,  // ~15%
      birthYear: '1500', deathYear: '1900',
      lifeExpectancy: '40', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'public', intelConfidence: 'high',
      rationale: 'ADR-0018 §historical: era=industrial → public; MMR ~600/100k births pre-Semmelweis',
    },

    // ── MODERN (1900 CE – 2025 CE) ────────────────────────────────────
    {
      era: 'modern', eraStartYear: 1900, eraEndYear: 2025,
      icdCluster: 'cardiovascular', icdLabel: 'Cardiovascular disease (dominant modern killer)',
      deathCauseIcd10: 'I00-I99',
      intelEstimatedCount: 1750000000,  // ~35% of ~5B modern deaths
      birthYear: '1900', deathYear: '2025',
      lifeExpectancy: '65', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'internal', intelConfidence: 'high',
      rationale: 'ADR-0018 §deceased_no_protect: JPN/GBR/IND/USA no perpetual protection → internal',
    },
    {
      era: 'modern', eraStartYear: 1900, eraEndYear: 2025,
      icdCluster: 'infectious_disease', icdLabel: 'Infectious diseases (incl. Spanish flu, COVID)',
      deathCauseIcd10: 'A00-B99',
      intelEstimatedCount: 1000000000,  // ~20%
      birthYear: '1900', deathYear: '2025',
      lifeExpectancy: '65', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'internal', intelConfidence: 'high',
      rationale: 'ADR-0018: Spanish flu 50M, COVID 7M, HIV/AIDS 40M, TB ongoing 1.5M/yr',
    },
    {
      era: 'modern', eraStartYear: 1900, eraEndYear: 2025,
      icdCluster: 'neoplasms', icdLabel: 'Neoplasms (cancer)',
      deathCauseIcd10: 'C00-D48',
      intelEstimatedCount: 750000000,  // ~15%
      birthYear: '1900', deathYear: '2025',
      lifeExpectancy: '65', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'internal', intelConfidence: 'high',
      rationale: 'ADR-0018: modern cancer burden 10M deaths/yr; WHO 2023 leading cause',
    },
    {
      era: 'modern', eraStartYear: 1900, eraEndYear: 2025,
      icdCluster: 'trauma_injury', icdLabel: 'Trauma (WWI, WWII, Korean, Vietnam, conflicts)',
      deathCauseIcd10: 'S00-T98',
      intelEstimatedCount: 750000000,  // ~15%
      birthYear: '1900', deathYear: '2025',
      lifeExpectancy: '65', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'internal', intelConfidence: 'high',
      rationale: 'ADR-0018: WWI 20M, WWII 70-85M, road traffic 1.35M/yr (WHO 2023)',
    },
    {
      era: 'modern', eraStartYear: 1900, eraEndYear: 2025,
      icdCluster: 'nutritional_deficiency', icdLabel: 'Nutritional deficiency (incl. great famines)',
      deathCauseIcd10: 'E40-E46',
      intelEstimatedCount: 750000000,  // ~15%
      birthYear: '1900', deathYear: '2025',
      lifeExpectancy: '65', primaryRegion: '001', primaryLanguage: 'mul',
      dataClassification: 'internal', intelConfidence: 'high',
      rationale: 'ADR-0018: Chinese famine 15-55M, Bengal 1943 3M, Great Leap 15-55M',
    },
  ];

  // Map era → population cohort population vertex_id (for edge_cohort_derived)
  const eraToPopCohortRkey: Record<string, string> = {
    prehistoric: 'upper_paleolithic-001-70000',
    ancient:     'neolithic-001-10000',
    medieval:    'medieval-001-1000',
    industrial:  'early_modern-001-1500',
    modern:      'modern_early-001-1900',
  };

  for (const c of cohorts) {
    const rkey = `deceased-${c.era}-${c.icdCluster}`;
    const vertex_id = `${REPO}/ai.gftd.apps.naturalPerson.cohortPerson/${rkey}`;
    const cohort_did = `${NP_DID}:deceased:${c.era}:${c.icdCluster}`;
    // DJB2 approximation using era+icd as hash input (deterministic rkey)
    const cohort_hash = Buffer.from(`${c.era}|${c.icdCluster}|deceased`).toString('hex').slice(0, 16);

    await sql`
      INSERT INTO vertex_natural_person_cohort_person (
        vertex_id, _seq, created_date, sensitivity_ord,
        owner_did, rkey, repo,
        cohort_hash, cohort_did,
        country, vital_status,
        birth_year, death_year, death_cause_icd10, era,
        intel_chain_id, intel_estimated_count, intel_confidence, intel_entity_type,
        data_classification, rationale,
        actor_did, org_did, created_at
      ) VALUES (
        ${vertex_id}, 1, '2026-04-28', 300,
        ${NP_DID}, ${rkey}, ${REPO},
        ${cohort_hash}, ${cohort_did},
        'WORLD', 'deceased',
        ${c.birthYear}, ${c.deathYear}, ${c.deathCauseIcd10}, ${c.era},
        ${`pop-chain:${c.era}:${c.icdCluster}`},
        ${c.intelEstimatedCount}, ${c.intelConfidence}, 'PopulationCohort',
        ${c.dataClassification}, ${c.rationale},
        ${NP_DID}, ${NP_DID}, ${NOW}
      )
    `.execute(db);

    // ── edge_cohort_derived: population cohort → deceased cohort person ──
    const popRkey = eraToPopCohortRkey[c.era];
    const popVid = `${REPO}/ai.gftd.apps.naturalPerson.populationCohort/${popRkey}`;
    const edgeId = `${REPO}/ai.gftd.apps.naturalPerson.cohortDerived/derv-${c.era}-${c.icdCluster}`;
    const eraEndDateApprox = c.eraEndYear > 0
      ? `${c.eraEndYear}-12-31`
      : '0001-01-01';

    await sql`
      INSERT INTO edge_cohort_derived (
        edge_id, src_vid, dst_vid,
        _seq, created_date, owner_did,
        posterior, fission_at
      ) VALUES (
        ${edgeId}, ${popVid}, ${vertex_id},
        1, '2026-04-28', ${NP_DID},
        0.85, ${eraEndDateApprox}
      )
    `.execute(db);

    // ── vertex_cohort_actor: ADR-0026 cohort actor registry ─────────────
    const actorVid = `${REPO}/ai.gftd.apps.naturalPerson.cohortActor/${rkey}`;
    await sql`
      INSERT INTO vertex_cohort_actor (
        vertex_id, cohort_did, handle,
        kind, segment_hash, k_anonymity,
        fission_enabled, derived_from, status,
        genesis_at, owner_did, _seq, created_date,
        actor_did, org_did
      ) VALUES (
        ${actorVid}, ${cohort_did},
        ${`${c.era}.${c.icdCluster}`},
        'deceased_population_cohort',
        ${cohort_hash},
        ${Math.floor(c.intelEstimatedCount / 1000000)},
        false,
        ${popVid},
        'active',
        ${NOW}, ${NP_DID}, 1, '2026-04-28',
        ${NP_DID}, ${NP_DID}
      )
    `.execute(db);
  }

  // ── Update dim_world_domain natural_person unit to reflect full scope ──
  await sql`
    UPDATE dim_world_domain
    SET unit = 'humans ever lived (100k BCE–2025 CE: 108B total, ${cohorts.length} deceased cohort classes)'
    WHERE app_host = 'natural-person'
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  // Remove all seeded deceased cohort persons
  await sql`
    DELETE FROM vertex_natural_person_cohort_person
    WHERE rkey LIKE 'deceased-%'
  `.execute(db);

  await sql`
    DELETE FROM edge_cohort_derived
    WHERE edge_id LIKE '%/cohortDerived/derv-%'
  `.execute(db);

  await sql`
    DELETE FROM vertex_cohort_actor
    WHERE kind = 'deceased_population_cohort'
  `.execute(db);

  await sql`
    UPDATE dim_world_domain
    SET unit = 'humans ever lived (100k-year historical scope)'
    WHERE app_host = 'natural-person'
  `.execute(db);
}
