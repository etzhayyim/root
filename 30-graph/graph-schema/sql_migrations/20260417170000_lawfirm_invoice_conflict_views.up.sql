CREATE VIEW view_lawfirm_invoice_ageing AS
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
    FROM vertex_atrecord_lawfirm_invoice i;

CREATE VIEW view_lawfirm_conflict_findings AS
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
    FROM vertex_atrecord_lawfirm_conflictcheck c;
