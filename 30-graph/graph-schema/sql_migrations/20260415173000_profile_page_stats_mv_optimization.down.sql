DROP INDEX IF EXISTS idx_mv_profile_page_stats_canonical_actor_did;

DROP INDEX IF EXISTS idx_mv_profile_page_stats_actor_did;

DROP MATERIALIZED VIEW IF EXISTS mv_profile_page_stats;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_profile_page_stats AS
    WITH
    social_counts AS (
      SELECT
        CASE
          WHEN actor_did LIKE 'did:web:site.etzhayyim.com:%'
            THEN CONCAT(
              'did:web:',
              SPLIT_PART(SPLIT_PART(actor_did, 'did:web:site.etzhayyim.com:', 2), ':', 1),
              '.etzhayyim.com'
            )
          WHEN actor_did LIKE 'did:web:%'
            THEN CONCAT('did:web:', SPLIT_PART(SPLIT_PART(actor_did, ':', 3), '/', 1))
          ELSE actor_did
        END AS canonical_actor_did,
        MAX(follower_count)::bigint AS follower_count,
        MAX(following_count)::bigint AS following_count,
        MAX(post_count)::bigint AS post_count
      FROM mv_actor_social_stats
      GROUP BY 1
    ),
    page_counts AS (
      SELECT
        CASE
          WHEN owner_did LIKE 'did:web:site.etzhayyim.com:%'
            THEN CONCAT(
              'did:web:',
              SPLIT_PART(SPLIT_PART(owner_did, 'did:web:site.etzhayyim.com:', 2), ':', 1),
              '.etzhayyim.com'
            )
          WHEN owner_did LIKE 'did:web:%'
            THEN CONCAT('did:web:', SPLIT_PART(SPLIT_PART(owner_did, ':', 3), '/', 1))
          ELSE owner_did
        END AS canonical_actor_did,
        COUNT(*)::bigint AS page_count
      FROM vertex_page
      WHERE owner_did IS NOT NULL AND owner_did <> ''
      GROUP BY 1
    ),
    governance_counts AS (
      SELECT
        CASE
          WHEN actor_did LIKE 'did:web:site.etzhayyim.com:%'
            THEN CONCAT(
              'did:web:',
              SPLIT_PART(SPLIT_PART(actor_did, 'did:web:site.etzhayyim.com:', 2), ':', 1),
              '.etzhayyim.com'
            )
          WHEN actor_did LIKE 'did:web:%'
            THEN CONCAT('did:web:', SPLIT_PART(SPLIT_PART(actor_did, ':', 3), '/', 1))
          ELSE actor_did
        END AS canonical_actor_did,
        COUNT(DISTINCT policy_vid)::bigint AS governance_count
      FROM mv_actor_governance_policy
      GROUP BY 1
    ),
    tool_counts AS (
      SELECT
        CASE
          WHEN actor_did LIKE 'did:web:site.etzhayyim.com:%'
            THEN CONCAT(
              'did:web:',
              SPLIT_PART(SPLIT_PART(actor_did, 'did:web:site.etzhayyim.com:', 2), ':', 1),
              '.etzhayyim.com'
            )
          WHEN actor_did LIKE 'did:web:%'
            THEN CONCAT('did:web:', SPLIT_PART(SPLIT_PART(actor_did, ':', 3), '/', 1))
          ELSE actor_did
        END AS canonical_actor_did,
        COUNT(DISTINCT tool_name)::bigint AS tool_count
      FROM mv_actor_tool_grants
      GROUP BY 1
    ),
    canonical_keys AS (
      SELECT canonical_actor_did FROM social_counts
      UNION
      SELECT canonical_actor_did FROM page_counts
      UNION
      SELECT canonical_actor_did FROM governance_counts
      UNION
      SELECT canonical_actor_did FROM tool_counts
    )
    SELECT
      k.canonical_actor_did AS actor_did,
      k.canonical_actor_did AS canonical_actor_did,
      COALESCE(sc.follower_count, 0) AS follower_count,
      COALESCE(sc.following_count, 0) AS following_count,
      COALESCE(sc.post_count, 0) AS post_count,
      COALESCE(pg.page_count, 0) AS page_count,
      COALESCE(g.governance_count, 0) AS governance_count,
      COALESCE(t.tool_count, 0) AS tool_count
    FROM canonical_keys k
    LEFT JOIN social_counts sc ON sc.canonical_actor_did = k.canonical_actor_did
    LEFT JOIN page_counts pg ON pg.canonical_actor_did = k.canonical_actor_did
    LEFT JOIN governance_counts g ON g.canonical_actor_did = k.canonical_actor_did
    LEFT JOIN tool_counts t ON t.canonical_actor_did = k.canonical_actor_did;
