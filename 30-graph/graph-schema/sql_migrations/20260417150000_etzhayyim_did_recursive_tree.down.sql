DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_identity_children;

FLUSH;

DROP INDEX IF EXISTS uq_vertex_etzhayyim_identity_parent_kind_value;

DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_parent_kind;

DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_parent;

FLUSH;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN revoked_at;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN material_hash_proof;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN material_kind;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN pubkey_multibase;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN segment_value;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN segment_kind;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN depth;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN parent_did;

FLUSH;
