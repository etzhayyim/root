CREATE TABLE IF NOT EXISTS vertex_graph_sos_intel_snapshot (
      vertex_id VARCHAR PRIMARY KEY,
      snapshot_id VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      scope VARCHAR NOT NULL,
      status VARCHAR NOT NULL,
      relation_total BIGINT NOT NULL DEFAULT 0,
      vertex_table_count BIGINT NOT NULL DEFAULT 0,
      edge_table_count BIGINT NOT NULL DEFAULT 0,
      mv_count BIGINT NOT NULL DEFAULT 0,
      idx_count BIGINT NOT NULL DEFAULT 0,
      anomaly_count BIGINT NOT NULL DEFAULT 0,
      stale_relation_count BIGINT NOT NULL DEFAULT 0,
      heavy_ddl_pending_count BIGINT NOT NULL DEFAULT 0,
      summary VARCHAR,
      recommendation_json VARCHAR,
      evidence_json VARCHAR,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR,
      owner_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 100
    );

CREATE TABLE IF NOT EXISTS vertex_graph_sos_intel_finding (
      vertex_id VARCHAR PRIMARY KEY,
      finding_id VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      finding_kind VARCHAR NOT NULL,
      severity VARCHAR NOT NULL,
      status VARCHAR NOT NULL,
      affected_relation VARCHAR,
      affected_relation_kind VARCHAR,
      summary VARCHAR NOT NULL,
      evidence_json VARCHAR,
      recommendation VARCHAR,
      recommended_action_kind VARCHAR,
      ddl_request_ref VARCHAR,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR,
      resolved_at VARCHAR,
      owner_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 100
    );

CREATE TABLE IF NOT EXISTS edge_graph_sos_finding_affects_relation (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation_name VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      finding_kind VARCHAR NOT NULL,
      severity VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 100
    );

CREATE TABLE IF NOT EXISTS vertex_graph_sos_relation_inventory (
      vertex_id VARCHAR PRIMARY KEY,
      schema_name VARCHAR NOT NULL,
      relation_name VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      table_type VARCHAR,
      is_insertable_into VARCHAR,
      observed_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 100
    );
