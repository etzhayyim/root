import { Kysely, sql } from 'kysely';

/**
 * Migration 0079: UN LOCODE + ISO 3166-1 countries + geographic concordances.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 6).
 *
 * ## New taxonomy masters
 *
 * | Collection                        | Rows    | Source                                       |
 * |-----------------------------------|---------|----------------------------------------------|
 * | app.etzhayyim.apps.locode.location      | 116,067 | UNECE UN/LOCODE 2024-1 (via GitHub/datasets) |
 * | app.etzhayyim.apps.iso3166.country      |     296 | World Bank API (ISO 3166-1 alpha-3)          |
 *
 * ### UN LOCODE (United Nations Code for Trade and Transport Locations)
 * 116,067 location codes covering 249+ countries/territories.
 * Function breakdown:
 *   - 17,520 sea ports (function bit 1)
 *   - 13,143 road terminals (function bit 3)
 *   -  9,029 airports (function bit 4)
 *   - Multiple locations serve multiple functions.
 *
 * Source: UNECE via github.com/datasets/un-locode (2024 edition).
 * LOCODE format: 5-char code = 2-char ISO 3166-1 alpha-2 country + 3-char location.
 * Fields stored: name, country, subdivision, function_flags, coordinates, iata_code, status.
 *
 * ### ISO 3166-1 countries (World Bank edition)
 * 296 entries including sovereign states + territories (alpha-3 rkey).
 * Fields stored: name, iso2_code, region, income_level, capital.
 * Source: World Bank API v2 (api.worldbank.org/v2/country).
 *
 * ## New concordance bridges
 *
 * | system            | edges | description                                      |
 * |-------------------|-------|--------------------------------------------------|
 * | sovereign_m49     |   219 | sovereign.sovereign → m49_region (via numericCode) |
 * | iso3166_sovereign |   215 | iso3166.country → sovereign.sovereign (iso3 JOIN) |
 *
 * ## New views
 *
 * - view_locode_location: projection of app.etzhayyim.apps.locode.location
 * - view_iso3166_country: projection of app.etzhayyim.apps.iso3166.country
 *
 * ## Topology integrity (post-apply)
 *
 * 0 orphan nodes (both collections are flat — no parent hierarchy).
 * 0 dangling edges across all 29 concordance systems.
 *
 * Full concordance inventory (29 systems, 86,601 total edges excl. openalex/ipc):
 *   hs22_hs17 (6,561), hs12_hs17 (6,528), hs96_hs02 (6,226), hs07_hs12 (6,197),
 *   hs02_hs07 (6,108), hs2017 (5,843), hs2017_cpc3 (5,740), hs2012 (5,584),
 *   hs2012_cpc3 (5,500), sitc3_sitc4 (5,408), cpc3 (4,391), sitc4 (3,776),
 *   sitc4_cpc3 (3,717), sitc2_sitc3 (2,805), sitc2_sitc4 (2,693), cpc (2,663),
 *   cpc_isic5 (2,504), sitc1_sitc2 (1,334), isic5 (700), nace_r2 (679),
 *   isic5_nace (625), isic31_isic5 (231), isic31_isic4 (229),
 *   sovereign_m49 (219), iso3166_sovereign (215), isic2_isic31 (76),
 *   naics_isic5 (24), naics_isic4 (24)
 *
 * dim_world_domain additions: locode, iso3166.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── views ──────────────────────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_locode_location AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'        AS name,
      value_json::jsonb->>'country'     AS country,
      value_json::jsonb->>'subdivision' AS subdivision,
      value_json::jsonb->>'function'    AS function_codes,
      value_json::jsonb->>'iata'        AS iata_code,
      value_json::jsonb->>'coords'      AS coordinates,
      value_json::jsonb->>'status'      AS status,
      (value_json::jsonb->>'has_port')::boolean    AS has_port,
      (value_json::jsonb->>'has_airport')::boolean AS has_airport,
      (value_json::jsonb->>'has_rail')::boolean    AS has_rail,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.locode.location'
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_iso3166_country AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'    AS name,
      value_json::jsonb->>'iso2'    AS iso2_code,
      value_json::jsonb->>'region'  AS region,
      value_json::jsonb->>'income'  AS income_level,
      value_json::jsonb->>'capital' AS capital,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.iso3166.country'
  `.execute(db);

  // ── dim_world_domain ───────────────────────────────────────────────────
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('locode', 'locode.etzhayyim.com', 116067, 'locations', 'transport')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('iso3166', 'iso3166.etzhayyim.com', 296, 'countries', 'governance')
  `.execute(db);

  // ── geographic concordances (data-only, idempotent) ───────────────────
  await sql`DELETE FROM edge_classified_as WHERE system = 'sovereign_m49'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'iso3166_sovereign'`.execute(db);

  // NB: bridges re-generated via JOIN at ingestion time.
  // sovereign_m49: sovereign.numericCode JOIN m49_region.rkey
  // iso3166_sovereign: iso3166.rkey JOIN sovereign.rkey (both use ISO3 alpha-3)
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_locode_location`.execute(db);
  await sql`DROP VIEW IF EXISTS view_iso3166_country`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'app.etzhayyim.apps.locode.location'`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'app.etzhayyim.apps.iso3166.country'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain IN ('locode','iso3166')`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system IN ('sovereign_m49','iso3166_sovereign')`.execute(db);
}
