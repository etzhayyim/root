CREATE TABLE IF NOT EXISTS vertex_historical_conflict (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      conflict_id VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      wikidata_qid VARCHAR,
      start_time VARCHAR,
      end_time VARCHAR,
      location_json VARCHAR,
      participant_qids_json VARCHAR,
      source_url VARCHAR,
      summary VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      props VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_historical_conflict_qid ON vertex_historical_conflict (wikidata_qid);

CREATE INDEX IF NOT EXISTS idx_historical_conflict_start ON vertex_historical_conflict (start_time);

CREATE TABLE IF NOT EXISTS vertex_historical_source_image (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      image_id VARCHAR NOT NULL,
      source VARCHAR NOT NULL,
      source_record_id VARCHAR,
      subject_vid VARCHAR,
      subject_kind VARCHAR,
      title VARCHAR,
      commons_file VARCHAR,
      commons_url VARCHAR,
      original_url VARCHAR,
      thumb_url VARCHAR,
      ipfs_cid VARCHAR,
      sha256 VARCHAR,
      mime_type VARCHAR,
      license VARCHAR,
      attribution VARCHAR,
      llm_analysis_json VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      props VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_historical_image_subject ON vertex_historical_source_image (subject_vid);

CREATE INDEX IF NOT EXISTS idx_historical_image_source_record ON vertex_historical_source_image (source, source_record_id);

CREATE INDEX IF NOT EXISTS idx_historical_image_ipfs ON vertex_historical_source_image (ipfs_cid);

CREATE TABLE IF NOT EXISTS edge_historical_conflict_treaty (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      relation VARCHAR,
      confidence DOUBLE PRECISION,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      props VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_hist_conflict_treaty_src ON edge_historical_conflict_treaty (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_hist_conflict_treaty_dst ON edge_historical_conflict_treaty (dst_vid);

CREATE TABLE IF NOT EXISTS edge_historical_conflict_actor (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      relation VARCHAR,
      confidence DOUBLE PRECISION,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      props VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_hist_conflict_actor_src ON edge_historical_conflict_actor (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_hist_conflict_actor_dst ON edge_historical_conflict_actor (dst_vid);

CREATE TABLE IF NOT EXISTS edge_historical_treaty_actor (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      relation VARCHAR,
      confidence DOUBLE PRECISION,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      props VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_hist_treaty_actor_src ON edge_historical_treaty_actor (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_hist_treaty_actor_dst ON edge_historical_treaty_actor (dst_vid);

CREATE TABLE IF NOT EXISTS edge_historical_image_subject (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      relation VARCHAR,
      confidence DOUBLE PRECISION,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      props VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_hist_image_subject_src ON edge_historical_image_subject (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_hist_image_subject_dst ON edge_historical_image_subject (dst_vid);
