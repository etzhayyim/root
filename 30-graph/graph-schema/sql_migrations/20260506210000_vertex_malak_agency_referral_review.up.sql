CREATE TABLE IF NOT EXISTS vertex_malak_agency_referral_review (
      vertex_id         VARCHAR PRIMARY KEY,
      rkey              VARCHAR NOT NULL,
      repo              VARCHAR NOT NULL,
      review_id         VARCHAR NOT NULL,
      referral_id       VARCHAR NOT NULL,
      decision          VARCHAR NOT NULL,
      draft_state       VARCHAR NOT NULL,
      reviewer_did      VARCHAR NOT NULL,
      reviewer_role     VARCHAR NOT NULL DEFAULT '',
      reason            VARCHAR NOT NULL,
      approval_ref      VARCHAR NOT NULL DEFAULT '',
      external_case_ref VARCHAR NOT NULL DEFAULT '',
      notes             VARCHAR NOT NULL DEFAULT '',
      payload_hash      VARCHAR NOT NULL,
      created_at        VARCHAR NOT NULL,
      created_date      DATE NOT NULL,
      sensitivity_ord   BIGINT NOT NULL DEFAULT 100,
      owner_did         VARCHAR NOT NULL,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_did         VARCHAR,
      org_did           VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_malak_agency_referral_review_referral_time
      ON vertex_malak_agency_referral_review (referral_id, created_at);

CREATE INDEX IF NOT EXISTS idx_malak_agency_referral_review_decision_time
      ON vertex_malak_agency_referral_review (decision, created_at);

FLUSH;
