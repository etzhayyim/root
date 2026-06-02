DROP MATERIALIZED VIEW IF EXISTS mv_cohort_k_drift;

DROP MATERIALIZED VIEW IF EXISTS mv_cohort_identity_posterior;

DROP TABLE IF EXISTS vertex_cohort_evidence;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cohort_identity_posterior AS
    SELECT
      cohort_did,
      COUNT(*)::BIGINT AS evidence_count,
      AVG(posterior)::DOUBLE PRECISION AS avg_posterior,
      MAX(posterior)::DOUBLE PRECISION AS max_posterior,
      SUM(CASE WHEN judge_agreement THEN 1 ELSE 0 END)::BIGINT AS judge_agree_count,
      SUM(CASE WHEN posterior > 0.95 AND judge_agreement THEN 1 ELSE 0 END)::BIGINT AS fission_ready_count,
      MAX(observed_at) AS last_evidence_at
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.cohort.evidence'
    GROUP BY cohort_did;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cohort_k_drift AS
    SELECT
      cohort_did,
      COUNT(DISTINCT signal_kind)::BIGINT AS distinct_signal_kinds,
      COUNT(*)::BIGINT AS evidence_count,
      CASE WHEN COUNT(DISTINCT signal_kind) = 0 THEN 0
           ELSE COUNT(*) / COUNT(DISTINCT signal_kind)
      END::BIGINT AS k_proxy
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.cohort.evidence'
    GROUP BY cohort_did;
