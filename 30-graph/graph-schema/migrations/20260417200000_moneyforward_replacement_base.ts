import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR-0031 — MoneyForward replacement base schema.
 *
 * 11 vertex + 5 edge + 3 MV + 2 plain VIEW across 4 actors:
 *   kaikei  (会計 GL / AP / 固定資産)
 *   seikyu  (請求書 / AR / インボイス)
 *   keiyaku (社内契約 / 電子署名)
 *   kousuu  (工数 / 個別原価)
 *
 * Existing `vertex_keiyaku_contract_{canonical,observation}` (migration
 * 20260416090000) tracks external government-procurement contracts and is
 * left untouched — our internal contracts use namespaced
 * `vertex_atrecord_keiyaku_agreement` to avoid collision.
 *
 * MV memory safety (graph-schema/CLAUDE.md §MV Memory Safety Guardrails):
 *   - All GROUP BY keys are bounded (<500K cardinality) and narrow
 *   - No MAX(varchar) fan-out
 *   - Plain VIEW used where materialization brings no freshness benefit
 *
 * Spec: 90-docs/adr/0031-moneyforward-actor-replacement.md
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── kaikei vertex ───────────────────────────────────────────────────
  await sql`
    CREATE TABLE vertex_atrecord_kaikei_account (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      rkey               VARCHAR NOT NULL,
      account_code       VARCHAR NOT NULL,
      account_name       VARCHAR NOT NULL,
      account_type       VARCHAR NOT NULL,
      parent_account_did VARCHAR,
      tax_code           VARCHAR,
      is_archived        BOOLEAN NOT NULL DEFAULT FALSE,
      created_at         TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_atrecord_kaikei_journal_entry (
      vertex_id           VARCHAR PRIMARY KEY,
      _seq                BIGINT NOT NULL,
      owner_did           VARCHAR NOT NULL,
      rkey                VARCHAR NOT NULL,
      period_ym           VARCHAR NOT NULL,
      posted_at           TIMESTAMPTZ NOT NULL,
      debit_account_did   VARCHAR NOT NULL,
      credit_account_did  VARCHAR NOT NULL,
      amount              DOUBLE PRECISION NOT NULL,
      currency            VARCHAR NOT NULL DEFAULT 'JPY',
      tax_code            VARCHAR,
      memo                VARCHAR,
      source_type         VARCHAR NOT NULL,
      source_did          VARCHAR,
      reversed_by_did     VARCHAR,
      created_at          TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_atrecord_kaikei_bank_transaction (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      bank_did           VARCHAR NOT NULL,
      bank_txn_id        VARCHAR NOT NULL,
      posted_at          TIMESTAMPTZ NOT NULL,
      amount             DOUBLE PRECISION NOT NULL,
      counterparty_name  VARCHAR,
      matched_je_did     VARCHAR,
      reconcile_status   VARCHAR NOT NULL DEFAULT 'pending',
      created_at         TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_atrecord_kaikei_fixed_asset (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT NOT NULL,
      owner_did             VARCHAR NOT NULL,
      asset_name            VARCHAR NOT NULL,
      acquisition_date      DATE NOT NULL,
      acquisition_cost      DOUBLE PRECISION NOT NULL,
      depreciation_method   VARCHAR NOT NULL,
      useful_life_months    INTEGER NOT NULL,
      account_did           VARCHAR NOT NULL,
      disposed_at           TIMESTAMPTZ,
      created_at            TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_atrecord_kaikei_ap_bill (
      vertex_id     VARCHAR PRIMARY KEY,
      _seq          BIGINT NOT NULL,
      owner_did     VARCHAR NOT NULL,
      vendor_did    VARCHAR NOT NULL,
      bill_number   VARCHAR NOT NULL,
      issued_at     TIMESTAMPTZ NOT NULL,
      due_at        TIMESTAMPTZ NOT NULL,
      amount        DOUBLE PRECISION NOT NULL,
      tax_amount    DOUBLE PRECISION,
      status        VARCHAR NOT NULL,
      approved_at   TIMESTAMPTZ,
      paid_at       TIMESTAMPTZ,
      payment_ref   VARCHAR,
      created_at    TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── seikyu vertex ──────────────────────────────────────────────────
  await sql`
    CREATE TABLE vertex_atrecord_seikyu_customer (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT NOT NULL,
      owner_did            VARCHAR NOT NULL,
      customer_name        VARCHAR NOT NULL,
      tax_id               VARCHAR,
      billing_address      VARCHAR,
      payment_terms_days   INTEGER NOT NULL DEFAULT 30,
      default_currency     VARCHAR NOT NULL DEFAULT 'JPY',
      created_at           TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_atrecord_seikyu_invoice (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      customer_did       VARCHAR NOT NULL,
      project_did        VARCHAR,
      agreement_did      VARCHAR,
      invoice_number     VARCHAR NOT NULL,
      period_from        DATE,
      period_to          DATE,
      issued_at          TIMESTAMPTZ NOT NULL,
      due_at             TIMESTAMPTZ NOT NULL,
      subtotal           DOUBLE PRECISION NOT NULL,
      tax_rate           DOUBLE PRECISION NOT NULL,
      tax_amount         DOUBLE PRECISION NOT NULL,
      total              DOUBLE PRECISION NOT NULL,
      currency           VARCHAR NOT NULL,
      status             VARCHAR NOT NULL,
      pdf_cid            VARCHAR,
      peppol_message_id  VARCHAR,
      sent_at            TIMESTAMPTZ,
      paid_at            TIMESTAMPTZ,
      created_at         TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── keiyaku (internal agreements) vertex ───────────────────────────
  await sql`
    CREATE TABLE vertex_atrecord_keiyaku_agreement (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      counterparty_did   VARCHAR NOT NULL,
      title              VARCHAR NOT NULL,
      agreement_type     VARCHAR NOT NULL,
      effective_from     DATE NOT NULL,
      term_months        INTEGER,
      auto_renew         BOOLEAN NOT NULL DEFAULT FALSE,
      total_amount       DOUBLE PRECISION,
      currency           VARCHAR,
      pdf_cid            VARCHAR NOT NULL,
      signing_status     VARCHAR NOT NULL,
      signed_at          TIMESTAMPTZ,
      terminated_at      TIMESTAMPTZ,
      created_at         TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── kousuu vertex ──────────────────────────────────────────────────
  await sql`
    CREATE TABLE vertex_atrecord_kousuu_project (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT NOT NULL,
      owner_did        VARCHAR NOT NULL,
      customer_did     VARCHAR,
      project_code     VARCHAR NOT NULL,
      project_name     VARCHAR NOT NULL,
      budget_hours     DOUBLE PRECISION,
      budget_cost_jpy  DOUBLE PRECISION,
      start_date       DATE NOT NULL,
      end_date         DATE,
      status           VARCHAR NOT NULL,
      created_at       TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_atrecord_kousuu_time_entry (
      vertex_id              VARCHAR PRIMARY KEY,
      _seq                   BIGINT NOT NULL,
      owner_did              VARCHAR NOT NULL,
      member_did             VARCHAR NOT NULL,
      project_did            VARCHAR NOT NULL,
      task_did               VARCHAR,
      entry_date             DATE NOT NULL,
      hours                  DOUBLE PRECISION NOT NULL,
      billable               BOOLEAN NOT NULL,
      invoice_lineitem_cid   VARCHAR,
      approval_status        VARCHAR NOT NULL,
      approved_by_did        VARCHAR,
      approved_at            TIMESTAMPTZ,
      created_at             TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_atrecord_kousuu_cost_rate (
      vertex_id                VARCHAR PRIMARY KEY,
      _seq                     BIGINT NOT NULL,
      owner_did                VARCHAR NOT NULL,
      member_did               VARCHAR NOT NULL,
      effective_from           DATE NOT NULL,
      hourly_cost_encrypted    VARCHAR NOT NULL,
      created_at               TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── edges ──────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE edge_journal_entry_source (
      edge_id       VARCHAR PRIMARY KEY,
      src_vid       VARCHAR NOT NULL,
      dst_vid       VARCHAR NOT NULL,
      source_type   VARCHAR NOT NULL,
      _seq          BIGINT NOT NULL,
      created_at    TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_invoice_to_project (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR NOT NULL,
      dst_vid           VARCHAR NOT NULL,
      _seq              BIGINT NOT NULL,
      amount_allocated  DOUBLE PRECISION,
      created_at        TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_agreement_to_invoice (
      edge_id       VARCHAR PRIMARY KEY,
      src_vid       VARCHAR NOT NULL,
      dst_vid       VARCHAR NOT NULL,
      _seq          BIGINT NOT NULL,
      scheduled_at  TIMESTAMPTZ NOT NULL,
      created_at    TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_time_entry_to_invoice (
      edge_id        VARCHAR PRIMARY KEY,
      src_vid        VARCHAR NOT NULL,
      dst_vid        VARCHAR NOT NULL,
      _seq           BIGINT NOT NULL,
      lineitem_cid   VARCHAR NOT NULL,
      created_at     TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_asset_to_depreciation (
      edge_id      VARCHAR PRIMARY KEY,
      src_vid      VARCHAR NOT NULL,
      dst_vid      VARCHAR NOT NULL,
      _seq         BIGINT NOT NULL,
      period_ym    VARCHAR NOT NULL,
      created_at   TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  // ── indexes ────────────────────────────────────────────────────────
  await sql`CREATE INDEX idx_kaikei_je_period      ON vertex_atrecord_kaikei_journal_entry (owner_did, period_ym, posted_at)`.execute(db);
  await sql`CREATE INDEX idx_kaikei_je_source      ON vertex_atrecord_kaikei_journal_entry (source_type, source_did)`.execute(db);
  await sql`CREATE INDEX idx_kaikei_ap_bill_status ON vertex_atrecord_kaikei_ap_bill (owner_did, status, due_at)`.execute(db);
  await sql`CREATE INDEX idx_seikyu_invoice_due    ON vertex_atrecord_seikyu_invoice (owner_did, status, due_at)`.execute(db);
  await sql`CREATE INDEX idx_seikyu_invoice_cust   ON vertex_atrecord_seikyu_invoice (customer_did, issued_at DESC)`.execute(db);
  await sql`CREATE INDEX idx_keiyaku_active        ON vertex_atrecord_keiyaku_agreement (owner_did, signing_status, effective_from)`.execute(db);
  await sql`CREATE INDEX idx_kousuu_time_proj      ON vertex_atrecord_kousuu_time_entry (project_did, entry_date)`.execute(db);
  await sql`CREATE INDEX idx_kousuu_time_member    ON vertex_atrecord_kousuu_time_entry (member_did, entry_date)`.execute(db);
  await sql`CREATE INDEX idx_cost_rate_member_eff  ON vertex_atrecord_kousuu_cost_rate (member_did, effective_from DESC)`.execute(db);

  // ── materialized views ─────────────────────────────────────────────
  // Trial balance: GROUP BY (owner_did, period_ym, account_did) — cardinality bounded by
  // owner_count × period_count × chart_of_accounts (~数十万行 max). No MAX(varchar). Safe.
  await sql`
    CREATE MATERIALIZED VIEW mv_kaikei_trial_balance AS
      SELECT
        owner_did,
        period_ym,
        debit_account_did AS account_did,
        'debit'           AS side,
        SUM(amount)       AS total_amount,
        COUNT(*)          AS entry_count,
        MAX(_seq)         AS _seq
      FROM vertex_atrecord_kaikei_journal_entry
      GROUP BY owner_did, period_ym, debit_account_did
      UNION ALL
      SELECT
        owner_did,
        period_ym,
        credit_account_did,
        'credit',
        SUM(amount),
        COUNT(*),
        MAX(_seq)
      FROM vertex_atrecord_kaikei_journal_entry
      GROUP BY owner_did, period_ym, credit_account_did
  `.execute(db);

  // Invoice aging: plain VIEW (RisingWave streaming MV restricts NOW() to WHERE/HAVING/ON/FROM,
  // and aging_bucket inherently moves with wall-clock time every day — MV freshness benefit is nil).
  await sql`
    CREATE VIEW view_seikyu_invoice_aging AS
      SELECT
        owner_did,
        customer_did,
        vertex_id      AS invoice_did,
        invoice_number,
        total,
        due_at,
        status,
        CASE
          WHEN due_at >  NOW()                        THEN 'current'
          WHEN due_at >  NOW() - INTERVAL '30 days'   THEN 'overdue_30'
          WHEN due_at >  NOW() - INTERVAL '60 days'   THEN 'overdue_60'
          WHEN due_at >  NOW() - INTERVAL '90 days'   THEN 'overdue_90'
          ELSE                                              'overdue_90plus'
        END AS aging_bucket,
        _seq
      FROM vertex_atrecord_seikyu_invoice
      WHERE status IN ('sent','partiallyPaid','overdue')
  `.execute(db);

  // Project burn: plain VIEW (lawfirm Phase D precedent — both source tables start empty,
  // streaming MV provided no freshness benefit and destabilized compute nodes on empty
  // LEFT JOIN GROUP BY at apply time 2026-04-17. Promote to MATERIALIZED VIEW when
  // timeEntry row count exceeds ~100K AND read latency of the burn query exceeds 200ms).
  await sql`
    CREATE VIEW view_kousuu_project_burn AS
      SELECT
        p.vertex_id                              AS project_did,
        p.owner_did,
        p.project_code,
        DATE_TRUNC('month', t.entry_date)        AS period_month,
        SUM(t.hours)                             AS actual_hours,
        SUM(CASE WHEN t.billable THEN t.hours ELSE 0 END) AS billable_hours,
        p.budget_hours
      FROM vertex_atrecord_kousuu_project p
      LEFT JOIN vertex_atrecord_kousuu_time_entry t
        ON t.project_did = p.vertex_id
       AND t.approval_status = 'approved'
      GROUP BY p.vertex_id, p.owner_did, p.project_code,
               DATE_TRUNC('month', t.entry_date), p.budget_hours
  `.execute(db);

  // Plain VIEW: active agreements (lawfirm Phase D pattern — OOM-safe, freshness benefit nil on small table).
  await sql`
    CREATE VIEW view_keiyaku_active_agreements AS
      SELECT
        owner_did,
        counterparty_did,
        vertex_id                                             AS agreement_did,
        title,
        agreement_type,
        effective_from,
        term_months,
        CASE
          WHEN term_months IS NOT NULL
          THEN effective_from + (term_months || ' months')::INTERVAL
          ELSE NULL
        END                                                   AS expires_at,
        auto_renew,
        total_amount,
        currency
      FROM vertex_atrecord_keiyaku_agreement
      WHERE signing_status = 'signed'
        AND terminated_at IS NULL
  `.execute(db);

  // Plain VIEW: AP bills due within 30 days.
  await sql`
    CREATE VIEW view_kaikei_ap_bill_upcoming AS
      SELECT
        owner_did,
        vendor_did,
        vertex_id        AS bill_did,
        bill_number,
        amount,
        due_at,
        status,
        _seq
      FROM vertex_atrecord_kaikei_ap_bill
      WHERE status IN ('pending','approved')
        AND due_at < NOW() + INTERVAL '30 days'
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_kaikei_ap_bill_upcoming`.execute(db);
  await sql`DROP VIEW IF EXISTS view_keiyaku_active_agreements`.execute(db);
  await sql`DROP VIEW IF EXISTS view_kousuu_project_burn`.execute(db);
  await sql`DROP VIEW IF EXISTS view_seikyu_invoice_aging`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kaikei_trial_balance`.execute(db);

  await sql`DROP TABLE IF EXISTS edge_asset_to_depreciation`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_time_entry_to_invoice`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_agreement_to_invoice`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_invoice_to_project`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_journal_entry_source`.execute(db);

  await sql`DROP TABLE IF EXISTS vertex_atrecord_kousuu_cost_rate`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_kousuu_time_entry`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_kousuu_project`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_keiyaku_agreement`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_seikyu_invoice`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_seikyu_customer`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_kaikei_ap_bill`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_kaikei_fixed_asset`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_kaikei_bank_transaction`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_kaikei_journal_entry`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_kaikei_account`.execute(db);
}
