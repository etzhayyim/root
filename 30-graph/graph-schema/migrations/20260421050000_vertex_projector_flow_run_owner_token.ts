import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 5b (ADR-0045): ownership token for vertex_projector_flow_run.
 *
 * RisingWave does not support pg_advisory_lock (see scripts/migrate.ts
 * RisingWaveAdapter — acquireMigrationLock is no-op). The Phase 4
 * runner scans runnable runs and advances each, but two cron isolates
 * hitting the same tick window can pick up the same run twice.
 *
 * Fix: optimistic ownership token.
 *   - scanRunnableRuns generates a tick UUID and UPDATEs each
 *     candidate with owner_token=$uuid, owner_token_expires_at=$now+5m
 *     only when the token is NULL or expired.
 *   - Subsequent SELECT returns only rows we claimed.
 *   - advanceRun clears the token on terminal states (done/failed/
 *     suspended) and extends expiry on long-running agentLoop calls
 *     that exceed the 5-minute window.
 *
 * Pre-existing runs have NULL tokens (free to claim). Expiry is
 * stored as ISO string to match the rest of the timestamp convention
 * in this repo (RW rejects `CURRENT_TIMESTAMP` defaults in several
 * column types).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    ALTER TABLE vertex_projector_flow_run
    ADD COLUMN IF NOT EXISTS owner_token VARCHAR
  `.execute(db);
  await sql`
    ALTER TABLE vertex_projector_flow_run
    ADD COLUMN IF NOT EXISTS owner_token_expires_at VARCHAR
  `.execute(db);

  // Index on (status, owner_token_expires_at) drives the runnable +
  // claimable scan.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_projector_flow_run_claimable
    ON vertex_projector_flow_run (status, owner_token_expires_at)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_projector_flow_run_claimable`.execute(db);
  await sql`ALTER TABLE vertex_projector_flow_run DROP COLUMN IF EXISTS owner_token_expires_at`.execute(db);
  await sql`ALTER TABLE vertex_projector_flow_run DROP COLUMN IF EXISTS owner_token`.execute(db);
}
