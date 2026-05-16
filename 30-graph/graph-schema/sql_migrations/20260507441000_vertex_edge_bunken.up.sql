CREATE TABLE IF NOT EXISTS vertex_bunken_collection_job (
      vertex_id VARCHAR PRIMARY KEY,
      id VARCHAR,
      scheme VARCHAR,
      source_url TEXT,
      source_domain VARCHAR,
      crawl_id VARCHAR,
      status VARCHAR,
      discovered_count BIGINT,
      registered_count BIGINT,
      started_at VARCHAR,
      completed_at VARCHAR,
      error TEXT,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_bunken_record (
      vertex_id VARCHAR PRIMARY KEY,
      scheme VARCHAR,
      external_id VARCHAR,
      did VARCHAR,
      source_url TEXT,
      title TEXT,
      author TEXT,
      year BIGINT,
      language VARCHAR,
      material_type VARCHAR,
      era VARCHAR,
      country VARCHAR,
      digital_url TEXT,
      did_registered BOOLEAN,
      did_registered_at VARCHAR,
      content_hash VARCHAR,
      discovered_at VARCHAR,
      enriched_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_bunken_same_as (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      src_did VARCHAR,
      dst_did VARCHAR,
      relation VARCHAR,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    );
