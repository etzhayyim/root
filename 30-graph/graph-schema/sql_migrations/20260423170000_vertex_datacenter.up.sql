CREATE TABLE vertex_datacenter_operation (
      vertex_id             varchar PRIMARY KEY,
      _seq                  bigint,
      created_date          date,
      sensitivity_ord       int,
      owner_did             varchar,
      facility_id           varchar NOT NULL,
      operation_kind        varchar NOT NULL,
      summary               varchar NOT NULL,
      risk_class            varchar NOT NULL,
      requires_approval     boolean NOT NULL,
      status                varchar NOT NULL,
      customer_impact       varchar,
      window_start          varchar,
      window_end            varchar,
      bpmn_instance_key     bigint,
      review_comment        varchar,
      execution_status      varchar,
      health_status         varchar,
      metric_ref            varchar,
      opened_at             varchar,
      reviewed_at           varchar,
      approved_at           varchar,
      approved_by_did       varchar,
      stabilized_at         varchar,
      completed_at          varchar,
      created_at            varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar
    );

CREATE TABLE edge_datacenter_facility_operation (
      edge_id               varchar PRIMARY KEY,
      _seq                  bigint,
      created_date          date,
      sensitivity_ord       int,
      owner_did             varchar,
      src_vid               varchar NOT NULL,
      dst_vid               varchar NOT NULL,
      facility_id           varchar NOT NULL,
      operation_kind        varchar NOT NULL,
      status                varchar NOT NULL,
      created_at            varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar
    );

CREATE MATERIALIZED VIEW mv_datacenter_active_incident AS
    SELECT
      facility_id,
      vertex_id,
      operation_kind,
      risk_class,
      status,
      customer_impact,
      metric_ref,
      opened_at,
      reviewed_at,
      approved_at,
      stabilized_at
    FROM vertex_datacenter_operation
    WHERE operation_kind = 'incident'
      AND status IN ('open', 'degraded', 'incident-stabilized');
