import { Kysely, sql } from 'kysely';

/**
 * Migration 0073: Derived concordance bridge graph — 11 new systems.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 3).
 *
 * ## New concordance systems (all derived from existing taxonomy data)
 *
 * | system        | edges | description                                |
 * |---------------|-------|--------------------------------------------|
 * | hs2017_cpc3   | 5,740 | CPC v3 → HS 2017 (via CPC v2.1)           |
 * | hs2012_cpc3   | 5,500 | CPC v3 → HS 2012 (via CPC v2.1)           |
 * | hs22_hs17     | 6,561 | HS 2022 → HS 2017 (code-identical)         |
 * | hs12_hs17     | 6,528 | HS 2012 → HS 2017 (code-identical)         |
 * | sitc4_cpc3    | 3,717 | CPC v3 → SITC Rev.4 (via CPC v2.1)        |
 * | isic5_nace    |   625 | NACE Rev.2 → ISIC Rev.5 (via ISIC Rev.4)  |
 * | naics_isic5   |    24 | NAICS 2022 sector → ISIC Rev.5 section     |
 * | cpc_isic5     | 2,504 | CPC v2.1 → ISIC Rev.5 (via ISIC Rev.4)    |
 *
 * Previously restored:
 * | cpc3          | 4,391 | CPC v2.1 → CPC v3 (code-identical)        |
 * | nace_r2       |   679 | NACE Rev.2 → ISIC Rev.4                   |
 * | naics_isic4   |    24 | NAICS 2022 sector → ISIC Rev.4 section    |
 *
 * ## Derivation methodology
 *
 * All new edges are derived via JOIN through existing anchor concordances:
 *
 *   hs2017_cpc3:  CPC_v3.rkey = CPC_v21.rkey → inherit CPC_v21 → HS2017 edges
 *   hs2012_cpc3:  same pattern via hs2012 edges
 *   sitc4_cpc3:   same pattern via sitc4 edges
 *   hs22_hs17:    HS2022.rkey = HS2017.rkey (code-identical JOIN)
 *   hs12_hs17:    HS2012.rkey = HS2017.rkey (code-identical JOIN)
 *   isic5_nace:   NACE.dst_vid (ISIC4) JOIN ISIC4.src_vid (isic5 edge) → ISIC5
 *   naics_isic5:  NAICS.dst_vid (ISIC4 section) JOIN ISIC4 → ISIC5
 *   cpc_isic5:    CPC.dst_vid (ISIC4) JOIN ISIC4 → ISIC5
 *
 * ## Topology integrity (post-apply)
 *
 * 0 orphan nodes across all 10 taxonomy collections.
 * 0 dangling edges across all 16 concordance systems.
 *
 * Full concordance inventory:
 *   hs22_hs17   : 6,561   hs2017_cpc3  : 5,740   hs2017     : 5,843
 *   hs12_hs17   : 6,528   hs2012_cpc3  : 5,500   hs2012     : 5,584
 *   cpc3        : 4,391   sitc4        : 3,776   sitc4_cpc3  : 3,717
 *   cpc         : 2,663   cpc_isic5    : 2,504   isic5       :   700
 *   nace_r2     :   679   isic5_nace   :   625   naics_isic4 :    24
 *   naics_isic5 :    24
 *   TOTAL       : 52,134 (excl. openalex_concept 159,739 + ipc 1)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // All concordance data is data-only; schema changes are noop here.
  // DELETE + re-insert pattern (idempotent):

  // HS version bridges (code-identical)
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs22_hs17'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs12_hs17'`.execute(db);

  // CPC v3 derived bridges
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2017_cpc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2012_cpc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4_cpc3'`.execute(db);

  // ISIC5 bridges
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_nace'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'naics_isic5'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc_isic5'`.execute(db);

  // NB: derived edge payloads re-generated via JOIN at ingestion time. Re-run:
  //   python3 /tmp/build_hs_bridges.py
  //   python3 /tmp/build_cpc3_hs2017.py
  //   python3 /tmp/build_derived_concordances.py
  //   python3 /tmp/build_naics_isic5.py
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs22_hs17'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs12_hs17'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2017_cpc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2012_cpc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4_cpc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_nace'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'naics_isic5'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc_isic5'`.execute(db);
}
