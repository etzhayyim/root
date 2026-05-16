CREATE TABLE IF NOT EXISTS edge_workspace_account_has_message (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      linked_at          VARCHAR,
      relation_status    VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_workspace_account_has_message_src ON edge_workspace_account_has_message (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_workspace_account_has_message_dst ON edge_workspace_account_has_message (dst_vid);

CREATE TABLE IF NOT EXISTS edge_workspace_message_in_thread (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      linked_at          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_workspace_message_in_thread_src ON edge_workspace_message_in_thread (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_workspace_message_in_thread_dst ON edge_workspace_message_in_thread (dst_vid);

CREATE TABLE IF NOT EXISTS edge_workspace_message_from_contact (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      linked_at          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_workspace_message_from_contact_src ON edge_workspace_message_from_contact (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_workspace_message_from_contact_dst ON edge_workspace_message_from_contact (dst_vid);

CREATE TABLE IF NOT EXISTS edge_workspace_message_to_contact (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      recipient_kind     VARCHAR,
      linked_at          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_workspace_message_to_contact_src ON edge_workspace_message_to_contact (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_workspace_message_to_contact_dst ON edge_workspace_message_to_contact (dst_vid);

CREATE TABLE IF NOT EXISTS edge_workspace_account_has_event (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      linked_at          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_workspace_account_has_event_src ON edge_workspace_account_has_event (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_workspace_account_has_event_dst ON edge_workspace_account_has_event (dst_vid);

CREATE TABLE IF NOT EXISTS edge_workspace_event_attendee_contact (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      attendee_status    VARCHAR,
      linked_at          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_workspace_event_attendee_contact_src ON edge_workspace_event_attendee_contact (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_workspace_event_attendee_contact_dst ON edge_workspace_event_attendee_contact (dst_vid);

CREATE TABLE IF NOT EXISTS edge_workspace_account_has_file (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      linked_at          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_workspace_account_has_file_src ON edge_workspace_account_has_file (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_workspace_account_has_file_dst ON edge_workspace_account_has_file (dst_vid);

CREATE TABLE IF NOT EXISTS edge_workspace_file_shared_with_contact (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      permission         VARCHAR,
      linked_at          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_workspace_file_shared_with_contact_src ON edge_workspace_file_shared_with_contact (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_workspace_file_shared_with_contact_dst ON edge_workspace_file_shared_with_contact (dst_vid);

CREATE TABLE IF NOT EXISTS edge_workspace_file_has_revision (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      provider           VARCHAR,
      linked_at          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_workspace_file_has_revision_src ON edge_workspace_file_has_revision (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_workspace_file_has_revision_dst ON edge_workspace_file_has_revision (dst_vid);

CREATE TABLE IF NOT EXISTS edge_workspace_same_as (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      src_provider       VARCHAR,
      dst_provider       VARCHAR,
      entity_kind        VARCHAR,
      confidence         DOUBLE PRECISION,
      match_method       VARCHAR,
      needs_review       BOOLEAN,
      matched_at         VARCHAR,
      linked_at          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_workspace_same_as_src ON edge_workspace_same_as (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_workspace_same_as_dst ON edge_workspace_same_as (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_workspace_same_as_confidence ON edge_workspace_same_as (entity_kind, confidence);
