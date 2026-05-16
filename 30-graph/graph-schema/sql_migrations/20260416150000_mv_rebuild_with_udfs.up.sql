DROP MATERIALIZED VIEW IF EXISTS mv_actor_repo_stats;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_repo_stats AS
    WITH roots AS (
      SELECT DISTINCT did_web_root(val) AS actor_did
      FROM (
        SELECT did  AS val FROM vertex_did          WHERE did     LIKE 'did:web:%'
        UNION
        SELECT repo AS val FROM vertex_did          WHERE repo    LIKE 'did:web:%'
        UNION
        SELECT repo AS val FROM vertex_repo_record  WHERE repo    LIKE 'did:web:%'
        UNION
        SELECT repo AS val FROM edge_follows        WHERE repo    LIKE 'did:web:%'
        UNION
        SELECT dst_vid AS val FROM edge_follows     WHERE dst_vid LIKE 'did:web:%'
      ) s
    ),
    follower_desc AS (
      SELECT
        did_web_root(dst_vid)      AS actor_did,
        COUNT(*)::bigint           AS descendant_follower_count
      FROM edge_follows
      WHERE dst_vid LIKE 'did:web:%:%'
      GROUP BY 1
    ),
    following_desc AS (
      SELECT
        did_web_root(repo)         AS actor_did,
        COUNT(*)::bigint           AS descendant_following_count
      FROM edge_follows
      WHERE repo LIKE 'did:web:%:%'
      GROUP BY 1
    ),
    subdid_desc AS (
      SELECT
        did_web_root(did)          AS actor_did,
        COUNT(*)::bigint           AS descendant_subdid_count
      FROM vertex_did
      WHERE did LIKE 'did:web:%:%'
      GROUP BY 1
    ),
    repo_rec AS (
      SELECT
        did_web_root(repo)         AS actor_did,
        COUNT(*)::bigint           AS repo_record_count
      FROM vertex_repo_record
      WHERE repo LIKE 'did:web:%'
      GROUP BY 1
    )
    SELECT
      r.actor_did,
      COALESCE(fd.descendant_follower_count,  0) AS descendant_follower_count,
      COALESCE(fo.descendant_following_count, 0) AS descendant_following_count,
      COALESCE(sd.descendant_subdid_count,    0) AS descendant_subdid_count,
      COALESCE(rr.repo_record_count,          0) AS repo_record_count
    FROM roots r
    LEFT JOIN follower_desc  fd ON fd.actor_did = r.actor_did
    LEFT JOIN following_desc fo ON fo.actor_did = r.actor_did
    LEFT JOIN subdid_desc    sd ON sd.actor_did = r.actor_did
    LEFT JOIN repo_rec       rr ON rr.actor_did = r.actor_did;

DROP INDEX IF EXISTS idx_mv_profile_page_stats_canonical_actor_did;

DROP INDEX IF EXISTS idx_mv_profile_page_stats_actor_did;

DROP MATERIALIZED VIEW IF EXISTS mv_profile_page_stats;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_profile_page_stats AS
    WITH
    social_counts AS (
      SELECT
        normalize_actor_did(actor_did)  AS canonical_actor_did,
        MAX(follower_count)::bigint     AS follower_count,
        MAX(following_count)::bigint    AS following_count,
        MAX(post_count)::bigint         AS post_count
      FROM mv_actor_social_stats
      GROUP BY 1
    ),
    governance_counts AS (
      SELECT
        normalize_actor_did(actor_did)      AS canonical_actor_did,
        COUNT(DISTINCT policy_vid)::bigint  AS governance_count
      FROM mv_actor_governance_policy
      GROUP BY 1
    ),
    tool_counts AS (
      SELECT
        normalize_actor_did(actor_did)      AS canonical_actor_did,
        COUNT(DISTINCT tool_name)::bigint   AS tool_count
      FROM mv_actor_tool_grants
      GROUP BY 1
    ),
    -- vertex_page (985M rows) is intentionally excluded (Option A, 2026-04-16).
    -- Page counts are served by view_page_count_by_canonical_did (plain VIEW).
    canonical_keys AS (
      SELECT canonical_actor_did FROM social_counts
      UNION
      SELECT canonical_actor_did FROM governance_counts
      UNION
      SELECT canonical_actor_did FROM tool_counts
    )
    SELECT
      k.canonical_actor_did                 AS actor_did,
      k.canonical_actor_did                 AS canonical_actor_did,
      COALESCE(sc.follower_count,   0)      AS follower_count,
      COALESCE(sc.following_count,  0)      AS following_count,
      COALESCE(sc.post_count,       0)      AS post_count,
      COALESCE(g.governance_count,  0)      AS governance_count,
      COALESCE(t.tool_count,        0)      AS tool_count
    FROM canonical_keys k
    LEFT JOIN social_counts     sc ON sc.canonical_actor_did = k.canonical_actor_did
    LEFT JOIN governance_counts g  ON g.canonical_actor_did  = k.canonical_actor_did
    LEFT JOIN tool_counts       t  ON t.canonical_actor_did  = k.canonical_actor_did;

CREATE INDEX IF NOT EXISTS idx_mv_profile_page_stats_actor_did
    ON mv_profile_page_stats (actor_did);

CREATE INDEX IF NOT EXISTS idx_mv_profile_page_stats_canonical_actor_did
    ON mv_profile_page_stats (canonical_actor_did);

DROP MATERIALIZED VIEW IF EXISTS mv_domain_coverage_live;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_domain_coverage_live AS
    SELECT
      t.kind,
      t.repo,
      t.app,
      t.authority_kind,
      t.authority_seed,
      t.rule_seed,
      t.scope_seed,
      t.total_seed,
      t.authority_target,
      t.rule_target,
      t.scope_target,
      t.total_target,
      COALESCE(d.did_count, 0)                                    AS did_count,
      COALESCE(a.authority_count, 0)                              AS authority_count,
      COALESCE(d.did_count, 0) + COALESCE(a.authority_count, 0)  AS live_record_count,
      safe_divide(
        COALESCE(d.did_count, 0)::double precision,
        t.total_target::double precision,
        0.0
      )                                                           AS live_coverage_did,
      safe_divide(
        (COALESCE(d.did_count, 0) + COALESCE(a.authority_count, 0))::double precision,
        t.total_target::double precision,
        0.0
      )                                                           AS live_coverage_record,
      safe_divide(
        t.total_seed::double precision,
        t.total_target::double precision,
        0.0
      )                                                           AS authority_rate,
      safe_divide(
        (t.total_seed - COALESCE(d.did_count, 0))::double precision,
        t.total_target::double precision,
        0.0
      )                                                           AS delta_did,
      safe_divide(
        (t.total_seed - (COALESCE(d.did_count, 0) + COALESCE(a.authority_count, 0)))::double precision,
        t.total_target::double precision,
        0.0
      )                                                           AS delta_record
    FROM dim_domain_coverage_target t
    LEFT JOIN mv_domain_repo_did_count d
      ON d.kind = t.kind AND d.repo = t.repo
    LEFT JOIN mv_domain_repo_authority_count a
      ON a.authority_kind = t.authority_kind AND a.repo = t.repo;
