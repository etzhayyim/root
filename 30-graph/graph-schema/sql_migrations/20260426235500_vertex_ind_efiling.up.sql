CREATE TABLE IF NOT EXISTS vertex_ind_efiling_provider (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      jurisdiction       varchar NOT NULL,
      provider_key       varchar NOT NULL,
      provider_kind      varchar NOT NULL,
      status             varchar NOT NULL,
      endpoint_ref       varchar,
      credential_ref     varchar,
      auth_model         varchar,
      terms_ref          varchar,
      last_verified_at   varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE TABLE IF NOT EXISTS vertex_ind_efiling_submission (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      jurisdiction           varchar NOT NULL,
      provider_key           varchar NOT NULL,
      provider_kind          varchar NOT NULL,
      source_vertex_id       varchar NOT NULL,
      idempotency_key        varchar NOT NULL,
      payload_hash           varchar NOT NULL,
      status                 varchar NOT NULL,
      external_reference     varchar,
      authorization_ref      varchar,
      credential_ref         varchar,
      approved_by_did        varchar,
      adapter_status         varchar,
      adapter_response_json  varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ind_efiling_submission_status AS
    SELECT
      jurisdiction,
      provider_key,
      provider_kind,
      source_vertex_id,
      idempotency_key,
      payload_hash,
      status,
      external_reference,
      adapter_status,
      created_at
    FROM vertex_ind_efiling_submission;
