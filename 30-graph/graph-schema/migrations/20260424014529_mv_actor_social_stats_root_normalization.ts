/**
 * ADR-2604241038 Phase α — Rebuild `mv_actor_social_stats` to aggregate
 * path-DID records (e.g. `did:web:x.etzhayyim.com:sub-actor`) under the
 * 3-segment root DID (`did:web:x.etzhayyim.com`).
 *
 * Why
 * ---
 * Raw `GROUP BY repo` left path-DIDs unaggregated. A profile page asking
 * for `actor=did:web:x.etzhayyim.com` would hit a row whose key is the root DID
 * and miss posts written by sub-actor DIDs, yielding `postsCount = 0`
 * even when the feed handler's `repo LIKE 'did:web:x.etzhayyim.com:%'` correctly
 * finds the posts.
 *
 * Observed 2026-04-24 on `did:web:sh1n5h1x.etzhayyim.com` — 5 posts on the root
 * DID via getAuthorFeed, `postsCount: 0` via getProfile.
 *
 * The fix
 * -------
 * Replace `GROUP BY repo` with `GROUP BY normalize_actor_did(repo)` in the
 * `post_counts` CTE. Follower/following counts already live on edge
 * tables whose src/dst columns are canonical DIDs, so the key space over
 * them is unchanged and the UNION of actor_keys keeps the same shape.
 *
 * Downstream `mv_profile_page_stats` (rebuilt 20260416150000 with UDFs)
 * reads this MV, so once this rebuild lands, path-DID posts
 * automatically start appearing in the canonical `postsCount`.
 *
 * Rollback
 * --------
 * `down()` restores the original `GROUP BY repo` shape.
 */

import { sql, type Kysely } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // Drop in reverse dep order. Live catalog dependency graph:
  //   mv_actor_social_stats
  //     ├─ mv_actor_canonical_did   (20260416160000)
  //     └─ mv_profile_core_stats    (20260415200000)
  //          └─ (mv_profile_page_stats absent from live DB)
  // mv_page_count_by_owner_canonical_did reads vertex_page, not
  // mv_actor_social_stats, so it doesn't participate. RisingWave has no
  // DROP CASCADE for MVs, so we have to drop by hand.
  await sql`DROP INDEX IF EXISTS idx_mv_profile_core_stats_canonical_actor_did`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_mv_profile_core_stats_actor_did`.execute(db);
  await sql`DROP VIEW IF EXISTS view_profile_page_stats`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_profile_core_stats`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_canonical_did`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_social_stats`.execute(db);

  // ── mv_actor_social_stats (path-DID-aware) ──────────────────────────────
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_social_stats AS
    WITH actor_keys AS (
      SELECT dst_vid AS actor_did FROM edge_follows
      UNION
      SELECT src_vid AS actor_did FROM edge_follows
      UNION
      SELECT normalize_actor_did(repo) AS actor_did
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
      SELECT
        normalize_actor_did(repo) AS actor_did,
        COUNT(*)::bigint           AS post_count
      FROM vertex_repo_record
      WHERE collection = 'app.bsky.feed.post'
      GROUP BY 1
    )
    SELECT
      k.actor_did,
      COALESCE(fi.follower_count, 0)  AS follower_count,
      COALESCE(fo.following_count, 0) AS following_count,
      COALESCE(p.post_count, 0)       AS post_count
    FROM actor_keys k
    LEFT JOIN follower_counts  fi ON fi.actor_did = k.actor_did
    LEFT JOIN following_counts fo ON fo.actor_did = k.actor_did
    LEFT JOIN post_counts       p ON p.actor_did = k.actor_did`.execute(db);

  // ── mv_actor_canonical_did (verbatim from 20260416160000) ───────────────
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_canonical_did AS
    SELECT DISTINCT
      raw_did,
      normalize_actor_did(raw_did) AS canonical_did
    FROM (
      SELECT actor_did AS raw_did FROM mv_actor_social_stats
      UNION ALL
      SELECT actor_did AS raw_did FROM mv_actor_governance_policy
      UNION ALL
      SELECT actor_did AS raw_did FROM mv_actor_tool_grants
    ) s`.execute(db);

  // ── mv_profile_core_stats (verbatim from 20260415200000) ────────────────
  // The CASE-based normalization here is redundant with
  // normalize_actor_did() upstream, but faithful restore of the canonical
  // shape keeps this migration reversible and avoids touching an
  // unrelated migration's DDL.
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_profile_core_stats AS
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
    LEFT JOIN tool_counts t ON t.canonical_actor_did = k.canonical_actor_did`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_mv_profile_core_stats_actor_did
    ON mv_profile_core_stats (actor_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_mv_profile_core_stats_canonical_actor_did
    ON mv_profile_core_stats (canonical_actor_did)`.execute(db);

  // view_profile_page_stats is not rebuilt here — its other dependency
  // (mv_page_count_by_owner_canonical_did from migration 20260415200000)
  // is absent from the live DB, so the view itself never materialized on
  // this cluster. If that MV lands later, rebuild view_profile_page_stats
  // as a separate migration.
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_mv_profile_core_stats_canonical_actor_did`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_mv_profile_core_stats_actor_did`.execute(db);
  await sql`DROP VIEW IF EXISTS view_profile_page_stats`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_profile_core_stats`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_canonical_did`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_social_stats`.execute(db);

  // Restore pre-ADR-2604241038 shape (raw repo GROUP BY).
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_social_stats AS
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
    LEFT JOIN post_counts       p ON p.actor_did = k.actor_did`.execute(db);

  // Re-create the 2 downstream MVs dropped in up() so the reverse leaves
  // the pre-migration DB state.
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_canonical_did AS
    SELECT DISTINCT
      raw_did,
      normalize_actor_did(raw_did) AS canonical_did
    FROM (
      SELECT actor_did AS raw_did FROM mv_actor_social_stats
      UNION ALL
      SELECT actor_did AS raw_did FROM mv_actor_governance_policy
      UNION ALL
      SELECT actor_did AS raw_did FROM mv_actor_tool_grants
    ) s`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_profile_core_stats AS
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
    LEFT JOIN tool_counts t ON t.canonical_actor_did = k.canonical_actor_did`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_mv_profile_core_stats_actor_did
    ON mv_profile_core_stats (actor_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_mv_profile_core_stats_canonical_actor_did
    ON mv_profile_core_stats (canonical_actor_did)`.execute(db);
}
