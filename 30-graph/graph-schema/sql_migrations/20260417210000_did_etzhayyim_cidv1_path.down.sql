DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_path_depth_dist;

DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_op_log_head;

FLUSH;

DROP INDEX IF EXISTS idx_vertex_etzhayyim_op_log_did_seq;

DROP TABLE IF EXISTS vertex_etzhayyim_op_log;

FLUSH;

DROP INDEX IF EXISTS idx_edge_etzhayyim_path_child_src;

DROP INDEX IF EXISTS idx_edge_etzhayyim_path_child_dst;

DROP TABLE IF EXISTS edge_etzhayyim_path_child;

FLUSH;

DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_genesis_cid;

DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_root;

FLUSH;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN path_segment;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN root_did;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN genesis_op_cid;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN multibase_prefix;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN multihash_code;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN multicodec;

ALTER TABLE vertex_etzhayyim_identity DROP COLUMN cid_version;

FLUSH;
