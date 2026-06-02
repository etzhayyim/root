import { Kysely, sql } from 'kysely';

/**
 * Migration 0067: NAICS 2022 + ISIC Rev.5 industry classification masters.
 *
 * Bootstrapped via direct psql against localhost:14566 on 2026-04-15.
 * Data sources:
 *   - US Census Bureau NAICS 2022:
 *     https://www.census.gov/naics/2022NAICS/2-6%20digit_2022_Codes.xlsx
 *     2,125 rows (sectors / subsectors / industry groups / NAICS industries
 *     / national industries)
 *   - UNSD ISIC Rev.5 (released 2024):
 *     https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/ISIC_Rev_5_english_structure.csv
 *     830 rows (sections / divisions / groups / classes)
 *
 * RisingWave state after apply:
 *   - vertex_repo_record @ collection='com.etzhayyim.apps.naics.industry'
 *       2,125 rows
 *   - vertex_repo_record @ collection='com.etzhayyim.apps.open_isic.economic_activity_rev5'
 *       830 rows
 *   - view_naics_industry  — typed projection of NAICS 2022
 *   - view_isic5_activity  — typed projection of ISIC Rev.5
 *   - dim_world_domain.naics.world_total : 2,125
 *   - dim_world_domain.isic5.world_total : 830
 *
 * NB: re-run to refresh:
 *   python3 scripts/seed-naics.py | psql $PG_URL
 *   python3 scripts/seed-isic5.py | psql $PG_URL
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── view_naics_industry ───────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_naics_industry AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'         AS name,
      value_json::jsonb->>'level'        AS level,
      value_json::jsonb->>'code'         AS original_code,
      value_json::jsonb->>'parent'       AS parent_code,
      value_json::jsonb->>'edition'      AS edition,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.naics.industry'
  `.execute(db);

  // ── view_isic5_activity ───────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_isic5_activity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'   AS name,
      value_json::jsonb->>'level'  AS level,
      value_json::jsonb->>'parent' AS parent_code,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.open_isic.economic_activity_rev5'
  `.execute(db);

  // ── dim_world_domain ──────────────────────────────────────────────────
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('naics', 'naics.etzhayyim.com', 2125, 'industries', 'industry')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('isic5', 'isic5.etzhayyim.com', 830, 'industries', 'governance')
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_isic5_activity`.execute(db);
  await sql`DROP VIEW IF EXISTS view_naics_industry`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'naics'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'isic5'`.execute(db);
}
