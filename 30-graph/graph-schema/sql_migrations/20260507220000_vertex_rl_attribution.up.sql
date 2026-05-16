ALTER TABLE vertex_rl_step
      ADD COLUMN IF NOT EXISTS triggered_by_dispatch VARCHAR;

ALTER TABLE vertex_rl_aif_dispatch_log
      ADD COLUMN IF NOT EXISTS outcome_step_id VARCHAR;

CREATE INDEX IF NOT EXISTS idx_rl_dispatch_outcome
      ON vertex_rl_aif_dispatch_log (outcome_step_id);

CREATE INDEX IF NOT EXISTS idx_rl_step_dispatch
      ON vertex_rl_step (triggered_by_dispatch);
