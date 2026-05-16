CREATE TABLE vertex_resource_flow_anomaly (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      anomaly_id             varchar NOT NULL,
      flow_class             varchar NOT NULL,
      source_did             varchar NOT NULL,
      counterparty_did       varchar,
      fiscal_period          varchar NOT NULL,
      industry_code          varchar,
      currency               varchar,
      service_class          varchar,
      observed_value         double precision NOT NULL,
      baseline_avg           double precision NOT NULL,
      baseline_window_days   integer NOT NULL,
      baseline_sample_count  integer NOT NULL,
      threshold_factor       double precision NOT NULL,
      severity               varchar NOT NULL,
      observed_at            varchar NOT NULL,
      detection_run_id       varchar NOT NULL,
      post_uri               varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    );

CREATE INDEX IF NOT EXISTS idx_resource_flow_anomaly_run        ON vertex_resource_flow_anomaly (detection_run_id);

CREATE INDEX IF NOT EXISTS idx_resource_flow_anomaly_source     ON vertex_resource_flow_anomaly (source_did, fiscal_period);

CREATE INDEX IF NOT EXISTS idx_resource_flow_anomaly_severity   ON vertex_resource_flow_anomaly (severity, observed_at);

FLUSH;

CREATE MATERIALIZED VIEW mv_resource_flow_anomaly_recent AS
      SELECT
        severity,
        flow_class,
        source_did,
        COUNT(*) AS anomaly_count
      FROM vertex_resource_flow_anomaly
      GROUP BY severity, flow_class, source_did;

FLUSH;
