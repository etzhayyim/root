import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * vertex_yoro_monitor_attestation + vertex_yoro_monitor_vote — triple-witness
 * autonomy monitoring for yoro.gftd.ai (ADR-0046).
 *
 * Three independent monitor actors (Monitor-L on jacob / Monitor-K on judah /
 * Monitor-B on CF Worker) attest per-axis health of yoro and cross-attest
 * each other. Corrective actions (pause / rollback / rotate-key) require a
 * 2-of-3 quorum recorded in vertex_yoro_monitor_vote. alert and escalate
 * actions are unilateral (informational only).
 *
 * Writes go through createKyselyDb(env.HYPERDRIVE) from each monitor's own
 * Worker (ADR-0036 worker-direct-hyperdrive). This bypasses the PDS commit
 * pipeline so a compromise of yoro's signing key cannot forge attestations
 * or cast ballots — each monitor key is independent.
 *
 * Phase 0 deliverable (see ADR-0046 §Implementation Phases).
 * No MV in this migration (§MV Memory Safety Guardrails in 30-graph/graph-schema/CLAUDE.md).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // Per-monitor per-tick observation record. One row every time a monitor
  // runs its cron (L: */5m, K: */15m, B: */10m). cross_seen_json captures
  // the last-tick timestamps the monitor saw from the other two peers so
  // a silent monitor is detected without a separate heartbeat table.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yoro_monitor_attestation (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      monitor_did VARCHAR, axis VARCHAR, subject_did VARCHAR,
      observed_at VARCHAR, status VARCHAR, fault_class VARCHAR,
      signals_json VARCHAR, cross_seen_json VARCHAR, sig_es256 VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yoro_monitor_attestation_monitor_observed
      ON vertex_yoro_monitor_attestation (monitor_did, observed_at DESC)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yoro_monitor_attestation_subject_axis_observed
      ON vertex_yoro_monitor_attestation (subject_did, axis, observed_at DESC)
  `.execute(db);

  // Corrective-action vote. One row per vote opened by any monitor.
  // ballots_json is updated-in-place as peers cast yea/nay; ballot_count
  // and yea_count are promoted so 2-of-3 quorum is an O(1) check.
  //
  // action tier (ADR-0046 §Corrective Action Tier):
  //   alert, escalate  — unilateral (resolution='passed' on open)
  //   pause, rollback, rotate-key — require 2-of-3 yea
  //
  // human_override carries a ticket URL when oncall force-passes a vote;
  // never populated by monitors themselves. Audit sink reads it directly.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yoro_monitor_vote (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      subject_did VARCHAR, action VARCHAR, reason VARCHAR, requested_by VARCHAR,
      opened_at VARCHAR, closes_at VARCHAR,
      ballots_json VARCHAR, ballot_count BIGINT, yea_count BIGINT,
      resolution VARCHAR, resolved_at VARCHAR, human_override VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_yoro_monitor_vote_subject_open
      ON vertex_yoro_monitor_vote (subject_did, resolution, opened_at DESC)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_yoro_monitor_vote_subject_open`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yoro_monitor_vote`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_yoro_monitor_attestation_subject_axis_observed`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_yoro_monitor_attestation_monitor_observed`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yoro_monitor_attestation`.execute(db);
}
