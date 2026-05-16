CREATE TABLE IF NOT EXISTS vertex_risingwave_operation (
      operation_id VARCHAR PRIMARY KEY,
      operation_kind VARCHAR NOT NULL,
      status VARCHAR NOT NULL,
      requested_by VARCHAR,
      session_id VARCHAR,
      purpose VARCHAR,
      lease_name VARCHAR,
      lease_holder VARCHAR,
      migration_name VARCHAR,
      helm_release VARCHAR,
      git_ref VARCHAR,
      payload_json VARCHAR,
      pre_state_json VARCHAR,
      health_gate_json VARCHAR,
      post_state_json VARCHAR,
      error_text VARCHAR,
      created_at VARCHAR NOT NULL,
      started_at VARCHAR,
      finished_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_risingwave_operation_depends_on (
      src_operation_id VARCHAR NOT NULL,
      dst_operation_id VARCHAR NOT NULL,
      dependency_kind VARCHAR NOT NULL,
      status VARCHAR NOT NULL,
      note VARCHAR,
      created_at VARCHAR NOT NULL,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_risingwave_operation_status ON vertex_risingwave_operation (status, created_at);

CREATE INDEX IF NOT EXISTS idx_vertex_risingwave_operation_kind ON vertex_risingwave_operation (operation_kind, created_at);

CREATE INDEX IF NOT EXISTS idx_edge_risingwave_operation_dep_src ON edge_risingwave_operation_depends_on (src_operation_id);

CREATE INDEX IF NOT EXISTS idx_edge_risingwave_operation_dep_dst ON edge_risingwave_operation_depends_on (dst_operation_id);
