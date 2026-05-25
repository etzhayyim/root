import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 0062: CPC / ISIC taxonomy + shohin product master.
 *
 * Records an authoritative Kysely migration for three objects that were
 * bootstrapped via direct psql against localhost:14566 on 2026-04-15
 * while the normal PDS write path was offline:
 *
 *   - TABLE  vertex_shohin         — global product master (seeded 30 rows)
 *   - VIEW   view_cpc_product      — typed projection of
 *                                    vertex_repo_record where
 *                                    collection='app.etzhayyim.apps.cpc.commodity_item'
 *                                    (UN CPC Ver.2.1 full hierarchy, 4,596 rows)
 *   - VIEW   view_isic_activity    — typed projection of
 *                                    vertex_repo_record where
 *                                    collection='app.etzhayyim.apps.open_isic.economic_activity'
 *                                    (UN ISIC Rev.4 full hierarchy, 766 rows)
 *
 * dim_world_domain adjustments (idempotent):
 *   - cpc.world_total  : 2738 → 4596 (UNSD authoritative count)
 *   - isic.world_total : 419  → 766  (full hierarchy not just classes)
 *   - hs               : new row (5300 products target)
 *
 * Pre-flight (graph-schema CLAUDE.md §MV Memory Safety Guardrails):
 *   - Plain VIEWs only (no MATERIALIZED VIEW) — query-time JSONB projection
 *     is cheap at this scale (5k rows). MV would add zero value.
 *   - vertex_shohin is a narrow table with primary-key writes only;
 *     no streaming aggregate state.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── vertex_shohin — global product master ────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shohin (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      gtin               VARCHAR,
      name               VARCHAR,
      brand              VARCHAR,
      category           VARCHAR,
      cpc_code           VARCHAR,
      country_of_origin  VARCHAR,
      manufacturer       VARCHAR,
      currency           VARCHAR,
      price_amount       DOUBLE PRECISION,
      created_at         VARCHAR
    )
  `.execute(db);

  // ── view_cpc_product — typed projection over vertex_repo_record ─────
  await sql`
    CREATE VIEW IF NOT EXISTS view_cpc_product AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'"group"'  AS group_code,
      value_json::jsonb->>'class'    AS class_code,
      value_json::jsonb->>'parent'   AS parent_code,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.cpc.commodity_item'
  `.execute(db);

  // ── view_isic_activity — typed projection over vertex_repo_record ───
  await sql`
    CREATE VIEW IF NOT EXISTS view_isic_activity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'   AS name,
      value_json::jsonb->>'level'  AS level,
      value_json::jsonb->>'parent' AS parent_code,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.open_isic.economic_activity'
  `.execute(db);

  // ── dim_world_domain corrections ─────────────────────────────────────
  await sql`UPDATE dim_world_domain SET world_total = 4596 WHERE domain = 'cpc'`.execute(db);
  await sql`UPDATE dim_world_domain SET world_total = 766  WHERE domain = 'isic'`.execute(db);
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('hs', 'hs.etzhayyim.com', 5300, 'products', 'trade')
    ON CONFLICT DO NOTHING
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_isic_activity`.execute(db);
  await sql`DROP VIEW IF EXISTS view_cpc_product`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shohin`.execute(db);
  await sql`UPDATE dim_world_domain SET world_total = 2738 WHERE domain = 'cpc'`.execute(db);
  await sql`UPDATE dim_world_domain SET world_total = 419  WHERE domain = 'isic'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'hs'`.execute(db);
}
