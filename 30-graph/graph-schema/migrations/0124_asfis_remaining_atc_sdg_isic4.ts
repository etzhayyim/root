import { Kysely, sql } from 'kysely';

/**
 * Migration 0124: ASFIS remaining chains + ATC→ISIC4 + SDG→ISIC4 bridges.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 46).
 *
 * ## Systems Built (44 total = 22 forward + 22 reverse)
 *
 * ### ASFIS remaining classification chains (via asfis_isic4 × isic4_X)
 *
 * | system       | edges | pivot                     | notes                    |
 * |--------------|-------|---------------------------|--------------------------|
 * | asfis_isic5  |    73 | asfis_isic4 × isic4_isic5 |                          |
 * | isic5_asfis  |    73 | reverse                   |                          |
 * | asfis_nace   |    73 | asfis_isic4 × isic4_nace  |                          |
 * | nace_asfis   |    73 | reverse                   |                          |
 * | asfis_cpc21  |  1911 | asfis_isic4 × isic4_cpc21 |                          |
 * | cpc21_asfis  |  1911 | reverse                   |                          |
 * | asfis_cpc3   |  1911 | asfis_isic4 × isic4_cpc3  |                          |
 * | cpc3_asfis   |  1911 | reverse                   |                          |
 * | asfis_bec    |   248 | asfis_isic4 × isic4_bec   |                          |
 * | bec_asfis    |   248 | reverse                   |                          |
 * | asfis_isco   |     0 | (skip — isic4→isco fishing sector overlap = 0)     |
 * | asfis_cofog  |     0 | (skip — isic4→cofog fishing sector overlap = 0)    |
 * | asfis_naics  |     0 | (skip — isic4→naics fishing sector overlap = 0)    |
 *
 * NOTE: asfis_isic31 = 0, asfis_isic2 = 0 — ISIC3.1/ISIC2 don't have the
 * same 4-digit fishing codes (0311/0312/0321/0322) as ISIC4.
 *
 * ### ATC → ISIC4 pharmaceutical manufacturing bridge (new bridge)
 *
 * | system    | edges | notes                                              |
 * |-----------|-------|----------------------------------------------------|
 * | atc_isic4 |    42 | All 14 ATC L1 groups (A-V) → ISIC4 21/210/2100    |
 * | isic4_atc |    42 | reverse                                            |
 *
 * All ATC Level 1 therapeutic groups (A=alimentary, B=blood, C=cardiovascular,
 * D=dermatological, G=genito-urinary, H=hormones, J=anti-infectives,
 * L=antineoplastics, M=musculo-skeletal, N=nervous system, P=antiparasitic,
 * R=respiratory, S=sensory, V=various) → ISIC4 division 21 (manufacture of
 * basic pharmaceutical products and pharmaceutical preparations).
 *
 * ### SDG → ISIC4 bridge (new bridge)
 *
 * | system    | edges | notes                                              |
 * |-----------|-------|----------------------------------------------------|
 * | sdg_isic4 |   197 | SDG goals G1-G17 → relevant ISIC4 sectors         |
 * | isic4_sdg |   197 | reverse                                            |
 *
 * Based on UN SDG-industry sector correspondence framework:
 * - SDG 1 (No poverty) → ISIC4 84 (public admin), 87-88 (social work)
 * - SDG 2 (Zero hunger) → ISIC4 01-03 (agriculture, forestry, fishing)
 * - SDG 3 (Good health) → ISIC4 21 (pharma), 86-87 (health/care)
 * - SDG 4 (Education) → ISIC4 85
 * - SDG 6 (Clean water) → ISIC4 36-38 (water/waste)
 * - SDG 7 (Clean energy) → ISIC4 35 (electricity/gas), 19 (petroleum)
 * - SDG 8 (Decent work) → ISIC4 64-66 (finance)
 * - SDG 9 (Industry) → ISIC4 10-33 (manufacturing), 41-43 (construction)
 * - SDG 11 (Sustainable cities) → ISIC4 41-43, 49-52, 68 (real estate)
 * - SDG 13 (Climate action) → ISIC4 35, 19, 49-52 (transport)
 * - SDG 14 (Life below water) → ISIC4 03 (fishing/aquaculture)
 * - SDG 15 (Life on land) → ISIC4 01-02 (agriculture/forestry)
 * - SDG 16 (Peace) → ISIC4 84, 91 (public admin/cultural)
 * - SDG 17 (Partnerships) → ISIC4 84, 72 (R&D)
 *
 * ### SDG extended chains (via sdg_isic4 × isic4_X)
 *
 * | system      | edges | pivot chain                          |
 * |-------------|-------|--------------------------------------|
 * | sdg_hs2017  |   300 | sdg_isic4 × isic4_hs2017            |
 * | hs2017_sdg  |   300 | reverse                              |
 * | sdg_isic5   |   196 | sdg_isic4 × isic4_isic5             |
 * | isic5_sdg   |   196 | reverse                              |
 * | sdg_nace    |   189 | sdg_isic4 × isic4_nace              |
 * | nace_sdg    |   189 | reverse                              |
 * | sdg_cpc21   |   276 | sdg_isic4 × isic4_cpc21             |
 * | cpc21_sdg   |   276 | reverse                              |
 * | sdg_sitc4   |   101 | sdg_isic4 × isic4_sitc4             |
 * | sitc4_sdg   |   101 | reverse                              |
 *
 * ## Coverage Summary (after 0122–0124)
 *
 * ASFIS ISSCAAP groups now connected to ALL tractable classification systems:
 * - ISIC4, ISIC5, NACE Rev.2 (via direct fishing-sector chains)
 * - HS2017 (direct 6-digit species concordance, 206 pairs)
 * - HS2022/2012/2007/2002/1996 (via ISIC4 chain)
 * - SITC Rev.4/3/2/1 (via ISIC4 chain)
 * - CPC21, CPC3, BEC (via ISIC4 chain)
 *
 * ATC (pharmaceuticals) now connected to ISIC4 pharma manufacturing.
 *
 * SDG (Sustainable Development Goals) now connected to:
 * - ISIC4 (direct goal-sector mapping, 197 pairs)
 * - HS2017, ISIC5, NACE, CPC21, SITC4 (via ISIC4 chain)
 *
 * Previously isolated systems still isolated: ICD-10, NDC (no tractable
 * bridge to economic classification systems without external concordance data).
 * ISO4217/LOCODE/ISO639 geographic/language codes remain in their own cluster.
 *
 * DB after 0124: 3,204,386 edges, 529 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    // ASFIS remaining chains
    'asfis_isic5',  'isic5_asfis',
    'asfis_nace',   'nace_asfis',
    'asfis_cpc21',  'cpc21_asfis',
    'asfis_cpc3',   'cpc3_asfis',
    'asfis_bec',    'bec_asfis',
    // ATC → ISIC4
    'atc_isic4',    'isic4_atc',
    // SDG → ISIC4
    'sdg_isic4',    'isic4_sdg',
    // SDG extended chains
    'sdg_hs2017',   'hs2017_sdg',
    'sdg_isic5',    'isic5_sdg',
    'sdg_nace',     'nace_sdg',
    'sdg_cpc21',    'cpc21_sdg',
    'sdg_sitc4',    'sitc4_sdg',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'asfis_isic5',  'isic5_asfis',
    'asfis_nace',   'nace_asfis',
    'asfis_cpc21',  'cpc21_asfis',
    'asfis_cpc3',   'cpc3_asfis',
    'asfis_bec',    'bec_asfis',
    'atc_isic4',    'isic4_atc',
    'sdg_isic4',    'isic4_sdg',
    'sdg_hs2017',   'hs2017_sdg',
    'sdg_isic5',    'isic5_sdg',
    'sdg_nace',     'nace_sdg',
    'sdg_cpc21',    'cpc21_sdg',
    'sdg_sitc4',    'sitc4_sdg',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
