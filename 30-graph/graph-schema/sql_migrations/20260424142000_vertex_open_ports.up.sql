CREATE TABLE vertex_open_ports_port (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      authority_org_id varchar NOT NULL, un_locode varchar NOT NULL, name varchar,
      latitude double precision, longitude double precision, berth_count int,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE vertex_open_ports_vessel (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      operator_org_id varchar NOT NULL, imo varchar NOT NULL, mmsi varchar, flag varchar,
      name varchar, vessel_type varchar, gross_tonnage double precision,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE vertex_open_ports_vessel_call (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      authority_org_id varchar NOT NULL, port_vid varchar NOT NULL, vessel_vid varchar NOT NULL,
      berth_label varchar, eta varchar NOT NULL, etd varchar NOT NULL,
      ata varchar, atd varchar, purpose varchar,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE vertex_open_ports_incident (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      authority_org_id varchar NOT NULL, port_vid varchar NOT NULL,
      vessel_vid varchar, call_vid varchar, category varchar NOT NULL, narrative varchar,
      spill_volume_tonnes double precision, severity varchar NOT NULL, require_public_notice boolean,
      status varchar NOT NULL, reported_at varchar NOT NULL, resolved_at varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE edge_open_ports_call_endpoint (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE MATERIALIZED VIEW mv_open_ports_open_incidents AS
    SELECT port_vid,
           COUNT(*) AS open_incident_count,
           MAX(severity) AS worst_severity,
           BOOL_OR(require_public_notice) AS any_public_notice,
           MAX(reported_at) AS latest_reported_at
    FROM vertex_open_ports_incident WHERE status='open' GROUP BY port_vid;
