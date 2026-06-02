import type { Kysely } from "kysely";
import { sql } from "kysely";

// Extend JP fiscal record coverage to include procurement bid records.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_budget_pipeline_coverage`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_collection_record_coverage`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_record_document_coverage`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_jp_fiscal_record_document_coverage AS
    SELECT
      records.collection,
      records.vertex_id,
      records.fiscal_year,
      records.account_type,
      records.doc_type,
      records.program_code,
      records.amount_jpy,
      records.source_id,
      records.document_id,
      d.sha256 AS document_sha256,
      d.media_type AS document_media_type,
      d.byte_length AS document_byte_length,
      CASE WHEN records.document_id IS NULL THEN false ELSE true END AS has_document_id,
      CASE WHEN d.vertex_id IS NULL THEN false ELSE true END AS has_document_vertex,
      CASE WHEN e.edge_id IS NULL THEN false ELSE true END AS has_record_evidence_edge,
      e.confidence AS record_evidence_confidence
    FROM (
      SELECT
        'com.etzhayyim.apps.jpFiscal.budgetBook' AS collection,
        vertex_id,
        fiscal_year,
        account_type,
        doc_type,
        NULL::varchar AS program_code,
        total_jpy AS amount_jpy,
        source_id,
        document_id
      FROM vertex_jp_fiscal_budget_book
      UNION ALL
      SELECT
        'com.etzhayyim.apps.jpFiscal.appropriation' AS collection,
        vertex_id,
        fiscal_year,
        account_type,
        doc_type,
        program_code,
        amount_jpy,
        source_id,
        document_id
      FROM vertex_jp_fiscal_appropriation
      UNION ALL
      SELECT
        'com.etzhayyim.apps.jpFiscal.procurementBid' AS collection,
        vertex_id,
        CASE
          WHEN EXTRACT(MONTH FROM opened_at) >= 4 THEN EXTRACT(YEAR FROM opened_at)::int
          ELSE EXTRACT(YEAR FROM opened_at)::int - 1
        END AS fiscal_year,
        'unknown'::varchar AS account_type,
        'announcement'::varchar AS doc_type,
        tender_no AS program_code,
        estimated_jpy AS amount_jpy,
        source_id,
        document_id
      FROM vertex_jp_fiscal_procurement_bid
    ) records
    LEFT JOIN vertex_jp_fiscal_document d
      ON d.vertex_id = records.document_id
    LEFT JOIN edge_jp_fiscal_evidence e
      ON e.src_vid = records.document_id
     AND e.dst_vid = records.vertex_id
     AND e.evidence_kind = 'DOCUMENT_SUPPORTS_RECORD'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_jp_fiscal_collection_record_coverage AS
    SELECT
      collection,
      fiscal_year,
      account_type,
      doc_type,
      COUNT(*) AS record_count,
      SUM(CASE WHEN has_document_id THEN 1 ELSE 0 END) AS record_with_document_id_count,
      SUM(CASE WHEN has_document_vertex THEN 1 ELSE 0 END) AS record_with_document_vertex_count,
      SUM(CASE WHEN has_record_evidence_edge THEN 1 ELSE 0 END) AS evidenced_record_count,
      SUM(COALESCE(amount_jpy, 0)) AS total_amount_jpy
    FROM mv_jp_fiscal_record_document_coverage
    GROUP BY collection, fiscal_year, account_type, doc_type
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_jp_fiscal_budget_pipeline_coverage AS
    SELECT
      b.vertex_id AS budget_book_vertex_id,
      b.fiscal_year,
      b.account_type,
      b.doc_type,
      b.total_jpy AS budget_total_jpy,
      COALESCE(a.appropriation_count, 0) AS appropriation_count,
      COALESCE(a.appropriation_total_jpy, 0) AS appropriation_total_jpy,
      COALESCE(f.appropriation_flow_count, 0) AS appropriation_flow_count,
      COALESCE(f.appropriation_flow_total_jpy, 0) AS appropriation_flow_total_jpy,
      COALESCE(e.document_record_evidence_count, 0) AS document_record_evidence_count,
      CASE WHEN COALESCE(a.appropriation_total_jpy, 0) = b.total_jpy THEN true ELSE false END AS appropriation_total_matches_budget,
      CASE WHEN COALESCE(f.appropriation_flow_total_jpy, 0) = b.total_jpy THEN true ELSE false END AS flow_total_matches_budget,
      CASE WHEN COALESCE(e.document_record_evidence_count, 0) = COALESCE(a.appropriation_count, 0) + 1 THEN true ELSE false END AS all_budget_records_evidenced
    FROM vertex_jp_fiscal_budget_book b
    LEFT JOIN (
      SELECT fiscal_year, account_type, doc_type, COUNT(*) AS appropriation_count, SUM(amount_jpy) AS appropriation_total_jpy
      FROM vertex_jp_fiscal_appropriation
      GROUP BY fiscal_year, account_type, doc_type
    ) a
      ON a.fiscal_year = b.fiscal_year
     AND a.account_type = b.account_type
     AND a.doc_type = b.doc_type
    LEFT JOIN (
      SELECT src_vid, COUNT(*) AS appropriation_flow_count, SUM(amount_jpy) AS appropriation_flow_total_jpy
      FROM edge_jp_fiscal_flow
      WHERE flow_type = 'appropriation'
      GROUP BY src_vid
    ) f
      ON f.src_vid = b.vertex_id
    LEFT JOIN (
      SELECT fiscal_year, account_type, doc_type, COUNT(*) AS document_record_evidence_count
      FROM mv_jp_fiscal_record_document_coverage
      WHERE collection IN ('com.etzhayyim.apps.jpFiscal.budgetBook', 'com.etzhayyim.apps.jpFiscal.appropriation')
        AND has_record_evidence_edge = true
      GROUP BY fiscal_year, account_type, doc_type
    ) e
      ON e.fiscal_year = b.fiscal_year
     AND e.account_type = b.account_type
     AND e.doc_type = b.doc_type
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_budget_pipeline_coverage`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_collection_record_coverage`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_record_document_coverage`.execute(db);
}
