import { Kysely, sql } from 'kysely';

/**
 * Actor social stats.
 *
 * Exact actor DID keyed aggregate used by profile / feed surfaces:
 *   - follower_count (incoming follows)
 *   - following_count (outgoing follows)
 *   - post_count (posts authored by repo)
 *
 * Pairwise relationship checks such as "viewer follows actor" stay as direct
 * queries; they are not actor-level aggregates.
 */
export async function up(db: Kysely<any>): Promise<void> {
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
      COALESCE(fi.follower_count, 0) AS follower_count,
      COALESCE(fo.following_count, 0) AS following_count,
      COALESCE(p.post_count, 0) AS post_count
    FROM actor_keys k
    LEFT JOIN follower_counts fi ON fi.actor_did = k.actor_did
    LEFT JOIN following_counts fo ON fo.actor_did = k.actor_did
    LEFT JOIN post_counts p ON p.actor_did = k.actor_did`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_social_stats`.execute(db);
}
