CREATE TABLE IF NOT EXISTS vertex_kami_flow_node (
      vertex_id VARCHAR PRIMARY KEY,
      rkey VARCHAR,
      repo VARCHAR,
      node_label VARCHAR NOT NULL,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      props TEXT,
      created_at VARCHAR,
      _alive BOOLEAN,
      _seq BIGINT,
      timestamp_ms BIGINT,
      owner_did VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS edge_kami_flow_relation (
      edge_id VARCHAR PRIMARY KEY,
      relation_label VARCHAR NOT NULL,
      rkey VARCHAR,
      repo VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      src_label VARCHAR,
      dst_label VARCHAR,
      weight DOUBLE PRECISION,
      props TEXT,
      created_at VARCHAR,
      _alive BOOLEAN,
      _seq BIGINT,
      timestamp_ms BIGINT,
      owner_did VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE INDEX IF NOT EXISTS idx_kami_flow_node_repo_label ON vertex_kami_flow_node (repo, node_label);

CREATE INDEX IF NOT EXISTS idx_kami_flow_node_collection ON vertex_kami_flow_node (collection);

CREATE INDEX IF NOT EXISTS idx_kami_flow_relation_repo_label ON edge_kami_flow_relation (repo, relation_label);

CREATE INDEX IF NOT EXISTS idx_kami_flow_relation_src ON edge_kami_flow_relation (src_vid);

CREATE INDEX IF NOT EXISTS idx_kami_flow_relation_dst ON edge_kami_flow_relation (dst_vid);

CREATE INDEX IF NOT EXISTS idx_kami_flow_relation_src_label ON edge_kami_flow_relation (src_label);

CREATE INDEX IF NOT EXISTS idx_kami_flow_relation_dst_label ON edge_kami_flow_relation (dst_label);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kami_flow_node_label_counts AS
    SELECT repo, node_label, count(*) AS cnt
    FROM vertex_kami_flow_node
    WHERE _alive IS DISTINCT FROM false
    GROUP BY repo, node_label;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kami_flow_relation_label_counts AS
    SELECT repo, relation_label, count(*) AS cnt
    FROM edge_kami_flow_relation
    WHERE _alive IS DISTINCT FROM false
    GROUP BY repo, relation_label;
