ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS isced4 VARCHAR;

ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS isced_broad VARCHAR;

ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS isced_narrow VARCHAR;

ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS name_en VARCHAR;

ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS name_ja VARCHAR;

ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS paradigm VARCHAR;

ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS maturity VARCHAR;

ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS interdisciplinarity VARCHAR;

ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS cohort_hash VARCHAR;

ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS publication_count BIGINT;

ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS citation_count BIGINT;

ALTER TABLE vertex_kenkyusha_discipline ADD COLUMN IF NOT EXISTS frontier_count BIGINT;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS frontier_id VARCHAR;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS title TEXT;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS description TEXT;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS detection_method VARCHAR;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS primary_discipline VARCHAR;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS urgency VARCHAR;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS evidence_level VARCHAR;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS consensus_level VARCHAR;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS cohort_hash VARCHAR;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS hypothesis_count BIGINT;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS evidence_count BIGINT;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS detected_at VARCHAR;

ALTER TABLE vertex_kenkyusha_frontier ADD COLUMN IF NOT EXISTS last_analyzed_at VARCHAR;

ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS hypothesis_id VARCHAR;

ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS frontier_id VARCHAR;

ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS statement TEXT;

ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS rationale TEXT;

ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS confidence_score DOUBLE PRECISION;

ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS llm_model VARCHAR;

ALTER TABLE vertex_kenkyusha_hypothesis ADD COLUMN IF NOT EXISTS evaluated_at VARCHAR;

ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS evidence_id VARCHAR;

ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS frontier_id VARCHAR;

ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS hypothesis_id VARCHAR;

ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS source_type VARCHAR;

ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS source_did VARCHAR;

ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS source_uri VARCHAR;

ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS relevance_score DOUBLE PRECISION;

ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS evidence_type VARCHAR;

ALTER TABLE vertex_kenkyusha_evidence ADD COLUMN IF NOT EXISTS extracted_claim TEXT;

ALTER TABLE vertex_kenkyusha_did_registration ADD COLUMN IF NOT EXISTS path VARCHAR;

ALTER TABLE vertex_kenkyusha_did_registration ADD COLUMN IF NOT EXISTS display_name VARCHAR;

CREATE INDEX IF NOT EXISTS idx_kenkyusha_discipline_isced ON vertex_kenkyusha_discipline (isced4);

CREATE INDEX IF NOT EXISTS idx_kenkyusha_discipline_broad ON vertex_kenkyusha_discipline (isced_broad);

CREATE INDEX IF NOT EXISTS idx_kenkyusha_frontier_id ON vertex_kenkyusha_frontier (frontier_id);

CREATE INDEX IF NOT EXISTS idx_kenkyusha_frontier_discipline ON vertex_kenkyusha_frontier (primary_discipline, status);

CREATE INDEX IF NOT EXISTS idx_kenkyusha_frontier_urgency ON vertex_kenkyusha_frontier (urgency, status);

CREATE INDEX IF NOT EXISTS idx_kenkyusha_hypothesis_id ON vertex_kenkyusha_hypothesis (hypothesis_id);

CREATE INDEX IF NOT EXISTS idx_kenkyusha_hypothesis_frontier ON vertex_kenkyusha_hypothesis (frontier_id, status);

CREATE INDEX IF NOT EXISTS idx_kenkyusha_evidence_frontier ON vertex_kenkyusha_evidence (frontier_id, source_type);

CREATE INDEX IF NOT EXISTS idx_kenkyusha_evidence_hypothesis ON vertex_kenkyusha_evidence (hypothesis_id, evidence_type);

DROP MATERIALIZED VIEW IF EXISTS mv_kenkyusha_frontier_status_counts;

CREATE MATERIALIZED VIEW mv_kenkyusha_frontier_status_counts AS
    SELECT primary_discipline, urgency, status, count(*)::BIGINT AS frontier_count
    FROM vertex_kenkyusha_frontier
    GROUP BY primary_discipline, urgency, status;

DROP MATERIALIZED VIEW IF EXISTS mv_kenkyusha_hypothesis_status_counts;

CREATE MATERIALIZED VIEW mv_kenkyusha_hypothesis_status_counts AS
    SELECT frontier_id, status, count(*)::BIGINT AS hypothesis_count, avg(confidence_score) AS avg_confidence_score
    FROM vertex_kenkyusha_hypothesis
    GROUP BY frontier_id, status;

DROP MATERIALIZED VIEW IF EXISTS mv_kenkyusha_evidence_type_counts;

CREATE MATERIALIZED VIEW mv_kenkyusha_evidence_type_counts AS
    SELECT frontier_id, hypothesis_id, source_type, evidence_type, count(*)::BIGINT AS evidence_count
    FROM vertex_kenkyusha_evidence
    GROUP BY frontier_id, hypothesis_id, source_type, evidence_type;
