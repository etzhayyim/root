CREATE TABLE IF NOT EXISTS vertex_shosha_consumer_cursor (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      consumer_id varchar NOT NULL,
      upstream_did varchar NOT NULL,
      collection_prefix varchar,
      last_seq bigint NOT NULL,
      last_ts_ms bigint,
      last_seen_at varchar,
      records_seen bigint,
      reactions_emitted bigint,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS vertex_shosha_reaction (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      reaction_id varchar NOT NULL,
      upstream_did varchar NOT NULL,
      upstream_collection varchar,
      upstream_seq bigint,
      upstream_rkey varchar,
      upstream_record_vid varchar,
      reaction_type varchar NOT NULL,
      commodity varchar,
      direction varchar,
      target_action varchar,
      rationale varchar,
      confidence double precision,
      llm_model varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shosha_reaction_count_by_upstream AS
      SELECT
        upstream_did,
        reaction_type,
        COUNT(*) AS reaction_count,
        AVG(COALESCE(confidence, 0)) AS avg_confidence
      FROM vertex_shosha_reaction
      WHERE status = 'active'
      GROUP BY upstream_did, reaction_type;

GRANT SELECT, INSERT, UPDATE ON vertex_shosha_consumer_cursor TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_shosha_consumer_cursor TO kaisya_app;

GRANT SELECT, INSERT, UPDATE ON vertex_shosha_reaction        TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_shosha_reaction        TO kaisya_app;
