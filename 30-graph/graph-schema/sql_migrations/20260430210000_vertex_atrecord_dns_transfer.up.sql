CREATE TABLE vertex_atrecord_dns_transfer_request (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      rkey               VARCHAR NOT NULL,
      domain             VARCHAR NOT NULL,
      from_registrar     VARCHAR NOT NULL,
      to_registrar       VARCHAR NOT NULL,
      requester_did      VARCHAR NOT NULL,
      cf_registrar_did   VARCHAR NOT NULL,
      sq_exporter_did    VARCHAR NOT NULL,
      project_convo_id   VARCHAR NOT NULL,
      status             VARCHAR NOT NULL,
      approvals_json     VARCHAR NOT NULL,
      requested_at       TIMESTAMPTZ NOT NULL,
      record_json        VARCHAR NOT NULL
    );

CREATE TABLE vertex_atrecord_dns_transfer_outcome (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT NOT NULL,
      owner_did            VARCHAR NOT NULL,
      rkey                 VARCHAR NOT NULL,
      transfer_request_uri VARCHAR,
      domain               VARCHAR NOT NULL,
      result               VARCHAR NOT NULL,
      zone_did             VARCHAR,
      cloudflare_zone_id   VARCHAR,
      failure_reason       VARCHAR,
      rollback_steps_json  VARCHAR NOT NULL,
      completed_at         TIMESTAMPTZ NOT NULL,
      record_json          VARCHAR NOT NULL
    );

CREATE TABLE vertex_atrecord_dns_ownership_transfer (
      vertex_id      VARCHAR PRIMARY KEY,
      _seq           BIGINT NOT NULL,
      owner_did      VARCHAR NOT NULL,
      domain         VARCHAR NOT NULL,
      from_registrar VARCHAR NOT NULL,
      to_registrar   VARCHAR NOT NULL,
      zone_did       VARCHAR NOT NULL,
      transfer_date  TIMESTAMPTZ NOT NULL,
      status         VARCHAR NOT NULL,
      record_json    VARCHAR NOT NULL
    );

CREATE INDEX idx_dns_transfer_request_domain ON vertex_atrecord_dns_transfer_request (domain, requested_at DESC);

CREATE INDEX idx_dns_transfer_outcome_domain ON vertex_atrecord_dns_transfer_outcome (domain, completed_at DESC);

CREATE INDEX idx_dns_ownership_domain ON vertex_atrecord_dns_ownership_transfer (domain, transfer_date DESC);
