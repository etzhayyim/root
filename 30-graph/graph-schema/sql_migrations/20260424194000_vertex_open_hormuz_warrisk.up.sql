CREATE TABLE vertex_open_hormuz_warrisk_zone (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      zone_code varchar NOT NULL, zone_name varchar, listing_authority varchar NOT NULL,
      listed boolean NOT NULL, listing_reason varchar,
      effective_from varchar NOT NULL, effective_until varchar,
      severity varchar NOT NULL, require_insurer_notice boolean,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_hormuz_warrisk_premium (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      quote_id varchar NOT NULL, insurer_lei varchar, flag varchar NOT NULL,
      vessel_type varchar NOT NULL, hull_value_usd double precision NOT NULL,
      premium_rate_bps double precision NOT NULL, premium_usd double precision NOT NULL,
      coverage_period_days int, rate_tier varchar NOT NULL,
      quoted_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_open_hormuz_premium_zone (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_open_hormuz_premium_by_flag AS
      SELECT flag, vessel_type, rate_tier, COUNT(*) AS quote_count,
             AVG(premium_rate_bps) AS avg_premium_bps,
             MAX(quoted_at) AS latest_quoted
      FROM vertex_open_hormuz_warrisk_premium WHERE status='active'
      GROUP BY flag, vessel_type, rate_tier;
