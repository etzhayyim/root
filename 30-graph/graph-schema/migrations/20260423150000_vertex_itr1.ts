import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR-0055 — ITR-1 Sahaj actor schema.
 *
 * Tier split:
 *   vertex_itr1_return       — Tier 1, federable, hash + totals + ack
 *   vertex_itr1_return_pii   — Tier 3, internal-trust, signal:v1: payloads
 *
 * Plus:
 *   edge_itr1_revised_chain  — predecessor → revised return (§139(5))
 *   mv_itr1_filed_returns    — taxpayer dashboard
 *
 * PAN goes through `taxpayer_pan_hash = sha256(PAN)` on Tier 1, raw PAN
 * lives only in Tier 3 `applicant_payload` (signal:v1: encrypted).
 *
 * Currency: bigint paise.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_itr1_return (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      taxpayer_pan_hash        varchar NOT NULL,
      assessment_year          varchar NOT NULL,
      process_type             varchar NOT NULL,
      status                   varchar NOT NULL,
      filing_hash              varchar NOT NULL,
      total_income_inr_paise   bigint,
      total_tax_inr_paise      bigint,
      refund_inr_paise         bigint,
      tax_payable_inr_paise    bigint,
      regime_selected          varchar,
      ack_number               varchar,
      filed_via                varchar,
      filed_at                 varchar,
      predecessor_vertex_id    varchar,
      revised_reason           varchar,
      amendment_count          int,
      bpmn_instance_key        bigint,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_itr1_return_pii (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      taxpayer_pan_hash      varchar NOT NULL,
      applicant_payload      varchar NOT NULL,
      income_payload         varchar NOT NULL,
      deductions_payload     varchar,
      tax_payload            varchar NOT NULL,
      amendment_log          varchar,
      retention_until        varchar NOT NULL,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_itr1_revised_chain (
      edge_id                varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      src_vid                varchar NOT NULL,
      dst_vid                varchar NOT NULL,
      revised_reason         varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_itr1_filed_returns AS
    SELECT
      taxpayer_pan_hash,
      assessment_year,
      vertex_id,
      status,
      ack_number,
      filed_via,
      total_income_inr_paise,
      total_tax_inr_paise,
      refund_inr_paise,
      tax_payable_inr_paise,
      filed_at
    FROM vertex_itr1_return
    WHERE status IN ('filed', 'revised')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_itr1_filed_returns`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_itr1_revised_chain`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_itr1_return_pii`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_itr1_return`.execute(db);
}
