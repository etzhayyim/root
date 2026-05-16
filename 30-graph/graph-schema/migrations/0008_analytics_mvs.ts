import { Kysely, sql } from 'kysely';

/**
 * Analytics Materialized Views (RisingWave native).
 *
 * 3 MVs for graph analytics:
 *   - mv_follow_2hop: 2-hop follow neighbors (friend-of-friend recommendation)
 *   - mv_weighted_in_degree: influence score (follows weighted by 1/out_degree)
 *   - mv_post_engagement: per-post engagement rate (like + repost counts)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // MV19: 2-hop follow neighbors — "friends of friends" for recommendation
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_follow_2hop AS
    SELECT DISTINCT f1.src_vid AS actor,
           f2.dst_vid AS suggestion,
           COUNT(*) AS mutual_count
    FROM edge_follows f1
    JOIN edge_follows f2 ON f1.dst_vid = f2.src_vid
    WHERE f1.src_vid != f2.dst_vid
    GROUP BY f1.src_vid, f2.dst_vid`.execute(db);

  // MV20: Weighted in-degree — influence score (low out-degree followers are more valuable)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_weighted_in_degree AS
    SELECT f.dst_vid,
           COUNT(*) AS in_degree,
           SUM(1.0 / GREATEST(d.out_degree, 1)) AS weighted_score
    FROM edge_follows f
    JOIN mv_follow_out_degree d ON d.src_vid = f.src_vid
    GROUP BY f.dst_vid`.execute(db);

  // MV21: Post engagement — like + repost count per post
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_post_engagement AS
    SELECT p.vertex_id AS post_id,
           p.repo AS author,
           p.rkey,
           COALESCE(l.like_count, 0) AS like_count,
           COALESCE(r.repost_count, 0) AS repost_count,
           COALESCE(l.like_count, 0) + COALESCE(r.repost_count, 0) AS total_engagement
    FROM vertex_post p
    LEFT JOIN mv_post_like_count l ON l.dst_vid = p.vertex_id
    LEFT JOIN (
      SELECT dst_vid, COUNT(*) AS repost_count
      FROM edge_reposts
      GROUP BY dst_vid
    ) r ON r.dst_vid = p.vertex_id`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_post_engagement`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_weighted_in_degree`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_follow_2hop`.execute(db);
}
