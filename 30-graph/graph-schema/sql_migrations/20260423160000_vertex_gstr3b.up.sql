CREATE TABLE vertex_gstr3b_return (
      vertex_id                       varchar PRIMARY KEY,
      _seq                            bigint,
      created_date                    date,
      sensitivity_ord                 int,
      owner_did                       varchar,
      gstin_hash                      varchar NOT NULL,
      tax_period                      varchar NOT NULL,
      process_type                    varchar NOT NULL,
      status                          varchar NOT NULL,
      filing_hash                     varchar NOT NULL,
      total_outward_tax_inr_paise     bigint,
      total_inward_itc_inr_paise      bigint,
      total_net_tax_inr_paise         bigint,
      filing_frequency                varchar,
      arn                             varchar,
      filed_via                       varchar,
      filed_at                        varchar,
      predecessor_vertex_id           varchar,
      amendment_reason                varchar,
      amendment_count                 int,
      bpmn_instance_key               bigint,
      created_at                      varchar,
      org_id                          varchar,
      user_id                         varchar,
      actor_id                        varchar
    );

CREATE TABLE vertex_gstr3b_return_pii (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      gstin_hash             varchar NOT NULL,
      applicant_payload      varchar NOT NULL,
      supplies_payload       varchar NOT NULL,
      itc_payload            varchar NOT NULL,
      tax_payment_payload    varchar NOT NULL,
      amendment_log          varchar,
      retention_until        varchar NOT NULL,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    );

CREATE TABLE edge_gstr3b_amend_chain (
      edge_id                varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      src_vid                varchar NOT NULL,
      dst_vid                varchar NOT NULL,
      amendment_reason       varchar,
      delta_tax_inr_paise    bigint,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    );

CREATE MATERIALIZED VIEW mv_gstr3b_filed_returns AS
    SELECT
      gstin_hash,
      tax_period,
      vertex_id,
      status,
      arn,
      filed_via,
      total_outward_tax_inr_paise,
      total_inward_itc_inr_paise,
      total_net_tax_inr_paise,
      filed_at
    FROM vertex_gstr3b_return
    WHERE status IN ('filed', 'amended');
