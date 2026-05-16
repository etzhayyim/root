CREATE TABLE vertex_open_freight_rate_index (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      index_id varchar NOT NULL, benchmark varchar NOT NULL, trade_lane varchar NOT NULL,
      value_usd_teu double precision NOT NULL, baseline_value double precision,
      week_over_week_pct double precision, shock_tier varchar NOT NULL,
      publish_date varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_freight_rate_spot (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      quote_id varchar NOT NULL, carrier_code varchar NOT NULL, trade_lane varchar NOT NULL,
      box_type varchar NOT NULL, rate_usd_box double precision NOT NULL,
      baf_usd double precision, peak_season_surcharge double precision,
      premium_tier varchar NOT NULL, quoted_at varchar NOT NULL, effective_from varchar NOT NULL,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
