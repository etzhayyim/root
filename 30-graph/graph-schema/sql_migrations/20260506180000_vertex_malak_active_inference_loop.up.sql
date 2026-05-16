CREATE TABLE IF NOT EXISTS vertex_malak_investigation_tick (
      vertex_id                  VARCHAR PRIMARY KEY,
      rkey                       VARCHAR NOT NULL,
      repo                       VARCHAR NOT NULL,
      actor_id                   VARCHAR NOT NULL,
      case_id                    VARCHAR,
      tick_kind                  VARCHAR NOT NULL,
      observation_refs_json      VARCHAR NOT NULL,
      candidate_actions_json     VARCHAR NOT NULL,
      expected_free_energy_json  VARCHAR NOT NULL,
      selected_action_id         VARCHAR,
      rejected_actions_json      VARCHAR NOT NULL,
      attribution_confidence     DOUBLE PRECISION NOT NULL DEFAULT 0,
      legal_basis                VARCHAR NOT NULL DEFAULT '',
      approval_ref               VARCHAR NOT NULL DEFAULT '',
      gate_pass                  BOOLEAN NOT NULL DEFAULT false,
      created_at                 VARCHAR NOT NULL,
      created_date               DATE NOT NULL,
      sensitivity_ord            BIGINT NOT NULL DEFAULT 100,
      owner_did                  VARCHAR NOT NULL,
      org_id                     VARCHAR,
      user_id                    VARCHAR,
      actor_did                  VARCHAR,
      org_did                    VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_malak_agency_referral_draft (
      vertex_id              VARCHAR PRIMARY KEY,
      rkey                   VARCHAR NOT NULL,
      repo                   VARCHAR NOT NULL,
      referral_id            VARCHAR NOT NULL,
      case_id                VARCHAR NOT NULL,
      actor_id               VARCHAR NOT NULL,
      agency                 VARCHAR NOT NULL,
      referral_kind          VARCHAR NOT NULL,
      tlp                    VARCHAR NOT NULL,
      attribution_confidence DOUBLE PRECISION NOT NULL,
      legal_basis            VARCHAR NOT NULL,
      approval_ref           VARCHAR NOT NULL,
      evidence_ids_json      VARCHAR NOT NULL,
      summary                VARCHAR NOT NULL,
      payload_hash           VARCHAR NOT NULL,
      draft_state            VARCHAR NOT NULL DEFAULT 'draft',
      created_at             VARCHAR NOT NULL,
      updated_at             VARCHAR NOT NULL,
      created_date           DATE NOT NULL,
      sensitivity_ord        BIGINT NOT NULL DEFAULT 100,
      owner_did              VARCHAR NOT NULL,
      org_id                 VARCHAR,
      user_id                VARCHAR,
      actor_did              VARCHAR,
      org_did                VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_malak_investigation_tick_actor_time
      ON vertex_malak_investigation_tick (actor_id, created_at);

CREATE INDEX IF NOT EXISTS idx_malak_investigation_tick_case_time
      ON vertex_malak_investigation_tick (case_id, created_at);

CREATE INDEX IF NOT EXISTS idx_malak_investigation_tick_selected
      ON vertex_malak_investigation_tick (selected_action_id, gate_pass);

CREATE INDEX IF NOT EXISTS idx_malak_agency_referral_actor_state
      ON vertex_malak_agency_referral_draft (actor_id, draft_state, created_at);

CREATE INDEX IF NOT EXISTS idx_malak_agency_referral_case
      ON vertex_malak_agency_referral_draft (case_id);

FLUSH;
