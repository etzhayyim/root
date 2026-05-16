CREATE TABLE vertex_open_carrier_schedule_proforma (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      schedule_id varchar NOT NULL, carrier_code varchar NOT NULL, string_code varchar NOT NULL,
      rotation_locodes varchar, transit_days int, frequency_days int,
      effective_from varchar NOT NULL, effective_until varchar, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_carrier_schedule_port_call (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      call_id varchar NOT NULL, imo varchar NOT NULL, carrier_code varchar,
      string_code varchar, voyage_number varchar, port_locode varchar NOT NULL, terminal varchar,
      eta varchar, etd varchar, ata varchar, atd varchar,
      schedule_tier varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
