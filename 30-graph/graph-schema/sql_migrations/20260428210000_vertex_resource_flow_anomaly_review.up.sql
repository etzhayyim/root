CREATE TABLE vertex_resource_flow_anomaly_review (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      review_id          varchar NOT NULL,
      anomaly_id         varchar NOT NULL,
      action             varchar NOT NULL,
      reason             varchar,
      reviewer_did       varchar NOT NULL,
      reviewer_facade    varchar,
      thread_post_uri    varchar,
      observed_at        varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar,
      root_did           varchar,
      root_did_hash      varchar,
      root_identity_addr varchar,
      facade_did         varchar,
      facade_did_hash    varchar,
      identity_method    varchar,
      migration_status   varchar
    );

CREATE INDEX IF NOT EXISTS idx_anomaly_review_anomaly  ON vertex_resource_flow_anomaly_review (anomaly_id);

CREATE INDEX IF NOT EXISTS idx_anomaly_review_observed ON vertex_resource_flow_anomaly_review (observed_at);

CREATE INDEX IF NOT EXISTS idx_anomaly_review_reviewer ON vertex_resource_flow_anomaly_review (reviewer_did);

FLUSH;

CREATE MATERIALIZED VIEW mv_resource_flow_anomaly_review_latest AS
      SELECT
        anomaly_id,
        MAX(observed_at) AS latest_observed_at,
        COUNT(*)         AS review_count
      FROM vertex_resource_flow_anomaly_review
      GROUP BY anomaly_id;

FLUSH;
