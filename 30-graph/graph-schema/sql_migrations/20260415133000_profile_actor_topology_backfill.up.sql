INSERT INTO vertex_actor (
      vertex_id,
      did,
      repo,
      handle,
      display_name,
      created_at,
      collection,
      classification,
      status
    )
    SELECT
      p.did AS vertex_id,
      p.did,
      p.repo,
      p.handle,
      p.display_name,
      p.created_at,
      p.collection,
      'profile_shadow',
      'active'
    FROM vertex_profile p
    LEFT JOIN vertex_actor a
      ON a.did = p.did
    WHERE p.did IS NOT NULL
      AND p.did <> ''
      AND a.vertex_id IS NULL;

DROP MATERIALIZED VIEW IF EXISTS mv_profile_identity_edges;

CREATE MATERIALIZED VIEW mv_profile_identity_edges AS
    SELECT
      CONCAT('profile-to-did:', p.vertex_id, ':', d.vertex_id) AS edge_id,
      p.vertex_id AS src_vid,
      d.vertex_id AS dst_vid,
      'profile_to_did'::varchar AS edge_kind
    FROM vertex_profile p
    JOIN vertex_did d ON d.did = p.did
    UNION ALL
    SELECT
      CONCAT('profile-to-actor:', p.vertex_id, ':', a.vertex_id) AS edge_id,
      p.vertex_id AS src_vid,
      a.vertex_id AS dst_vid,
      'profile_to_actor'::varchar AS edge_kind
    FROM vertex_profile p
    JOIN vertex_actor a ON a.did = p.did;
