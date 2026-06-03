import { Kysely, sql } from 'kysely';

/**
 * ADR-0031 Phase C — P/L + B/S streaming MVs for kaikei.
 *
 * Built on vertex_atrecord_kaikei_journal_entry (with debit_amount /
 * credit_amount separated columns from β4).  Groupings bounded by
 * owner_count (~3) × period_count (~80) × account_type (5) → < 2K rows.
 * No MAX(varchar), no wide column fan-out — safe for streaming MV.
 *
 * Account-type convention matches ingest_year_multi.py classify():
 *   asset / liability / equity / revenue / expense.
 *
 * DID format:
 *   j.debit_account_did   = 'did:plc:etzhayyim-works:account:{hash16}'
 *   a.vertex_id           = 'did:plc:etzhayyim-works|com.etzhayyim.apps.kaikei.account|{hash16}'
 *   → JOIN via SPLIT_PART(..., ':', 5) on the account DID hash.
 *
 * Spec: 90-docs/adr/0031-moneyforward-actor-replacement.md §Phase C.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── mv_kaikei_pl_period ────────────────────────────────────────────
  // Flow per owner × period × account_type.  Expense accounts accumulate on
  // the debit side; revenue accounts accumulate on the credit side.  Emitted
  // as UNION ALL of the two sides so streaming agg state stays narrow.
  await sql`
    CREATE MATERIALIZED VIEW mv_kaikei_pl_period AS
      SELECT
        owner_did,
        period_ym,
        account_type,
        SUM(amount)  AS total,
        COUNT(*)     AS entry_count,
        MAX(_seq)    AS _seq
      FROM (
        SELECT
          j.owner_did,
          j.period_ym,
          a.account_type,
          j.debit_amount  AS amount,
          j._seq
        FROM vertex_atrecord_kaikei_journal_entry j
        JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did = j.owner_did
         AND a.vertex_id = j.owner_did || '|com.etzhayyim.apps.kaikei.account|'
                         || SPLIT_PART(j.debit_account_did, ':', 5)
        WHERE a.account_type = 'expense'
        UNION ALL
        SELECT
          j.owner_did,
          j.period_ym,
          a.account_type,
          j.credit_amount AS amount,
          j._seq
        FROM vertex_atrecord_kaikei_journal_entry j
        JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did = j.owner_did
         AND a.vertex_id = j.owner_did || '|com.etzhayyim.apps.kaikei.account|'
                         || SPLIT_PART(j.credit_account_did, ':', 5)
        WHERE a.account_type = 'revenue'
      ) x
      GROUP BY owner_did, period_ym, account_type
  `.execute(db);

  // ── mv_kaikei_bs_delta ─────────────────────────────────────────────
  // Per-period DELTA for balance-sheet account_types.  Asset balance moves
  // with (debit − credit); liability/equity with (credit − debit).  Caller
  // sums across periods from open to target period_ym for the cumulative
  // snapshot — keeps MV state bounded and streaming-safe.
  await sql`
    CREATE MATERIALIZED VIEW mv_kaikei_bs_delta AS
      SELECT
        owner_did,
        period_ym,
        account_type,
        SUM(net_amount) AS delta,
        COUNT(*)        AS entry_count,
        MAX(_seq)       AS _seq
      FROM (
        SELECT
          j.owner_did,
          j.period_ym,
          a.account_type,
          j.debit_amount  AS net_amount,
          j._seq
        FROM vertex_atrecord_kaikei_journal_entry j
        JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did = j.owner_did
         AND a.vertex_id = j.owner_did || '|com.etzhayyim.apps.kaikei.account|'
                         || SPLIT_PART(j.debit_account_did, ':', 5)
        WHERE a.account_type IN ('asset','liability','equity')
        UNION ALL
        SELECT
          j.owner_did,
          j.period_ym,
          a.account_type,
          -j.credit_amount AS net_amount,
          j._seq
        FROM vertex_atrecord_kaikei_journal_entry j
        JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did = j.owner_did
         AND a.vertex_id = j.owner_did || '|com.etzhayyim.apps.kaikei.account|'
                         || SPLIT_PART(j.credit_account_did, ':', 5)
        WHERE a.account_type = 'asset'
        UNION ALL
        SELECT
          j.owner_did,
          j.period_ym,
          a.account_type,
          j.credit_amount AS net_amount,
          j._seq
        FROM vertex_atrecord_kaikei_journal_entry j
        JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did = j.owner_did
         AND a.vertex_id = j.owner_did || '|com.etzhayyim.apps.kaikei.account|'
                         || SPLIT_PART(j.credit_account_did, ':', 5)
        WHERE a.account_type IN ('liability','equity')
        UNION ALL
        SELECT
          j.owner_did,
          j.period_ym,
          a.account_type,
          -j.debit_amount AS net_amount,
          j._seq
        FROM vertex_atrecord_kaikei_journal_entry j
        JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did = j.owner_did
         AND a.vertex_id = j.owner_did || '|com.etzhayyim.apps.kaikei.account|'
                         || SPLIT_PART(j.debit_account_did, ':', 5)
        WHERE a.account_type IN ('liability','equity')
      ) x
      GROUP BY owner_did, period_ym, account_type
  `.execute(db);

  // ── view_kaikei_monthly_summary ────────────────────────────────────
  // Plain VIEW: one row per (owner, period, account_type) covering both P/L
  // flows and B/S deltas.  Consumed by /xrpc/...getMonthlySummary.
  await sql`
    CREATE VIEW view_kaikei_monthly_summary AS
      SELECT
        owner_did,
        period_ym,
        account_type,
        total              AS flow_amount,
        NULL::DOUBLE PRECISION AS bs_delta,
        entry_count,
        _seq
      FROM mv_kaikei_pl_period
      UNION ALL
      SELECT
        owner_did,
        period_ym,
        account_type,
        NULL::DOUBLE PRECISION AS flow_amount,
        delta                   AS bs_delta,
        entry_count,
        _seq
      FROM mv_kaikei_bs_delta
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_kaikei_monthly_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kaikei_bs_delta`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kaikei_pl_period`.execute(db);
}
