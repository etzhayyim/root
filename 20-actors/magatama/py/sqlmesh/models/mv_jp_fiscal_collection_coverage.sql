-- JP fiscal collection coverage: row counts per collection across all fiscal tables.
MODEL (
  name dev.mv_jp_fiscal_collection_coverage,
  kind FULL,
  dialect postgres,
  description 'Per collection: row count and distinct source count across 14 JP fiscal vertex tables.',
  grain [collection],
  tags [jp_fiscal, collection, coverage]
);

SELECT
  collection,
  COUNT(*) AS row_count,
  COUNT(DISTINCT source_id) AS source_count
FROM (
  SELECT 'ai.gftd.apps.jpFiscal.budgetBook' AS collection, source_id FROM vertex_jp_fiscal_budget_book
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.appropriation', source_id FROM vertex_jp_fiscal_appropriation
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.budgetExecution', source_id FROM vertex_jp_fiscal_budget_execution
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.procurementBid', source_id FROM vertex_jp_fiscal_procurement_bid
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.contract', source_id FROM vertex_jp_fiscal_contract
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.paymentRecord', source_id FROM vertex_jp_fiscal_payment_record
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.subsidyGrant', source_id FROM vertex_jp_fiscal_subsidy_grant
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.taxPayment', source_id FROM vertex_jp_fiscal_tax_payment
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.kofuzeiTransfer', source_id FROM vertex_jp_fiscal_kofuzei_transfer
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.lgFinance', source_id FROM vertex_jp_fiscal_lg_finance
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.incorpFinance', source_id FROM vertex_jp_fiscal_incorp_finance
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.programReview', source_id FROM vertex_jp_fiscal_program_review
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.auditFinding', source_id FROM vertex_jp_fiscal_audit_finding
  UNION ALL SELECT 'ai.gftd.apps.jpFiscal.beneficialOwner', source_id FROM vertex_jp_fiscal_beneficial_owner
) records
GROUP BY collection
