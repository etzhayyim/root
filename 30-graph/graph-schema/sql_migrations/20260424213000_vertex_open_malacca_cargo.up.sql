CREATE TABLE vertex_open_malacca_container_flow (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    flow_id varchar NOT NULL, terminal_code varchar NOT NULL,
    imo varchar NOT NULL, teu_in int NOT NULL, teu_out int NOT NULL,
    call_date varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_malacca_bunker_delivery (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    delivery_id varchar NOT NULL, imo varchar NOT NULL, bunker_type varchar NOT NULL,
    volume_tonnes double precision NOT NULL, price_usd_tonne double precision,
    supplier varchar, delivered_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
