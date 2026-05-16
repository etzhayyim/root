DROP VIEW IF EXISTS view_page_count_by_canonical_did;

CREATE VIEW view_page_count_by_canonical_did AS
    SELECT
      normalize_actor_did(owner_did) AS canonical_actor_did,
      CAST(COUNT(*) AS BIGINT) AS page_count
    FROM vertex_page
    WHERE owner_did IS NOT NULL AND owner_did <> ''
    GROUP BY 1;

DROP MATERIALIZED VIEW IF EXISTS mv_actor_canonical_did;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_canonical_did AS
    SELECT DISTINCT
      raw_did,
      normalize_actor_did(raw_did) AS canonical_did
    FROM (
      SELECT actor_did AS raw_did FROM mv_actor_social_stats
      UNION ALL
      SELECT actor_did AS raw_did FROM mv_actor_governance_policy
      UNION ALL
      SELECT actor_did AS raw_did FROM mv_actor_tool_grants
    ) s;

DROP MATERIALIZED VIEW IF EXISTS mv_did_web_root_index;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_did_web_root_index AS
    SELECT DISTINCT
      did  AS sub_did,
      did_web_root(did) AS root_did
    FROM vertex_did
    WHERE did LIKE 'did:web:%';
