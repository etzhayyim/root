CREATE TABLE IF NOT EXISTS vertex_rl_aif_model (
      vertex_id         VARCHAR PRIMARY KEY,  -- 'aif:model:{actor_did}:{action_nsid_slug}'

      actor_did         VARCHAR NOT NULL,
      action_nsid       VARCHAR NOT NULL,

      -- Matrices stored as JSON-encoded 2D/3D arrays (RisingWave has no JSONB)
      A_json            VARCHAR NOT NULL,      -- [[float]] shape (n_obs, n_states)
      B_json            VARCHAR NOT NULL,      -- [[[float]]] shape (n_states, n_states, n_actions)
      C_json            VARCHAR NOT NULL,      -- [float] shape (n_obs,) — log preferences
      D_json            VARCHAR NOT NULL,      -- [float] shape (n_states,) — state prior
      E_json            VARCHAR NOT NULL,      -- [float] shape (n_actions,) — action prior

      -- Dirichlet sufficient statistics for online learning
      A_counts_json     VARCHAR NOT NULL,      -- [[float]] same shape as A
      B_counts_json     VARCHAR NOT NULL,      -- [[[float]]] same shape as B

      n_obs             INTEGER NOT NULL,      -- = 50 (2×5×5 flattened)
      n_states          INTEGER NOT NULL,      -- = 4
      n_actions         INTEGER NOT NULL,      -- action index size for this model

      -- Maps action_nsid to index 0..n_actions-1
      action_index_json VARCHAR NOT NULL,      -- {"ai.gftd.apps.foo.bar": 0, ...}

      version           INTEGER DEFAULT 1,
      updated_at        TIMESTAMP NOT NULL,

      sensitivity_ord   INTEGER DEFAULT 1,
      owner_did         VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_aif_model_actor
      ON vertex_rl_aif_model (actor_did);

CREATE TABLE IF NOT EXISTS vertex_rl_aif_belief (
      vertex_id         VARCHAR PRIMARY KEY,  -- 'aif:belief:{step_id}'

      episode_id        VARCHAR NOT NULL,
      actor_did         VARCHAR NOT NULL,
      step_id           VARCHAR NOT NULL,     -- FK vertex_rl_step.vertex_id

      -- q(s) = categorical distribution over hidden states
      belief_json       VARCHAR NOT NULL,     -- [float] shape (n_states,) sums to 1.0
      free_energy       DOUBLE PRECISION NOT NULL,

      updated_at        TIMESTAMP NOT NULL,

      sensitivity_ord   INTEGER DEFAULT 1,
      owner_did         VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_aif_belief_actor
      ON vertex_rl_aif_belief (actor_did);

CREATE INDEX IF NOT EXISTS idx_aif_belief_step
      ON vertex_rl_aif_belief (step_id);

CREATE TABLE IF NOT EXISTS vertex_rl_aif_efe (
      vertex_id         VARCHAR PRIMARY KEY,  -- 'aif:efe:{step_id}:{action_nsid_slug}'

      episode_id        VARCHAR NOT NULL,
      actor_did         VARCHAR NOT NULL,
      step_id           VARCHAR NOT NULL,
      action_nsid       VARCHAR NOT NULL,

      -- G(a) decomposition
      efe_total         DOUBLE PRECISION NOT NULL,   -- G = -pragmatic - epistemic
      pragmatic_value   DOUBLE PRECISION NOT NULL,   -- E_q[C(o)] under policy a
      epistemic_value   DOUBLE PRECISION NOT NULL,   -- I(o;s|a) = H[P(o)] - E_s[H[A[:,s]]]

      -- Softmax(-γ·G) — γ=16.0 precision parameter
      policy_prob       DOUBLE PRECISION NOT NULL,

      -- Full G vector across all actions for this step (compact storage)
      all_efe_json      VARCHAR NOT NULL,     -- {"nsid": efe_total, ...}

      created_at        TIMESTAMP NOT NULL,

      sensitivity_ord   INTEGER DEFAULT 1,
      owner_did         VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_aif_efe_actor
      ON vertex_rl_aif_efe (actor_did);

CREATE INDEX IF NOT EXISTS idx_aif_efe_step
      ON vertex_rl_aif_efe (step_id);

CREATE TABLE IF NOT EXISTS vertex_rl_aif_obs_cursor (
      vertex_id         VARCHAR PRIMARY KEY,  -- 'aif:cursor:{actor_did}:{action_nsid_slug}'

      actor_did         VARCHAR NOT NULL,
      action_nsid       VARCHAR NOT NULL,
      last_step_ts      VARCHAR NOT NULL DEFAULT '',
      steps_processed   BIGINT DEFAULT 0,

      updated_at        TIMESTAMP NOT NULL
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_rl_aif_actor_stats AS
    SELECT
      b.actor_did,
      COUNT(*)                              AS total_beliefs,
      AVG(b.free_energy)                   AS mean_free_energy,
      MIN(b.free_energy)                   AS min_free_energy,
      MAX(b.free_energy)                   AS max_free_energy,
      MAX(b.updated_at)                    AS last_belief_at
    FROM vertex_rl_aif_belief b
    GROUP BY b.actor_did;
