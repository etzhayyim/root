CREATE TABLE vertex_open_airplane_airport (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      operator_org_id varchar NOT NULL,
      icao            varchar NOT NULL,
      iata            varchar,
      name            varchar,
      latitude        double precision,
      longitude       double precision,
      runways         int,
      status          varchar NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    );

CREATE TABLE vertex_open_airplane_aircraft (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      operator_org_id varchar NOT NULL,
      tail_number     varchar NOT NULL,
      icao24          varchar,
      type_icao       varchar,
      status          varchar NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    );

CREATE TABLE vertex_open_airplane_flight (
      vertex_id         varchar PRIMARY KEY,
      _seq              bigint,
      created_date      date,
      sensitivity_ord   int,
      owner_did         varchar,
      operator_org_id   varchar NOT NULL,
      aircraft_vid      varchar NOT NULL,
      origin_vid        varchar NOT NULL,
      destination_vid   varchar NOT NULL,
      flight_number     varchar NOT NULL,
      scheduled_off     varchar NOT NULL,
      scheduled_in      varchar NOT NULL,
      status            varchar NOT NULL,
      created_at        varchar,
      org_id            varchar,
      user_id           varchar,
      actor_id          varchar
    );

CREATE TABLE vertex_open_airplane_incident (
      vertex_id             varchar PRIMARY KEY,
      _seq                  bigint,
      created_date          date,
      sensitivity_ord       int,
      owner_did             varchar,
      operator_org_id       varchar NOT NULL,
      aircraft_vid          varchar NOT NULL,
      flight_vid            varchar,
      category              varchar NOT NULL,
      narrative             varchar,
      injuries              int,
      severity              varchar NOT NULL,
      require_public_notice boolean,
      status                varchar NOT NULL,
      reported_at           varchar NOT NULL,
      resolved_at           varchar,
      created_at            varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar
    );

CREATE TABLE edge_open_airplane_flight_route (
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

CREATE MATERIALIZED VIEW mv_open_airplane_open_incidents AS
    SELECT
      aircraft_vid,
      COUNT(*)                       AS open_incident_count,
      MAX(severity)                  AS worst_severity,
      BOOL_OR(require_public_notice) AS any_public_notice,
      MAX(reported_at)               AS latest_reported_at
    FROM vertex_open_airplane_incident
    WHERE status = 'open'
    GROUP BY aircraft_vid;
