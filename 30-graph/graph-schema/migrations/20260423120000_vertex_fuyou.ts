import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR-0051 — fuyou-koujo (扶養控除等異動申告) actor schema.
 *
 * Two-tier PII split per ADR-0018:
 *   vertex_fuyou_declaration       — Tier 1, federable, hash + status only
 *   vertex_fuyou_declaration_pii   — Tier 3, internal-trust only, signal:v1: BYTEA
 *
 * Plus:
 *   edge_fuyou_employment           — employee did → employer org did (in-effect dates)
 *   mv_fuyou_active_dependents_count — kaikei monthly withholding feed
 *
 * RisingWave constraints handled:
 *   - one ALTER per stmt → using single-stmt CREATE TABLE only
 *   - retention_until kept as varchar (ISO 8601) to dodge timestamp-cast edge cases
 *     observed in 2026-04-22 yabai_sender_reputation work
 *   - Tier 3 payload columns kept as varchar (signal:v1: prefix is opaque base64)
 *     instead of BYTEA — avoids RW psycopg3 binary-mode quirks. The 'signal:v1:'
 *     prefix is the runtime tag (10-protocol/wproto/src/signal.ts).
 *   - MV body avoids GROUP BY on high-cardinality columns; cardinality is bounded
 *     by ~10K employees × ~3 employers × ~5 tax years << 500K threshold.
 *
 * Promoted columns (per 30-graph/graph-schema/CLAUDE.md convention):
 *   vertex_id (PK), _seq, created_date, sensitivity_ord, owner_did, org_id,
 *   user_id, actor_id + entity-specific columns.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_fuyou_declaration (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      employee_did       varchar NOT NULL,
      employer_org_id    varchar NOT NULL,
      tax_year           smallint NOT NULL,
      process_type       varchar NOT NULL,
      status             varchar NOT NULL,
      declaration_hash   varchar NOT NULL,
      amendment_count    int,
      bpmn_instance_key  bigint,
      submitted_at       varchar,
      approved_at        varchar,
      approved_by_did    varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_fuyou_declaration_pii (
      vertex_id           varchar PRIMARY KEY,
      _seq                bigint,
      created_date        date,
      sensitivity_ord     int,
      owner_did           varchar,
      applicant_payload   varchar NOT NULL,
      spouse_payload      varchar,
      dependents_payload  varchar NOT NULL,
      minor_dep_payload   varchar,
      special_status      varchar,
      amendment_log       varchar,
      retention_until     varchar NOT NULL,
      created_at          varchar,
      org_id              varchar,
      user_id             varchar,
      actor_id            varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_fuyou_employment (
      edge_id          varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      src_vid          varchar NOT NULL,
      dst_vid          varchar NOT NULL,
      effective_from   varchar NOT NULL,
      effective_to     varchar,
      employment_kind  varchar,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  /**
   * Streaming MV that kaikei reads at month-close to recompute
   * monthly withholding. Weights are applied at query time
   * (general 38, specific 63, elderly 48, elderlyCohabit 58, spouse 38).
   *
   * vertex_fuyou_declaration_pii.dependents_payload holds the encrypted
   * authoritative array, so the count cannot be derived here without
   * decrypting. Phase 1 strategy: kaikei fetches the row (RLS-gated)
   * and decrypts client-side (= host SDK side) before applying the
   * deduction-unit weights. This MV therefore only exposes the lifecycle
   * pivot (one row per active approved declaration), not the dependent
   * count itself.
   */
  await sql`
    CREATE MATERIALIZED VIEW mv_fuyou_active_declaration AS
    SELECT
      employee_did,
      employer_org_id,
      tax_year,
      vertex_id,
      status,
      amendment_count,
      approved_at
    FROM vertex_fuyou_declaration
    WHERE status IN ('approved', 'amended')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_fuyou_active_declaration`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_fuyou_employment`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fuyou_declaration_pii`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fuyou_declaration`.execute(db);
}
