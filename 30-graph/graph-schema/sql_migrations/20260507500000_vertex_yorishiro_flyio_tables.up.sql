CREATE TABLE IF NOT EXISTS vertex_yorishiroFlyio_cancellationJob (
      vertex_id           VARCHAR PRIMARY KEY,
      job_id              VARCHAR NOT NULL,
      phase               VARCHAR NOT NULL,
      email               VARCHAR,
      delete_all_apps_first BOOLEAN,
      provider            VARCHAR,
      entry_url           VARCHAR,
      status              VARCHAR NOT NULL DEFAULT 'pending',
      created_at          VARCHAR NOT NULL,
      org_id              VARCHAR,
      user_id             VARCHAR,
      actor_id            VARCHAR,
      sensitivity_ord     BIGINT NOT NULL DEFAULT 2,
      owner_did           VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_yorishiroFlyio_cancellationJob_job_id
      ON vertex_yorishiroFlyio_cancellationJob (job_id);

CREATE INDEX IF NOT EXISTS idx_yorishiroFlyio_cancellationJob_phase
      ON vertex_yorishiroFlyio_cancellationJob (phase);

CREATE TABLE IF NOT EXISTS vertex_yorishiroFlyio_appDeleteJob (
      vertex_id       VARCHAR PRIMARY KEY,
      job_id          VARCHAR NOT NULL,
      app_name        VARCHAR NOT NULL,
      org_slug        VARCHAR,
      provider        VARCHAR,
      status          VARCHAR NOT NULL DEFAULT 'pending',
      created_at      VARCHAR NOT NULL,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 2,
      owner_did       VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_yorishiroFlyio_appDeleteJob_job_id
      ON vertex_yorishiroFlyio_appDeleteJob (job_id);

CREATE INDEX IF NOT EXISTS idx_yorishiroFlyio_appDeleteJob_app_name
      ON vertex_yorishiroFlyio_appDeleteJob (app_name);

CREATE TABLE IF NOT EXISTS vertex_yorishiroFlyio_orgDeleteJob (
      vertex_id       VARCHAR PRIMARY KEY,
      job_id          VARCHAR NOT NULL,
      org_slug        VARCHAR NOT NULL,
      org_name        VARCHAR,
      provider        VARCHAR,
      status          VARCHAR NOT NULL DEFAULT 'pending',
      created_at      VARCHAR NOT NULL,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      sensitivity_ord BIGINT NOT NULL DEFAULT 2,
      owner_did       VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_yorishiroFlyio_orgDeleteJob_job_id
      ON vertex_yorishiroFlyio_orgDeleteJob (job_id);

CREATE INDEX IF NOT EXISTS idx_yorishiroFlyio_orgDeleteJob_org_slug
      ON vertex_yorishiroFlyio_orgDeleteJob (org_slug);
