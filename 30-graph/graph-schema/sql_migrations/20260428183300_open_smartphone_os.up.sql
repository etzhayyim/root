CREATE TABLE IF NOT EXISTS vertex_open_smartphone_os_build (
      vertex_id VARCHAR PRIMARY KEY,
      build_id VARCHAR NOT NULL,
      os_name VARCHAR NOT NULL,
      os_base VARCHAR NOT NULL,
      version VARCHAR NOT NULL,
      kernel_version VARCHAR NOT NULL,
      soc_support VARCHAR,
      open_blobs_pct DOUBLE PRECISION,
      verified_boot BOOLEAN NOT NULL DEFAULT false,
      build_url VARCHAR,
      release_date VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-os'
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_smartphone_os_ota (
      vertex_id VARCHAR PRIMARY KEY,
      ota_id VARCHAR NOT NULL,
      os_did VARCHAR NOT NULL,
      from_version VARCHAR,
      to_version VARCHAR NOT NULL,
      release_notes_url VARCHAR,
      patch_level VARCHAR,
      cve_fixes VARCHAR,
      ota_size_mb DOUBLE PRECISION,
      signed BOOLEAN NOT NULL DEFAULT false,
      release_date VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'released',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-os'
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_smartphone_os_hal_driver (
      vertex_id VARCHAR PRIMARY KEY,
      driver_id VARCHAR NOT NULL,
      os_did VARCHAR NOT NULL,
      soc_did VARCHAR,
      sensor_did VARCHAR,
      driver_type VARCHAR NOT NULL,
      upstream_status VARCHAR,
      vendor_blobs_required BOOLEAN NOT NULL DEFAULT false,
      license VARCHAR,
      version VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-os'
    );

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_smartphone_os_cve_exposure AS
    SELECT
      b.vertex_id AS os_build_id,
      b.os_name,
      b.version,
      b.patch_level AS latest_patch_level,
      b.open_blobs_pct,
      b.verified_boot
    FROM vertex_open_smartphone_os_build b
    WHERE b.status = 'active';

FLUSH;
