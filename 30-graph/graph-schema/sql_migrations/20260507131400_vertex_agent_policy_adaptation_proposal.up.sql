CREATE TABLE IF NOT EXISTS vertex_agent_policy_adaptation_proposal (
      vertex_id             VARCHAR PRIMARY KEY,
      agent_did             VARCHAR NOT NULL,
      preference_key        VARCHAR NOT NULL,
      proposal_hash         VARCHAR NOT NULL,
      proposal_json         VARCHAR NOT NULL,
      mokuteki_gate_pass    BOOLEAN NOT NULL DEFAULT false,
      triple_witness_pass   BOOLEAN NOT NULL DEFAULT false,
      blockers_json         VARCHAR NOT NULL,
      proposal_state        VARCHAR NOT NULL,
      created_at            VARCHAR NOT NULL,
      sensitivity_ord       BIGINT DEFAULT 1,
      actor_id              VARCHAR,
      owner_did             VARCHAR,
      org_id                VARCHAR,
      user_id               VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_agent_policy_adaptation_agent_state
    ON vertex_agent_policy_adaptation_proposal (agent_did, proposal_state, created_at);

CREATE INDEX IF NOT EXISTS idx_agent_policy_adaptation_key
    ON vertex_agent_policy_adaptation_proposal (preference_key, proposal_hash);
