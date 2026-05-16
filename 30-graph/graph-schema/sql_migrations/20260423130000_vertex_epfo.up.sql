CREATE TABLE vertex_epfo_ecr (
      vertex_id                     varchar PRIMARY KEY,
      _seq                          bigint,
      created_date                  date,
      sensitivity_ord               int,
      owner_did                     varchar,
      employer_org_id               varchar NOT NULL,
      establishment_pf_code         varchar NOT NULL,
      wage_month                    varchar NOT NULL,
      process_type                  varchar NOT NULL,
      status                        varchar NOT NULL,
      declaration_hash              varchar NOT NULL,
      total_members                 int,
      total_wage_inr_paise          bigint,
      total_employer_pf_inr_paise   bigint,
      total_employee_pf_inr_paise   bigint,
      total_eps_inr_paise           bigint,
      total_admin_inr_paise         bigint,
      trrn                          varchar,
      bpmn_instance_key             bigint,
      submitted_at                  varchar,
      approved_at                   varchar,
      approved_by_did               varchar,
      created_at                    varchar,
      org_id                        varchar,
      user_id                       varchar,
      actor_id                      varchar
    );

CREATE TABLE vertex_epfo_ecr_pii (
      vertex_id               varchar PRIMARY KEY,
      _seq                    bigint,
      created_date            date,
      sensitivity_ord         int,
      owner_did               varchar,
      establishment_pf_code   varchar NOT NULL,
      roster_payload          varchar NOT NULL,
      aadhaar_payload         varchar,
      pan_payload             varchar,
      bank_payload            varchar,
      amendment_log           varchar,
      retention_until         varchar NOT NULL,
      created_at              varchar,
      org_id                  varchar,
      user_id                 varchar,
      actor_id                varchar
    );

CREATE TABLE edge_epfo_employer_employee (
      edge_id                 varchar PRIMARY KEY,
      _seq                    bigint,
      created_date            date,
      sensitivity_ord         int,
      owner_did               varchar,
      src_vid                 varchar NOT NULL,
      dst_vid                 varchar NOT NULL,
      establishment_pf_code   varchar NOT NULL,
      member_uan              varchar,
      joining_date            varchar,
      leaving_date            varchar,
      created_at              varchar,
      org_id                  varchar,
      user_id                 varchar,
      actor_id                varchar
    );

CREATE MATERIALIZED VIEW mv_epfo_active_ecr AS
    SELECT
      employer_org_id,
      establishment_pf_code,
      wage_month,
      vertex_id,
      status,
      total_members,
      total_wage_inr_paise,
      total_employer_pf_inr_paise,
      total_employee_pf_inr_paise,
      total_eps_inr_paise,
      trrn,
      approved_at
    FROM vertex_epfo_ecr
    WHERE status IN ('submitted', 'amended');
