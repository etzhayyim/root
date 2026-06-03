CREATE INDEX IF NOT EXISTS idx_erc725_linked_method_at_did
      ON vertex_erc725_linked_method (at_did);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_erc725_at_resolution AS
    SELECT at_did, actor_did
    FROM vertex_erc725_linked_method
    WHERE at_did IS NOT NULL
      AND revoked_at IS NULL;

DROP MATERIALIZED VIEW IF EXISTS mv_actor_canonical_did;

CREATE MATERIALIZED VIEW mv_actor_canonical_did AS
    SELECT DISTINCT raw_did, canonical_did
    FROM (
      -- Path A: did:web path normalization for registered etzhayyim actors.
      SELECT
        raw_did,
        normalize_actor_did(raw_did) AS canonical_did
      FROM (
        SELECT actor_did AS raw_did FROM mv_actor_social_stats
        UNION ALL
        SELECT actor_did AS raw_did FROM mv_actor_governance_policy
        UNION ALL
        SELECT actor_did AS raw_did FROM mv_actor_tool_grants
      ) AS s
      UNION ALL
      -- Path B: AT Protocol at_did → ERC725 actor_did resolution.
      --         Handles did:plc and non-etzhayyim did:web federation aliases.
      SELECT at_did AS raw_did, actor_did AS canonical_did
      FROM mv_erc725_at_resolution
    ) AS combined;
