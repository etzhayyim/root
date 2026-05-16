CREATE TABLE vertex_open_hormuz_military_incident (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      incident_id varchar NOT NULL, imo varchar, vessel_name varchar, flag varchar,
      aggressor_party varchar, incident_type varchar NOT NULL,
      lat double precision, lon double precision, narrative varchar,
      casualties int, vessel_seized boolean,
      severity varchar NOT NULL, require_international_notice boolean,
      occurred_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_hormuz_navigational_incident (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      incident_id varchar NOT NULL, imo varchar, vessel_name varchar, flag varchar,
      incident_type varchar NOT NULL, lat double precision, lon double precision,
      narrative varchar, spill_volume_tonnes double precision,
      severity varchar NOT NULL, require_public_notice boolean,
      occurred_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_open_hormuz_incident_vessel (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_open_hormuz_military_by_severity AS
      SELECT aggressor_party, severity, COUNT(*) AS incident_count,
             BOOL_OR(vessel_seized) AS any_seizure, MAX(occurred_at) AS latest_occurred
      FROM vertex_open_hormuz_military_incident WHERE status='confirmed'
      GROUP BY aggressor_party, severity;
