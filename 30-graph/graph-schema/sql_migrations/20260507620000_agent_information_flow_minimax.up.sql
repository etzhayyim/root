CREATE TABLE IF NOT EXISTS vertex_agent_information_node (
      vertex_id VARCHAR PRIMARY KEY,
      agent_did VARCHAR NOT NULL,
      info_ref VARCHAR NOT NULL,
      info_kind VARCHAR NOT NULL,
      abstraction_level BIGINT NOT NULL DEFAULT 0,
      confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      uncertainty DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      protected_asset_ref VARCHAR,
      counterparty_ref VARCHAR,
      value_json VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      sensitivity_ord BIGINT DEFAULT 1,
      actor_id VARCHAR,
      owner_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_agent_information_depends_on (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      dependency_kind VARCHAR NOT NULL,
      weight DOUBLE PRECISION NOT NULL DEFAULT 1.0,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord BIGINT DEFAULT 1
    );

CREATE TABLE IF NOT EXISTS edge_agent_information_flows_to (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      flow_kind VARCHAR NOT NULL,
      bandwidth_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      control_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord BIGINT DEFAULT 1
    );

CREATE INDEX IF NOT EXISTS idx_agent_info_node_agent_level ON vertex_agent_information_node (agent_did, abstraction_level);

CREATE INDEX IF NOT EXISTS idx_agent_info_node_counterparty ON vertex_agent_information_node (counterparty_ref, info_kind);

CREATE INDEX IF NOT EXISTS idx_agent_info_dep_src ON edge_agent_information_depends_on (src_vid);

CREATE INDEX IF NOT EXISTS idx_agent_info_dep_dst ON edge_agent_information_depends_on (dst_vid);

CREATE INDEX IF NOT EXISTS idx_agent_info_flow_src ON edge_agent_information_flows_to (src_vid);

CREATE INDEX IF NOT EXISTS idx_agent_info_flow_dst ON edge_agent_information_flows_to (dst_vid);

DROP MATERIALIZED VIEW IF EXISTS mv_agent_information_height;

CREATE MATERIALIZED VIEW mv_agent_information_height AS
    SELECT agent_did, counterparty_ref, info_kind,
           MAX(abstraction_level) AS max_information_height,
           COUNT(*)::BIGINT AS node_count
    FROM vertex_agent_information_node
    GROUP BY agent_did, counterparty_ref, info_kind;

DROP MATERIALIZED VIEW IF EXISTS mv_agent_information_flow_control;

CREATE MATERIALIZED VIEW mv_agent_information_flow_control AS
    SELECT src_vid, COUNT(*)::BIGINT AS out_flow_count,
           AVG(control_score) AS avg_control_score,
           AVG(bandwidth_score) AS avg_bandwidth_score
    FROM edge_agent_information_flows_to
    GROUP BY src_vid;
