import { Kysely, sql } from 'kysely';

/**
 * ADR-0036: vertex_cpc_product typed table.
 *
 * Replaces the vertex_repo_record-backed view_cpc_product_live with a
 * Hyperdrive-direct table so the CPC app can write via createKyselyDb
 * instead of com.atproto.repo.createRecord.
 *
 * Steps:
 * 1. Drop downstream MVs + old view (dependency order)
 * 2. Create vertex_cpc_product typed table
 * 3. Recreate view_cpc_product_live reading from the new table
 * 4. Recreate mv_cpc_patent_prefix_match + mv_cpc_patent_coverage
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // Drop downstream dependents first
  await sql`DROP INDEX IF EXISTS idx_mv_cpc_patent_coverage_cpc`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_mv_cpc_patent_prefix_match_patent`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_mv_cpc_patent_prefix_match_cpc`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cpc_patent_coverage`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cpc_patent_prefix_match`.execute(db);
  await sql`DROP VIEW IF EXISTS view_cpc_product_live`.execute(db);

  // Typed table for CPC product catalog (ADR-0036 Tier 2 domain write)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cpc_product (
      vertex_id       VARCHAR NOT NULL PRIMARY KEY,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      owner_did       VARCHAR,
      actor_did       VARCHAR NOT NULL DEFAULT 'anon',
      org_did         VARCHAR NOT NULL DEFAULT 'anon',
      at_did          VARCHAR,
      created_at      VARCHAR NOT NULL,
      cpc_code        VARCHAR,
      name            VARCHAR,
      level           VARCHAR,
      section         VARCHAR,
      division        VARCHAR,
      group_code      VARCHAR,
      class_code      VARCHAR,
      subclass_code   VARCHAR,
      patent_ipc_prefixes VARCHAR,
      patent_cpc_prefixes VARCHAR,
      patent_hint_csv VARCHAR,
      tsukuru_process VARCHAR,
      actor_id        VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_cpc_product_code
    ON vertex_cpc_product (cpc_code)
  `.execute(db);

  // Recreate the live view pointing at the typed table
  await sql`
    CREATE VIEW IF NOT EXISTS view_cpc_product_live AS
    SELECT
      COALESCE(cpc_code, '') AS code,
      name,
      level,
      section,
      division,
      group_code,
      class_code,
      subclass_code,
      COALESCE(patent_ipc_prefixes, '[]') AS patent_ipc_prefixes,
      COALESCE(patent_cpc_prefixes, '[]') AS patent_cpc_prefixes,
      patent_hint_csv,
      tsukuru_process,
      vertex_id AS uri,
      created_at AS indexed_at
    FROM vertex_cpc_product
  `.execute(db);

  // Recreate downstream MVs
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cpc_patent_prefix_match AS
    WITH cpc_prefixes AS (
      SELECT
        code AS cpc_code,
        name AS cpc_name,
        subclass_code,
        tsukuru_process,
        patent_hint_csv,
        'ipc' AS code_system,
        jsonb_array_elements_text(patent_ipc_prefixes::jsonb) AS class_prefix
      FROM view_cpc_product_live
      WHERE level = 'subclass'
        AND patent_ipc_prefixes <> '[]'
      UNION ALL
      SELECT
        code AS cpc_code,
        name AS cpc_name,
        subclass_code,
        tsukuru_process,
        patent_hint_csv,
        'cpc' AS code_system,
        jsonb_array_elements_text(patent_cpc_prefixes::jsonb) AS class_prefix
      FROM view_cpc_product_live
      WHERE level = 'subclass'
        AND patent_cpc_prefixes <> '[]'
    ),
    patent_codes AS (
      SELECT
        vertex_id AS patent_vertex_id,
        jurisdiction,
        app_number,
        pub_number,
        grant_number,
        title,
        filed_at,
        published_at,
        granted_at,
        'ipc' AS code_system,
        jsonb_array_elements_text(ipc_codes::jsonb) AS patent_class_code
      FROM vertex_patent
      WHERE ipc_codes IS NOT NULL
        AND ipc_codes <> ''
      UNION ALL
      SELECT
        vertex_id AS patent_vertex_id,
        jurisdiction,
        app_number,
        pub_number,
        grant_number,
        title,
        filed_at,
        published_at,
        granted_at,
        'cpc' AS code_system,
        jsonb_array_elements_text(cpc_codes::jsonb) AS patent_class_code
      FROM vertex_patent
      WHERE cpc_codes IS NOT NULL
        AND cpc_codes <> ''
    )
    SELECT DISTINCT
      c.cpc_code,
      c.cpc_name,
      c.subclass_code,
      c.tsukuru_process,
      c.patent_hint_csv,
      c.code_system,
      c.class_prefix,
      p.patent_vertex_id,
      p.jurisdiction,
      p.app_number,
      p.pub_number,
      p.grant_number,
      p.title,
      p.patent_class_code,
      p.filed_at,
      p.published_at,
      p.granted_at
    FROM cpc_prefixes c
    JOIN patent_codes p
      ON p.code_system = c.code_system
     AND p.patent_class_code LIKE c.class_prefix || '%'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cpc_patent_coverage AS
    SELECT
      cpc_code,
      MAX(cpc_name) AS cpc_name,
      MAX(subclass_code) AS subclass_code,
      MAX(tsukuru_process) AS tsukuru_process,
      MAX(patent_hint_csv) AS patent_hint_csv,
      COUNT(*) AS matched_prefix_hits,
      COUNT(DISTINCT patent_vertex_id) AS matched_patent_count,
      MAX(published_at) AS latest_published_at
    FROM mv_cpc_patent_prefix_match
    GROUP BY cpc_code
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_mv_cpc_patent_prefix_match_cpc
    ON mv_cpc_patent_prefix_match (cpc_code)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_mv_cpc_patent_prefix_match_patent
    ON mv_cpc_patent_prefix_match (patent_vertex_id)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_mv_cpc_patent_coverage_cpc
    ON mv_cpc_patent_coverage (cpc_code)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_mv_cpc_patent_coverage_cpc`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_mv_cpc_patent_prefix_match_patent`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_mv_cpc_patent_prefix_match_cpc`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cpc_patent_coverage`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cpc_patent_prefix_match`.execute(db);
  await sql`DROP VIEW IF EXISTS view_cpc_product_live`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_cpc_product_code`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cpc_product`.execute(db);

  // Restore original view reading from vertex_repo_record
  await sql`
    CREATE VIEW IF NOT EXISTS view_cpc_product_live AS
    SELECT
      COALESCE(NULLIF(value_json::jsonb->>'cpcCode', ''), rkey) AS code,
      value_json::jsonb->>'name' AS name,
      value_json::jsonb->>'level' AS level,
      value_json::jsonb->>'section' AS section,
      value_json::jsonb->>'division' AS division,
      value_json::jsonb->>'group' AS group_code,
      value_json::jsonb->>'classCode' AS class_code,
      value_json::jsonb->>'subclass' AS subclass_code,
      COALESCE(
        CASE
          WHEN jsonb_typeof(value_json::jsonb->'patentIpcPrefixes') = 'array'
            THEN (value_json::jsonb->'patentIpcPrefixes')::VARCHAR
          ELSE NULL
        END,
        '[]'
      ) AS patent_ipc_prefixes,
      COALESCE(
        CASE
          WHEN jsonb_typeof(value_json::jsonb->'patentCpcPrefixes') = 'array'
            THEN (value_json::jsonb->'patentCpcPrefixes')::VARCHAR
          ELSE NULL
        END,
        '[]'
      ) AS patent_cpc_prefixes,
      value_json::jsonb->>'patentHintCsv' AS patent_hint_csv,
      value_json::jsonb->>'tsukuruProcess' AS tsukuru_process,
      uri,
      indexed_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.apps.cpc.product'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cpc_patent_prefix_match AS
    WITH cpc_prefixes AS (
      SELECT
        code AS cpc_code,
        name AS cpc_name,
        subclass_code,
        tsukuru_process,
        patent_hint_csv,
        'ipc' AS code_system,
        jsonb_array_elements_text(patent_ipc_prefixes::jsonb) AS class_prefix
      FROM view_cpc_product_live
      WHERE level = 'subclass'
        AND patent_ipc_prefixes <> '[]'
      UNION ALL
      SELECT
        code AS cpc_code,
        name AS cpc_name,
        subclass_code,
        tsukuru_process,
        patent_hint_csv,
        'cpc' AS code_system,
        jsonb_array_elements_text(patent_cpc_prefixes::jsonb) AS class_prefix
      FROM view_cpc_product_live
      WHERE level = 'subclass'
        AND patent_cpc_prefixes <> '[]'
    ),
    patent_codes AS (
      SELECT
        vertex_id AS patent_vertex_id,
        jurisdiction,
        app_number,
        pub_number,
        grant_number,
        title,
        filed_at,
        published_at,
        granted_at,
        'ipc' AS code_system,
        jsonb_array_elements_text(ipc_codes::jsonb) AS patent_class_code
      FROM vertex_patent
      WHERE ipc_codes IS NOT NULL
        AND ipc_codes <> ''
      UNION ALL
      SELECT
        vertex_id AS patent_vertex_id,
        jurisdiction,
        app_number,
        pub_number,
        grant_number,
        title,
        filed_at,
        published_at,
        granted_at,
        'cpc' AS code_system,
        jsonb_array_elements_text(cpc_codes::jsonb) AS patent_class_code
      FROM vertex_patent
      WHERE cpc_codes IS NOT NULL
        AND cpc_codes <> ''
    )
    SELECT DISTINCT
      c.cpc_code,
      c.cpc_name,
      c.subclass_code,
      c.tsukuru_process,
      c.patent_hint_csv,
      c.code_system,
      c.class_prefix,
      p.patent_vertex_id,
      p.jurisdiction,
      p.app_number,
      p.pub_number,
      p.grant_number,
      p.title,
      p.patent_class_code,
      p.filed_at,
      p.published_at,
      p.granted_at
    FROM cpc_prefixes c
    JOIN patent_codes p
      ON p.code_system = c.code_system
     AND p.patent_class_code LIKE c.class_prefix || '%'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cpc_patent_coverage AS
    SELECT
      cpc_code,
      MAX(cpc_name) AS cpc_name,
      MAX(subclass_code) AS subclass_code,
      MAX(tsukuru_process) AS tsukuru_process,
      MAX(patent_hint_csv) AS patent_hint_csv,
      COUNT(*) AS matched_prefix_hits,
      COUNT(DISTINCT patent_vertex_id) AS matched_patent_count,
      MAX(published_at) AS latest_published_at
    FROM mv_cpc_patent_prefix_match
    GROUP BY cpc_code
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_mv_cpc_patent_prefix_match_cpc
    ON mv_cpc_patent_prefix_match (cpc_code)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_mv_cpc_patent_prefix_match_patent
    ON mv_cpc_patent_prefix_match (patent_vertex_id)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_mv_cpc_patent_coverage_cpc
    ON mv_cpc_patent_coverage (cpc_code)
  `.execute(db);
}
