CREATE TABLE vertex_open_spr_level (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      snapshot_id varchar NOT NULL, country varchar NOT NULL,
      operator_org_id varchar, reserve_mmbbl double precision NOT NULL,
      capacity_mmbbl double precision NOT NULL, pct_full double precision,
      coverage_days double precision, measured_at varchar NOT NULL,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_spr_drawdown (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      drawdown_id varchar NOT NULL, country varchar NOT NULL,
      volume_mmbbl double precision NOT NULL, trigger_event varchar,
      coordinated_with_iea boolean, effective_from varchar NOT NULL,
      effective_until varchar, scope_tier varchar NOT NULL,
      require_market_notice boolean, authorized_at varchar NOT NULL,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_open_spr_level_country (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_open_spr_by_country AS
      SELECT country, COUNT(*) AS snapshot_count,
             AVG(pct_full) AS avg_pct_full, AVG(coverage_days) AS avg_coverage_days,
             MAX(measured_at) AS latest_measured
      FROM vertex_open_spr_level WHERE status='published'
      GROUP BY country;
