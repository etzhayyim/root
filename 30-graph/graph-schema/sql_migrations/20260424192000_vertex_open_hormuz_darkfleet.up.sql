CREATE TABLE vertex_open_hormuz_darkfleet_flag (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      imo varchar NOT NULL, mmsi varchar, vessel_name varchar,
      current_flag varchar NOT NULL, prior_flags varchar,
      ais_gap_hours double precision, sanctioned_owner_lei varchar,
      risk_score double precision NOT NULL, risk_tier varchar NOT NULL,
      require_port_state_notice boolean,
      flagged_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_hormuz_sts_transfer (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      transfer_id varchar NOT NULL, donor_imo varchar NOT NULL, receiver_imo varchar NOT NULL,
      lat double precision, lon double precision, cargo_type varchar,
      estimated_volume_tonnes double precision,
      duration_hours double precision, outside_designated_area boolean,
      observed_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_open_hormuz_darkfleet_pair (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_open_hormuz_darkfleet_by_flag AS
      SELECT current_flag, risk_tier, COUNT(*) AS flagged_count,
             AVG(risk_score) AS avg_score, MAX(flagged_at) AS latest_flagged
      FROM vertex_open_hormuz_darkfleet_flag WHERE status='active'
      GROUP BY current_flag, risk_tier;
