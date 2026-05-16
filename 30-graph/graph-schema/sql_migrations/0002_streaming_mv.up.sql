CREATE MATERIALIZED VIEW IF NOT EXISTS mv_followers AS
    SELECT dst_vid, src_vid, edge_id, rkey, repo, created_at, _seq
    FROM edge_follows;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_liked_by AS
    SELECT dst_vid, src_vid, edge_id, rkey, repo, subject_uri, _seq
    FROM edge_likes;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_reposted_by AS
    SELECT dst_vid, src_vid, edge_id, rkey, repo, subject_uri, _seq
    FROM edge_reposts;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_replied_by AS
    SELECT dst_vid, src_vid, edge_id, _seq
    FROM edge_reply;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_count_by_status AS
    SELECT status, COUNT(*) AS cnt
    FROM vertex_actor GROUP BY status;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_follow_out_degree AS
    SELECT src_vid, COUNT(*) AS out_degree
    FROM edge_follows GROUP BY src_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_follow_in_degree AS
    SELECT dst_vid, COUNT(*) AS in_degree
    FROM edge_follows GROUP BY dst_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_post_like_count AS
    SELECT dst_vid, COUNT(*) AS like_count
    FROM edge_likes GROUP BY dst_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_suggestions AS
    SELECT vertex_id, did, handle, display_name, status
    FROM vertex_actor WHERE status = 'active';

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_by_did AS
    SELECT did, vertex_id, handle, display_name, avatar_cid, status
    FROM vertex_actor;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_follow_with_actor AS
    SELECT f.src_vid, f.dst_vid, a.did, a.handle, a.display_name
    FROM edge_follows f
    JOIN vertex_actor a ON a.vertex_id = f.dst_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_feed_timeline AS
    SELECT f.src_vid AS viewer,
           p.vertex_id AS post_id,
           p.repo AS author,
           p.rkey,
           p._seq
    FROM edge_follows f
    JOIN vertex_post p ON p.repo = f.dst_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mutual_follows AS
    SELECT a.src_vid AS actor_a, a.dst_vid AS actor_b
    FROM edge_follows a
    JOIN edge_follows b ON a.src_vid = b.dst_vid AND a.dst_vid = b.src_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_user_likes_with_post AS
    SELECT l.src_vid AS liker, l.dst_vid AS post_vid,
           p.repo AS author, p.rkey
    FROM edge_likes l
    JOIN vertex_post p ON p.vertex_id = l.dst_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cc_domain_page_count AS
    SELECT src_vid AS domain_did, COUNT(*) AS page_count
    FROM edge_hosts_page
    GROUP BY src_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cc_domain_out_degree AS
    SELECT src_vid AS domain_did, COUNT(*) AS out_degree, SUM(count) AS total_links
    FROM edge_links_to_domain
    GROUP BY src_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cc_domain_in_degree AS
    SELECT dst_vid AS domain_did, COUNT(*) AS in_degree, SUM(count) AS total_links
    FROM edge_links_to_domain
    GROUP BY dst_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cc_domain_coverage AS
    SELECT d.vertex_id AS domain_did,
           d.domain,
           d.topics,
           d.performer_type,
           d.status,
           a.vertex_id AS actor_vertex_id,
           a.handle,
           a.display_name
    FROM vertex_domain d
    LEFT JOIN vertex_actor a ON a.did = d.did;
