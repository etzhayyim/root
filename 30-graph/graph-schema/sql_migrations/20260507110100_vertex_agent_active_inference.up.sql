CREATE TABLE IF NOT EXISTS vertex_agent_observation (
      vertex_id        VARCHAR PRIMARY KEY,
      agent_did        VARCHAR NOT NULL,
      source_kind      VARCHAR NOT NULL,
      source_ref       VARCHAR,
      observed_at      VARCHAR NOT NULL,
      payload_json     VARCHAR NOT NULL,
      confidence       DOUBLE PRECISION NOT NULL,
      uncertainty      DOUBLE PRECISION NOT NULL,
      sensitivity_ord  BIGINT DEFAULT 1,
      actor_id         VARCHAR,
      owner_did        VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_agent_observation_agent_time ON vertex_agent_observation (agent_did, observed_at);

CREATE INDEX IF NOT EXISTS idx_agent_observation_source ON vertex_agent_observation (source_kind, source_ref);

CREATE TABLE IF NOT EXISTS vertex_agent_belief_state (
      vertex_id                  VARCHAR PRIMARY KEY,
      agent_did                  VARCHAR NOT NULL,
      belief_kind                VARCHAR NOT NULL,
      state_key                  VARCHAR NOT NULL,
      state_value_json           VARCHAR NOT NULL,
      posterior_confidence       DOUBLE PRECISION NOT NULL,
      posterior_entropy          DOUBLE PRECISION NOT NULL,
      updated_from_observation   VARCHAR,
      updated_at                 VARCHAR NOT NULL,
      sensitivity_ord            BIGINT DEFAULT 1,
      actor_id                   VARCHAR,
      owner_did                  VARCHAR,
      org_id                     VARCHAR,
      user_id                    VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_agent_belief_agent_key ON vertex_agent_belief_state (agent_did, belief_kind, state_key);

CREATE TABLE IF NOT EXISTS vertex_agent_prior_preference (
      vertex_id          VARCHAR PRIMARY KEY,
      agent_did          VARCHAR NOT NULL,
      preference_key     VARCHAR NOT NULL,
      target_range_json  VARCHAR NOT NULL,
      hard_floor         BOOLEAN NOT NULL DEFAULT false,
      weight             DOUBLE PRECISION NOT NULL DEFAULT 1.0,
      depends_on_adr     VARCHAR,
      active             BOOLEAN NOT NULL DEFAULT true,
      created_at         VARCHAR NOT NULL,
      updated_at         VARCHAR NOT NULL,
      sensitivity_ord    BIGINT DEFAULT 1,
      actor_id           VARCHAR,
      owner_did          VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_agent_prior_active ON vertex_agent_prior_preference (agent_did, active, preference_key);

CREATE TABLE IF NOT EXISTS vertex_agent_active_inference_tick (
      vertex_id                  VARCHAR PRIMARY KEY,
      agent_did                  VARCHAR NOT NULL,
      tick_kind                  VARCHAR NOT NULL,
      belief_snapshot_hash       VARCHAR NOT NULL,
      candidate_actions_json     VARCHAR NOT NULL,
      expected_free_energy_json  VARCHAR NOT NULL,
      selected_action_id         VARCHAR,
      mokuteki_gate_pass         BOOLEAN NOT NULL DEFAULT false,
      created_at                 VARCHAR NOT NULL,
      sensitivity_ord            BIGINT DEFAULT 1,
      actor_id                   VARCHAR,
      owner_did                  VARCHAR,
      org_id                     VARCHAR,
      user_id                    VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_agent_aif_tick_agent_time ON vertex_agent_active_inference_tick (agent_did, created_at);

CREATE INDEX IF NOT EXISTS idx_agent_aif_tick_kind ON vertex_agent_active_inference_tick (tick_kind, mokuteki_gate_pass);

CREATE TABLE IF NOT EXISTS vertex_agent_action_proposal (
      vertex_id        VARCHAR PRIMARY KEY,
      agent_did        VARCHAR NOT NULL,
      action_kind      VARCHAR NOT NULL,
      target_surface   VARCHAR NOT NULL,
      proposal_json    VARCHAR NOT NULL,
      simulation_ref   VARCHAR,
      approval_ref     VARCHAR,
      safety_state     VARCHAR NOT NULL DEFAULT 'draft',
      dispatch_ref     VARCHAR,
      created_at       VARCHAR NOT NULL,
      updated_at       VARCHAR NOT NULL,
      sensitivity_ord  BIGINT DEFAULT 1,
      actor_id         VARCHAR,
      owner_did        VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_agent_action_agent_state ON vertex_agent_action_proposal (agent_did, safety_state, created_at);

CREATE INDEX IF NOT EXISTS idx_agent_action_kind ON vertex_agent_action_proposal (action_kind, target_surface);

CREATE TABLE IF NOT EXISTS vertex_agent_realworld_effect (
      vertex_id               VARCHAR PRIMARY KEY,
      action_proposal_id      VARCHAR NOT NULL,
      agent_did               VARCHAR NOT NULL,
      principal_did           VARCHAR,
      channel                 VARCHAR NOT NULL,
      effect_class            VARCHAR NOT NULL,
      target_ref_hash         VARCHAR,
      payload_hash            VARCHAR NOT NULL,
      summary                 VARCHAR NOT NULL,
      approval_ref            VARCHAR,
      budget_ref              VARCHAR,
      dispatch_state          VARCHAR NOT NULL,
      dispatch_receipt_ref    VARCHAR,
      observation_plan_json   VARCHAR,
      created_at              VARCHAR NOT NULL,
      updated_at              VARCHAR NOT NULL,
      sensitivity_ord         BIGINT DEFAULT 1,
      actor_id                VARCHAR,
      owner_did               VARCHAR,
      org_id                  VARCHAR,
      user_id                 VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_agent_realworld_action ON vertex_agent_realworld_effect (action_proposal_id);

CREATE INDEX IF NOT EXISTS idx_agent_realworld_agent_state ON vertex_agent_realworld_effect (agent_did, dispatch_state, updated_at);

CREATE INDEX IF NOT EXISTS idx_agent_realworld_channel ON vertex_agent_realworld_effect (channel, effect_class);

CREATE TABLE IF NOT EXISTS vertex_agent_homeostasis_snapshot (
      vertex_id                 VARCHAR PRIMARY KEY,
      agent_did                 VARCHAR NOT NULL,
      compute_budget_remaining  DOUBLE PRECISION NOT NULL,
      storage_pressure          DOUBLE PRECISION NOT NULL,
      lease_seconds_remaining   BIGINT NOT NULL,
      error_rate_1h             DOUBLE PRECISION NOT NULL,
      tool_success_rate_1h      DOUBLE PRECISION NOT NULL,
      energy_or_cost_proxy      DOUBLE PRECISION NOT NULL,
      viability_state           VARCHAR NOT NULL,
      created_at                VARCHAR NOT NULL,
      sensitivity_ord           BIGINT DEFAULT 1,
      actor_id                  VARCHAR,
      owner_did                 VARCHAR,
      org_id                    VARCHAR,
      user_id                   VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_agent_homeostasis_agent_time ON vertex_agent_homeostasis_snapshot (agent_did, created_at);

CREATE INDEX IF NOT EXISTS idx_agent_homeostasis_state ON vertex_agent_homeostasis_snapshot (viability_state);
