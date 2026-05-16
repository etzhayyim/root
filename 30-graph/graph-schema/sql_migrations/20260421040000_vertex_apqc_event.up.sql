CREATE TABLE IF NOT EXISTS vertex_apqc_event (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      ocel_event_id VARCHAR, apqc_code VARCHAR, apqc_l1_name VARCHAR,
      task_id VARCHAR, event_type VARCHAR, case_id VARCHAR,
      objects_json VARCHAR, attributes_json VARCHAR, timestamp VARCHAR,
      run_vertex_id VARCHAR, node_key VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_apqc_event_run
            ON vertex_apqc_event (run_vertex_id, _seq);

CREATE INDEX IF NOT EXISTS idx_apqc_event_case
            ON vertex_apqc_event (case_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_apqc_event_type
            ON vertex_apqc_event (event_type, _seq);
