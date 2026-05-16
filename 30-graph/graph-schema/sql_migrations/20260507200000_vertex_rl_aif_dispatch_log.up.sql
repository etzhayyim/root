CREATE TABLE IF NOT EXISTS vertex_rl_aif_dispatch_log (
      vertex_id                VARCHAR PRIMARY KEY,  -- 'aif:dispatch:{actor_did}:{dispatched_at}'

      actor_did                VARCHAR NOT NULL,
      action_nsid              VARCHAR NOT NULL,     -- sampled action (BPMN NSID)
      dispatched_at            TIMESTAMP NOT NULL,

      free_energy_at_dispatch  DOUBLE PRECISION,     -- EFE total at time of dispatch (nullable if no data)
      epsilon                  DOUBLE PRECISION NOT NULL,
      was_exploration          BOOLEAN NOT NULL,     -- true = ε random, false = policy weighted
      dispatch_ok              BOOLEAN NOT NULL,
      dispatch_error           VARCHAR,              -- empty string if ok

      sensitivity_ord          INTEGER DEFAULT 1,
      owner_did                VARCHAR,
      org_id                   VARCHAR,
      user_id                  VARCHAR,
      actor_id                 VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_rl_dispatch_actor
      ON vertex_rl_aif_dispatch_log (actor_did);

CREATE INDEX IF NOT EXISTS idx_rl_dispatch_at
      ON vertex_rl_aif_dispatch_log (dispatched_at);
