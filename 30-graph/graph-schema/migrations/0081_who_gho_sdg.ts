import { Kysely, sql } from 'kysely';

/**
 * Migration 0081: WHO GHO health indicators + UN SDG framework.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 7).
 *
 * ## New taxonomy masters
 *
 * | Collection                       | Rows  | Source                                    |
 * |----------------------------------|-------|-------------------------------------------|
 * | ai.gftd.apps.who.gho_indicator   | 3,057 | WHO GHO API (ghoapi.azureedge.net)        |
 * | ai.gftd.apps.sdg.indicator       |   437 | UN SDG API (unstats.un.org/sdgs)          |
 *
 * ### WHO Global Health Observatory (GHO) indicators
 * 3,057 unique health indicators (English, deduplicated by IndicatorCode).
 * Source: WHO GHO OData API v1 (full indicator list, no pagination needed).
 * Major indicator groups: SA (456), GDO (220), NCD (176), RSUD (166), GOE (92),
 *   TB (76), TOBACCO (70), FOODBORNE (52), FINPROTECTION (49), …
 * Used by: World Health Report, IHME GBD, WHO SCORE framework, country profiles.
 * Stored as flat list (no parent hierarchy); grouped by code prefix.
 *
 * ### UN Sustainable Development Goals (SDG) framework
 * 437 nodes in 3-level hierarchy:
 *   - 17 goals (SDG 1–17)
 *   - 169 targets (e.g. "1.1", "3.b")
 *   - 251 indicators with tier classification (Tier I/II/III)
 * Source: UN Statistics Division UNSDG API v5 (unstats.un.org/sdgs/UNSDGAPIV5).
 * 0 orphan nodes: all targets point to goal nodes, all indicators point to targets.
 * Tier I = methodologically established + data available for >50% countries.
 *
 * ## New views
 *
 * - view_who_gho_indicator: projection of ai.gftd.apps.who.gho_indicator
 * - view_sdg_indicator: projection of ai.gftd.apps.sdg.indicator
 *
 * ## Topology integrity
 *
 * SDG: 0 orphan nodes (target.parent = goal node, indicator.parent = target node).
 * GHO: 0 orphan nodes (flat single-level structure).
 * No new concordance edges.
 *
 * dim_world_domain additions: who_gho, sdg.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE VIEW IF NOT EXISTS view_who_gho_indicator AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'  AS name,
      value_json::jsonb->>'group' AS indicator_group,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.who.gho_indicator'
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_sdg_indicator AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'   AS name,
      value_json::jsonb->>'level'  AS level,
      value_json::jsonb->>'goal'   AS goal,
      value_json::jsonb->>'target' AS target,
      value_json::jsonb->>'tier'   AS tier,
      value_json::jsonb->>'parent' AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.sdg.indicator'
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('who_gho', 'gho.etzhayyim.com', 3057, 'health indicators', 'healthcare')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('sdg', 'sdg.etzhayyim.com', 251, 'SDG indicators', 'governance')
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_who_gho_indicator`.execute(db);
  await sql`DROP VIEW IF EXISTS view_sdg_indicator`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.who.gho_indicator'`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.sdg.indicator'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain IN ('who_gho','sdg')`.execute(db);
}
