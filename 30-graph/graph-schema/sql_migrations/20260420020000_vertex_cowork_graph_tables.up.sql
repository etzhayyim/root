CREATE TABLE IF NOT EXISTS vertex_cowork_graph_sync_job (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      rkey            VARCHAR,
      repo            VARCHAR,
      job_type        VARCHAR,
      status          VARCHAR,
      actor_did       VARCHAR,
      error_message   VARCHAR,
      started_at      VARCHAR,
      done_at         VARCHAR,
      created_at      VARCHAR,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_cowork_graph_mail_draft (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      rkey            VARCHAR,
      repo            VARCHAR,
      draft_id        VARCHAR,
      user_id         VARCHAR,
      subject         VARCHAR,
      to_addrs        VARCHAR,
      cc_addrs        VARCHAR,
      importance      VARCHAR,
      web_link        VARCHAR,
      approved_at     VARCHAR,
      sent_at         VARCHAR,
      created_at      VARCHAR,
      org_id          VARCHAR,
      actor_id        VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_cowork_graph_tool_grant (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      rkey            VARCHAR,
      repo            VARCHAR,
      caller_did      VARCHAR,
      tool_nsid       VARCHAR,
      effect          VARCHAR,
      granted_by      VARCHAR,
      expires_at      VARCHAR,
      revoked_at      VARCHAR,
      created_at      VARCHAR,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cowork_graph_draft_pending AS
    SELECT
      draft_id,
      user_id,
      subject,
      to_addrs,
      importance,
      web_link,
      created_at
    FROM vertex_cowork_graph_mail_draft
    WHERE approved_at IS NULL AND sent_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_cowork_graph_sync_job_type
      ON vertex_cowork_graph_sync_job (job_type, created_date);

CREATE INDEX IF NOT EXISTS idx_cowork_graph_mail_draft_user
      ON vertex_cowork_graph_mail_draft (user_id, created_date);

CREATE INDEX IF NOT EXISTS idx_cowork_graph_tool_grant_caller
      ON vertex_cowork_graph_tool_grant (caller_did, tool_nsid);
