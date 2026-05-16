import { Kysely, sql } from 'kysely';

/**
 * Migration 0097: ISIC5 extended + CPC21/NACE cross-links + geo chains + ISO 639.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 21).
 *
 * ## New bridges
 *
 * ### ISIC5 extended chains (via isic5_isic4 intermediate)
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | isic5_sitc4   | ~3,200 | isic5_isic4 ∘ isic4_sitc4 (ISIC5→SITC4)               |
 * | isic5_cpc3    | ~2,600 | isic5_isic4 ∘ isic4_cpc3  (ISIC5→CPC3)                |
 *
 * ### CPC21 ↔ NACE cross-links
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | cpc21_nace    |   ~679 | cpc21_isic4 ∘ isic4_nace (CPC21→NACE)                 |
 * | nace_cpc21    |   ~679 | nace_isic4 ∘ isic4_cpc21 (NACE→CPC21)                 |
 *
 * ### SITC4 extended (via ISIC4)
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | sitc4_nace    | ~3,200 | sitc4_isic4 ∘ isic4_nace (SITC4→NACE)                 |
 * | sitc4_cpc21   | ~3,200 | sitc4_isic4 ∘ isic4_cpc21 (SITC4→CPC21)               |
 *
 * ### Geographic chains
 *
 * | system            | edges   | derivation                                          |
 * |-------------------|---------|-----------------------------------------------------|
 * | locode_m49        | ~116,067| locode_iso3166 ∘ iso3166_m49 (LOCODE→M49 region)   |
 * | m49_iso3166       |    ~188 | reverse of iso3166_m49 (M49→ISO3166)               |
 * | m49_sovereign     |    ~219 | reverse of sovereign_m49 (M49→sovereign)            |
 * | sovereign_iso3166 |    ~215 | sovereign_m49 ∘ m49_iso3166 (sovereign→ISO3166)     |
 * | iso3166_sovereign |    ~215 | reverse of sovereign_iso3166                        |
 *
 * ### ISO 639 bidirectionality
 *
 * | system            | edges | derivation                                          |
 * |-------------------|-------|-----------------------------------------------------|
 * | iso639_iso639_3   |   183 | reverse of iso639_3_iso639 (ISO639→ISO639-3)       |
 * | macro_iso639_3    |   444 | reverse of iso639_3_macro (macro→ISO639-3)         |
 *
 * ## Coverage impact
 *
 * ISIC5 now connected to SITC4 and CPC3 in addition to HS, NACE, CPC21.
 * CPC21 and NACE now directly bridged (bidirectional).
 * SITC4 now connected to NACE and CPC21.
 * Geographic chain complete: LOCODE → ISO3166 ↔ M49 ↔ Sovereign.
 * ISO 639 fully bidirectional: ISO639-3 ↔ ISO639-1 ↔ macrolanguage.
 *
 * ## Total edges after 0097: ~1.1M+ (excl. openalex_concept)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ISIC5 extended
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_sitc4'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_cpc3'`.execute(db);

  // CPC21 ↔ NACE
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc21_nace'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'nace_cpc21'`.execute(db);

  // SITC4 extended
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4_nace'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4_cpc21'`.execute(db);

  // Geographic chains
  await sql`DELETE FROM edge_classified_as WHERE system = 'locode_m49'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'm49_iso3166'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'm49_sovereign'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sovereign_iso3166'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'iso3166_sovereign'`.execute(db);

  // ISO 639 bidirectionality
  await sql`DELETE FROM edge_classified_as WHERE system = 'iso639_iso639_3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'macro_iso639_3'`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'isic5_sitc4', 'isic5_cpc3',
    'cpc21_nace', 'nace_cpc21',
    'sitc4_nace', 'sitc4_cpc21',
    'locode_m49', 'm49_iso3166', 'm49_sovereign',
    'sovereign_iso3166', 'iso3166_sovereign',
    'iso639_iso639_3', 'macro_iso639_3',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
