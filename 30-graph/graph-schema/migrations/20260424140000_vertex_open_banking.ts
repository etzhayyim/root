import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * open-banking Phase 1 schema (ADR-0056 BPMN-as-actor).
 *
 * Double-entry ledger — balance is derived, never stored.
 *   vertex_open_banking_account
 *   vertex_open_banking_ledger_entry  (1 debit + 1 credit row per transfer)
 *   edge_open_banking_transfer_pair   (link debit↔credit for audit)
 *   mv_open_banking_balance           (derived balance per account)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_banking_account (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar NOT NULL,
      account_number   varchar NOT NULL,
      account_type     varchar NOT NULL,
      currency         varchar NOT NULL,
      display_name     varchar,
      status           varchar NOT NULL,
      opened_at        varchar NOT NULL,
      closed_at        varchar,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_open_banking_ledger_entry (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      account_vid      varchar NOT NULL,
      transaction_id   varchar NOT NULL,
      direction        varchar NOT NULL,
      amount           double precision NOT NULL,
      currency         varchar NOT NULL,
      counterparty_vid varchar,
      memo             varchar,
      executed_at      varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_open_banking_transfer_pair (
      edge_id          varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      src_vid          varchar NOT NULL,
      dst_vid          varchar NOT NULL,
      transaction_id   varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_open_banking_balance AS
    SELECT
      account_vid,
      currency,
      SUM(CASE WHEN direction = 'credit' THEN amount ELSE 0 END) -
      SUM(CASE WHEN direction = 'debit'  THEN amount ELSE 0 END) AS balance,
      COUNT(*)                                                   AS entry_count,
      MAX(executed_at)                                           AS last_executed_at
    FROM vertex_open_banking_ledger_entry
    GROUP BY account_vid, currency
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_banking_balance`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_banking_transfer_pair`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_banking_ledger_entry`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_banking_account`.execute(db);
}
