CREATE TABLE vertex_pds_tail_event (
      event_id          varchar PRIMARY KEY,
      event_ts          timestamptz NOT NULL,
      script_name       varchar NOT NULL,
      script_version_id varchar,
      outcome           varchar NOT NULL,
      nsid              varchar,
      rpc_method        varchar,
      request_url       varchar,
      request_method    varchar,
      cf_ray            varchar,
      cf_country        varchar,
      cf_colo           varchar,
      client_ip         varchar,
      user_agent        varchar,
      wall_time_ms      int,
      cpu_time_ms       int,
      truncated         boolean,
      logs_text         text,
      exceptions_text   text,
      created_date      date NOT NULL,
      sensitivity_ord   int,
      owner_did         varchar,
      _seq              bigint
    );

CREATE INDEX idx_pds_tail_event_nsid_ts ON vertex_pds_tail_event (nsid, event_ts DESC);

CREATE INDEX idx_pds_tail_event_outcome_ts ON vertex_pds_tail_event (outcome, event_ts DESC);

CREATE INDEX idx_pds_tail_event_created_date ON vertex_pds_tail_event (created_date);

CREATE MATERIALIZED VIEW mv_pds_tail_by_nsid_outcome_hour AS
    SELECT
      nsid,
      outcome,
      date_trunc('hour', event_ts) AS event_hour,
      COUNT(*) AS cnt
    FROM vertex_pds_tail_event
    WHERE nsid IS NOT NULL
    GROUP BY nsid, outcome, date_trunc('hour', event_ts);
