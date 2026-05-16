CREATE TABLE IF NOT EXISTS vertex_open_smartphone_sensor_module (
      vertex_id VARCHAR PRIMARY KEY,
      sensor_id VARCHAR NOT NULL,
      sensor_type VARCHAR NOT NULL,
      vendor VARCHAR NOT NULL,
      model VARCHAR NOT NULL,
      interface_type VARCHAR,
      open_driver BOOLEAN NOT NULL DEFAULT false,
      mainline_kernel_status VARCHAR,
      pixel_count_mp DOUBLE PRECISION,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-sensor'
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_smartphone_sensor_calibration (
      vertex_id VARCHAR PRIMARY KEY,
      sensor_did VARCHAR NOT NULL,
      calibration_type VARCHAR NOT NULL,
      standard_ref VARCHAR,
      calibrated_at VARCHAR NOT NULL,
      valid_until VARCHAR,
      calibrated_by VARCHAR,
      pass BOOLEAN NOT NULL DEFAULT true,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-sensor'
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_smartphone_sensor_driver (
      vertex_id VARCHAR PRIMARY KEY,
      sensor_type VARCHAR NOT NULL,
      driver_name VARCHAR NOT NULL,
      kernel_version VARCHAR,
      mainlined BOOLEAN NOT NULL DEFAULT false,
      os_build_did VARCHAR,
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-sensor'
    );

FLUSH;
