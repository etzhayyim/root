CREATE TABLE IF NOT EXISTS vertex_kaisya_task (
      vertex_id        VARCHAR PRIMARY KEY,
      agent_id         VARCHAR NOT NULL,   -- kaisya_ceo_agent etc.
      human_did        VARCHAR NOT NULL,   -- responsible approver DID
      title            VARCHAR NOT NULL,
      context_json     VARCHAR,            -- JSON blob (task details, links)
      priority         INTEGER DEFAULT 2,  -- 1=critical 2=normal 3=low
      status           VARCHAR NOT NULL DEFAULT 'pending',
      -- 'pending' | 'approved' | 'rejected' | 'expired'
      due_at           TIMESTAMP,
      resolved_at      TIMESTAMP,
      resolved_by      VARCHAR,
      resolution_note  VARCHAR,

      -- RLS 3-col
      owner_did        VARCHAR NOT NULL,
      org_id           VARCHAR NOT NULL,
      user_id          VARCHAR NOT NULL,

      sensitivity_ord  INTEGER NOT NULL DEFAULT 1,
      actor_id         VARCHAR,
      created_at       TIMESTAMP NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_kaisya_task_human
      ON vertex_kaisya_task (human_did, status, created_at);

CREATE INDEX IF NOT EXISTS idx_kaisya_task_agent
      ON vertex_kaisya_task (agent_id, status);

CREATE TABLE IF NOT EXISTS vertex_kaisya_agent_run (
      vertex_id        VARCHAR PRIMARY KEY,
      agent_id         VARCHAR NOT NULL,   -- kaisya_ceo_agent etc.
      process_id       VARCHAR NOT NULL,   -- BPMN processId
      task_type        VARCHAR NOT NULL,   -- dailyBriefing / deployHealthCheck etc.
      human_did        VARCHAR NOT NULL,   -- associated human
      status           VARCHAR NOT NULL DEFAULT 'ok',
      -- 'ok' | 'partial' | 'error'
      output_summary   VARCHAR,
      tasks_created    BIGINT DEFAULT 0,
      ran_at           TIMESTAMP NOT NULL,

      -- RLS 3-col
      owner_did        VARCHAR NOT NULL,
      org_id           VARCHAR NOT NULL,
      user_id          VARCHAR NOT NULL,

      sensitivity_ord  INTEGER NOT NULL DEFAULT 1,
      actor_id         VARCHAR,
      created_at       TIMESTAMP NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_kaisya_run_agent
      ON vertex_kaisya_agent_run (agent_id, ran_at);

CREATE INDEX IF NOT EXISTS idx_kaisya_run_human
      ON vertex_kaisya_agent_run (human_did, ran_at);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kaisya_pending_count AS
    SELECT
      human_did,
      COUNT(*)                                    AS pending_count,
      COUNT(*) FILTER (WHERE priority = 1)        AS critical_count,
      MIN(due_at)                                 AS earliest_due_at,
      MAX(created_at)                             AS latest_task_at
    FROM vertex_kaisya_task
    WHERE status = 'pending'
    GROUP BY human_did;
