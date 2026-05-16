DROP INDEX IF EXISTS idx_mv_cpc_patent_coverage_cpc;

DROP INDEX IF EXISTS idx_mv_cpc_patent_prefix_match_patent;

DROP INDEX IF EXISTS idx_mv_cpc_patent_prefix_match_cpc;

DROP MATERIALIZED VIEW IF EXISTS mv_cpc_patent_coverage;

DROP MATERIALIZED VIEW IF EXISTS mv_cpc_patent_prefix_match;

DROP VIEW IF EXISTS view_cpc_product_live;

DROP INDEX IF EXISTS idx_vertex_cpc_product_code;

DROP TABLE IF EXISTS vertex_cpc_product;

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
    WHERE collection = 'ai.gftd.apps.cpc.product';

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
     AND p.patent_class_code LIKE c.class_prefix || '%';

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
    GROUP BY cpc_code;

CREATE INDEX IF NOT EXISTS idx_mv_cpc_patent_prefix_match_cpc
    ON mv_cpc_patent_prefix_match (cpc_code);

CREATE INDEX IF NOT EXISTS idx_mv_cpc_patent_prefix_match_patent
    ON mv_cpc_patent_prefix_match (patent_vertex_id);

CREATE INDEX IF NOT EXISTS idx_mv_cpc_patent_coverage_cpc
    ON mv_cpc_patent_coverage (cpc_code);
