CREATE TABLE vertex_open_power_node (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      utility_org_id  varchar NOT NULL,
      node_type       varchar NOT NULL,
      name            varchar,
      voltage_kv      double precision,
      latitude        double precision,
      longitude       double precision,
      status          varchar NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    );

CREATE TABLE vertex_open_power_feeder (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      utility_org_id     varchar NOT NULL,
      from_vertex_id     varchar NOT NULL,
      to_vertex_id       varchar NOT NULL,
      voltage_kv         double precision NOT NULL,
      capacity_amps      double precision,
      length_km          double precision,
      installed_at       varchar,
      status             varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE TABLE vertex_open_power_outage (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      utility_org_id         varchar NOT NULL,
      feeder_vertex_id       varchar NOT NULL,
      cause                  varchar NOT NULL,
      customers_affected     int,
      severity               varchar NOT NULL,
      require_public_notice  boolean,
      status                 varchar NOT NULL,
      reported_at            varchar NOT NULL,
      restored_at            varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    );

CREATE TABLE edge_open_power_feeder_endpoint (
      edge_id         varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      src_vid         varchar NOT NULL,
      dst_vid         varchar NOT NULL,
      role            varchar NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    );

CREATE MATERIALIZED VIEW mv_open_power_open_outages AS
    SELECT
      feeder_vertex_id,
      COUNT(*)                       AS open_outage_count,
      MAX(severity)                  AS worst_severity,
      BOOL_OR(require_public_notice) AS any_public_notice,
      SUM(customers_affected)        AS total_customers_affected,
      MAX(reported_at)               AS latest_reported_at
    FROM vertex_open_power_outage
    WHERE status = 'open'
    GROUP BY feeder_vertex_id;
