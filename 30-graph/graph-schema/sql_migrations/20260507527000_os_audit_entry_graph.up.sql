CREATE TABLE IF NOT EXISTS vertex_os_audit_entry (
      vertex_id VARCHAR PRIMARY KEY,
      audit_id VARCHAR,
      agent_id VARCHAR,
      event VARCHAR,
      target VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS edge_os_agent_audit_entry (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      agent_id VARCHAR,
      relation VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE INDEX IF NOT EXISTS idx_vertex_os_audit_entry_agent ON vertex_os_audit_entry (agent_id, created_at);

CREATE INDEX IF NOT EXISTS idx_vertex_os_audit_entry_event ON vertex_os_audit_entry (event, created_at);

CREATE INDEX IF NOT EXISTS idx_edge_os_agent_audit_entry_src ON edge_os_agent_audit_entry (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_os_agent_audit_entry_dst ON edge_os_agent_audit_entry (dst_vid);
