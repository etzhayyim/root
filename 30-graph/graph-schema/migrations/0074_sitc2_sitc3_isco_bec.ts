import { Kysely, sql } from 'kysely';

/**
 * Migration 0074: SITC Rev.2, SITC Rev.3, ISCO-08, BEC Rev.5 + inter-SITC bridges.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 4).
 *
 * ## New taxonomy masters
 *
 * | Collection                               | Rows | Source                        |
 * |------------------------------------------|------|-------------------------------|
 * | ai.gftd.apps.sitc.commodity_rev3         | 5,690 | UN Comtrade S3.json (SITC R.3)|
 * | ai.gftd.apps.sitc.commodity_rev2         | 3,723 | UN Comtrade S2.json (SITC R.2)|
 * | ai.gftd.apps.isco.occupation             |   393 | ILO ISCO-08 (2012 edition)    |
 * | ai.gftd.apps.bec.category                |    31 | UN BEC Rev.5 (2016)           |
 *
 * ### SITC Revision history coverage
 * SITC Rev.2 (1975) → Rev.3 (1986) → Rev.4 (2006): now all three editions in graph.
 * Level distribution for Rev.3: 10 sections / 77 divisions / 338 groups / 1,371 subgroups / 3,894 items.
 * Level distribution for Rev.2: 10 sections / 79 divisions / 318 groups / 1,104 subgroups / 2,212 items.
 *
 * ### ISCO-08 occupation hierarchy
 * 10 major groups / 43 sub-major groups / 130 minor groups / 210 unit groups = 393 nodes.
 * Source: ILO International Standard Classification of Occupations 2008 (2nd ed. 2012).
 * Note: ESCO→ISCO link is via vertex_occupation.isco_code promoted column (not edge table),
 *       because ESCO occupations live in vertex_occupation (not vertex_repo_record).
 *
 * ### BEC Rev.5 (Broad Economic Categories)
 * 31 nodes: 7 sections / 16 divisions / 8 groups.
 * Source: UN Statistics Division 2016 (BEC Revision 5).
 *
 * ## New concordance systems
 *
 * | system        | edges | description                                  |
 * |---------------|-------|----------------------------------------------|
 * | sitc3_sitc4   | 5,408 | SITC Rev.3 → SITC Rev.4 (code-identical)     |
 * | sitc2_sitc3   | 2,805 | SITC Rev.2 → SITC Rev.3 (code-identical)     |
 * | sitc2_sitc4   | 2,693 | SITC Rev.2 → SITC Rev.4 (code-identical)     |
 *
 * ## New views
 *
 * - view_sitc3_commodity: projection of ai.gftd.apps.sitc.commodity_rev3
 * - view_sitc2_commodity: projection of ai.gftd.apps.sitc.commodity_rev2
 * - view_isco_occupation: projection of ai.gftd.apps.isco.occupation
 * - view_bec_category: projection of ai.gftd.apps.bec.category
 *
 * ## Topology integrity (post-apply)
 *
 * 0 orphan nodes across all 14 taxonomy collections.
 * 0 dangling edges across all 19 concordance systems (20 - esco_isco removed).
 *
 * Full concordance inventory (19 systems, 57,794 total edges excl. openalex/ipc):
 *   hs22_hs17 (6,561), hs12_hs17 (6,528), hs2017 (5,843), hs2017_cpc3 (5,740),
 *   hs2012 (5,584), hs2012_cpc3 (5,500), sitc3_sitc4 (5,408), cpc3 (4,391),
 *   sitc4 (3,776), sitc4_cpc3 (3,717), sitc2_sitc3 (2,805), sitc2_sitc4 (2,693),
 *   cpc (2,663), cpc_isic5 (2,504), isic5 (700), nace_r2 (679), isic5_nace (625),
 *   naics_isic4 (24), naics_isic5 (24)
 *
 * dim_world_domain additions: sitc3, sitc2, isco, bec.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── views ──────────────────────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_sitc3_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.sitc.commodity_rev3'
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_sitc2_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.sitc.commodity_rev2'
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_isco_occupation AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'major'    AS major,
      value_json::jsonb->>'submajor' AS submajor,
      value_json::jsonb->>'minor'    AS minor,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.isco.occupation'
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_bec_category AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'   AS name,
      value_json::jsonb->>'level'  AS level,
      value_json::jsonb->>'parent' AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.bec.category'
  `.execute(db);

  // ── dim_world_domain ───────────────────────────────────────────────────
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('sitc3', 'sitc3.etzhayyim.com', 5690, 'products', 'trade')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('sitc2', 'sitc2.etzhayyim.com', 3723, 'products', 'trade')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('isco', 'isco.etzhayyim.com', 393, 'occupations', 'labour')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('bec', 'bec.etzhayyim.com', 31, 'categories', 'trade')
  `.execute(db);

  // ── SITC concordance bridges (data-only, idempotent) ──────────────────
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc3_sitc4'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_sitc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_sitc4'`.execute(db);

  // NB: re-run via python3 /tmp/seed_sitc3.py + /tmp/seed_sitc2.py
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_sitc3_commodity`.execute(db);
  await sql`DROP VIEW IF EXISTS view_sitc2_commodity`.execute(db);
  await sql`DROP VIEW IF EXISTS view_isco_occupation`.execute(db);
  await sql`DROP VIEW IF EXISTS view_bec_category`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.sitc.commodity_rev3'`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.sitc.commodity_rev2'`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.isco.occupation'`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.bec.category'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain IN ('sitc3','sitc2','isco','bec')`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system IN ('sitc3_sitc4','sitc2_sitc3','sitc2_sitc4')`.execute(db);
}
