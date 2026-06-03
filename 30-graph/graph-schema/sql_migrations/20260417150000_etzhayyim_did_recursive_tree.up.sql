ALTER TABLE vertex_etzhayyim_identity ADD COLUMN parent_did VARCHAR;

FLUSH;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN depth BIGINT;

FLUSH;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN segment_kind VARCHAR;

FLUSH;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN segment_value VARCHAR;

FLUSH;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN pubkey_multibase VARCHAR;

FLUSH;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN material_kind VARCHAR;

FLUSH;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN material_hash_proof VARCHAR;

FLUSH;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN revoked_at VARCHAR;

FLUSH;

UPDATE vertex_etzhayyim_identity
    SET depth = 1,
        segment_kind = 'root',
        segment_value = SUBSTRING(did FROM 10)
    WHERE depth IS NULL
      AND parent_did IS NULL
      AND did LIKE 'did:etzhayyim:%';

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_parent
    ON vertex_etzhayyim_identity(parent_did);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_parent_kind
    ON vertex_etzhayyim_identity(parent_did, segment_kind);

FLUSH;

CREATE UNIQUE INDEX IF NOT EXISTS uq_vertex_etzhayyim_identity_parent_kind_value
    ON vertex_etzhayyim_identity(parent_did, segment_kind, segment_value);

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_identity_children AS
    SELECT
      parent_did,
      segment_kind,
      COUNT(*) AS child_count,
      COUNT(*) FILTER (WHERE revoked_at IS NULL) AS active_child_count
    FROM vertex_etzhayyim_identity
    WHERE parent_did IS NOT NULL
    GROUP BY parent_did, segment_kind;

FLUSH;
