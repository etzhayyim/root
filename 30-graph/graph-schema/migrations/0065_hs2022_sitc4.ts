import { Kysely, sql } from 'kysely';

/**
 * Migration 0065: HS 2022 (H6) + SITC Rev.4 commodity masters.
 *
 * Bootstrapped via direct psql against localhost:14566 on 2026-04-15.
 * Data sources (UN Comtrade authoritative):
 *   - https://comtradeapi.un.org/files/v1/app/reference/H6.json
 *     → 6,939 rows: chapters / headings / subheadings (HS 2022)
 *   - https://comtradeapi.un.org/files/v1/app/reference/S4.json
 *     → 5,484 rows: sections / divisions / groups (SITC Rev.4)
 *
 * RisingWave state after apply:
 *   - vertex_repo_record @ collection='app.etzhayyim.apps.hs.commodity2022'
 *       6,939 rows (97 chapters + 1,228 headings + 5,614 subheadings)
 *   - vertex_repo_record @ collection='app.etzhayyim.apps.sitc.commodity'
 *       5,484 rows
 *   - view_hs2022_commodity  — typed projection of HS 2022
 *   - view_sitc_commodity    — typed projection of SITC Rev.4
 *   - dim_world_domain.hs2022.world_total : 6,939
 *   - dim_world_domain.sitc.world_total   : 5,484
 *
 * NB: re-run the ingest scripts to repopulate rows:
 *   python3 scripts/seed-hs-comtrade.py --edition H6 | psql $PG_URL
 *   python3 scripts/seed-sitc-comtrade.py | psql $PG_URL
 * Both pipelines are idempotent (DELETE + INSERT).
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── view_hs2022_commodity ─────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_hs2022_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'    AS name,
      value_json::jsonb->>'level'   AS level,
      value_json::jsonb->>'chapter' AS chapter,
      value_json::jsonb->>'heading' AS heading,
      value_json::jsonb->>'parent'  AS parent_code,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.hs.commodity2022'
  `.execute(db);

  // ── view_sitc_commodity ───────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_sitc_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'parent'   AS parent_code,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.sitc.commodity'
  `.execute(db);

  // ── dim_world_domain ──────────────────────────────────────────────────
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('hs2022', 'hs2022.etzhayyim.com', 6939, 'products', 'trade')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('sitc', 'sitc.etzhayyim.com', 5484, 'products', 'trade')
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_sitc_commodity`.execute(db);
  await sql`DROP VIEW IF EXISTS view_hs2022_commodity`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'hs2022'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'sitc'`.execute(db);
}
