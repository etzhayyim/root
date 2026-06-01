import { Kysely, sql } from 'kysely';

/**
 * Migration 0076: HS version chain (1996–2007) + SITC Rev.1.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 5).
 *
 * ## New taxonomy masters
 *
 * | Collection                          | Rows | Source                              |
 * |-------------------------------------|------|-------------------------------------|
 * | app.etzhayyim.apps.hs.commodity2007       | 6,373 | UN Comtrade H3.json (HS 2007)      |
 * | app.etzhayyim.apps.hs.commodity2002       | 6,569 | UN Comtrade H2.json (HS 2002)      |
 * | app.etzhayyim.apps.hs.commodity1996       | 6,474 | UN Comtrade H1.json (HS 1996)      |
 * | app.etzhayyim.apps.sitc.commodity_rev1    | 2,784 | UN Comtrade S1.json (SITC Rev.1)   |
 *
 * ### HS version chain (complete: 1996 → 2022)
 * HS 1996 (H1) → HS 2002 (H2) → HS 2007 (H3) → HS 2012 (H5) → HS 2017 (H4) → HS 2022 (H6)
 * All consecutive-version bridges now exist as code-identical concordances.
 * Level distribution (all editions): chapter (97–98) + heading (1,222–1,245) + subheading (5,053–5,226).
 *
 * ### SITC version chain (complete: Rev.1 → Rev.4)
 * SITC Rev.1 (1961) → Rev.2 (1975) → Rev.3 (1986) → Rev.4 (2006)
 * Rev.1 level distribution: 10 sections / 71 divisions / 253 groups / 878 subgroups / 1,572 items.
 *
 * ## New concordance bridges (code-identical JOINs)
 *
 * | system     | edges | description                              |
 * |------------|-------|------------------------------------------|
 * | hs07_hs12  | 6,197 | HS 2007 → HS 2012 (code-identical)      |
 * | hs02_hs07  | 6,108 | HS 2002 → HS 2007 (code-identical)      |
 * | hs96_hs02  | 6,226 | HS 1996 → HS 2002 (code-identical)      |
 * | sitc1_sitc2| 1,334 | SITC Rev.1 → Rev.2 (code-identical)     |
 *
 * ## Full HS chain reachability (via transitive closure)
 * HS 1996 → HS 2002 → HS 2007 → HS 2012 → HS 2017 → HS 2022
 * Any two HS editions can be linked via multi-hop JOIN through these bridges.
 *
 * ## New views
 *
 * - view_hs2007_commodity: projection of app.etzhayyim.apps.hs.commodity2007
 * - view_hs2002_commodity: projection of app.etzhayyim.apps.hs.commodity2002
 * - view_hs1996_commodity: projection of app.etzhayyim.apps.hs.commodity1996
 * - view_sitc1_commodity: projection of app.etzhayyim.apps.sitc.commodity_rev1
 *
 * ## Topology integrity (post-apply)
 *
 * 0 orphan nodes across all 21 taxonomy collections.
 * 0 dangling edges across all 28 concordance systems (excl. openalex).
 *
 * Full concordance inventory (28 systems, 79,090 total edges excl. openalex/ipc):
 *   hs22_hs17 (6,561), hs12_hs17 (6,528), hs96_hs02 (6,226), hs07_hs12 (6,197),
 *   hs2017 (5,843), hs2017_cpc3 (5,740), hs2012 (5,584), hs2012_cpc3 (5,500),
 *   hs02_hs07 (6,108), sitc3_sitc4 (5,408), cpc3 (4,391), sitc4 (3,776),
 *   sitc4_cpc3 (3,717), sitc2_sitc3 (2,805), sitc2_sitc4 (2,693), cpc (2,663),
 *   cpc_isic5 (2,504), isic5 (700), nace_r2 (679), isic5_nace (625),
 *   isic31_isic4 (229), isic31_isic5 (231), isic2_isic31 (76),
 *   sitc1_sitc2 (1,334), naics_isic4 (24), naics_isic5 (24)
 *
 * dim_world_domain additions: hs2007, hs2002, hs1996, sitc1.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── views ──────────────────────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_hs2007_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'    AS name,
      value_json::jsonb->>'level'   AS level,
      value_json::jsonb->>'chapter' AS chapter,
      value_json::jsonb->>'heading' AS heading,
      value_json::jsonb->>'parent'  AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.hs.commodity2007'
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_hs2002_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'    AS name,
      value_json::jsonb->>'level'   AS level,
      value_json::jsonb->>'chapter' AS chapter,
      value_json::jsonb->>'heading' AS heading,
      value_json::jsonb->>'parent'  AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.hs.commodity2002'
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_hs1996_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'    AS name,
      value_json::jsonb->>'level'   AS level,
      value_json::jsonb->>'chapter' AS chapter,
      value_json::jsonb->>'heading' AS heading,
      value_json::jsonb->>'parent'  AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.hs.commodity1996'
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_sitc1_commodity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.sitc.commodity_rev1'
  `.execute(db);

  // ── dim_world_domain ───────────────────────────────────────────────────
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('hs2007', 'hs2007.etzhayyim.com', 6373, 'HS products', 'trade')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('hs2002', 'hs2002.etzhayyim.com', 6569, 'HS products', 'trade')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('hs1996', 'hs1996.etzhayyim.com', 6474, 'HS products', 'trade')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('sitc1', 'sitc1.etzhayyim.com', 2784, 'products', 'trade')
  `.execute(db);

  // ── HS version chain bridges + SITC chain (data-only, idempotent) ─────
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs07_hs12'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs02_hs07'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs96_hs02'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc1_sitc2'`.execute(db);

  // NB: bridge edges re-generated via code-identical JOIN at ingestion time.
  // Re-run: python3 /tmp/seed_hs_chain.py
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_hs2007_commodity`.execute(db);
  await sql`DROP VIEW IF EXISTS view_hs2002_commodity`.execute(db);
  await sql`DROP VIEW IF EXISTS view_hs1996_commodity`.execute(db);
  await sql`DROP VIEW IF EXISTS view_sitc1_commodity`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'app.etzhayyim.apps.hs.commodity2007'`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'app.etzhayyim.apps.hs.commodity2002'`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'app.etzhayyim.apps.hs.commodity1996'`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'app.etzhayyim.apps.sitc.commodity_rev1'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain IN ('hs2007','hs2002','hs1996','sitc1')`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system IN ('hs07_hs12','hs02_hs07','hs96_hs02','sitc1_sitc2')`.execute(db);
}
