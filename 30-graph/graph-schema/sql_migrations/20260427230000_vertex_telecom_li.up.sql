CREATE TABLE vertex_telecom_li_warrant (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      warrant_id           varchar NOT NULL,
      jurisdiction         varchar NOT NULL,
      law_authority_id     varchar NOT NULL,
      warrant_number_hash  varchar NOT NULL,
      warrant_kind         varchar NOT NULL,
      intercept_scope      varchar NOT NULL,
      valid_from           varchar NOT NULL,
      valid_until          varchar NOT NULL,
      lemf_id              varchar NOT NULL,
      warrant_document_ref varchar,
      registered_at        varchar NOT NULL,
      closed_at            varchar,
      closure_reason       varchar,
      retention_until      varchar,
      final_report_ref     varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_li_target (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      target_id            varchar NOT NULL,
      warrant_vid          varchar NOT NULL,
      identifier_kind      varchar NOT NULL,
      identifier_hash      varchar NOT NULL,
      licf_nf_vid          varchar NOT NULL,
      lipf_nf_vid          varchar,
      activated_at         varchar NOT NULL,
      deactivated_at       varchar,
      deactivation_reason  varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_li_iri_delivery (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      iri_id               varchar NOT NULL,
      target_vid           varchar NOT NULL,
      event_kind           varchar NOT NULL,
      event_vid            varchar NOT NULL,
      x2_sequence          bigint NOT NULL,
      df2_nf_vid           varchar NOT NULL,
      lemf_id              varchar NOT NULL,
      payload_hash         varchar NOT NULL,
      payload_size         bigint,
      observed_at          varchar NOT NULL,
      ack_status           varchar,
      acked_at             varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_li_cc_delivery (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      cc_id                varchar NOT NULL,
      target_vid           varchar NOT NULL,
      content_kind         varchar NOT NULL,
      x3_sequence          bigint NOT NULL,
      df3_nf_vid           varchar NOT NULL,
      lemf_id              varchar NOT NULL,
      payload_hash         varchar NOT NULL,
      payload_size         bigint,
      encryption_ref       varchar,
      observed_at          varchar NOT NULL,
      ack_status           varchar,
      acked_at             varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_li_delivery_ack (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      ack_id               varchar NOT NULL,
      delivery_kind        varchar NOT NULL,
      delivery_vid         varchar NOT NULL,
      lemf_id              varchar NOT NULL,
      ack_result           varchar NOT NULL,
      ack_code             varchar,
      acked_at             varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_li_access_audit (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      audit_id             varchar NOT NULL,
      warrant_vid          varchar,
      target_vid           varchar,
      access_kind          varchar NOT NULL,
      accessor_hash        varchar NOT NULL,
      accessor_role        varchar NOT NULL,
      justification        varchar,
      record_kind          varchar NOT NULL,
      record_vid           varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE edge_telecom_li_target_under_warrant (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_li_iri_for_event (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_li_audit_to_record (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_telecom_li_warrant_state AS
      SELECT jurisdiction, warrant_kind, intercept_scope, status, COUNT(*) AS warrant_count
      FROM vertex_telecom_li_warrant
      GROUP BY jurisdiction, warrant_kind, intercept_scope, status;

CREATE MATERIALIZED VIEW mv_telecom_li_active_targets AS
      SELECT identifier_kind, status, COUNT(*) AS target_count
      FROM vertex_telecom_li_target
      GROUP BY identifier_kind, status;

CREATE MATERIALIZED VIEW mv_telecom_li_delivery_loss AS
      SELECT 'iri' AS delivery_kind, ack_status, COUNT(*) AS delivery_count
      FROM vertex_telecom_li_iri_delivery
      GROUP BY ack_status
      UNION ALL
      SELECT 'cc' AS delivery_kind, ack_status, COUNT(*) AS delivery_count
      FROM vertex_telecom_li_cc_delivery
      GROUP BY ack_status;

CREATE MATERIALIZED VIEW mv_telecom_li_access_audit_summary AS
      SELECT accessor_role, access_kind, record_kind, COUNT(*) AS access_count
      FROM vertex_telecom_li_access_audit
      GROUP BY accessor_role, access_kind, record_kind;
