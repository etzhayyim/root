CREATE TABLE IF NOT EXISTS vertex_lora_adapter (
      vertex_id VARCHAR PRIMARY KEY,
      did VARCHAR NOT NULL,
      rkey VARCHAR NOT NULL,
      adapter_id VARCHAR NOT NULL,
      domain VARCHAR,
      status VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS edge_lora_adapter_affinity (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      src_label VARCHAR,
      dst_label VARCHAR,
      relation VARCHAR NOT NULL,
      weight DOUBLE PRECISION,
      created_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE INDEX IF NOT EXISTS idx_lora_adapter_did_status ON vertex_lora_adapter (did, status);

CREATE INDEX IF NOT EXISTS idx_lora_adapter_adapter_id ON vertex_lora_adapter (adapter_id);

CREATE INDEX IF NOT EXISTS idx_lora_adapter_domain ON vertex_lora_adapter (domain);

CREATE INDEX IF NOT EXISTS idx_edge_lora_adapter_affinity_dst ON edge_lora_adapter_affinity (dst_vid, dst_label);

CREATE INDEX IF NOT EXISTS idx_edge_lora_adapter_affinity_src_label ON edge_lora_adapter_affinity (src_label);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lora_adapter_actor_status AS
    SELECT did, status, count(*) AS adapter_count, max(created_at) AS latest_created_at
    FROM vertex_lora_adapter
    GROUP BY did, status;
