import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Rebuild three MVs to use the SQL UDFs introduced in 20260416140000.
 *
 * Affected MVs:
 *
 *   mv_actor_repo_stats (originally 0016_actor_repo_stats_mv.ts)
 *     Before: 4 CTEs each repeating split_part(v,':',1)||':'||... (12 calls total)
 *     After:  did_web_root(v)   — 4 calls, same semantics
 *
 *   mv_profile_page_stats (originally 20260415173000_profile_page_stats_mv_optimization.ts)
 *     Before: 4 CTEs each with a 6-line CASE/CONCAT/SPLIT_PART block (24 lines total)
 *     After:  normalize_actor_did(v) — 3 calls (social + governance + tools)
 *     NOTE: vertex_page (985M rows) excluded — Option A (2026-04-16).
 *     Page counts are exposed via view_page_count_by_canonical_did (plain VIEW,
 *     created in 20260416160000_mv_canonical_did_intermediate.ts).
 *
 *   mv_domain_coverage_live (originally 0014_domain_coverage_live_mv.ts)
 *     Before: 5 × CASE WHEN total_target > 0 THEN x/y ELSE 0.0 END inline expressions
 *     After:  safe_divide(x, y, 0.0) — 5 calls, same semantics
 *
 * down() restores the pre-UDF inline SQL for each MV so the previous migration
 * state is fully recoverable.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── 1. mv_actor_repo_stats ─────────────────────────────────────────────────
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_repo_stats`.execute(db);

  await sql`
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
    LEFT JOIN repo_rec       rr ON rr.actor_did = r.actor_did
  `.execute(db);

  // ── 2. mv_profile_page_stats ──────────────────────────────────────────────
  await sql`DROP INDEX IF EXISTS idx_mv_profile_page_stats_canonical_actor_did`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_mv_profile_page_stats_actor_did`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_profile_page_stats`.execute(db);

  await sql`
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
    LEFT JOIN tool_counts       t  ON t.canonical_actor_did  = k.canonical_actor_did
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_mv_profile_page_stats_actor_did
    ON mv_profile_page_stats (actor_did)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_mv_profile_page_stats_canonical_actor_did
    ON mv_profile_page_stats (canonical_actor_did)
  `.execute(db);

  // ── 3. mv_domain_coverage_live ────────────────────────────────────────────
  // Only the final coverage MV needs rebuilding; the two upstream MVs
  // (mv_domain_repo_did_count, mv_domain_repo_authority_count) are unchanged.
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_domain_coverage_live`.execute(db);

  await sql`
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
      ON a.authority_kind = t.authority_kind AND a.repo = t.repo
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // ── 3. restore mv_domain_coverage_live (inline CASE expressions) ──────────
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_domain_coverage_live`.execute(db);

  await sql`
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
      CASE WHEN t.total_target > 0
        THEN COALESCE(d.did_count, 0)::double precision / t.total_target::double precision
        ELSE 0.0
      END AS live_coverage_did,
      CASE WHEN t.total_target > 0
        THEN (COALESCE(d.did_count, 0) + COALESCE(a.authority_count, 0))::double precision / t.total_target::double precision
        ELSE 0.0
      END AS live_coverage_record,
      CASE WHEN t.total_target > 0
        THEN t.total_seed::double precision / t.total_target::double precision
        ELSE 0.0
      END AS authority_rate,
      CASE WHEN t.total_target > 0
        THEN (t.total_seed - COALESCE(d.did_count, 0))::double precision / t.total_target::double precision
        ELSE 0.0
      END AS delta_did,
      CASE WHEN t.total_target > 0
        THEN (t.total_seed - (COALESCE(d.did_count, 0) + COALESCE(a.authority_count, 0)))::double precision / t.total_target::double precision
        ELSE 0.0
      END AS delta_record
    FROM dim_domain_coverage_target t
    LEFT JOIN mv_domain_repo_did_count d
      ON d.kind = t.kind AND d.repo = t.repo
    LEFT JOIN mv_domain_repo_authority_count a
      ON a.authority_kind = t.authority_kind AND a.repo = t.repo
  `.execute(db);

  // ── 2. restore mv_profile_page_stats (inline SPLIT_PART CASE blocks) ──────
  await sql`DROP INDEX IF EXISTS idx_mv_profile_page_stats_canonical_actor_did`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_mv_profile_page_stats_actor_did`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_profile_page_stats`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_profile_page_stats AS
    WITH
    social_counts AS (
      SELECT
        CASE
          WHEN actor_did LIKE 'did:web:site.etzhayyim.com:%'
            THEN CONCAT('did:web:', SPLIT_PART(SPLIT_PART(actor_did, 'did:web:site.etzhayyim.com:', 2), ':', 1), '.etzhayyim.com')
          WHEN actor_did LIKE 'did:web:%'
            THEN CONCAT('did:web:', SPLIT_PART(SPLIT_PART(actor_did, ':', 3), '/', 1))
          ELSE actor_did
        END AS canonical_actor_did,
        MAX(follower_count)::bigint  AS follower_count,
        MAX(following_count)::bigint AS following_count,
        MAX(post_count)::bigint      AS post_count
      FROM mv_actor_social_stats
      GROUP BY 1
    ),
    governance_counts AS (
      SELECT
        CASE
          WHEN actor_did LIKE 'did:web:site.etzhayyim.com:%'
            THEN CONCAT('did:web:', SPLIT_PART(SPLIT_PART(actor_did, 'did:web:site.etzhayyim.com:', 2), ':', 1), '.etzhayyim.com')
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
            THEN CONCAT('did:web:', SPLIT_PART(SPLIT_PART(actor_did, 'did:web:site.etzhayyim.com:', 2), ':', 1), '.etzhayyim.com')
          WHEN actor_did LIKE 'did:web:%'
            THEN CONCAT('did:web:', SPLIT_PART(SPLIT_PART(actor_did, ':', 3), '/', 1))
          ELSE actor_did
        END AS canonical_actor_did,
        COUNT(DISTINCT tool_name)::bigint AS tool_count
      FROM mv_actor_tool_grants
      GROUP BY 1
    ),
    -- vertex_page excluded (Option A, 2026-04-16): view_page_count_by_canonical_did serves page counts.
    canonical_keys AS (
      SELECT canonical_actor_did FROM social_counts
      UNION
      SELECT canonical_actor_did FROM governance_counts
      UNION
      SELECT canonical_actor_did FROM tool_counts
    )
    SELECT
      k.canonical_actor_did                AS actor_did,
      k.canonical_actor_did                AS canonical_actor_did,
      COALESCE(sc.follower_count,  0)      AS follower_count,
      COALESCE(sc.following_count, 0)      AS following_count,
      COALESCE(sc.post_count,      0)      AS post_count,
      COALESCE(g.governance_count, 0)      AS governance_count,
      COALESCE(t.tool_count,       0)      AS tool_count
    FROM canonical_keys k
    LEFT JOIN social_counts     sc ON sc.canonical_actor_did = k.canonical_actor_did
    LEFT JOIN governance_counts g  ON g.canonical_actor_did  = k.canonical_actor_did
    LEFT JOIN tool_counts       t  ON t.canonical_actor_did  = k.canonical_actor_did
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_mv_profile_page_stats_actor_did
    ON mv_profile_page_stats (actor_did)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_mv_profile_page_stats_canonical_actor_did
    ON mv_profile_page_stats (canonical_actor_did)
  `.execute(db);

  // ── 1. restore mv_actor_repo_stats (inline split_part concat) ─────────────
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_repo_stats`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_repo_stats AS
    WITH roots AS (
      SELECT DISTINCT
        split_part(val, ':', 1) || ':' || split_part(val, ':', 2) || ':' || split_part(val, ':', 3) AS actor_did
      FROM (
        SELECT did AS val FROM vertex_did WHERE did LIKE 'did:web:%'
        UNION
        SELECT repo AS val FROM vertex_did WHERE repo LIKE 'did:web:%'
        UNION
        SELECT repo AS val FROM vertex_repo_record WHERE repo LIKE 'did:web:%'
        UNION
        SELECT repo AS val FROM edge_follows WHERE repo LIKE 'did:web:%'
        UNION
        SELECT dst_vid AS val FROM edge_follows WHERE dst_vid LIKE 'did:web:%'
      ) s
    ),
    follower_desc AS (
      SELECT
        split_part(dst_vid, ':', 1) || ':' || split_part(dst_vid, ':', 2) || ':' || split_part(dst_vid, ':', 3) AS actor_did,
        COUNT(*)::bigint AS descendant_follower_count
      FROM edge_follows
      WHERE dst_vid LIKE 'did:web:%:%'
      GROUP BY 1
    ),
    following_desc AS (
      SELECT
        split_part(repo, ':', 1) || ':' || split_part(repo, ':', 2) || ':' || split_part(repo, ':', 3) AS actor_did,
        COUNT(*)::bigint AS descendant_following_count
      FROM edge_follows
      WHERE repo LIKE 'did:web:%:%'
      GROUP BY 1
    ),
    subdid_desc AS (
      SELECT
        split_part(did, ':', 1) || ':' || split_part(did, ':', 2) || ':' || split_part(did, ':', 3) AS actor_did,
        COUNT(*)::bigint AS descendant_subdid_count
      FROM vertex_did
      WHERE did LIKE 'did:web:%:%'
      GROUP BY 1
    ),
    repo_rec AS (
      SELECT
        split_part(repo, ':', 1) || ':' || split_part(repo, ':', 2) || ':' || split_part(repo, ':', 3) AS actor_did,
        COUNT(*)::bigint AS repo_record_count
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
    LEFT JOIN repo_rec       rr ON rr.actor_did = r.actor_did
  `.execute(db);
}
