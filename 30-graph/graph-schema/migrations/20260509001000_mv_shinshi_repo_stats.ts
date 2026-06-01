import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Streaming MV `mv_shinshi_repo_stats` — combined per-repo stats for
 * the shinshi sub-DID namespace. Covers BOTH the modelProfile-presence
 * check AND the per-repo post count in a single MV.
 *
 * Replaces the still-slow Q1 (DISTINCT modelProfile repos) in
 * `lg_shinshi/graphs/coverage.py`. Even after `mv_shinshi_post_counts`
 * (migration 20260509000000), Q1 was still hitting `vertex_repo_record`
 * directly at 5s under RW load. This MV pre-aggregates BOTH signals
 * (is_model + post_count) per repo so the coverage graph becomes a
 * single MV scan in <300ms.
 *
 * Cardinality: ~1649 distinct shinshi sub-DIDs (well under 500k limit).
 * Source filter: collection IN (modelProfile, feed.post) AND repo LIKE
 * shinshi prefix → ~11K source rows. Tiny aggregation state.
 *
 * NOTE: keeps `mv_shinshi_post_counts` (20260509000000) for any other
 * caller that depends on the simpler shape — both MVs can coexist
 * cheaply, RW shares state where it can.
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shinshi_repo_stats AS
    SELECT
      repo,
      COUNT(*) FILTER (WHERE collection = 'app.etzhayyim.apps.shinshi.modelProfile') AS model_profile_count,
      COUNT(*) FILTER (WHERE collection = 'app.bsky.feed.post') AS post_count
    FROM vertex_repo_record
    WHERE repo LIKE 'did:web:sh1n5h1x.etzhayyim.com:%'
      AND repo != 'did:web:sh1n5h1x.etzhayyim.com'
      AND collection IN ('app.etzhayyim.apps.shinshi.modelProfile', 'app.bsky.feed.post')
    GROUP BY repo
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shinshi_repo_stats`.execute(db);
}
