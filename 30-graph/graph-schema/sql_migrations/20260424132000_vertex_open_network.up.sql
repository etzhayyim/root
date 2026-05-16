CREATE TABLE vertex_open_network_site (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      operator_org_id varchar NOT NULL,
      site_type       varchar NOT NULL,
      name            varchar,
      latitude        double precision,
      longitude       double precision,
      status          varchar NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    );

CREATE TABLE vertex_open_network_link (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      operator_org_id    varchar NOT NULL,
      from_vertex_id     varchar NOT NULL,
      to_vertex_id       varchar NOT NULL,
      capacity_mbps      double precision NOT NULL,
      media              varchar NOT NULL,
      installed_at       varchar,
      status             varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE TABLE vertex_open_network_change (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      operator_org_id        varchar NOT NULL,
      target_vertex_id       varchar NOT NULL,
      change_type            varchar NOT NULL,
      narrative              varchar,
      affected_customers     int,
      risk                   varchar NOT NULL,
      require_cab_approval   boolean,
      status                 varchar NOT NULL,
      requested_at           varchar NOT NULL,
      approved_at            varchar,
      implemented_at         varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    );

CREATE TABLE edge_open_network_link_endpoint (
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

CREATE MATERIALIZED VIEW mv_open_network_pending_changes AS
    SELECT
      target_vertex_id,
      COUNT(*)                     AS pending_change_count,
      MAX(risk)                    AS worst_risk,
      BOOL_OR(require_cab_approval) AS any_cab_approval,
      MAX(requested_at)            AS latest_requested_at
    FROM vertex_open_network_change
    WHERE status IN ('requested', 'approved')
    GROUP BY target_vertex_id;
