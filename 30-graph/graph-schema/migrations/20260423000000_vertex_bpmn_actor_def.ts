import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * F0 — BPMN-as-actor-source-of-truth schema.
 *
 * Two tables:
 *   vertex_bpmn_process_def     : authoritative BPMN XML (one row per process+version)
 *   vertex_bpmn_lexicon_binding : NSID → bpmnProcessId routing for the
 *                                 generic XRPC dispatcher (F4)
 *
 * The intent is for **most T1/T2 actors to live as data here** instead of
 * shipping per-actor TS apps:
 *   - new actor = INSERT vertex_bpmn_process_def + INSERT vertex_bpmn_lexicon_binding
 *   - generic dispatcher (CF Worker) reads lexicon_binding, calls
 *     Zeebe.run_process_with_result(bpmn_process_id, body)
 *   - generic primitives in zeebe-worker handle the actual side effects
 *     (db / llm / pds / http)
 *
 * Sync from RW → Zeebe is done by a small watcher loop in zeebe-worker
 * (or a dedicated CronJob). Zeebe's deploy_resource is idempotent on
 * (bpmnProcessId, version) so the watcher just needs to upsert any row
 * not yet deployed.
 *
 * RisingWave constraints handled:
 *   - one ALTER per stmt (we use CREATE TABLE which is fine for one stmt)
 *   - deployed_at stays as ISO varchar (no timestamp cast trouble)
 *   - xml column is varchar; BPMN XML is small (<256KB) so no need for
 *     external blob storage
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_bpmn_process_def (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      bpmn_process_id    varchar NOT NULL,
      version            int     NOT NULL,
      xml                varchar NOT NULL,
      xml_byte_size      int,
      source_path        varchar,
      deployed_at        varchar,
      deployed_zeebe_key bigint,
      status             varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_bpmn_lexicon_binding (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      nsid               varchar NOT NULL,
      bpmn_process_id    varchar NOT NULL,
      bpmn_version       int,
      result_timeout_ms  int,
      status             varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_bpmn_lexicon_binding`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bpmn_process_def`.execute(db);
}
