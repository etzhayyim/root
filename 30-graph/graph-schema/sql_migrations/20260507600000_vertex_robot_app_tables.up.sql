CREATE TABLE IF NOT EXISTS vertex_robot_mission (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      robot_did VARCHAR,
      goal VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_robot_mission_robot_did ON vertex_robot_mission (robot_did);

CREATE INDEX IF NOT EXISTS idx_robot_mission_status ON vertex_robot_mission (status);

CREATE TABLE IF NOT EXISTS vertex_robot_workflow_instance (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      process_id VARCHAR,
      robot_did VARCHAR,
      mission_id VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_robot_workflow_robot_did ON vertex_robot_workflow_instance (robot_did);

CREATE INDEX IF NOT EXISTS idx_robot_workflow_mission_id ON vertex_robot_workflow_instance (mission_id);

CREATE INDEX IF NOT EXISTS idx_robot_workflow_status ON vertex_robot_workflow_instance (status);

CREATE TABLE IF NOT EXISTS vertex_robot_telemetry (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      robot_did VARCHAR,
      topic VARCHAR,
      ts VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_robot_telemetry_robot_did ON vertex_robot_telemetry (robot_did);

CREATE INDEX IF NOT EXISTS idx_robot_telemetry_topic ON vertex_robot_telemetry (topic);
