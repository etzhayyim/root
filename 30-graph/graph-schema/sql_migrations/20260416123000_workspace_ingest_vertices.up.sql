CREATE TABLE IF NOT EXISTS vertex_workspace_account (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      tenant_id          VARCHAR,
      account_id         VARCHAR,
      principal_email    VARCHAR,
      display_name       VARCHAR,
      status             VARCHAR,
      last_synced_at     VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      props              VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_account_provider_tenant ON vertex_workspace_account (provider, tenant_id);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_account_email ON vertex_workspace_account (principal_email);

CREATE TABLE IF NOT EXISTS vertex_workspace_cursor (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      source_kind        VARCHAR,
      scope_key          VARCHAR,
      cursor_token       VARCHAR,
      watermark_ts       VARCHAR,
      status             VARCHAR,
      fail_count         BIGINT,
      last_success_at    VARCHAR,
      last_error_at      VARCHAR,
      last_error_code    VARCHAR,
      last_error_message VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      props              VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_cursor_scope_key ON vertex_workspace_cursor (scope_key);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_cursor_provider_source ON vertex_workspace_cursor (provider, source_kind);

CREATE TABLE IF NOT EXISTS vertex_workspace_raw_event (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      source_kind        VARCHAR,
      native_id          VARCHAR,
      native_parent_id   VARCHAR,
      operation_kind     VARCHAR,
      account_vid        VARCHAR,
      scope_key          VARCHAR,
      cursor_token       VARCHAR,
      payload_hash       VARCHAR,
      payload            VARCHAR,
      occurred_at        VARCHAR,
      ingested_at        VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      props              VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_raw_event_scope ON vertex_workspace_raw_event (provider, source_kind, scope_key);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_raw_event_native ON vertex_workspace_raw_event (source_kind, native_id);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_raw_event_ingested ON vertex_workspace_raw_event (ingested_at);

CREATE TABLE IF NOT EXISTS vertex_workspace_sync_job (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      source_kind        VARCHAR,
      scope_key          VARCHAR,
      cursor_before      VARCHAR,
      cursor_after       VARCHAR,
      started_at         VARCHAR,
      ended_at           VARCHAR,
      status             VARCHAR,
      rows_fetched       BIGINT,
      rows_written       BIGINT,
      error_code         VARCHAR,
      error_message      VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      props              VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_sync_job_scope_started ON vertex_workspace_sync_job (provider, source_kind, scope_key, started_at);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_sync_job_status ON vertex_workspace_sync_job (status, ended_at);

CREATE TABLE IF NOT EXISTS vertex_workspace_thread (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      tenant_id          VARCHAR,
      thread_id          VARCHAR,
      subject            VARCHAR,
      subject_normalized VARCHAR,
      message_count      BIGINT,
      last_message_at    VARCHAR,
      status             VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      props              VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_thread_provider_thread ON vertex_workspace_thread (provider, thread_id);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_thread_last_message ON vertex_workspace_thread (last_message_at);

CREATE TABLE IF NOT EXISTS vertex_workspace_message (
      vertex_id              VARCHAR PRIMARY KEY,
      _seq                   BIGINT,
      created_date           DATE,
      sensitivity_ord        BIGINT,
      owner_did              VARCHAR,
      provider               VARCHAR,
      tenant_id              VARCHAR,
      message_id             VARCHAR,
      thread_id              VARCHAR,
      internet_message_id    VARCHAR,
      subject                VARCHAR,
      subject_normalized     VARCHAR,
      sender_email           VARCHAR,
      sender_name            VARCHAR,
      to_emails              VARCHAR,
      cc_emails              VARCHAR,
      bcc_emails             VARCHAR,
      sent_at                VARCHAR,
      received_at            VARCHAR,
      is_read                BOOLEAN,
      has_attachments        BOOLEAN,
      body_hash              VARCHAR,
      status                 VARCHAR,
      created_at             VARCHAR,
      updated_at             VARCHAR,
      props                  VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_message_provider_message ON vertex_workspace_message (provider, message_id);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_message_thread ON vertex_workspace_message (thread_id);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_message_internet_id ON vertex_workspace_message (internet_message_id);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_message_received ON vertex_workspace_message (received_at);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_message_unread ON vertex_workspace_message (owner_did, is_read);

CREATE TABLE IF NOT EXISTS vertex_workspace_event (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      tenant_id          VARCHAR,
      event_id           VARCHAR,
      calendar_id        VARCHAR,
      i_cal_uid          VARCHAR,
      title              VARCHAR,
      title_normalized   VARCHAR,
      organizer_email    VARCHAR,
      start_at           VARCHAR,
      end_at             VARCHAR,
      timezone           VARCHAR,
      location           VARCHAR,
      attendee_count     BIGINT,
      status             VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      props              VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_event_provider_event ON vertex_workspace_event (provider, event_id);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_event_ical ON vertex_workspace_event (i_cal_uid);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_event_start ON vertex_workspace_event (start_at);

CREATE TABLE IF NOT EXISTS vertex_workspace_contact (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      tenant_id          VARCHAR,
      contact_id         VARCHAR,
      display_name       VARCHAR,
      display_normalized VARCHAR,
      primary_email      VARCHAR,
      phones_e164        VARCHAR,
      company            VARCHAR,
      title              VARCHAR,
      status             VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      props              VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_contact_provider_contact ON vertex_workspace_contact (provider, contact_id);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_contact_primary_email ON vertex_workspace_contact (primary_email);

CREATE TABLE IF NOT EXISTS vertex_workspace_file (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      tenant_id          VARCHAR,
      file_id            VARCHAR,
      parent_file_id     VARCHAR,
      name               VARCHAR,
      name_normalized    VARCHAR,
      mime_type          VARCHAR,
      size_bytes         BIGINT,
      checksum           VARCHAR,
      owner_email        VARCHAR,
      web_url            VARCHAR,
      modified_at        VARCHAR,
      is_folder          BOOLEAN,
      status             VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      props              VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_file_provider_file ON vertex_workspace_file (provider, file_id);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_file_checksum_size ON vertex_workspace_file (checksum, size_bytes);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_file_modified ON vertex_workspace_file (modified_at);

CREATE TABLE IF NOT EXISTS vertex_workspace_file_revision (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      tenant_id          VARCHAR,
      revision_id        VARCHAR,
      file_id            VARCHAR,
      checksum           VARCHAR,
      size_bytes         BIGINT,
      modified_at        VARCHAR,
      modified_by_email  VARCHAR,
      status             VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      props              VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_file_revision_provider_revision ON vertex_workspace_file_revision (provider, revision_id);

CREATE INDEX IF NOT EXISTS idx_vertex_workspace_file_revision_file ON vertex_workspace_file_revision (file_id, modified_at);
