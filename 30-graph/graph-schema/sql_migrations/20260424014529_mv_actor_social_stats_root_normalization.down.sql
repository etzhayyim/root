DROP INDEX IF EXISTS idx_mv_profile_core_stats_canonical_actor_did;

DROP INDEX IF EXISTS idx_mv_profile_core_stats_actor_did;

DROP VIEW IF EXISTS view_profile_page_stats;

DROP MATERIALIZED VIEW IF EXISTS mv_profile_core_stats;

DROP MATERIALIZED VIEW IF EXISTS mv_actor_canonical_did;

DROP MATERIALIZED VIEW IF EXISTS mv_actor_social_stats;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_social_stats AS
    WITH actor_keys AS (
      SELECT dst_vid AS actor_did FROM edge_follows
      UNION
      SELECT src_vid AS actor_did FROM edge_follows
      UNION
      SELECT repo AS actor_did
      FROM vertex_repo_record
      WHERE collection = 'app.bsky.feed.post'
    ),
    follower_counts AS (
      SELECT dst_vid AS actor_did, COUNT(*)::bigint AS follower_count
      FROM edge_follows
      GROUP BY dst_vid
    ),
    following_counts AS (
      SELECT src_vid AS actor_did, COUNT(*)::bigint AS following_count
      FROM edge_follows
      GROUP BY src_vid
    ),
    post_counts AS (
      SELECT repo AS actor_did, COUNT(*)::bigint AS post_count
      FROM vertex_repo_record
      WHERE collection = 'app.bsky.feed.post'
      GROUP BY repo
    )
    SELECT
      k.actor_did,
      COALESCE(fi.follower_count, 0)  AS follower_count,
      COALESCE(fo.following_count, 0) AS following_count,
      COALESCE(p.post_count, 0)       AS post_count
    FROM actor_keys k
    LEFT JOIN follower_counts  fi ON fi.actor_did = k.actor_did
    LEFT JOIN following_counts fo ON fo.actor_did = k.actor_did
    LEFT JOIN post_counts       p ON p.actor_did = k.actor_did;

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

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_profile_core_stats AS
    WITH
    social_counts AS (
      SELECT
        CASE
          WHEN actor_did LIKE 'did:web:site.gftd.ai:%'
            THEN CONCAT(
              'did:web:',
              SPLIT_PART(SPLIT_PART(actor_did, 'did:web:site.gftd.ai:', 2), ':', 1),
              '.gftd.ai'
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
    governance_counts AS (
      SELECT
        CASE
          WHEN actor_did LIKE 'did:web:site.gftd.ai:%'
            THEN CONCAT(
              'did:web:',
              SPLIT_PART(SPLIT_PART(actor_did, 'did:web:site.gftd.ai:', 2), ':', 1),
              '.gftd.ai'
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
          WHEN actor_did LIKE 'did:web:site.gftd.ai:%'
            THEN CONCAT(
              'did:web:',
              SPLIT_PART(SPLIT_PART(actor_did, 'did:web:site.gftd.ai:', 2), ':', 1),
              '.gftd.ai'
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
      COALESCE(g.governance_count, 0) AS governance_count,
      COALESCE(t.tool_count, 0) AS tool_count
    FROM canonical_keys k
    LEFT JOIN social_counts sc ON sc.canonical_actor_did = k.canonical_actor_did
    LEFT JOIN governance_counts g ON g.canonical_actor_did = k.canonical_actor_did
    LEFT JOIN tool_counts t ON t.canonical_actor_did = k.canonical_actor_did;

CREATE INDEX IF NOT EXISTS idx_mv_profile_core_stats_actor_did
    ON mv_profile_core_stats (actor_did);

CREATE INDEX IF NOT EXISTS idx_mv_profile_core_stats_canonical_actor_did
    ON mv_profile_core_stats (canonical_actor_did);
