CREATE TABLE vertex_open_malacca_pilotage (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    pilotage_id varchar NOT NULL, imo varchar NOT NULL, authority varchar NOT NULL,
    pilot_station varchar, boarding_at varchar NOT NULL, disembark_at varchar,
    status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_malacca_anchorage (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    anchorage_id varchar NOT NULL, imo varchar NOT NULL, anchorage_zone varchar NOT NULL,
    arrived_at varchar NOT NULL, departed_at varchar, dwell_hours double precision,
    purpose varchar, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
