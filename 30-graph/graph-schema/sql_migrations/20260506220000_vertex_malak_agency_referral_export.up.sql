CREATE TABLE IF NOT EXISTS vertex_malak_agency_referral_export (
      vertex_id          VARCHAR PRIMARY KEY,
      rkey               VARCHAR NOT NULL,
      repo               VARCHAR NOT NULL,
      package_id         VARCHAR NOT NULL,
      referral_id        VARCHAR NOT NULL,
      package_format     VARCHAR NOT NULL,
      payload_hash       VARCHAR NOT NULL,
      transmission_state VARCHAR NOT NULL DEFAULT 'not_transmitted',
      exported_at        VARCHAR NOT NULL,
      created_date       DATE NOT NULL,
      sensitivity_ord    BIGINT NOT NULL DEFAULT 100,
      owner_did          VARCHAR NOT NULL,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_did          VARCHAR,
      org_did            VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_malak_agency_referral_export_referral_time
      ON vertex_malak_agency_referral_export (referral_id, exported_at);

CREATE INDEX IF NOT EXISTS idx_malak_agency_referral_export_package
      ON vertex_malak_agency_referral_export (package_id);

CREATE INDEX IF NOT EXISTS idx_malak_agency_referral_export_transmission
      ON vertex_malak_agency_referral_export (transmission_state, exported_at);

FLUSH;
