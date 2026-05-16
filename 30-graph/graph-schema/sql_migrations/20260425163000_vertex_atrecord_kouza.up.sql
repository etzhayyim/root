CREATE TABLE vertex_atrecord_kouza_institution_connection (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT NOT NULL,
      owner_did            VARCHAR NOT NULL,
      rkey                 VARCHAR NOT NULL,
      institution_name     VARCHAR NOT NULL,
      institution_kind     VARCHAR NOT NULL,
      provider_key         VARCHAR NOT NULL,
      credential_vault_ref VARCHAR,
      scopes_json          VARCHAR NOT NULL,
      consent_expires_at   TIMESTAMPTZ,
      status               VARCHAR NOT NULL,
      last_sync_run_did    VARCHAR,
      created_at           TIMESTAMPTZ NOT NULL,
      updated_at           TIMESTAMPTZ
    );

CREATE TABLE vertex_atrecord_kouza_financial_account (
      vertex_id                VARCHAR PRIMARY KEY,
      _seq                     BIGINT NOT NULL,
      owner_did                VARCHAR NOT NULL,
      rkey                     VARCHAR NOT NULL,
      connection_did           VARCHAR NOT NULL,
      external_account_id_hash VARCHAR NOT NULL,
      masked_account_number    VARCHAR,
      display_name             VARCHAR,
      account_kind             VARCHAR NOT NULL,
      currency                 VARCHAR NOT NULL,
      current_balance_minor    BIGINT,
      balance_as_of            TIMESTAMPTZ,
      kaikei_account_did       VARCHAR,
      status                   VARCHAR NOT NULL,
      created_at               TIMESTAMPTZ NOT NULL,
      updated_at               TIMESTAMPTZ
    );

CREATE TABLE vertex_atrecord_kouza_external_transaction (
      vertex_id                    VARCHAR PRIMARY KEY,
      _seq                         BIGINT NOT NULL,
      owner_did                    VARCHAR NOT NULL,
      rkey                         VARCHAR NOT NULL,
      financial_account_did        VARCHAR NOT NULL,
      external_txn_id              VARCHAR NOT NULL,
      posted_at                    TIMESTAMPTZ NOT NULL,
      value_at                     TIMESTAMPTZ,
      amount_minor                 BIGINT NOT NULL,
      currency                     VARCHAR NOT NULL,
      counterparty_name            VARCHAR,
      description                  VARCHAR,
      category_hint                VARCHAR,
      document_did                 VARCHAR,
      kaikei_bank_transaction_did  VARCHAR,
      accounting_status            VARCHAR NOT NULL,
      created_at                   TIMESTAMPTZ NOT NULL
    );

CREATE TABLE vertex_atrecord_kouza_account_document (
      vertex_id              VARCHAR PRIMARY KEY,
      _seq                   BIGINT NOT NULL,
      owner_did              VARCHAR NOT NULL,
      rkey                   VARCHAR NOT NULL,
      financial_account_did  VARCHAR NOT NULL,
      document_kind          VARCHAR NOT NULL,
      title                  VARCHAR,
      period_from            TIMESTAMPTZ,
      period_to              TIMESTAMPTZ,
      issued_at              TIMESTAMPTZ NOT NULL,
      vault_cid              VARCHAR NOT NULL,
      content_hash           VARCHAR NOT NULL,
      mime_type              VARCHAR,
      created_at             TIMESTAMPTZ NOT NULL
    );

CREATE TABLE vertex_atrecord_kouza_sync_run (
      vertex_id              VARCHAR PRIMARY KEY,
      _seq                   BIGINT NOT NULL,
      owner_did              VARCHAR NOT NULL,
      rkey                   VARCHAR NOT NULL,
      connection_did         VARCHAR NOT NULL,
      adapter_key            VARCHAR,
      started_at             TIMESTAMPTZ NOT NULL,
      finished_at            TIMESTAMPTZ,
      accounts_imported      INTEGER,
      transactions_imported  INTEGER,
      documents_imported     INTEGER,
      cursor_hash_before     VARCHAR,
      cursor_hash_after      VARCHAR,
      status                 VARCHAR NOT NULL,
      error_code             VARCHAR,
      error_message          VARCHAR,
      created_at             TIMESTAMPTZ NOT NULL
    );

CREATE MATERIALIZED VIEW mv_kouza_account_sync_health AS
    SELECT
      owner_did,
      connection_did,
      COUNT(*) AS sync_run_count,
      SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_run_count,
      MAX(started_at) AS latest_started_at,
      MAX(finished_at) AS latest_finished_at
    FROM vertex_atrecord_kouza_sync_run
    GROUP BY owner_did, connection_did;
