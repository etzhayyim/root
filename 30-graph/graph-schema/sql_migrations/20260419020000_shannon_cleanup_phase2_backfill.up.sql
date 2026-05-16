SET enable_locality_backfill = true;

INSERT INTO vertex_actor_profile (
      vertex_id, did, handle, display_name,
      avatar_cid, banner_cid, execution_tier, performer_type,
      nanoid, category, country, status,
      created_at, _seq, created_date, sensitivity_ord, owner_did
    )
    SELECT
      a.vertex_id, a.did, a.handle, a.display_name,
      a.avatar_cid, a.banner_cid, a.execution_tier, a.performer_type,
      a.nanoid, a.category, a.country, a.status,
      a.created_at, a._seq, a.created_date, a.sensitivity_ord, a.owner_did
    FROM vertex_actor a
    WHERE a.vertex_id IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM vertex_actor_profile p
        WHERE p.vertex_id = a.vertex_id
      );

FLUSH;

SET enable_locality_backfill = false;
