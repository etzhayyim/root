CREATE TABLE IF NOT EXISTS vertex_open_jpn_mynumber_audit_event (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      event_type         varchar NOT NULL,
      person_ref         varchar,
      requester_agency   varchar,
      holder_agency      varchar,
      purpose_code       varchar,
      dataset_code       varchar,
      result             varchar NOT NULL,
      payload_json       varchar NOT NULL,
      created_at         varchar NOT NULL,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE TABLE IF NOT EXISTS vertex_open_jpn_mynumber_consent_receipt (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      person_ref         varchar NOT NULL,
      requester_agency   varchar NOT NULL,
      purpose_code       varchar NOT NULL,
      scope_json         varchar NOT NULL,
      expires_at         varchar,
      revoked_at         varchar,
      created_at         varchar NOT NULL,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE TABLE IF NOT EXISTS vertex_open_jpn_mynumber_agency_alias (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      person_ref         varchar NOT NULL,
      agency_code        varchar NOT NULL,
      alias_kind         varchar NOT NULL,
      alias_value_hash   varchar NOT NULL,
      created_at         varchar NOT NULL,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE TABLE IF NOT EXISTS vertex_open_jpn_mynumber_oauth_token (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      requester_agency   varchar NOT NULL,
      client_id_hash     varchar NOT NULL,
      scope_json         varchar NOT NULL,
      purpose_code       varchar NOT NULL,
      active             boolean NOT NULL,
      expires_at         varchar NOT NULL,
      revoked_at         varchar,
      created_at         varchar NOT NULL,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE TABLE IF NOT EXISTS vertex_open_jpn_mynumber_file_manifest (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      requester_agency     varchar NOT NULL,
      purpose_code         varchar NOT NULL,
      file_manifest_hash   varchar NOT NULL,
      file_count           int NOT NULL,
      total_bytes          bigint NOT NULL,
      manifest_json        varchar NOT NULL,
      created_at           varchar NOT NULL,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE IF NOT EXISTS vertex_open_jpn_mynumber_file_transfer (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      requester_agency     varchar NOT NULL,
      holder_agency        varchar,
      purpose_code         varchar NOT NULL,
      file_manifest_hash   varchar NOT NULL,
      file_count           int NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar NOT NULL,
      updated_at           varchar NOT NULL,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE IF NOT EXISTS edge_open_jpn_mynumber_event_subject (
      edge_id          varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      from_vertex_id   varchar NOT NULL,
      to_ref           varchar NOT NULL,
      to_ref_kind      varchar NOT NULL,
      edge_type        varchar NOT NULL,
      created_at       varchar NOT NULL,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    );

CREATE TABLE IF NOT EXISTS edge_open_jpn_mynumber_transfer_manifest (
      edge_id          varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      from_vertex_id   varchar NOT NULL,
      to_vertex_id     varchar NOT NULL,
      edge_type        varchar NOT NULL,
      created_at       varchar NOT NULL,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_jpn_mynumber_oauth_token_status AS
    SELECT
      vertex_id AS token_ref,
      requester_agency,
      purpose_code,
      scope_json,
      active,
      expires_at,
      revoked_at,
      created_at,
      CASE
        WHEN active IS TRUE AND revoked_at IS NULL THEN 'active'
        WHEN revoked_at IS NOT NULL THEN 'revoked'
        ELSE 'inactive'
      END AS status
    FROM vertex_open_jpn_mynumber_oauth_token;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_jpn_mynumber_file_transfer_status AS
    SELECT
      t.vertex_id AS transfer_id,
      t.requester_agency,
      t.holder_agency,
      t.purpose_code,
      t.file_manifest_hash,
      m.vertex_id AS file_manifest_vertex_id,
      t.file_count,
      m.total_bytes,
      t.status,
      t.created_at,
      t.updated_at
    FROM vertex_open_jpn_mynumber_file_transfer t
    LEFT JOIN vertex_open_jpn_mynumber_file_manifest m
      ON m.file_manifest_hash = t.file_manifest_hash;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_jpn_mynumber_audit_timeline AS
    SELECT
      vertex_id AS audit_event_vertex_id,
      event_type,
      person_ref,
      requester_agency,
      holder_agency,
      purpose_code,
      dataset_code,
      result,
      created_at
    FROM vertex_open_jpn_mynumber_audit_event;
