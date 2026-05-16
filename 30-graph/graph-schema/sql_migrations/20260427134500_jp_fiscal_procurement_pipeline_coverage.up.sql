CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_fiscal_procurement_bid_contract_coverage AS
    SELECT
      b.vertex_id AS procurement_bid_vertex_id,
      b.tender_no,
      b.issuer_did,
      b.method,
      b.title,
      CASE
        WHEN EXTRACT(MONTH FROM b.opened_at) >= 4 THEN EXTRACT(YEAR FROM b.opened_at)::int
        ELSE EXTRACT(YEAR FROM b.opened_at)::int - 1
      END AS fiscal_year,
      b.opened_at,
      b.closed_at,
      b.awarded_at,
      b.awarded_amount_jpy,
      b.awarded_contract_did,
      b.tender_url,
      b.source_id,
      b.document_id,
      CASE WHEN d.vertex_id IS NULL THEN false ELSE true END AS has_document_vertex,
      CASE WHEN ev.edge_id IS NULL THEN false ELSE true END AS has_document_evidence_edge,
      c.vertex_id AS contract_vertex_id,
      c.contract_no,
      c.contractor_did,
      c.contractor_jcn,
      c.amount_jpy AS contract_amount_jpy,
      c.signed_date AS contract_signed_date,
      cp.edge_id AS contract_procurement_edge_id,
      CASE WHEN c.vertex_id IS NULL THEN false ELSE true END AS has_contract_vertex,
      CASE WHEN cp.edge_id IS NULL THEN false ELSE true END AS has_contract_procurement_edge,
      CASE
        WHEN b.awarded_amount_jpy IS NULL OR c.amount_jpy IS NULL THEN NULL
        WHEN b.awarded_amount_jpy = c.amount_jpy THEN true
        ELSE false
      END AS awarded_amount_matches_contract
    FROM vertex_jp_fiscal_procurement_bid b
    LEFT JOIN vertex_jp_fiscal_document d
      ON d.vertex_id = b.document_id
    LEFT JOIN edge_jp_fiscal_evidence ev
      ON ev.dst_vid = b.vertex_id
     AND ev.src_vid = b.document_id
     AND ev.evidence_kind = 'DOCUMENT_SUPPORTS_RECORD'
    LEFT JOIN edge_jp_fiscal_contract_procurement cp
      ON cp.src_vid = b.vertex_id
    LEFT JOIN vertex_jp_fiscal_contract c
      ON c.vertex_id = cp.dst_vid;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_fiscal_procurement_pipeline_coverage AS
    SELECT
      fiscal_year,
      issuer_did,
      method,
      source_id,
      COUNT(*) AS bid_count,
      SUM(CASE WHEN has_document_vertex THEN 1 ELSE 0 END) AS bid_with_document_count,
      SUM(CASE WHEN has_document_evidence_edge THEN 1 ELSE 0 END) AS evidenced_bid_count,
      SUM(CASE WHEN awarded_at IS NOT NULL THEN 1 ELSE 0 END) AS awarded_bid_count,
      SUM(CASE WHEN awarded_amount_jpy IS NOT NULL THEN 1 ELSE 0 END) AS bid_with_awarded_amount_count,
      SUM(CASE WHEN has_contract_vertex THEN 1 ELSE 0 END) AS bid_with_contract_count,
      SUM(CASE WHEN has_contract_procurement_edge THEN 1 ELSE 0 END) AS bid_with_contract_edge_count,
      SUM(COALESCE(awarded_amount_jpy, 0)) AS awarded_amount_total_jpy,
      SUM(COALESCE(contract_amount_jpy, 0)) AS contract_amount_total_jpy
    FROM mv_jp_fiscal_procurement_bid_contract_coverage
    GROUP BY fiscal_year, issuer_did, method, source_id;
