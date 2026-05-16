CREATE TABLE vertex_open_redsea_transit_passage (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    imo varchar NOT NULL, vessel_name varchar, flag varchar, waypoint varchar NOT NULL,
    direction varchar NOT NULL, lat double precision, lon double precision, sog_knots double precision,
    cargo_type varchar, laden boolean, observed_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_redsea_houthi_risk (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    assessment_id varchar NOT NULL, imo varchar NOT NULL, flag varchar,
    owner_lei varchar, ties_to_israel boolean, ties_to_us boolean, ties_to_uk boolean,
    risk_score double precision NOT NULL, risk_tier varchar NOT NULL, require_reroute_advisory boolean,
    assessed_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
