CREATE MATERIALIZED VIEW IF NOT EXISTS mv_profile_identity_topology AS
    SELECT
      p.vertex_id AS profile_vertex_id,
      p.did,
      p.repo,
      p.handle,
      a.vertex_id AS actor_vertex_id,
      d.vertex_id AS did_vertex_id
    FROM vertex_profile p
    LEFT JOIN vertex_actor a
      ON a.did = p.did
    LEFT JOIN vertex_did d
      ON d.did = p.did;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_profile_identity_summary AS
    SELECT
      COUNT(*)::bigint AS total_profiles,
      SUM(CASE WHEN actor_vertex_id IS NOT NULL THEN 1 ELSE 0 END)::bigint AS linked_actor_profiles,
      SUM(CASE WHEN did_vertex_id IS NOT NULL THEN 1 ELSE 0 END)::bigint AS linked_did_profiles,
      SUM(CASE WHEN actor_vertex_id IS NOT NULL AND did_vertex_id IS NOT NULL THEN 1 ELSE 0 END)::bigint AS fully_linked_profiles
    FROM mv_profile_identity_topology;
