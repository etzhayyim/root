import { Kysely, sql } from 'kysely';

/**
 * Migration 0010: drop legacy `vertex_post` and `vertex_profile`.
 *
 * These predate the AT Protocol-faithful repo store. They are fully
 * subsumed by `vertex_repo_record` (migration 0009), filtered by
 * collection:
 *   vertex_post    → vertex_repo_record WHERE collection = 'app.bsky.feed.post'
 *   vertex_profile → vertex_repo_record WHERE collection = 'app.bsky.actor.profile'
 *
 * Both tables are empty stubs at the time of this migration (the previous
 * `13-drop-legacy-post-profile.sql` drop was reverted by the archived
 * `ensureGraphSchema` cron, which is now gone — so this time the drop
 * actually sticks).
 *
 * CASCADE is required because two downstream materialized views
 * reference `vertex_post`:
 *   - mv_feed_timeline
 *   - mv_user_likes_with_post
 * These MVs are themselves legacy and have been superseded by
 * `mv_post_like_count_v` / `mv_post_repost_count` / `mv_post_reply_count`
 * (sql/14-engagement-mv.sql, shipped alongside P8).
 */
export async function up(db: Kysely<any>): Promise<void> {
  await db.executeQuery(sql`DROP TABLE IF EXISTS "vertex_post" CASCADE`.compile(db));
  await db.executeQuery(sql`DROP TABLE IF EXISTS "vertex_profile" CASCADE`.compile(db));
}

export async function down(_db: Kysely<any>): Promise<void> {
  // No-op. `vertex_post` / `vertex_profile` were legacy tables whose
  // schemas lived in archived DDL. Rolling back 0010 would require
  // re-creating them from that archive, which we have no reason to do
  // — everything is served from `vertex_repo_record` now.
}
