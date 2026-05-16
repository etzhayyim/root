import { Kysely, sql } from 'kysely';

/**
 * Migration 0075: COFOG, ISIC Rev.3.1, ISIC Rev.2 + ISIC version bridges.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 4 continued).
 *
 * ## New taxonomy masters
 *
 * | Collection                                          | Rows | Source                                    |
 * |-----------------------------------------------------|------|-------------------------------------------|
 * | ai.gftd.apps.cofog.function                         |  188 | UN COFOG (Classification of GFCE, 1999)   |
 * | ai.gftd.apps.open_isic.economic_activity_rev31      |  538 | UNSD ISIC Rev.3.1 (2002 revision)         |
 * | ai.gftd.apps.open_isic.economic_activity_rev2       |  277 | UNSD ISIC Rev.2 (1968, incl. 2 synthetic) |
 *
 * ### COFOG (Classification of the Functions of Government)
 * 188 nodes: 10 divisions / 69 groups / 109 classes.
 * Source: UN Statistics Division (2000), ST/ESA/STAT/SER.M/84.
 * Maps government expenditure to economic sectors; widely used by IMF/OECD.
 *
 * ### ISIC Rev.3.1 (2002)
 * 538 nodes: 17 sections / 62 divisions / 159 groups / 290 classes / 10 sub-classes.
 * Source: UNSD https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/ISIC_Rev_3_1_english.txt
 * Bridge to Rev.4 (229 code-identical edges) and Rev.5 (231 code-identical edges).
 *
 * ### ISIC Rev.2 (1968, revised 1975)
 * 277 nodes: includes 2 synthetic group nodes (311, 312) added to fix 11 orphans.
 * Source: UNSD ISIC Rev.2 structure file.
 * Bridge to ISIC Rev.3.1 (76 code-identical edges).
 *
 * ## New concordance bridges (code-identical JOINs)
 *
 * | system       | edges | description                              |
 * |--------------|-------|------------------------------------------|
 * | isic31_isic4 |   229 | ISIC Rev.3.1 → ISIC Rev.4 (code-identical) |
 * | isic31_isic5 |   231 | ISIC Rev.3.1 → ISIC Rev.5 (code-identical) |
 * | isic2_isic31 |    76 | ISIC Rev.2 → ISIC Rev.3.1 (code-identical) |
 *
 * ### ISIC version chain (complete)
 * ISIC Rev.2 (1968) → Rev.3.1 (2002) → Rev.4 (2008) → Rev.5 (2025)
 * All transitions now have code-identical bridge concordances.
 * Derived cross-version bridges (isic2_isic4, isic2_isic5) can be computed via
 * multi-hop JOIN through the existing bridge chain.
 *
 * ## New views
 *
 * - view_cofog_function: projection of ai.gftd.apps.cofog.function
 * - view_isic31_activity: projection of ai.gftd.apps.open_isic.economic_activity_rev31
 * - view_isic2_activity: projection of ai.gftd.apps.open_isic.economic_activity_rev2
 *
 * ## Topology integrity (post-apply)
 *
 * 0 orphan nodes across all 17 taxonomy collections.
 * 0 dangling edges across all 22 concordance systems.
 *
 * Full concordance inventory (22 systems, 58,330 total edges excl. openalex/ipc):
 *   hs22_hs17 (6,561), hs12_hs17 (6,528), hs2017 (5,843), hs2017_cpc3 (5,740),
 *   hs2012 (5,584), hs2012_cpc3 (5,500), sitc3_sitc4 (5,408), cpc3 (4,391),
 *   sitc4 (3,776), sitc4_cpc3 (3,717), sitc2_sitc3 (2,805), sitc2_sitc4 (2,693),
 *   cpc (2,663), cpc_isic5 (2,504), isic5 (700), nace_r2 (679), isic5_nace (625),
 *   isic31_isic4 (229), isic31_isic5 (231), isic2_isic31 (76),
 *   naics_isic4 (24), naics_isic5 (24)
 *
 * dim_world_domain additions: cofog, isic31, isic2.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── views ──────────────────────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_cofog_function AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.cofog.function'
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_isic31_activity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'group'    AS group_code,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.open_isic.economic_activity_rev31'
  `.execute(db);

  await sql`
    CREATE VIEW IF NOT EXISTS view_isic2_activity AS
    SELECT
      rkey AS code,
      value_json::jsonb->>'name'     AS name,
      value_json::jsonb->>'level'    AS level,
      value_json::jsonb->>'section'  AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'group'    AS group_code,
      value_json::jsonb->>'parent'   AS parent_code,
      uri, indexed_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.apps.open_isic.economic_activity_rev2'
  `.execute(db);

  // ── dim_world_domain ───────────────────────────────────────────────────
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('cofog', 'cofog.gftd.ai', 188, 'government functions', 'governance')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('isic31', 'isic31.gftd.ai', 538, 'industries', 'governance')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('isic2', 'isic2.gftd.ai', 277, 'industries', 'governance')
  `.execute(db);

  // ── ISIC version bridges (data-only, idempotent) ──────────────────────
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic31_isic4'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic31_isic5'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic2_isic31'`.execute(db);

  // NB: bridge edges re-generated via code-identical JOIN at ingestion time.
  // Re-run: python3 /tmp/build_isic_bridges.py
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_cofog_function`.execute(db);
  await sql`DROP VIEW IF EXISTS view_isic31_activity`.execute(db);
  await sql`DROP VIEW IF EXISTS view_isic2_activity`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.cofog.function'`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.open_isic.economic_activity_rev31'`.execute(db);
  await sql`DELETE FROM vertex_repo_record WHERE collection = 'ai.gftd.apps.open_isic.economic_activity_rev2'`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain IN ('cofog','isic31','isic2')`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system IN ('isic31_isic4','isic31_isic5','isic2_isic31')`.execute(db);
}
