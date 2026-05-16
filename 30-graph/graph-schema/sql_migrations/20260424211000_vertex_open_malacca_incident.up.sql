CREATE TABLE vertex_open_malacca_piracy (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    incident_id varchar NOT NULL, imo varchar, vessel_name varchar, flag varchar,
    recaap_category varchar NOT NULL, lat double precision, lon double precision,
    narrative varchar, casualties int, cargo_stolen_usd double precision,
    severity varchar NOT NULL, require_recaap_notice boolean,
    occurred_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_malacca_nav_incident (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    incident_id varchar NOT NULL, imo varchar, incident_type varchar NOT NULL,
    lat double precision, lon double precision, narrative varchar,
    spill_volume_tonnes double precision, severity varchar NOT NULL, require_public_notice boolean,
    occurred_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
