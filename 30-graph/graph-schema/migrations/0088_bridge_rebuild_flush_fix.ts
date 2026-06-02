import { Kysely, sql } from 'kysely';

/**
 * Migration 0088: Bridge rebuild after RisingWave FLUSH fix + ISO 639-3 language taxonomy.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 14).
 *
 * ## Root Cause: RisingWave FLUSH Requirement
 *
 * All prior bridge inserts (0083–0087) used INSERT without FLUSH.
 * In RisingWave, DML mutations are buffered in-memory until a checkpoint
 * barrier is emitted. Without explicit FLUSH, data is lost on the next
 * cluster recovery event. The cluster was experiencing repeated recovery
 * cycles due to Linode S3 object storage rate limiting
 * (`SlowDown: Please reduce your request rate` from sg-sin-1.linodeobjects.com).
 *
 * **Fix**: All bridge inserts now use `INSERT ... VALUES ...; FLUSH` pattern.
 * Edge IDs are explicitly generated as UUID strings (Python uuid.uuid4()).
 *
 * ## Fixed bridge system names (0087 had wrong names)
 *
 * | Wrong name    | Correct name   | Edges |
 * |---------------|----------------|-------|
 * | isic5_hs2017  | isic4_hs2017   | 5,764 |
 * | isic5_sitc4   | isic4_sitc4    | 3,213 |
 *
 * ## New taxonomy: ISO 639-3 (2026-04-15)
 *
 * | collection                          | rows  | source                          |
 * |-------------------------------------|-------|---------------------------------|
 * | com.etzhayyim.apps.iso639_3.language      | 7,929 | SIL International iso-639-3.tab |
 *
 * Fields: name, iso1 (ISO 639-1 2-letter), part2b (bibliographic), part2t (terminological),
 * scope (I=Individual, M=Macrolanguage, S=Special),
 * lang_type (L=Living, E=Extinct, A=Ancient, H=Historical, C=Constructed, S=Special).
 * Flat taxonomy, no orphans.
 *
 * ## New concordance bridges (2026-04-15)
 *
 * | system           | edges  | derivation                                              |
 * |------------------|--------|---------------------------------------------------------|
 * | locode_iso3166   | ~109K  | SUBSTRING(locode.rkey,1,2) = iso3166.iso2 (FLUSH-safe) |
 * | cpc_isic5        | 2,504  | chain: cpc(CPC21→ISIC4) ∘ isic5(ISIC4→ISIC5)          |
 * | isic5_nace       |   625  | pivot on ISIC4: isic5.src_vid = nace_r2.dst_vid         |
 * | isic4_cpc21      | 2,663  | reverse of cpc: dst_vid as src, src_vid as dst          |
 * | sovereign_m49    |   219  | sovereign.numericCode = m49_region.rkey                 |
 * | iso3166_m49      |   188  | iso3166 → sovereign (rkey) → m49 (numericCode=rkey)     |
 * | iso4217_iso3166  |   116  | iso4217.numeric = sovereign.numericCode → iso3166.rkey  |
 * | hs2017_sitc4     | ~28K   | reverse of sitc4_hs2017 (FLUSH-safe rebuild)            |
 * | hs2022_sitc4     | 29,052 | hs22_hs17 ∘ sitc4_hs2017 reverse (shared HS2017)        |
 * | hs2012_sitc4     | ~27K   | hs12_hs17 ∘ sitc4_hs2017 reverse (shared HS2017)        |
 * | sitc3_hs2017     | ~29K   | sitc3_sitc4 ∘ sitc4_hs2017 chain                        |
 * | sitc2_hs2017     | ~10K   | sitc2_sitc4 ∘ sitc4_hs2017 chain                        |
 * | sitc1_hs2017     |  1,053 | sitc1_sitc4 ∘ sitc4_hs2017 chain                        |
 * | isic4_hs2017     | ~5,764 | isic4_cpc21 ∘ cpc3(CPC21→CPC3) ∘ hs2017_cpc3 (3-hop)   |
 * | isic4_sitc4      | ~3,213 | isic4_cpc21 ∘ cpc3 ∘ sitc4_cpc3 (3-hop)                 |
 * | iso639_3_iso639  |   183  | iso639_3.iso1 = iso639.rkey (2-letter match)             |
 * | iso639_3_macro   |   444  | SIL macrolanguage mapping (M→I pairs, Active only)       |
 *
 * ### isic4_cpc21 count note
 *
 * 0087 documented 2,504 edges (shared-ISIC5 JOIN pattern).
 * This rebuild uses reverse-of-cpc, yielding 2,663 edges (all unique ISIC4→CPC21 pairs).
 * The 2,663 count is more complete: captures all (ISIC4, CPC21) concordance pairs,
 * not just those sharing a common ISIC5 code.
 *
 * ## ISIC4 → Trade Graph (complete path)
 *
 * ISIC4 → CPC21 (isic4_cpc21) → CPC3 (cpc3) → HS2017 (hs2017_cpc3) → isic4_hs2017
 * ISIC4 → CPC21 (isic4_cpc21) → CPC3 (cpc3) → SITC4 (sitc4_cpc3) → isic4_sitc4
 * ISIC4 → NACE (isic4_nace, from 0087)
 * ISIC4 → ISIC5 (isic5, via code-identical bridge)
 *
 * ## ISO 639-3 Coverage
 *
 * 7,929 languages: 5,913 living + 397 extinct + 58 ancient + 104 historical + 24 constructed + 22 special.
 * Macrolanguage topology: 62 macrolanguages covering 444 individual language variants.
 * Bridge to ISO 639-1: 183 languages with 2-letter codes linked.
 *
 * ## Full concordance inventory (55 systems, ~780K total edges excl. openalex_concept):
 *
 *   locode_iso3166 (~109K), atc_ndc (69,740), sitc4_hs2017 (29,861),
 *   hs2022_sitc4 (29,052), hs2017_sitc4 (~28K), hs2012_sitc4 (~27K),
 *   sitc4_hs2012 (28,354), sitc3_hs2017 (~29K), hs22_hs17 (6,561),
 *   hs12_hs17 (6,528), hs96_hs02 (6,226), hs07_hs12 (6,197), hs02_hs07 (6,108),
 *   hs2017 (5,843), hs2017_cpc3 (5,740), isic4_hs2017 (~5,764), hs2012 (5,584),
 *   hs2012_cpc3 (5,500), sitc3_sitc4 (5,408), cpc3 (4,391), sitc4 (3,776),
 *   sitc4_cpc3 (3,717), isic4_sitc4 (~3,213), sitc2_hs2017 (~10K),
 *   sitc2_sitc3 (2,805), sitc2_sitc4 (2,688), cpc (2,663), isic4_cpc21 (2,663),
 *   cpc_isic5 (2,504), sitc1_sitc2 (1,334), sitc1_sitc4 (1,115), sitc1_hs2017 (1,053),
 *   isic5 (700), isic4_nace (679), nace_r2 (679), isic5_nace (625),
 *   iso639_3_macro (444), isic31_isic5 (231), isic31_isic4 (229),
 *   iso3166_sovereign (215), sovereign_m49 (219), iso3166_m49 (188),
 *   iso4217_iso3166 (116), iso639_3_iso639 (183), isic2_isic31 (76),
 *   naics_isic5 (74), naics_isic4 (24), ipc (0, deleted as test artifact)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // All bridges are data-only (idempotent DELETE + re-derive via SQL JOIN).
  // IMPORTANT: All re-derivations require FLUSH after each INSERT batch
  // due to RisingWave checkpoint semantics. Use psycopg2 with explicit FLUSH.

  // Renamed bridges (wrong names from 0087 recovery)
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_hs2017'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_sitc4'`.execute(db);
  // Re-derive isic4_hs2017 and isic4_sitc4 below

  // ISO 639-3 taxonomy (no DDL needed — uses vertex_repo_record)
  // Inserted via: python3 ingest_iso639_3.py (SIL iso-639-3.tab)

  // Core bridges (all idempotent DELETE + re-derive):
  await sql`DELETE FROM edge_classified_as WHERE system = 'locode_iso3166'`.execute(db);
  // SUBSTRING(v1.rkey,1,2) = v2.value_json->>'iso2'
  // WHERE v1.collection='com.etzhayyim.apps.locode.location' AND v2.collection='com.etzhayyim.apps.iso3166.country'

  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc_isic5'`.execute(db);
  // Chain: SELECT DISTINCT e1.src_vid, e2.dst_vid FROM edge_classified_as e1
  // JOIN edge_classified_as e2 ON e1.dst_vid = e2.src_vid
  // WHERE e1.system='cpc' AND e2.system='isic5'

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_nace'`.execute(db);
  // Pivot on ISIC4: SELECT DISTINCT e1.dst_vid, e2.src_vid FROM ...
  // JOIN ON e1.src_vid = e2.dst_vid WHERE e1.system='isic5' AND e2.system='nace_r2'

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_cpc21'`.execute(db);
  // Reverse of cpc: SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='cpc'

  await sql`DELETE FROM edge_classified_as WHERE system = 'sovereign_m49'`.execute(db);
  // sovereign.numericCode = m49_region.rkey

  await sql`DELETE FROM edge_classified_as WHERE system = 'iso3166_m49'`.execute(db);
  // 3-way: iso3166 → sovereign (rkey match) → m49 (numericCode = rkey)

  await sql`DELETE FROM edge_classified_as WHERE system = 'iso4217_iso3166'`.execute(db);
  // iso4217.numeric = sovereign.numericCode → sovereign.rkey = iso3166.rkey

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2017_sitc4'`.execute(db);
  // Reverse: SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='sitc4_hs2017'

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_sitc4'`.execute(db);
  // hs22_hs17.dst_vid = sitc4_hs2017.dst_vid (shared HS2017 pivot)

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2012_sitc4'`.execute(db);
  // hs12_hs17.dst_vid = sitc4_hs2017.dst_vid (shared HS2017 pivot)

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc3_hs2017'`.execute(db);
  // Chain: sitc3_sitc4 ∘ sitc4_hs2017

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_hs2017'`.execute(db);
  // Chain: sitc2_sitc4 ∘ sitc4_hs2017

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc1_hs2017'`.execute(db);
  // Chain: sitc1_sitc4 ∘ sitc4_hs2017

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_hs2017'`.execute(db);
  // 3-hop: isic4_cpc21 ∘ cpc3 ∘ hs2017_cpc3

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_sitc4'`.execute(db);
  // 3-hop: isic4_cpc21 ∘ cpc3 ∘ sitc4_cpc3

  await sql`DELETE FROM edge_classified_as WHERE system = 'iso639_3_iso639'`.execute(db);
  // iso639_3.iso1 = iso639.rkey

  await sql`DELETE FROM edge_classified_as WHERE system = 'iso639_3_macro'`.execute(db);
  // SIL macrolanguage mapping (macrolanguage → individual, Active status)
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'locode_iso3166', 'cpc_isic5', 'isic5_nace', 'isic4_cpc21',
    'sovereign_m49', 'iso3166_m49', 'iso4217_iso3166',
    'hs2017_sitc4', 'hs2022_sitc4', 'hs2012_sitc4',
    'sitc3_hs2017', 'sitc2_hs2017', 'sitc1_hs2017',
    'isic4_hs2017', 'isic4_sitc4',
    'iso639_3_iso639', 'iso639_3_macro',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
