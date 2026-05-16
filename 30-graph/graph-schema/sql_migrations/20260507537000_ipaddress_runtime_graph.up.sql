CREATE TABLE IF NOT EXISTS vertex_ipaddress_asn (
      vertex_id VARCHAR PRIMARY KEY,
      number BIGINT NOT NULL,
      did VARCHAR,
      name VARCHAR,
      country VARCHAR,
      rir VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2
    );

CREATE TABLE IF NOT EXISTS vertex_ipaddress_range (
      vertex_id VARCHAR PRIMARY KEY,
      range_id VARCHAR NOT NULL,
      family VARCHAR NOT NULL,
      start_address VARCHAR NOT NULL,
      end_address VARCHAR,
      cidr VARCHAR,
      country VARCHAR,
      rir VARCHAR,
      status VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2
    );

CREATE TABLE IF NOT EXISTS vertex_ipaddress_scan_job (
      vertex_id VARCHAR PRIMARY KEY,
      job_id VARCHAR NOT NULL,
      cidr VARCHAR NOT NULL,
      ports VARCHAR,
      status VARCHAR NOT NULL,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2
    );

ALTER TABLE vertex_scan_result ADD COLUMN IF NOT EXISTS job_id VARCHAR;

ALTER TABLE vertex_scan_result ADD COLUMN IF NOT EXISTS created_at VARCHAR;

ALTER TABLE vertex_ip_address ADD COLUMN IF NOT EXISTS node_id VARCHAR;

ALTER TABLE vertex_ip_address ADD COLUMN IF NOT EXISTS version VARCHAR;

ALTER TABLE vertex_ip_address ADD COLUMN IF NOT EXISTS first_seen VARCHAR;

ALTER TABLE vertex_ip_address ADD COLUMN IF NOT EXISTS last_seen VARCHAR;

ALTER TABLE vertex_ip_address ADD COLUMN IF NOT EXISTS updated_at VARCHAR;

CREATE INDEX IF NOT EXISTS idx_ipaddress_asn_number
      ON vertex_ipaddress_asn (number);

CREATE INDEX IF NOT EXISTS idx_ipaddress_asn_rir_country
      ON vertex_ipaddress_asn (rir, country);

CREATE INDEX IF NOT EXISTS idx_ipaddress_range_rir_country
      ON vertex_ipaddress_range (rir, country);

CREATE INDEX IF NOT EXISTS idx_ipaddress_scan_job_status
      ON vertex_ipaddress_scan_job (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ipaddress_address
      ON vertex_ip_address (address);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ipaddress_rir_coverage AS
    SELECT rir, COUNT(*) AS range_count, MAX(updated_at) AS latest_updated_at
    FROM vertex_ipaddress_range
    GROUP BY rir;
