CREATE TABLE IF NOT EXISTS vertex_malak_phishing_trap (
      vertex_id        VARCHAR PRIMARY KEY,
      rkey             VARCHAR NOT NULL,
      repo             VARCHAR NOT NULL,
      trap_id          VARCHAR NOT NULL,
      trap_kind        VARCHAR NOT NULL,
      address          VARCHAR NOT NULL,
      provider         VARCHAR NOT NULL,
      label            VARCHAR NOT NULL DEFAULT '',
      legal_basis      VARCHAR NOT NULL,
      retention_policy VARCHAR NOT NULL DEFAULT '',
      status           VARCHAR NOT NULL DEFAULT 'active',
      created_at       VARCHAR NOT NULL,
      updated_at       VARCHAR NOT NULL,
      created_date     DATE NOT NULL,
      sensitivity_ord  BIGINT NOT NULL DEFAULT 100,
      owner_did        VARCHAR NOT NULL,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_did        VARCHAR,
      org_did          VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_malak_trap_message (
      vertex_id           VARCHAR PRIMARY KEY,
      rkey                VARCHAR NOT NULL,
      repo                VARCHAR NOT NULL,
      message_id          VARCHAR NOT NULL,
      evidence_id         VARCHAR NOT NULL,
      trap_id             VARCHAR NOT NULL DEFAULT '',
      trap_kind           VARCHAR NOT NULL,
      recipient           VARCHAR NOT NULL,
      provider            VARCHAR NOT NULL,
      provider_message_id VARCHAR NOT NULL DEFAULT '',
      sender              VARCHAR NOT NULL,
      subject             VARCHAR NOT NULL DEFAULT '',
      body_preview        VARCHAR NOT NULL,
      urls_json           VARCHAR NOT NULL,
      headers_json        VARCHAR NOT NULL DEFAULT '',
      raw_payload_hash    VARCHAR NOT NULL DEFAULT '',
      payload_hash        VARCHAR NOT NULL,
      tlp                 VARCHAR NOT NULL DEFAULT 'amber',
      received_at         VARCHAR NOT NULL,
      created_at          VARCHAR NOT NULL,
      created_date        DATE NOT NULL,
      sensitivity_ord     BIGINT NOT NULL DEFAULT 100,
      owner_did           VARCHAR NOT NULL,
      org_id              VARCHAR,
      user_id             VARCHAR,
      actor_did           VARCHAR,
      org_did             VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_malak_phishing_trap_address
      ON vertex_malak_phishing_trap (trap_kind, address);

CREATE INDEX IF NOT EXISTS idx_malak_trap_message_evidence
      ON vertex_malak_trap_message (evidence_id);

CREATE INDEX IF NOT EXISTS idx_malak_trap_message_recipient_time
      ON vertex_malak_trap_message (recipient, received_at);

CREATE INDEX IF NOT EXISTS idx_malak_trap_message_sender_time
      ON vertex_malak_trap_message (sender, received_at);

FLUSH;
