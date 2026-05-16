ALTER TABLE vertex_agent_realworld_effect
    ADD COLUMN IF NOT EXISTS authority_ref VARCHAR;

ALTER TABLE vertex_agent_action_proposal
    ADD COLUMN IF NOT EXISTS authority_ref VARCHAR;

CREATE TABLE IF NOT EXISTS vertex_agent_delegated_authority_policy (
      vertex_id               VARCHAR PRIMARY KEY,
      authority_ref           VARCHAR NOT NULL,
      policy_ref              VARCHAR NOT NULL,
      agent_did               VARCHAR NOT NULL,
      principal_did           VARCHAR,
      channels_json           VARCHAR NOT NULL,
      effect_classes_json     VARCHAR NOT NULL,
      target_bindings_json    VARCHAR NOT NULL,
      payload_constraints_json VARCHAR NOT NULL,
      budget_ref              VARCHAR,
      rate_limit_json         VARCHAR NOT NULL,
      expires_at              VARCHAR NOT NULL,
      policy_cid              VARCHAR,
      signature_ref           VARCHAR NOT NULL,
      status                  VARCHAR NOT NULL,
      created_at              VARCHAR NOT NULL,
      updated_at              VARCHAR NOT NULL,
      sensitivity_ord         BIGINT DEFAULT 1,
      actor_id                VARCHAR,
      owner_did               VARCHAR,
      org_id                  VARCHAR,
      user_id                 VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_agent_authority_policy_ref
    ON vertex_agent_delegated_authority_policy (authority_ref, policy_ref, status);

CREATE INDEX IF NOT EXISTS idx_agent_authority_policy_agent
    ON vertex_agent_delegated_authority_policy (agent_did, status, expires_at);
