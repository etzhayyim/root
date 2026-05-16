CREATE TABLE vertex_telecom_alarm (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      alarm_id             varchar NOT NULL,
      source_kind          varchar NOT NULL,
      source_vid           varchar NOT NULL,
      alarm_type           varchar NOT NULL,
      severity             varchar NOT NULL,
      perceived_severity   varchar,
      probable_cause       varchar,
      alarm_text           varchar,
      raised_at            varchar NOT NULL,
      cleared_at           varchar,
      mttr_seconds         double precision,
      clear_kind           varchar,
      cleared_by           varchar,
      resolution_ref       varchar,
      suppress_until       varchar,
      suppression_reason   varchar,
      suppressed_by        varchar,
      window_vid           varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_alarm_correlation (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      correlation_id       varchar NOT NULL,
      parent_alarm_vid     varchar NOT NULL,
      child_count          int NOT NULL,
      correlation_kind     varchar NOT NULL,
      rule_ref             varchar,
      confidence           double precision,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_change_request (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      change_id            varchar NOT NULL,
      requester_id         varchar NOT NULL,
      change_kind          varchar NOT NULL,
      risk_level           varchar NOT NULL,
      scope_kind           varchar NOT NULL,
      scope_vid            varchar NOT NULL,
      summary              varchar NOT NULL,
      plan_ref             varchar,
      planned_start        varchar NOT NULL,
      planned_end          varchar NOT NULL,
      scheduled_start      varchar,
      scheduled_end        varchar,
      rollback_plan_ref    varchar,
      submitted_at         varchar NOT NULL,
      decision             varchar,
      decision_reason      varchar,
      approver_id          varchar,
      approver_role        varchar,
      decided_at           varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_change_approval (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      approval_id          varchar NOT NULL,
      change_vid           varchar NOT NULL,
      decision             varchar NOT NULL,
      approver_id          varchar NOT NULL,
      approver_role        varchar NOT NULL,
      decision_reason      varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_config_snapshot (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      snapshot_id          varchar NOT NULL,
      scope_kind           varchar NOT NULL,
      scope_vid            varchar NOT NULL,
      source_system        varchar NOT NULL,
      config_hash          varchar NOT NULL,
      config_ref           varchar,
      config_size          bigint,
      baseline_snapshot_vid varchar,
      drift                boolean NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_capacity_forecast (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      forecast_id          varchar NOT NULL,
      scope_kind           varchar NOT NULL,
      scope_vid            varchar NOT NULL,
      metric               varchar NOT NULL,
      current_value        double precision NOT NULL,
      forecast_value       double precision NOT NULL,
      forecast_horizon_days int NOT NULL,
      capacity_limit       double precision NOT NULL,
      breach_predicted     boolean NOT NULL,
      model_kind           varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE edge_telecom_alarm_on_source (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_alarm_correlated_under (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_change_targets_scope (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_telecom_alarm_state AS
      SELECT source_kind, severity, status, COUNT(*) AS alarm_count
      FROM vertex_telecom_alarm
      GROUP BY source_kind, severity, status;

CREATE MATERIALIZED VIEW mv_telecom_alarm_mttr AS
      SELECT source_kind, severity,
             AVG(mttr_seconds) AS avg_mttr_seconds,
             MIN(mttr_seconds) AS min_mttr_seconds,
             MAX(mttr_seconds) AS max_mttr_seconds,
             COUNT(*) AS cleared_count
      FROM vertex_telecom_alarm
      WHERE status = 'cleared' AND mttr_seconds IS NOT NULL
      GROUP BY source_kind, severity;

CREATE MATERIALIZED VIEW mv_telecom_change_pipeline AS
      SELECT change_kind, risk_level, status, COUNT(*) AS change_count
      FROM vertex_telecom_change_request
      GROUP BY change_kind, risk_level, status;

CREATE MATERIALIZED VIEW mv_telecom_config_drift AS
      SELECT scope_kind, source_system, drift, COUNT(*) AS snapshot_count
      FROM vertex_telecom_config_snapshot
      GROUP BY scope_kind, source_system, drift;

CREATE MATERIALIZED VIEW mv_telecom_capacity_breach AS
      SELECT scope_kind, metric, model_kind, breach_predicted, COUNT(*) AS forecast_count
      FROM vertex_telecom_capacity_forecast
      GROUP BY scope_kind, metric, model_kind, breach_predicted;
