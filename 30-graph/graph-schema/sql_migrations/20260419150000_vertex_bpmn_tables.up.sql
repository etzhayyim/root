CREATE TABLE IF NOT EXISTS vertex_bpmn_process (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      process_id VARCHAR, name VARCHAR, version BIGINT,
      xml_r2_key VARCHAR, json_r2_key VARCHAR, xsd_valid VARCHAR,
      deployed_at VARCHAR, deployed_by VARCHAR, deprecated VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_bpmn_instance (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      instance_id VARCHAR, process_id VARCHAR, state VARCHAR,
      variables_json VARCHAR, current_token_json VARCHAR, correlation_key VARCHAR,
      started_at VARCHAR, completed_at VARCHAR, error_code VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_bpmn_activity_event (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      event_id VARCHAR, instance_id VARCHAR, activity_id VARCHAR, event_type VARCHAR,
      payload_json VARCHAR, occurred_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_bpmn_signal_log (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      instance_id VARCHAR, activity_id VARCHAR, message_name VARCHAR,
      payload_json VARCHAR, occurred_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_bpmn_instance_of_process (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      instance_id VARCHAR, process_id VARCHAR, created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_bpmn_event_in_instance (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      event_id VARCHAR, instance_id VARCHAR, created_at VARCHAR
    );
