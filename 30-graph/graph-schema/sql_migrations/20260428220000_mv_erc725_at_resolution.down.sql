DROP MATERIALIZED VIEW IF EXISTS mv_actor_canonical_did;

CREATE MATERIALIZED VIEW mv_actor_canonical_did AS
    SELECT DISTINCT raw_did, normalize_actor_did(raw_did) AS canonical_did
    FROM (
      SELECT actor_did AS raw_did FROM mv_actor_social_stats
      UNION ALL
      SELECT actor_did AS raw_did FROM mv_actor_governance_policy
      UNION ALL
      SELECT actor_did AS raw_did FROM mv_actor_tool_grants
    ) AS s;

DROP MATERIALIZED VIEW IF EXISTS mv_erc725_at_resolution;

DROP INDEX IF EXISTS idx_erc725_linked_method_at_did;
