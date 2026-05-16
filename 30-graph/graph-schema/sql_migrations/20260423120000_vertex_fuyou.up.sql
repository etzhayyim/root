CREATE TABLE vertex_fuyou_declaration (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      employee_did       varchar NOT NULL,
      employer_org_id    varchar NOT NULL,
      tax_year           smallint NOT NULL,
      process_type       varchar NOT NULL,
      status             varchar NOT NULL,
      declaration_hash   varchar NOT NULL,
      amendment_count    int,
      bpmn_instance_key  bigint,
      submitted_at       varchar,
      approved_at        varchar,
      approved_by_did    varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE TABLE vertex_fuyou_declaration_pii (
      vertex_id           varchar PRIMARY KEY,
      _seq                bigint,
      created_date        date,
      sensitivity_ord     int,
      owner_did           varchar,
      applicant_payload   varchar NOT NULL,
      spouse_payload      varchar,
      dependents_payload  varchar NOT NULL,
      minor_dep_payload   varchar,
      special_status      varchar,
      amendment_log       varchar,
      retention_until     varchar NOT NULL,
      created_at          varchar,
      org_id              varchar,
      user_id             varchar,
      actor_id            varchar
    );

CREATE TABLE edge_fuyou_employment (
      edge_id          varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      src_vid          varchar NOT NULL,
      dst_vid          varchar NOT NULL,
      effective_from   varchar NOT NULL,
      effective_to     varchar,
      employment_kind  varchar,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    );

CREATE MATERIALIZED VIEW mv_fuyou_active_declaration AS
    SELECT
      employee_did,
      employer_org_id,
      tax_year,
      vertex_id,
      status,
      amendment_count,
      approved_at
    FROM vertex_fuyou_declaration
    WHERE status IN ('approved', 'amended');
