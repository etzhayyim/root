CREATE TABLE vertex_open_hormuz_transit_passage (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      imo varchar NOT NULL, mmsi varchar, vessel_name varchar, flag varchar,
      waypoint varchar NOT NULL, direction varchar NOT NULL,
      lat double precision, lon double precision, sog_knots double precision,
      cargo_type varchar, laden boolean, observed_at varchar NOT NULL,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_hormuz_transit_exposure (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      passage_vid varchar NOT NULL, cargo_value_usd double precision,
      alt_route varchar, alt_route_days_delta double precision,
      alt_route_cost_delta_usd double precision,
      exposure_tier varchar NOT NULL, require_warning boolean,
      assessed_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_open_hormuz_transit_passage_exposure (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_open_hormuz_daily_transit AS
      SELECT created_date, direction, flag, COUNT(*) AS passage_count,
             SUM(CASE WHEN laden THEN 1 ELSE 0 END) AS laden_count,
             MAX(observed_at) AS latest_observed
      FROM vertex_open_hormuz_transit_passage WHERE status='recorded'
      GROUP BY created_date, direction, flag;
