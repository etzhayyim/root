CREATE TABLE IF NOT EXISTS vertex_maps_job (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date TIMESTAMP,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      label VARCHAR,
      did VARCHAR,
      name VARCHAR,
      display_name VARCHAR,
      description TEXT,
      category VARCHAR,
      status VARCHAR,
      job_id VARCHAR,
      source_id VARCHAR,
      dataset_type VARCHAR,
      region VARCHAR,
      priority VARCHAR,
      phase BIGINT,
      stage VARCHAR,
      progress_pct DOUBLE PRECISION,
      pipeline_type VARCHAR,
      sequence_id VARCHAR,
      chunk_key VARCHAR,
      chunk_size_meters BIGINT,
      bbox_json TEXT,
      stage_order_json TEXT,
      coverage_threshold_ratio DOUBLE PRECISION,
      heading_threshold_deg DOUBLE PRECISION,
      frame_threshold_count BIGINT,
      frame_count BIGINT,
      records_count BIGINT,
      coverage_ratio DOUBLE PRECISION,
      heading_span_deg DOUBLE PRECISION,
      view_cluster_count BIGINT,
      occlusion_risk DOUBLE PRECISION,
      dynamic_object_risk DOUBLE PRECISION,
      recommended_chunk_class VARCHAR,
      error_message TEXT,
      props TEXT,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_maps_job_job_id ON vertex_maps_job (job_id);

CREATE INDEX IF NOT EXISTS idx_vertex_maps_job_source_status ON vertex_maps_job (source_id, status);

CREATE INDEX IF NOT EXISTS idx_vertex_maps_job_stage ON vertex_maps_job (stage);

CREATE INDEX IF NOT EXISTS idx_vertex_maps_job_chunk_key ON vertex_maps_job (chunk_key);

CREATE INDEX IF NOT EXISTS idx_vertex_maps_job_pipeline_type ON vertex_maps_job (pipeline_type);
