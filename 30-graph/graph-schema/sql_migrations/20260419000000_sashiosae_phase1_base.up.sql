CREATE TABLE vertex_atrecord_sashiosae_choushuu_case (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT NOT NULL,
      owner_did       VARCHAR NOT NULL,
      rkey            VARCHAR NOT NULL,
      case_id         VARCHAR NOT NULL,
      authority_did   VARCHAR NOT NULL,
      case_type       VARCHAR NOT NULL,
      status          VARCHAR NOT NULL,
      amount_bucket   VARCHAR NOT NULL,
      period_ym       VARCHAR NOT NULL,
      tax_kind        VARCHAR,
      created_at      TIMESTAMPTZ NOT NULL,
      closed_at       TIMESTAMPTZ
    );

CREATE TABLE vertex_atrecord_sashiosae_notice (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT NOT NULL,
      owner_did       VARCHAR NOT NULL,
      rkey            VARCHAR NOT NULL,
      notice_id       VARCHAR NOT NULL,
      case_id         VARCHAR NOT NULL,
      authority_did   VARCHAR NOT NULL,
      property_type   VARCHAR NOT NULL,
      priority_rank   INTEGER,
      noticed_at      TIMESTAMPTZ NOT NULL,
      effective_at    TIMESTAMPTZ,
      created_at      TIMESTAMPTZ NOT NULL
    );

CREATE TABLE vertex_atrecord_sashiosae_release (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT NOT NULL,
      owner_did       VARCHAR NOT NULL,
      rkey            VARCHAR NOT NULL,
      release_id      VARCHAR NOT NULL,
      notice_id       VARCHAR NOT NULL,
      case_id         VARCHAR NOT NULL,
      authority_did   VARCHAR NOT NULL,
      reason          VARCHAR NOT NULL,
      released_at     TIMESTAMPTZ NOT NULL,
      created_at      TIMESTAMPTZ NOT NULL
    );

CREATE TABLE vertex_atrecord_sashiosae_kanka_result (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      rkey              VARCHAR NOT NULL,
      kanka_id          VARCHAR NOT NULL,
      notice_id         VARCHAR NOT NULL,
      case_id           VARCHAR NOT NULL,
      authority_did     VARCHAR NOT NULL,
      kanka_method      VARCHAR NOT NULL,
      auction_id        VARCHAR NOT NULL,
      property_type     VARCHAR,
      estimated_value   DOUBLE PRECISION,
      scheduled_at      TIMESTAMPTZ NOT NULL,
      venue_url         VARCHAR,
      closed_at         TIMESTAMPTZ,
      clearing_bucket   VARCHAR,
      status            VARCHAR NOT NULL,
      created_at        TIMESTAMPTZ NOT NULL
    );

CREATE INDEX idx_sashiosae_case_authority_period ON vertex_atrecord_sashiosae_choushuu_case (authority_did, period_ym);

CREATE INDEX idx_sashiosae_case_type_status ON vertex_atrecord_sashiosae_choushuu_case (case_type, status);

CREATE INDEX idx_sashiosae_notice_case ON vertex_atrecord_sashiosae_notice (case_id);

CREATE INDEX idx_sashiosae_kanka_scheduled ON vertex_atrecord_sashiosae_kanka_result (scheduled_at, status);

CREATE INDEX idx_sashiosae_kanka_authority ON vertex_atrecord_sashiosae_kanka_result (authority_did, scheduled_at);

CREATE MATERIALIZED VIEW mv_sashiosae_stats_by_type AS
    SELECT
      case_type,
      authority_did,
      period_ym,
      amount_bucket,
      status,
      COUNT(*) AS case_count
    FROM vertex_atrecord_sashiosae_choushuu_case
    GROUP BY case_type, authority_did, period_ym, amount_bucket, status;

CREATE TABLE edge_sashiosae_case_notice (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR NOT NULL,
      dst_vid          VARCHAR NOT NULL,
      _seq             BIGINT NOT NULL,
      owner_did        VARCHAR NOT NULL,
      priority_rank    INTEGER,
      created_at       TIMESTAMPTZ NOT NULL
    );

CREATE INDEX idx_edge_sashiosae_case_notice_src ON edge_sashiosae_case_notice (src_vid);

CREATE INDEX idx_edge_sashiosae_case_notice_dst ON edge_sashiosae_case_notice (dst_vid);

ALTER TABLE vertex_page ADD COLUMN IF NOT EXISTS extracted_for_sashiosae TIMESTAMPTZ;
