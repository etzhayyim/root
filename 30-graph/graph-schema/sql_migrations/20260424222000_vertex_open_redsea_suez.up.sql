CREATE TABLE vertex_open_redsea_suez_transit (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    transit_id varchar NOT NULL, imo varchar NOT NULL, direction varchar NOT NULL,
    convoy_id varchar, scn_booked boolean, suez_toll_usd double precision,
    entered_at varchar NOT NULL, cleared_at varchar, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_redsea_suez_toll (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    toll_id varchar NOT NULL, effective_from varchar NOT NULL,
    vessel_type varchar NOT NULL, laden boolean, rate_usd_scnt double precision NOT NULL,
    discount_pct double precision, surcharge_pct double precision, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
