CREATE TABLE vertex_open_asia_refinery_receipt (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      receipt_id varchar NOT NULL, refinery_code varchar NOT NULL,
      refinery_name varchar, country varchar NOT NULL,
      imo varchar NOT NULL, vessel_name varchar,
      manifest_vid varchar, crude_grade varchar NOT NULL,
      volume_tonnes double precision NOT NULL, discharged_at varchar NOT NULL,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_asia_refinery_crack_spread (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      quote_id varchar NOT NULL, refinery_code varchar NOT NULL,
      benchmark varchar NOT NULL, spread_usd_bbl double precision NOT NULL,
      health_tier varchar NOT NULL, require_alert boolean,
      quoted_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_open_asia_refinery_receipt_manifest (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_open_asia_refinery_throughput AS
      SELECT refinery_code, country, crude_grade, COUNT(*) AS receipt_count,
             SUM(volume_tonnes) AS total_tonnes, MAX(discharged_at) AS latest_discharge
      FROM vertex_open_asia_refinery_receipt WHERE status='received'
      GROUP BY refinery_code, country, crude_grade;
