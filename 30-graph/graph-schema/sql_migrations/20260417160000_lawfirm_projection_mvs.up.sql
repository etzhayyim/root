CREATE VIEW view_lawfirm_matter_roster AS
    SELECT
      m.did                   AS matter_did,
      m.parent_did            AS firm_did,
      m.controller_did,
      m.handle                AS matter_handle,
      m.status                AS identity_status,
      m.material_hash_proof,
      m.created_at,
      m.updated_at,
      m.revoked_at,
      firm.handle             AS firm_handle,
      firm.display_name       AS firm_display_name,
      firm.actor_score        AS firm_actor_score,
      COALESCE(docs.child_count,         0) AS total_doc_count,
      COALESCE(docs.active_child_count,  0) AS active_doc_count,
      COALESCE(grants.child_count,       0) AS total_grant_count,
      COALESCE(grants.active_child_count,0) AS active_grant_count
    FROM vertex_etzhayyim_identity m
    LEFT JOIN vertex_etzhayyim_identity firm
      ON firm.did = m.parent_did
    LEFT JOIN mv_etzhayyim_identity_children docs
      ON docs.parent_did = m.did AND docs.material_kind = 'doc'
    LEFT JOIN mv_etzhayyim_identity_children grants
      ON grants.parent_did = m.did AND grants.material_kind = 'grant'
    WHERE m.material_kind = 'matter'
      AND m.parent_did IS NOT NULL
      AND m.depth = 2;

CREATE VIEW view_lawfirm_external_counsel_access AS
    SELECT
      g.did                      AS grant_did,
      g.parent_did               AS matter_did,
      g.controller_did           AS inviter_did,
      g.material_hash_proof,
      g.status,
      g.created_at,
      g.updated_at,
      g.revoked_at,
      m.revoked_at               AS parent_revoked_at
    FROM vertex_etzhayyim_identity g
    LEFT JOIN vertex_etzhayyim_identity m
      ON m.did = g.parent_did
    WHERE g.material_kind = 'grant'
      AND g.parent_did IS NOT NULL
      AND g.depth = 3;
