CREATE TABLE IF NOT EXISTS vertex_yoro_monitor_attestation (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      monitor_did VARCHAR, axis VARCHAR, subject_did VARCHAR,
      observed_at VARCHAR, status VARCHAR, fault_class VARCHAR,
      signals_json VARCHAR, cross_seen_json VARCHAR, sig_es256 VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_yoro_monitor_attestation_monitor_observed
      ON vertex_yoro_monitor_attestation (monitor_did, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_yoro_monitor_attestation_subject_axis_observed
      ON vertex_yoro_monitor_attestation (subject_did, axis, observed_at DESC);

CREATE TABLE IF NOT EXISTS vertex_yoro_monitor_vote (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      subject_did VARCHAR, action VARCHAR, reason VARCHAR, requested_by VARCHAR,
      opened_at VARCHAR, closes_at VARCHAR,
      ballots_json VARCHAR, ballot_count BIGINT, yea_count BIGINT,
      resolution VARCHAR, resolved_at VARCHAR, human_override VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_yoro_monitor_vote_subject_open
      ON vertex_yoro_monitor_vote (subject_did, resolution, opened_at DESC);
