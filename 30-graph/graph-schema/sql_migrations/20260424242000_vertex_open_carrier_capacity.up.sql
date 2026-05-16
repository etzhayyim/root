CREATE TABLE vertex_open_carrier_capacity_blanked (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      blanked_id varchar NOT NULL, carrier_code varchar NOT NULL, string_code varchar NOT NULL,
      skipped_weeks int NOT NULL, teu_removed_total double precision,
      reason varchar, impact_tier varchar NOT NULL, require_shipper_notice boolean,
      effective_from varchar NOT NULL, effective_until varchar, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_carrier_capacity_utilization (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      util_id varchar NOT NULL, carrier_code varchar NOT NULL, trade_lane varchar NOT NULL,
      period_week varchar NOT NULL, teu_offered double precision NOT NULL, teu_lifted double precision NOT NULL,
      utilization_pct double precision NOT NULL, saturation_tier varchar NOT NULL,
      reported_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
