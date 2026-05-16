CREATE TABLE IF NOT EXISTS vertex_ossekai_signal (
      vertex_id        VARCHAR PRIMARY KEY,
      signal_id        VARCHAR NOT NULL,
      target_did       VARCHAR NOT NULL,
      target_handle    VARCHAR,
      signal_kind      VARCHAR NOT NULL,
      content_uri      VARCHAR,
      summary          VARCHAR,
      sentiment_score  DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      relevance_score  DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      raw_text         VARCHAR,
      observed_at      VARCHAR NOT NULL,
      created_at       VARCHAR NOT NULL,
      sensitivity_ord  INTEGER NOT NULL DEFAULT 0,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      actor_did        VARCHAR,
      org_did          VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_ossekai_brief (
      vertex_id        VARCHAR PRIMARY KEY,
      brief_id         VARCHAR NOT NULL,
      target_did       VARCHAR NOT NULL,
      target_handle    VARCHAR,
      brief_kind       VARCHAR NOT NULL DEFAULT 'intel',
      title            VARCHAR NOT NULL,
      summary          VARCHAR NOT NULL,
      key_signals      VARCHAR,
      confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      signal_ids       VARCHAR,
      generated_at     VARCHAR NOT NULL,
      created_at       VARCHAR NOT NULL,
      sensitivity_ord  INTEGER NOT NULL DEFAULT 0,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR,
      actor_did        VARCHAR,
      org_did          VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_ossekai_arbitrage (
      vertex_id          VARCHAR PRIMARY KEY,
      arb_id             VARCHAR NOT NULL,
      opportunity_kind   VARCHAR NOT NULL,
      supply_actor_did   VARCHAR,
      demand_actor_did   VARCHAR,
      supply_signal_id   VARCHAR,
      demand_signal_id   VARCHAR,
      gap_description    VARCHAR NOT NULL,
      estimated_value    DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      confidence_score   DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      recommended_action VARCHAR,
      status             VARCHAR NOT NULL DEFAULT 'open',
      created_at         VARCHAR NOT NULL,
      sensitivity_ord    INTEGER NOT NULL DEFAULT 0,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      actor_did          VARCHAR,
      org_did            VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_ossekai_wellbecoming_plan (
      vertex_id             VARCHAR PRIMARY KEY,
      plan_id               VARCHAR NOT NULL,
      target_did            VARCHAR NOT NULL,
      consent_did           VARCHAR NOT NULL,
      current_kyu_dan       VARCHAR NOT NULL DEFAULT '6kyu',
      target_kyu_dan        VARCHAR NOT NULL DEFAULT '5kyu',
      jocho_score           DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      engagement_delta      DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      competence_delta      DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      contribution_delta    DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      growth_delta          DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      resilience_delta      DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      action_items          VARCHAR,
      trust_score           DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      next_review_at        VARCHAR,
      status                VARCHAR NOT NULL DEFAULT 'active',
      created_at            VARCHAR NOT NULL,
      sensitivity_ord       INTEGER NOT NULL DEFAULT 3,
      org_id                VARCHAR,
      user_id               VARCHAR,
      actor_id              VARCHAR,
      actor_did             VARCHAR,
      org_did               VARCHAR
    );

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ossekai_signal_recent AS
    SELECT
      target_did,
      count(*) AS signal_count,
      avg(sentiment_score) AS avg_sentiment,
      avg(relevance_score) AS avg_relevance,
      max(observed_at) AS last_observed_at
    FROM vertex_ossekai_signal
    GROUP BY target_did;

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ossekai_arbitrage_open AS
    SELECT
      opportunity_kind,
      count(*) AS opportunity_count,
      avg(confidence_score) AS avg_confidence,
      sum(estimated_value) AS total_estimated_value
    FROM vertex_ossekai_arbitrage
    WHERE status = 'open'
    GROUP BY opportunity_kind;

FLUSH;
