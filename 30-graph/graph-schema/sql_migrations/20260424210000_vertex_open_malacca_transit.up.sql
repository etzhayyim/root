CREATE TABLE vertex_open_malacca_transit_passage (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    imo varchar NOT NULL, vessel_name varchar, flag varchar, vts_gate varchar NOT NULL,
    direction varchar NOT NULL, lat double precision, lon double precision, sog_knots double precision,
    cargo_type varchar, laden boolean, observed_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_malacca_transit_congestion (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    assessment_id varchar NOT NULL, vts_gate varchar NOT NULL,
    vessel_count_hour int NOT NULL, avg_sog_knots double precision,
    queue_tier varchar NOT NULL, require_notice boolean,
    assessed_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
