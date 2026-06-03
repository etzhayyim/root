DROP VIEW IF EXISTS view_actor_unified;

FLUSH;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN profile_json;

FLUSH;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN capabilities;

FLUSH;

DROP INDEX IF EXISTS idx_vertex_actor_profile_handle;

DROP INDEX IF EXISTS idx_vertex_actor_profile_did;

DROP TABLE IF EXISTS vertex_actor_profile;

FLUSH;
