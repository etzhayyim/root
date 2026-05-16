import { Kysely, sql } from 'kysely';

/**
 * Phase C++ — lawfirm invoice ageing + conflict findings projections.
 *
 * Depends on the PDS pipeline having provisioned:
 *   - vertex_atrecord_lawfirm_invoice       (created on first invoice writeRecord)
 *   - vertex_atrecord_lawfirm_conflictcheck (created on first runConflictCheck)
 *
 * Both tables are P10v2 GraphAr auto-generated from the AT record schema.
 * Views fall back to 0 rows if the source table is absent (SELECT against a
 * missing table raises, which the Worker handler catches → empty list).
 *
 * View 1 — view_lawfirm_invoice_ageing
 *   Per-invoice summary with derived ageing bucket computed from due_at.
 *   ageing_bucket ∈ {current, dueSoon, overdue30, overdue60, overdue90}.
 *
 * View 2 — view_lawfirm_conflict_findings
 *   Per-conflictCheck summary. Lightweight: full conflicts[] detail stays in
 *   the AT record; view surfaces counts + result + scope for list paths.
 *
 * Plain VIEW (not MATERIALIZED) — same rationale as 20260417160000: the lawfirm
 * workload is early-stage (empty tables on fresh cluster), and the live
 * cluster has been rejecting streaming MV creation with "failed to collect
 * barrier" for these JOIN shapes. Promote to MV under the same trigger
 * condition documented there.
 *
 * Spec: 00-contracts/lexicons/ai/gftd/apps/lawfirm/{listInvoices,listConflictChecks}.json
 */

export async function up(db: Kysely<any>): Promise<void> {
  await sql`CREATE VIEW view_lawfirm_invoice_ageing AS
    SELECT
      i.matter_did,
      i.invoice_did,
      i.firm_did,
      i.client_did,
      i.invoice_number,
      i.subtotal,
      i.tax_amount,
      i.discount_amount,
      i.total,
      i.currency,
      i.issued_at,
      i.due_at,
      i.paid_at,
      i.status,
      CASE
        WHEN i.status IN ('paid', 'void') THEN 0
        WHEN i.due_at IS NULL              THEN 0
        WHEN i.due_at > NOW()              THEN 0
        ELSE EXTRACT(DAY FROM (NOW() - i.due_at::TIMESTAMP))::INTEGER
      END AS days_overdue,
      CASE
        WHEN i.status IN ('paid', 'void')                                       THEN 'paid'
        WHEN i.due_at IS NULL OR i.due_at > NOW() + INTERVAL '7 days'            THEN 'current'
        WHEN i.due_at > NOW()                                                    THEN 'dueSoon'
        WHEN i.due_at > NOW() - INTERVAL '30 days'                               THEN 'overdue30'
        WHEN i.due_at > NOW() - INTERVAL '60 days'                               THEN 'overdue60'
        ELSE                                                                          'overdue90'
      END AS ageing_bucket
    FROM vertex_atrecord_lawfirm_invoice i`.execute(db);

  await sql`CREATE VIEW view_lawfirm_conflict_findings AS
    SELECT
      c.rkey,
      c.matter_did,
      c.scan_scope,
      c.candidate_did,
      c.result,
      c.conflicts_count,
      c.wall_id,
      c.scanned_by,
      c.scanned_at
    FROM vertex_atrecord_lawfirm_conflictcheck c`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_lawfirm_conflict_findings`.execute(db);
  await sql`DROP VIEW IF EXISTS view_lawfirm_invoice_ageing`.execute(db);
}
