CREATE TABLE vertex_esic_contribution (
      vertex_id                              varchar PRIMARY KEY,
      _seq                                   bigint,
      created_date                           date,
      sensitivity_ord                        int,
      owner_did                              varchar,
      employer_org_id                        varchar NOT NULL,
      establishment_esi_code                 varchar NOT NULL,
      wage_month                             varchar NOT NULL,
      process_type                           varchar NOT NULL,
      status                                 varchar NOT NULL,
      declaration_hash                       varchar NOT NULL,
      total_members                          int,
      total_wage_inr_paise                   bigint,
      total_employee_contribution_inr_paise  bigint,
      total_employer_contribution_inr_paise  bigint,
      total_contribution_inr_paise           bigint,
      challan_reference                      varchar,
      challan_paid_at                        varchar,
      bpmn_instance_key                      bigint,
      amendment_count                        int,
      submitted_at                           varchar,
      approved_at                            varchar,
      approved_by_did                        varchar,
      created_at                             varchar,
      org_id                                 varchar,
      user_id                                varchar,
      actor_id                               varchar
    );

CREATE TABLE vertex_esic_contribution_pii (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      establishment_esi_code   varchar NOT NULL,
      roster_payload           varchar NOT NULL,
      ip_number_payload        varchar,
      aadhaar_payload          varchar,
      nominee_payload          varchar,
      amendment_log            varchar,
      retention_until          varchar NOT NULL,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    );

CREATE TABLE edge_esic_employer_member (
      edge_id                  varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      src_vid                  varchar NOT NULL,
      dst_vid                  varchar NOT NULL,
      establishment_esi_code   varchar NOT NULL,
      member_ip_number         varchar,
      joining_date             varchar,
      leaving_date             varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    );

CREATE MATERIALIZED VIEW mv_esic_active_contribution AS
    SELECT
      employer_org_id,
      establishment_esi_code,
      wage_month,
      vertex_id,
      status,
      total_members,
      total_wage_inr_paise,
      total_employee_contribution_inr_paise,
      total_employer_contribution_inr_paise,
      total_contribution_inr_paise,
      challan_reference,
      approved_at
    FROM vertex_esic_contribution
    WHERE status IN ('submitted', 'amended');
