CREATE TABLE IF NOT EXISTS vertex_naphtha_market_node (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  repo VARCHAR,
  node_code VARCHAR NOT NULL,
  node_kind VARCHAR NOT NULL,
  display_name VARCHAR,
  country_code VARCHAR,
  locode VARCHAR,
  operator_did VARCHAR,
  refinery_code VARCHAR,
  product_code VARCHAR,
  capacity_tonnes_day DOUBLE PRECISION,
  status VARCHAR,
  collection VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR
);

CREATE TABLE IF NOT EXISTS vertex_naphtha_cargo (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  repo VARCHAR,
  cargo_id VARCHAR NOT NULL,
  grade_code VARCHAR,
  origin_node_vid VARCHAR,
  destination_node_vid VARCHAR,
  load_port VARCHAR,
  discharge_port VARCHAR,
  vessel_imo VARCHAR,
  quantity_tonnes DOUBLE PRECISION,
  laycan_start VARCHAR,
  laycan_end VARCHAR,
  status VARCHAR,
  collection VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR
);

CREATE TABLE IF NOT EXISTS vertex_naphtha_price_assessment (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  repo VARCHAR,
  assessment_id VARCHAR NOT NULL,
  benchmark_code VARCHAR NOT NULL,
  region VARCHAR,
  grade_code VARCHAR,
  price_usd_tonne DOUBLE PRECISION,
  spread_to_brent_usd_bbl DOUBLE PRECISION,
  assessed_at VARCHAR NOT NULL,
  publisher VARCHAR,
  status VARCHAR,
  collection VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR
);

CREATE TABLE IF NOT EXISTS vertex_naphtha_cracker_demand (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  repo VARCHAR,
  demand_id VARCHAR NOT NULL,
  consumer_node_vid VARCHAR NOT NULL,
  product_family VARCHAR,
  demand_tonnes_day DOUBLE PRECISION,
  substitution_feedstock VARCHAR,
  effective_from VARCHAR,
  effective_to VARCHAR,
  status VARCHAR,
  collection VARCHAR,
  actor_did VARCHAR,
  org_did VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_naphtha_supply_link (
  edge_id VARCHAR PRIMARY KEY,
  src_vid VARCHAR NOT NULL,
  dst_vid VARCHAR NOT NULL,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  relationship VARCHAR NOT NULL,
  grade_code VARCHAR,
  capacity_tonnes_day DOUBLE PRECISION,
  contract_type VARCHAR,
  status VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_naphtha_cargo_route (
  edge_id VARCHAR PRIMARY KEY,
  src_vid VARCHAR NOT NULL,
  dst_vid VARCHAR NOT NULL,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  cargo_vid VARCHAR NOT NULL,
  route_role VARCHAR NOT NULL,
  event_at VARCHAR,
  status VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_naphtha_feedstock_to_derivative (
  edge_id VARCHAR PRIMARY KEY,
  src_vid VARCHAR NOT NULL,
  dst_vid VARCHAR NOT NULL,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  derivative_family VARCHAR NOT NULL,
  conversion_yield_pct DOUBLE PRECISION,
  status VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_vertex_naphtha_market_node_kind_country
  ON vertex_naphtha_market_node (node_kind, country_code);

CREATE INDEX IF NOT EXISTS idx_vertex_naphtha_market_node_refinery
  ON vertex_naphtha_market_node (refinery_code);

CREATE INDEX IF NOT EXISTS idx_vertex_naphtha_cargo_route_ports
  ON vertex_naphtha_cargo (load_port, discharge_port);

CREATE INDEX IF NOT EXISTS idx_vertex_naphtha_cargo_status_grade
  ON vertex_naphtha_cargo (status, grade_code);

CREATE INDEX IF NOT EXISTS idx_vertex_naphtha_price_region_time
  ON vertex_naphtha_price_assessment (region, assessed_at);

CREATE INDEX IF NOT EXISTS idx_vertex_naphtha_demand_consumer
  ON vertex_naphtha_cracker_demand (consumer_node_vid, status);

CREATE INDEX IF NOT EXISTS idx_edge_naphtha_supply_src
  ON edge_naphtha_supply_link (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_naphtha_supply_dst
  ON edge_naphtha_supply_link (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_naphtha_cargo_route_cargo
  ON edge_naphtha_cargo_route (cargo_vid);

CREATE INDEX IF NOT EXISTS idx_edge_naphtha_derivative_src
  ON edge_naphtha_feedstock_to_derivative (src_vid);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_naphtha_supply_chain_trace AS
  SELECT
    e.edge_id,
    e.relationship,
    src.vertex_id AS src_vid,
    src.node_code AS src_node_code,
    src.node_kind AS src_node_kind,
    src.display_name AS src_name,
    src.country_code AS src_country_code,
    dst.vertex_id AS dst_vid,
    dst.node_code AS dst_node_code,
    dst.node_kind AS dst_node_kind,
    dst.display_name AS dst_name,
    dst.country_code AS dst_country_code,
    e.grade_code,
    e.capacity_tonnes_day,
    e.contract_type,
    e.status
  FROM edge_naphtha_supply_link e
  JOIN vertex_naphtha_market_node src ON src.vertex_id = e.src_vid
  JOIN vertex_naphtha_market_node dst ON dst.vertex_id = e.dst_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_naphtha_country_balance AS
  SELECT
    country_code,
    SUM(CASE WHEN node_kind IN ('refinery', 'splitter', 'export_terminal') THEN COALESCE(capacity_tonnes_day, 0.0) ELSE 0.0 END) AS supply_capacity_tonnes_day,
    SUM(CASE WHEN node_kind IN ('steam_cracker', 'petrochemical_plant', 'import_terminal') THEN COALESCE(capacity_tonnes_day, 0.0) ELSE 0.0 END) AS demand_capacity_tonnes_day,
    SUM(CASE WHEN node_kind IN ('refinery', 'splitter', 'export_terminal') THEN COALESCE(capacity_tonnes_day, 0.0) ELSE 0.0 END)
      - SUM(CASE WHEN node_kind IN ('steam_cracker', 'petrochemical_plant', 'import_terminal') THEN COALESCE(capacity_tonnes_day, 0.0) ELSE 0.0 END) AS balance_tonnes_day,
    COUNT(*)::bigint AS node_count
  FROM vertex_naphtha_market_node
  WHERE status IS NULL OR status <> 'deleted'
  GROUP BY country_code;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_naphtha_cargo_flow AS
  SELECT
    COALESCE(split_part(load_port, '-', 1), 'ZZ') AS load_country_code,
    COALESCE(split_part(discharge_port, '-', 1), 'ZZ') AS discharge_country_code,
    grade_code,
    status,
    COUNT(*)::bigint AS cargo_count,
    SUM(COALESCE(quantity_tonnes, 0.0)) AS total_tonnes,
    MAX(laycan_end) AS latest_laycan_end
  FROM vertex_naphtha_cargo
  GROUP BY
    COALESCE(split_part(load_port, '-', 1), 'ZZ'),
    COALESCE(split_part(discharge_port, '-', 1), 'ZZ'),
    grade_code,
    status;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_naphtha_price_latest AS
  SELECT p.*
  FROM vertex_naphtha_price_assessment p
  JOIN (
    SELECT benchmark_code, region, MAX(assessed_at) AS assessed_at
    FROM vertex_naphtha_price_assessment
    WHERE status IS NULL OR status = 'active'
    GROUP BY benchmark_code, region
  ) latest
    ON latest.benchmark_code = p.benchmark_code
   AND latest.region = p.region
   AND latest.assessed_at = p.assessed_at;
