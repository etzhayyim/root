CREATE INDEX IF NOT EXISTS idx_intel_cohort_subject_domain ON vertex_intel_inferred_cohort (subject_did, target_domain);

CREATE INDEX IF NOT EXISTS idx_intel_cohort_confidence ON vertex_intel_inferred_cohort (confidence);

CREATE INDEX IF NOT EXISTS idx_intel_evidence_payload ON vertex_intel_evidence (payload_json);

INSERT INTO edge_intel_report_entity (
      edge_id, src_vid, dst_vid, relation, analysis_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:intel:report-entity:' || r.analysis_id || ':' || e.entity_id,
      r.vertex_id,
      e.vertex_id,
      'MENTIONS_ENTITY',
      r.analysis_id,
      coalesce(e.owner_did, r.owner_did),
      e.actor_id,
      e.created_at
    FROM vertex_intel_report r
    JOIN vertex_intel_entity_did e ON e.source_analysis = r.analysis_id
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_intel_chain_cohort (
      edge_id, src_vid, dst_vid, relation, chain_id, cohort_id, confidence, owner_did, actor_id, created_at
    )
    SELECT
      'edge:intel:chain-cohort:' || c.chain_id || ':' || h.cohort_id,
      c.vertex_id,
      h.vertex_id,
      'GENERATED_COHORT',
      c.chain_id,
      h.cohort_id,
      h.confidence,
      coalesce(h.owner_did, c.owner_did),
      h.actor_id,
      h.created_at
    FROM vertex_intel_inference_chain c
    JOIN vertex_intel_inferred_cohort h ON h.chain_id = c.chain_id
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_intel_chain_evidence (
      edge_id, src_vid, dst_vid, relation, chain_id, owner_did, actor_id, created_at
    )
    SELECT
      'edge:intel:chain-evidence:' || c.chain_id || ':' || e.evidence_id,
      c.vertex_id,
      e.vertex_id,
      'SUPPORTED_BY_EVIDENCE',
      c.chain_id,
      coalesce(e.owner_did, c.owner_did),
      e.actor_id,
      e.created_at
    FROM vertex_intel_inference_chain c
    JOIN vertex_intel_evidence e ON e.payload_json LIKE '%"chainId":"' || c.chain_id || '"%'
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_intel_cohort_evidence (
      edge_id, src_vid, dst_vid, relation, chain_id, cohort_id, confidence, owner_did, actor_id, created_at
    )
    SELECT
      'edge:intel:cohort-evidence:' || h.cohort_id || ':' || e.evidence_id,
      h.vertex_id,
      e.vertex_id,
      'STABILIZED_BY_EVIDENCE',
      h.chain_id,
      h.cohort_id,
      h.confidence,
      coalesce(e.owner_did, h.owner_did),
      e.actor_id,
      e.created_at
    FROM vertex_intel_inferred_cohort h
    JOIN vertex_intel_evidence e ON e.payload_json LIKE '%"cohortId":"' || h.cohort_id || '"%'
    ON CONFLICT (edge_id) DO NOTHING;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_intel_inference_chain_flow AS
    SELECT
      c.chain_id,
      c.subject_did,
      c.subject_name,
      c.industry,
      c.status,
      count(DISTINCT h.vertex_id) AS cohort_count,
      avg(h.confidence) AS avg_confidence,
      count(DISTINCT e.dst_vid) AS evidence_count,
      max(coalesce(h.created_at, c.created_at)) AS latest_at
    FROM vertex_intel_inference_chain c
    LEFT JOIN vertex_intel_inferred_cohort h ON h.chain_id = c.chain_id
    LEFT JOIN edge_intel_chain_evidence e ON e.src_vid = c.vertex_id
    GROUP BY c.chain_id, c.subject_did, c.subject_name, c.industry, c.status;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_intel_coverage_projection AS
    SELECT
      target_domain,
      status,
      count(*) AS cohort_count,
      sum(estimated_count) AS estimated_count,
      avg(confidence) AS avg_confidence,
      max(created_at) AS latest_created_at
    FROM vertex_intel_inferred_cohort
    GROUP BY target_domain, status;
