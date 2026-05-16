import { Kysely, sql } from 'kysely';

/**
 * Migration 0131: icd10_sdg repair + ATC completeness + NAICS/ISIC3.1/ISIC2 remaining chains.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 53).
 *
 * ## Systems Built (TBD total)
 *
 * ### icd10_sdg repair
 * | system    | edges  | note                                           |
 * |-----------|--------|------------------------------------------------|
 * | icd10_sdg | 18,802 | repair: 0→18,802 (lost to cluster reset in 0130) |
 *
 * ### ATC completeness
 * | system  | edges | pivot chain                    |
 * |---------|-------|--------------------------------|
 * | atc_cpc3 |   98 | atc_isic4 × isic4_cpc3         |
 * | cpc3_atc |   98 | reverse                        |
 *
 * ### NAICS remaining chains (via naics_isic4 × isic4_X)
 * ALL = 0. naics_isic4 = 24 coarse sector mappings (NAICS division → ISIC4 section A-U).
 * These sector codes don't align with the healthcare/pharma/SDG ISIC4 codes in
 * isic4_{icd10,sdg,gho,atc} — no chain overlap.
 * naics_cpc3 was already built; all others skipped.
 *
 * ### ISIC Rev.3.1 remaining chains (via isic31_isic4 × isic4_X)
 * | system       | edges | pivot                      |
 * |--------------|-------|----------------------------|
 * | isic31_sdg   |   100 | isic31_isic4 × isic4_sdg   |
 * | sdg_isic31   |   100 | reverse                    |
 * | isic31_atc   |    28 | isic31_isic4 × isic4_atc   |
 * | atc_isic31   |    28 | reverse                    |
 *
 * NOTE: isic31_icd10 = 0 (ISIC3.1 has 229 edges to ISIC4, but none land on healthcare
 * ISIC4 86/87/88). isic31_gho = 0 (same reason). isic31_sdg/atc non-zero because
 * ISIC3.1 maps to some pharma (2420) → ISIC4 2100 → ATC L1.
 *
 * ### ISIC Rev.2 remaining chains (via isic2_isic4 × isic4_X)
 * | system      | edges | pivot                     |
 * |-------------|-------|---------------------------|
 * | isic2_sdg   |    35 | isic2_isic4 × isic4_sdg   |
 * | sdg_isic2   |    35 | reverse                   |
 *
 * NOTE: isic2_icd10 = 0 (isic2_isic4 = 43 sparse sector edges, none into healthcare).
 *
 * DB after 0131: 7,687,914 edges, 623 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    // ATC completeness
    'atc_cpc3',     'cpc3_atc',
    // ISIC3.1 remaining (NAICS/icd10/gho chains = 0, skipped)
    'isic31_sdg',   'sdg_isic31',
    'isic31_atc',   'atc_isic31',
    // ISIC2 remaining (icd10 chain = 0, skipped)
    'isic2_sdg',    'sdg_isic2',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'atc_cpc3',     'cpc3_atc',
    'isic31_sdg',   'sdg_isic31',
    'isic31_atc',   'atc_isic31',
    'isic2_sdg',    'sdg_isic2',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
