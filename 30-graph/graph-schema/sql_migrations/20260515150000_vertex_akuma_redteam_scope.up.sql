-- ADR-2605151400 — akuma authorized red team actor.
-- 4 append-only tables backing com.etzhayyim.apps.akuma.{registerScope,
-- approveScope, runProbe, recordFinding} XRPC. RisingWave-friendly
-- (varchar/bigint, no JSONB, no soft delete).

-- vertex_akuma_scope: owner-attested + amanomibashira-approved target set.
CREATE TABLE IF NOT EXISTS vertex_akuma_scope (
  vertex_id              VARCHAR PRIMARY KEY,
  _seq                   BIGINT,
  created_date           DATE,
  sensitivity_ord        BIGINT,
  owner_did              VARCHAR,
  repo                   VARCHAR,
  scope_id               VARCHAR NOT NULL,
  status                 VARCHAR NOT NULL,
  target_kind            VARCHAR NOT NULL,
  targets                VARCHAR,
  excluded_targets       VARCHAR,
  allowed_ports          VARCHAR,
  allowed_paths          VARCHAR,
  intrusiveness_tier     VARCHAR NOT NULL,
  valid_from_ms          BIGINT NOT NULL,
  valid_until_ms         BIGINT NOT NULL,
  rate_limit_rps         BIGINT,
  legal_basis            VARCHAR,
  authority_did          VARCHAR,
  owner_signature        VARCHAR,
  authority_signature    VARCHAR,
  payload_hash           VARCHAR,
  approved_at_ms         BIGINT,
  revoked_at_ms          BIGINT,
  revoked_by_did         VARCHAR,
  revoke_reason          VARCHAR,
  actor_did              VARCHAR,
  actor_id               VARCHAR,
  created_at             VARCHAR NOT NULL
);

-- vertex_akuma_probe: a single probe execution attempt.
CREATE TABLE IF NOT EXISTS vertex_akuma_probe (
  vertex_id              VARCHAR PRIMARY KEY,
  _seq                   BIGINT,
  created_date           DATE,
  sensitivity_ord        BIGINT,
  owner_did              VARCHAR,
  repo                   VARCHAR,
  probe_id               VARCHAR NOT NULL,
  scope_id               VARCHAR NOT NULL,
  tool                   VARCHAR NOT NULL,
  target                 VARCHAR NOT NULL,
  port                   BIGINT,
  intrusiveness          VARCHAR NOT NULL,
  tool_args              VARCHAR,
  status                 VARCHAR NOT NULL,
  started_at_ms          BIGINT,
  completed_at_ms        BIGINT,
  exit_code              BIGINT,
  output_bytes           BIGINT,
  vault_ciphertext_cid   VARCHAR,
  actor_did              VARCHAR,
  actor_id               VARCHAR,
  created_at             VARCHAR NOT NULL
);

-- vertex_akuma_finding: probe-derived finding metadata.
-- Raw payload lives in vault.etzhayyim.com under vault_ciphertext_cid.
CREATE TABLE IF NOT EXISTS vertex_akuma_finding (
  vertex_id              VARCHAR PRIMARY KEY,
  _seq                   BIGINT,
  created_date           DATE,
  sensitivity_ord        BIGINT,
  owner_did              VARCHAR,
  repo                   VARCHAR,
  finding_id             VARCHAR NOT NULL,
  scope_id               VARCHAR NOT NULL,
  probe_uri              VARCHAR NOT NULL,
  target                 VARCHAR NOT NULL,
  severity               VARCHAR NOT NULL,
  summary                VARCHAR,
  cve_ids                VARCHAR,
  cvss_score_centile     BIGINT,
  vault_ciphertext_cid   VARCHAR NOT NULL,
  status                 VARCHAR NOT NULL,
  remediated_at_ms       BIGINT,
  remediation_note       VARCHAR,
  verify_probe_uri       VARCHAR,
  verify_status          VARCHAR,
  actor_did              VARCHAR,
  actor_id               VARCHAR,
  created_at             VARCHAR NOT NULL
);

-- vertex_akuma_audit: every runProbe attempt (allow or deny) is appended.
-- Used by the Rego policy gate (rate budget query) and for forensic
-- review. Hard delete only via authority-signed deletion record.
CREATE TABLE IF NOT EXISTS vertex_akuma_audit (
  vertex_id              VARCHAR PRIMARY KEY,
  _seq                   BIGINT,
  created_date           DATE,
  sensitivity_ord        BIGINT,
  owner_did              VARCHAR,
  repo                   VARCHAR,
  audit_id               VARCHAR NOT NULL,
  scope_id               VARCHAR NOT NULL,
  target                 VARCHAR NOT NULL,
  tool                   VARCHAR NOT NULL,
  intrusiveness          VARCHAR NOT NULL,
  allowed                BOOLEAN NOT NULL,
  reason                 VARCHAR NOT NULL,
  attempted_at_ms        BIGINT NOT NULL,
  caller_did             VARCHAR,
  request_id             VARCHAR,
  actor_did              VARCHAR,
  actor_id               VARCHAR,
  created_at             VARCHAR NOT NULL
);

-- Indexes (created in a separate phase per RW catalog visibility note in
-- 30-graph/graph-schema/CLAUDE.md "Multi-Head Alembic Workaround").
CREATE INDEX IF NOT EXISTS idx_vertex_akuma_scope_status
  ON vertex_akuma_scope (status);

CREATE INDEX IF NOT EXISTS idx_vertex_akuma_scope_owner
  ON vertex_akuma_scope (owner_did);

CREATE INDEX IF NOT EXISTS idx_vertex_akuma_probe_scope
  ON vertex_akuma_probe (scope_id);

CREATE INDEX IF NOT EXISTS idx_vertex_akuma_finding_scope_status
  ON vertex_akuma_finding (scope_id, status);

CREATE INDEX IF NOT EXISTS idx_vertex_akuma_audit_scope_target_ts
  ON vertex_akuma_audit (scope_id, target, attempted_at_ms);
