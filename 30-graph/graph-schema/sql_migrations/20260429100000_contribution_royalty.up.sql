CREATE TABLE IF NOT EXISTS vertex_contribution_source (
      vertex_id        VARCHAR PRIMARY KEY,
      source_hash      VARCHAR     NOT NULL,
      canonical_id     VARCHAR     NOT NULL,
      source_type      VARCHAR     NOT NULL,
      contributor_did  VARCHAR,
      contributor_addr VARCHAR,
      royalty_bps      INT         NOT NULL DEFAULT 100,
      description      VARCHAR,
      license          VARCHAR,
      created_at       VARCHAR     NOT NULL,
      actor_did        VARCHAR     NOT NULL,
      org_did          VARCHAR     NOT NULL DEFAULT 'anon'
    );

CREATE INDEX IF NOT EXISTS idx_contribution_source_hash
      ON vertex_contribution_source (source_hash);

CREATE INDEX IF NOT EXISTS idx_contribution_source_type
      ON vertex_contribution_source (source_type);

CREATE TABLE IF NOT EXISTS vertex_contribution_usage (
      vertex_id      VARCHAR PRIMARY KEY,
      source_hash    VARCHAR     NOT NULL,
      consumer_did   VARCHAR     NOT NULL,
      usage_type     VARCHAR     NOT NULL,
      gcc_value_wei  VARCHAR     NOT NULL DEFAULT '0',
      used_at        VARCHAR     NOT NULL,
      actor_did      VARCHAR     NOT NULL,
      org_did        VARCHAR     NOT NULL DEFAULT 'anon'
    );

CREATE INDEX IF NOT EXISTS idx_contribution_usage_source_hash
      ON vertex_contribution_usage (source_hash);

CREATE INDEX IF NOT EXISTS idx_contribution_usage_used_at
      ON vertex_contribution_usage (used_at);

CREATE INDEX IF NOT EXISTS idx_contribution_usage_consumer
      ON vertex_contribution_usage (consumer_did);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_contribution_royalty_daily AS
    SELECT
      cs.source_hash,
      cs.contributor_did,
      cs.contributor_addr,
      DATE_TRUNC('day', used_at::TIMESTAMP) AS distribution_date,
      COUNT(*)                               AS usage_count,
      SUM(
        CAST(cu.gcc_value_wei AS DOUBLE PRECISION) * cs.royalty_bps / 10000
      )                                      AS earned_wei
    FROM vertex_contribution_usage cu
    JOIN vertex_contribution_source cs USING (source_hash)
    GROUP BY
      cs.source_hash,
      cs.contributor_did,
      cs.contributor_addr,
      DATE_TRUNC('day', used_at::TIMESTAMP);
