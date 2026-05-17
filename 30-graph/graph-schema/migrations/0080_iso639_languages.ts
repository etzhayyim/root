import { Kysely, sql } from 'kysely';

/**
 * Migration 0080: ISO 639-1 language codes + iso3166_m49 concordance.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 6 continued).
 *
 * ## New taxonomy master
 *
 * | Collection                     | Rows | Source                                         |
 * |--------------------------------|------|------------------------------------------------|
 * | ai.gftd.apps.iso639.language   |  184 | ISO 639-1 via github.com/haliaeetus/iso-639    |
 *
 * ### ISO 639-1 (language codes)
 * 184 language codes with ISO 639-1 (2-char) and ISO 639-2 (3-char) codes.
 * Fields: name, native_name, language_family, iso639_2_code.
 * Used by: HTML lang attr, BCP 47, Unicode CLDR, all content localization.
 * Links to: the `i18n` domain (7,168 living languages total — ISO 639-1 is the
 * top-level 184 standardized codes, a subset of the full language inventory).
 *
 * ## New concordance bridge
 *
 * | system        | edges | description                                    |
 * |---------------|-------|------------------------------------------------|
 * | iso3166_m49   |   215 | iso3166.country → m49_region (via country-code) |
 *
 * ## New view
 *
 * - view_iso639_language: projection of ai.gftd.apps.iso639.language
 *
 * ## Topology integrity
 *
 * 0 orphan nodes (flat single-level hierarchy).
 * 0 dangling edges for iso3166_m49.
 *
 * Full concordance inventory (30 systems, 86,816 total edges excl. openalex/ipc):
 *   hs22_hs17 (6,561), hs12_hs17 (6,528), hs96_hs02 (6,226), hs07_hs12 (6,197),
 *   hs02_hs07 (6,108), hs2017 (5,843), hs2017_cpc3 (5,740), hs2012 (5,584),
 *   hs2012_cpc3 (5,500), sitc3_sitc4 (5,408), cpc3 (4,391), sitc4 (3,776),
 *   sitc4_cpc3 (3,717), sitc2_sitc3 (2,805), sitc2_sitc4 (2,693), cpc (2,663),
 *   cpc_isic5 (2,504), sitc1_sitc2 (1,334), isic5 (700), nace_r2 (679),
 *   isic5_nace (625), isic31_isic5 (231), isic31_isic4 (229),
 *   sovereign_m49 (219), iso3166_sovereign (215), iso3166_m49 (215),
 *   isic2_isic31 (76), naics_isic5 (24), naics_isic4 (24)
 *
 * dim_world_domain addition: iso639.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE VIEW IF NOT EXISTS view_iso639_language AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'        AS name,
      value_json::jsonb->>'native_name' AS native_name,
      value_json::jsonb->>'family'      AS language_family,
      value_json::jsonb->>'iso639_2'    AS iso639_2_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.iso639.language'
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('iso639', 'iso639.etzhayyim.com', 184, 'languages', 'culture')
  `.execute(db);

  await sql`DELETE FROM edge_classified_as WHERE system = 'iso3166_m49'`.execute(db);
  // NB: iso3166_m49 edges re-generated via JOIN on country-code (ISO 3166 numeric = M49 numeric)
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_iso639_language`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.iso639.language'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'iso639'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'iso3166_m49'`.execute(db);
}
