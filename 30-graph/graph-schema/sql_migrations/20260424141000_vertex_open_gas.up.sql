CREATE TABLE vertex_open_gas_node (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
      utility_org_id   varchar NOT NULL,
      node_type        varchar NOT NULL,
      name             varchar,
      outlet_pressure_kpa double precision,
      latitude         double precision,
      longitude        double precision,
      status           varchar NOT NULL,
      created_at       varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE vertex_open_gas_segment (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
      utility_org_id   varchar NOT NULL,
      from_vertex_id   varchar NOT NULL,
      to_vertex_id     varchar NOT NULL,
      diameter_mm      int NOT NULL,
      material         varchar NOT NULL,
      length_m         double precision NOT NULL,
      maop_kpa         double precision,
      installed_at     varchar,
      status           varchar NOT NULL,
      created_at       varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE vertex_open_gas_leak (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint, created_date date, sensitivity_ord int, owner_did varchar,
      utility_org_id         varchar NOT NULL,
      segment_vertex_id      varchar NOT NULL,
      latitude               double precision,
      longitude              double precision,
      concentration_lel_pct  double precision,
      near_ignition          boolean,
      leak_class             int NOT NULL,
      require_public_notice  boolean,
      status                 varchar NOT NULL,
      reported_at            varchar NOT NULL,
      resolved_at            varchar,
      created_at             varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE edge_open_gas_segment_endpoint (
      edge_id         varchar PRIMARY KEY,
      _seq            bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid         varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at      varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE MATERIALIZED VIEW mv_open_gas_open_leaks AS
    SELECT segment_vertex_id,
           COUNT(*) AS open_leak_count,
           MIN(leak_class) AS worst_class,
           BOOL_OR(require_public_notice) AS any_public_notice,
           MAX(reported_at) AS latest_reported_at
    FROM vertex_open_gas_leak WHERE status='open' GROUP BY segment_vertex_id;
