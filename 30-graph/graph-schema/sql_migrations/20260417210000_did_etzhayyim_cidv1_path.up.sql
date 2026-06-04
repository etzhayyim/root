ALTER TABLE vertex_etzhayyim_identity ADD COLUMN cid_version       BIGINT;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN multicodec        VARCHAR;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN multihash_code    VARCHAR;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN multibase_prefix  VARCHAR;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN genesis_op_cid    VARCHAR;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN root_did          VARCHAR;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN path_segment      VARCHAR;

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_root
    ON vertex_etzhayyim_identity(root_did);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_genesis_cid
    ON vertex_etzhayyim_identity(genesis_op_cid);

FLUSH;

CREATE TABLE IF NOT EXISTS edge_etzhayyim_path_child (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,    -- parent did:etzhayyim
    dst_vid         VARCHAR,    -- child  did:etzhayyim
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    segment         VARCHAR,
    created_at      VARCHAR
  );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_path_child_dst
    ON edge_etzhayyim_path_child(dst_vid);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_path_child_src
    ON edge_etzhayyim_path_child(src_vid);

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_etzhayyim_op_log (
    vertex_id       VARCHAR PRIMARY KEY,    -- {did}:{seq}
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    did             VARCHAR,    -- did:etzhayyim
    op_seq          BIGINT,     -- 0 = genesis, 1+ = updates
    op_type         VARCHAR,    -- 'create' | 'update' | 'deactivate'
    op_cid          VARCHAR,    -- CIDv1 of this op CBOR
    prev_cid        VARCHAR,    -- CIDv1 of previous op (NULL at genesis)
    op_cbor_hex     VARCHAR,    -- canonical DAG-CBOR encoded op (hex)
    sig             VARCHAR,    -- signature over op_cid (NULL at genesis)
    sig_kid         VARCHAR,    -- verificationMethod id used to sign
    created_at      VARCHAR
  );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_op_log_did_seq
    ON vertex_etzhayyim_op_log(did, op_seq);

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_op_log_head AS
    SELECT did, MAX(op_seq) AS head_seq
    FROM vertex_etzhayyim_op_log
    GROUP BY did;

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_path_depth_dist AS
    SELECT depth, COUNT(*) AS dids
    FROM vertex_etzhayyim_identity
    WHERE depth IS NOT NULL
    GROUP BY depth;

FLUSH;
