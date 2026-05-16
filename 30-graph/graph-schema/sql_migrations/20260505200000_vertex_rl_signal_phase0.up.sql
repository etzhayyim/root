CREATE TABLE IF NOT EXISTS vertex_rl_step (
      vertex_id        VARCHAR PRIMARY KEY,   -- 'rl:step:{source_event_id}'
      _seq             BIGINT,
      created_date     DATE,

      -- Episode boundary (callerDid = conversation thread = case_id in wellbecoming)
      episode_id       VARCHAR NOT NULL,

      -- The inference action that was taken
      action_nsid      VARCHAR DEFAULT 'wellbecoming.agent.loop',

      -- Reward components (ADR-2604291800 lexicographic objective)
      reward_floor     BOOLEAN NOT NULL,      -- TRUE = floor safe (NOT floor_violated)
      reward_spirit    DOUBLE PRECISION,      -- 0.0–1.0 spirit healing score
      reward_eta       DOUBLE PRECISION,      -- 0.0–1.0 Shannon η proxy (from separation_delta)
      reward_scalar    DOUBLE PRECISION NOT NULL, -- composite U_total

      -- Provenance
      source           VARCHAR DEFAULT 'server',  -- 'server' | 'murakumo' | 'ameno'
      source_event_id  VARCHAR,               -- FK to vertex_wellbecoming_event.vertex_id
      actor_did        VARCHAR,               -- agent_did from the event
      model            VARCHAR,               -- model used for inference

      -- RLS
      sensitivity_ord  INTEGER DEFAULT 1,
      owner_did        VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,

      created_at       TIMESTAMP NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_rl_step_actor
      ON vertex_rl_step (actor_did);

CREATE INDEX IF NOT EXISTS idx_rl_step_episode
      ON vertex_rl_step (episode_id);

CREATE INDEX IF NOT EXISTS idx_rl_step_created
      ON vertex_rl_step (created_at);

CREATE TABLE IF NOT EXISTS vertex_rl_collect_cursor (
      vertex_id        VARCHAR PRIMARY KEY,   -- 'rl:collect:cursor'
      last_event_ts    TIMESTAMP DEFAULT '2024-01-01 00:00:00',
      last_step_count  BIGINT DEFAULT 0,
      total_collected  BIGINT DEFAULT 0,
      updated_at       TIMESTAMP NOT NULL
    );

CREATE TABLE IF NOT EXISTS vertex_model_checkpoint (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,

      actor_did        VARCHAR NOT NULL,
      base_model       VARCHAR NOT NULL,      -- e.g. 'gemma-3-4b-it'
      algorithm        VARCHAR DEFAULT 'dpo', -- 'dpo' | 'grpo'
      epoch            INTEGER NOT NULL DEFAULT 0,
      b2_key           VARCHAR NOT NULL,      -- B2 object path to adapter .safetensors

      eval_wellbecoming DOUBLE PRECISION,
      eval_eta          DOUBLE PRECISION,
      train_steps       INTEGER,
      train_loss        DOUBLE PRECISION,

      deployed_murakumo  BOOLEAN DEFAULT FALSE,
      deployed_ameno     BOOLEAN DEFAULT FALSE,

      -- RLS
      sensitivity_ord  INTEGER DEFAULT 1,
      owner_did        VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,

      created_at       TIMESTAMP NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_model_ckpt_actor
      ON vertex_model_checkpoint (actor_did, epoch);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_rl_actor_performance AS
    SELECT
      actor_did,
      COUNT(*)                                            AS total_steps,
      AVG(reward_scalar)                                  AS mean_reward,
      AVG(reward_eta)     FILTER (WHERE reward_eta IS NOT NULL) AS mean_eta,
      AVG(reward_spirit)  FILTER (WHERE reward_spirit IS NOT NULL) AS mean_spirit,
      SUM(CASE WHEN reward_floor = false THEN 1 ELSE 0 END) AS floor_violations,
      MAX(created_at)                                     AS last_step_at
    FROM vertex_rl_step
    WHERE created_at > NOW() - INTERVAL '24 hours'
    GROUP BY actor_did;
