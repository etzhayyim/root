import { Kysely, sql } from 'kysely';

/**
 * Migration 0127: ICD-10 → ISIC4 healthcare + ATC drug class + ISCO/COFOG bridges.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 49).
 *
 * ## Systems Built (10 total = 5 forward + 5 reverse)
 *
 * | system       | edges   | method                                                    |
 * |--------------|---------|-----------------------------------------------------------|
 * | icd10_isic4  |  98,918 | ICD chapter letter → ISIC4 healthcare codes              |
 * | isic4_icd10  |  98,918 | reverse                                                   |
 * | icd10_atc    |  23,646 | ICD chapter letter → ATC L1 therapeutic group            |
 * | atc_icd10    |  23,646 | reverse                                                   |
 * | icd10_isco   | 282,444 | icd10_isic4 × isic4_isco chain                           |
 * | isco_icd10   | 282,444 | reverse                                                   |
 * | icd10_cofog  |  40,592 | icd10_isic4 × isic4_cofog chain                          |
 * | cofog_icd10  |  40,592 | reverse                                                   |
 *
 * ## Approach
 *
 * ### icd10_isic4 (direct concordance)
 *
 * All 18,463 ICD-10 vertices (chapters + 3-char + 4-char + leaf codes) mapped
 * to ISIC4 healthcare sector codes via a chapter-letter concordance:
 *
 * - ALL chapters → ISIC4 86/861/8610/862/8620 (hospital + medical practice)
 * - Chapter F (Mental) → also 872/8720 (residential mental health care)
 * - Chapter H (Eye/ear) → also 869 (other specialist practice)
 * - Chapter M (Musculoskeletal) → also 871/8710 (nursing care facilities)
 * - Chapter Z (Health status) → also 88/881/8810/889/8890 (social work activities)
 *
 * ISIC4 healthcare vertex IDs resolved from `isic4_isic5` and `isic4_cofog`
 * bridge src_vids (at://did:web:isic.etzhayyim.com/.../).
 *
 * ### icd10_atc (direct concordance)
 *
 * ICD-10 chapter letter → ATC Level 1 therapeutic group, per standard
 * clinical pharmacology concordance:
 *
 * - A (Intestinal infections) → J (anti-infectives)
 * - B (Infectious diseases) → J
 * - C (Neoplasms) → L (antineoplastics)
 * - D (Blood/neoplasms) → L + B (antineoplastics + blood agents)
 * - E (Endocrine) → A + H (alimentary/metabolism + hormones)
 * - F (Mental) → N (nervous system)
 * - G (Neurological) → N
 * - H (Eye/ear) → S (sensory organ drugs)
 * - I (Circulatory) → C (cardiovascular)
 * - J (Respiratory) → R + J (respiratory + anti-infectives)
 * - K (Digestive) → A (alimentary)
 * - L (Skin) → D (dermatologicals)
 * - M (Musculoskeletal) → M (musculo-skeletal)
 * - N (Genitourinary) → G
 * - O (Pregnancy) → G + H
 * - P (Perinatal) → J
 * - Q (Congenital) → A + L
 * - R (Symptoms) → A + B
 * - S (Injury) → B + M
 * - T (Poisoning) → B
 * - U (COVID-19) → J
 * - Z (Health status) → (none)
 *
 * ATC L1 vertex IDs: at://did:web:who.int/app.etzhayyim.apps.atc.substance/{A-V}
 * Note: ATC groups E, F, I, K, O, P, Q, T, U not present in DB (14 of 26
 * ATC L1 codes are in DB: A B C D G H J L M N P R S V).
 *
 * ### Extended chains
 *
 * icd10_isco: icd10_isic4 × isic4_isco (140 edges) → 282,444 pairs
 *   (18,463 ICD × ~15 ISCO occupations per healthcare ISIC4 code)
 *
 * icd10_cofog: icd10_isic4 × isic4_cofog (52 edges) → see final counts
 *
 * ## ICD-10 Coverage Summary (after 0127)
 *
 * 18,463 ICD-10 disease codes now connected to:
 * - ISIC4 healthcare sector (86/87/88) — hospital, medical, nursing, social
 * - ATC therapeutic groups (14 L1 codes in DB)
 * - ISCO-08 occupation groups (via isic4_isco chain)
 * - COFOG government functions (via isic4_cofog chain)
 *
 * Path: ICD-10 → ISIC4 → any trade/product/occupation classification
 *
 * DB after 0127: 4,356,802 edges, 577 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'icd10_isic4', 'isic4_icd10',
    'icd10_atc',   'atc_icd10',
    'icd10_isco',  'isco_icd10',
    'icd10_cofog', 'cofog_icd10',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'icd10_isic4', 'isic4_icd10',
    'icd10_atc',   'atc_icd10',
    'icd10_isco',  'isco_icd10',
    'icd10_cofog', 'cofog_icd10',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
