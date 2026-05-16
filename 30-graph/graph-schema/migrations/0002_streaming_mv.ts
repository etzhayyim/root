import { Kysely, sql } from 'kysely';

/**
 * Streaming Materialized Views (RisingWave native).
 *
 * 18 MVs:
 *   - CSC replacement (MV1-4): incoming edge traversal
 *   - Aggregation (MV5-8): count/degree pre-computation
 *   - Lookup (MV9-10): index replacements for autocomplete/lookup
 *   - JOIN pre-computation (MV11-14): enriched joins
 *   - Common Crawl (MV15-18): site coverage aggregation
 *
 * Note: CREATE MATERIALIZED VIEW is RisingWave-native DDL.
 * Executed via sql`...`.execute(db) which passes through the PG wire protocol.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // MV1: Followers (CSC of edge_follows) — "who follows user X?"
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_followers AS
    SELECT dst_vid, src_vid, edge_id, rkey, repo, created_at, _seq
    FROM edge_follows`.execute(db);

  // MV2: Liked-by (CSC of edge_likes) — "who liked post X?"
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_liked_by AS
    SELECT dst_vid, src_vid, edge_id, rkey, repo, subject_uri, _seq
    FROM edge_likes`.execute(db);

  // MV3: Reposted-by (CSC of edge_reposts) — "who reposted post X?"
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_reposted_by AS
    SELECT dst_vid, src_vid, edge_id, rkey, repo, subject_uri, _seq
    FROM edge_reposts`.execute(db);

  // MV4: Replied-by (CSC of edge_reply) — "what replies does post X have?"
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_replied_by AS
    SELECT dst_vid, src_vid, edge_id, _seq
    FROM edge_reply`.execute(db);

  // MV5: Actor count per status
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_count_by_status AS
    SELECT status, COUNT(*) AS cnt
    FROM vertex_actor GROUP BY status`.execute(db);

  // MV6: Follow out-degree (CSR)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_follow_out_degree AS
    SELECT src_vid, COUNT(*) AS out_degree
    FROM edge_follows GROUP BY src_vid`.execute(db);

  // MV7: Follow in-degree
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_follow_in_degree AS
    SELECT dst_vid, COUNT(*) AS in_degree
    FROM edge_follows GROUP BY dst_vid`.execute(db);

  // MV8: Post like count
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_post_like_count AS
    SELECT dst_vid, COUNT(*) AS like_count
    FROM edge_likes GROUP BY dst_vid`.execute(db);

  // MV9: Actor suggestions (lightweight columns for autocomplete)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_suggestions AS
    SELECT vertex_id, did, handle, display_name, status
    FROM vertex_actor WHERE status = 'active'`.execute(db);

  // MV10: Actor by DID (reverse lookup)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_by_did AS
    SELECT did, vertex_id, handle, display_name, avatar_cid, status
    FROM vertex_actor`.execute(db);

  // MV11: Follow with actor details (enriched follow edges)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_follow_with_actor AS
    SELECT f.src_vid, f.dst_vid, a.did, a.handle, a.display_name
    FROM edge_follows f
    JOIN vertex_actor a ON a.vertex_id = f.dst_vid`.execute(db);

  // MV12: Feed timeline (follows × posts — streaming pre-computation)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_feed_timeline AS
    SELECT f.src_vid AS viewer,
           p.vertex_id AS post_id,
           p.repo AS author,
           p.rkey,
           p._seq
    FROM edge_follows f
    JOIN vertex_post p ON p.repo = f.dst_vid`.execute(db);

  // MV13: Mutual follows (bidirectional — CSR ∩ CSC)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mutual_follows AS
    SELECT a.src_vid AS actor_a, a.dst_vid AS actor_b
    FROM edge_follows a
    JOIN edge_follows b ON a.src_vid = b.dst_vid AND a.dst_vid = b.src_vid`.execute(db);

  // MV14: User likes with post details (enriched likes)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_user_likes_with_post AS
    SELECT l.src_vid AS liker, l.dst_vid AS post_vid,
           p.repo AS author, p.rkey
    FROM edge_likes l
    JOIN vertex_post p ON p.vertex_id = l.dst_vid`.execute(db);

  // MV15: Domain page count (real-time aggregation from edge_hosts_page)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cc_domain_page_count AS
    SELECT src_vid AS domain_did, COUNT(*) AS page_count
    FROM edge_hosts_page
    GROUP BY src_vid`.execute(db);

  // MV16: Domain outgoing link degree
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cc_domain_out_degree AS
    SELECT src_vid AS domain_did, COUNT(*) AS out_degree, SUM(count) AS total_links
    FROM edge_links_to_domain
    GROUP BY src_vid`.execute(db);

  // MV17: Domain incoming link degree
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cc_domain_in_degree AS
    SELECT dst_vid AS domain_did, COUNT(*) AS in_degree, SUM(count) AS total_links
    FROM edge_links_to_domain
    GROUP BY dst_vid`.execute(db);

  // MV18: CC domain coverage (domain + actor join via DID)
  // 2026-04-13: removed d.slug and d.page_count — neither column exists on
  // vertex_domain per migration 0001. page_count is in mv_cc_domain_page_count;
  // slug is derived from `domain` by callers when needed.
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cc_domain_coverage AS
    SELECT d.vertex_id AS domain_did,
           d.domain,
           d.topics,
           d.performer_type,
           d.status,
           a.vertex_id AS actor_vertex_id,
           a.handle,
           a.display_name
    FROM vertex_domain d
    LEFT JOIN vertex_actor a ON a.did = d.did`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  // Drop in reverse order (sinks depending on MVs must be dropped first via 0003 down)
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cc_domain_coverage`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cc_domain_in_degree`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cc_domain_out_degree`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cc_domain_page_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_user_likes_with_post`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_mutual_follows`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_feed_timeline`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_follow_with_actor`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_by_did`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_suggestions`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_post_like_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_follow_in_degree`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_follow_out_degree`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_count_by_status`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_replied_by`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_reposted_by`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_liked_by`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_followers`.execute(db);
}
