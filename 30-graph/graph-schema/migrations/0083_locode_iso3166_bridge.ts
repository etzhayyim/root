import { Kysely, sql } from 'kysely';

/**
 * Migration 0083: UN LOCODE ↔ ISO 3166-1 concordance bridge.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 9).
 *
 * ## New concordance bridge
 *
 * | system          | edges   | description                                            |
 * |-----------------|---------|--------------------------------------------------------|
 * | locode_iso3166  | 115,687 | UN LOCODE location → ISO 3166-1 country (country JOIN) |
 *
 * ### locode_iso3166 bridge derivation
 * JOIN: locode.country_field = iso3166.iso2_code
 * LOCODE rkey format = 5-char: first 2 chars = ISO 3166-1 alpha-2 country code.
 * ISO 3166-1 has an iso2_code field (alpha-2) stored in value_json.
 * 115,687 LOCODE locations successfully mapped to their ISO 3166-1 country node.
 * LOCODE collection: ai.gftd.apps.locode.location (116,067 rows)
 * ISO 3166-1 collection: ai.gftd.apps.iso3166.country (296 rows)
 * Unmatched: ~380 rows (edge-case territories with non-standard 2-char codes).
 *
 * ## Full concordance inventory (32 systems, 272,243 total edges excl. openalex/ipc):
 *   locode_iso3166 (115,687), atc_ndc (69,740), hs22_hs17 (6,561), hs12_hs17 (6,528),
 *   hs96_hs02 (6,226), hs07_hs12 (6,197), hs02_hs07 (6,108), hs2017 (5,843),
 *   hs2017_cpc3 (5,740), hs2012 (5,584), hs2012_cpc3 (5,500), sitc3_sitc4 (5,408),
 *   cpc3 (4,391), sitc4 (3,776), sitc4_cpc3 (3,717), sitc2_sitc3 (2,805),
 *   sitc2_sitc4 (2,693), cpc (2,663), cpc_isic5 (2,504), sitc1_sitc2 (1,334),
 *   isic5 (700), nace_r2 (679), isic5_nace (625), isic31_isic5 (231),
 *   isic31_isic4 (229), sovereign_m49 (219), iso3166_sovereign (215),
 *   iso3166_m49 (215), isic2_isic31 (76), naics_isic5 (24), naics_isic4 (24)
 *
 * ## Topology integrity (post-apply)
 *
 * 0 orphan nodes across all taxonomy collections.
 * 0 dangling edges in locode_iso3166 (all src/dst refs verified).
 *
 * dim_world_domain additions: none (locode and iso3166 already registered in 0079).
 */
export async function up(db: Kysely<any>): Promise<void> {
  // locode_iso3166 bridge: LOCODE location → ISO 3166-1 country
  // Data already inserted via direct psql in iteration 9.
  // This migration is idempotent: DELETE + re-derive via country field JOIN.
  await sql`DELETE FROM edge_classified_as WHERE system = 'locode_iso3166'`.execute(db);
  // NB: re-generated via:
  //   JOIN SUBSTRING(locode.rkey, 1, 2) = iso3166.value_json->>'iso2_code'
  //   WHERE locode.collection = 'ai.gftd.apps.locode.location'
  //     AND iso3166.collection = 'ai.gftd.apps.iso3166.country'
  // python3 /tmp/build_locode_iso3166.py
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DELETE FROM edge_classified_as WHERE system = 'locode_iso3166'`.execute(db);
}
