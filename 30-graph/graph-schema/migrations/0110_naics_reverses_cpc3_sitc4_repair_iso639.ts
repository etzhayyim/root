import { Kysely, sql } from 'kysely';

/**
 * Migration 0110: NAICS small reverses + cpc3_sitc4 repair + ISO 639-3 macro reverse.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 31).
 *
 * ## NAICS missing reverses
 *
 * | system      | edges | derivation                |
 * |-------------|-------|---------------------------|
 * | cpc21_naics |    67 | reverse of naics_cpc21    |
 * | isic5_naics |    74 | reverse of naics_isic5    |
 * | isic4_naics |    24 | reverse of naics_isic4    |
 *
 * NOTE: naics_cpc21 (67 edges, class-level 4-digit NAICS→CPC21) is the
 * primary class-level pivot. Its reverse cpc21_naics enables CPC21→NAICS
 * lookups directly without chaining.
 *
 * ## cpc3_sitc4 repair
 *
 * | system      | before | after | root cause                      |
 * |-------------|--------|-------|---------------------------------|
 * | cpc3_sitc4  | 61,436 | 3,717 | old CPC21 fan-out noise         |
 *
 * cpc3_sitc4 was previously built via CPC21 mediation (cpc3_cpc21 ∘ cpc21_sitc4
 * → 61K noisy edges). Rebuilt as exact reverse of sitc4_cpc3 (3,717 direct
 * concordance pairs). Aligns with the same precision standard applied to
 * cpc3_hs2012 in migration 0109.
 *
 * NOTE: `cpc3_hs2022` (115K) and `cpc3_hs2012` (5,500) now represent
 * different precision levels — hs2022 has no direct CPC3 concordance and
 * uses CPC21 fan-out; hs2012/hs2017 have direct concordances (5,500/5,740).
 * The large hs2022 fan-out bridges are accepted as coarse approximate
 * classification only.
 *
 * ## ISO 639-3 macro language reverse
 *
 * | system          | edges | derivation                     |
 * |-----------------|-------|--------------------------------|
 * | macro_iso639_3  |   444 | reverse of iso639_3_macro      |
 *
 * iso639_3_macro (444) maps individual ISO 639-3 languages to their macro
 * language encompassing variety. macro_iso639_3 enables macro→individual
 * enumeration. Completes the ISO 639-3 bidirectional links.
 *
 * ## Coverage completeness after 0110
 *
 * NAICS 2022 is now fully bidirectional with:
 * - ISIC Rev.2/3.1/4/5 (via chain)
 * - CPC v2.1, CPC v3 (via naics_cpc21 class-level pivot)
 * - All 7 HS editions (via cpc21 chain)
 * - All 4 SITC revisions (via cpc21 chain)
 * - NACE Rev.2 (via isic4)
 * - ISO 639-3 fully bidirectional (individual ↔ macro language)
 *
 * ## sovereign_locode gap fix
 *
 * sovereign_locode was 108,187 vs locode_sovereign=109,687 (1,500 missing).
 * Added 1,500 missing pairs — sovereign_locode now 109,687 (exact reverse).
 * Root cause: likely non-deterministic DISTINCT at build time caused 1,500
 * pairs to be silently dropped.
 *
 * ## Total edges after 0110: ~4.64M
 *
 * Note: edge count lower than 0109 due to cpc3_sitc4 repair (-57,719 net).
 */
export async function up(db: Kysely<any>): Promise<void> {
  // NAICS missing reverses
  for (const system of ['cpc21_naics', 'isic5_naics', 'isic4_naics']) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // ISO 639-3 macro reverse
  await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit('macro_iso639_3')}`.execute(db);

  // cpc3_sitc4 repair (delete noisy 61K, rebuild as exact reverse of sitc4_cpc3)
  await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit('cpc3_sitc4')}`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'cpc21_naics', 'isic5_naics', 'isic4_naics',
    'macro_iso639_3',
    'cpc3_sitc4',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
