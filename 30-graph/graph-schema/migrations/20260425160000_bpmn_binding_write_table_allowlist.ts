import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Add per-binding `write_table_allowlist` to enforce that a BPMN
 * `generic.db.insert` task can only write to tables explicitly declared
 * for the calling NSID. Without this column the pyzeebe worker holds
 * root-level psycopg credentials and any well-formed BPMN can write to
 * any table — violating ADR-0036 spirit (worker scoped to own actor's
 * vertex_*).
 *
 * Format: comma-separated table names, NULL = no enforcement (legacy).
 * pyzeebe handler reads this from binding lookup on each job and rejects
 * `table` parameter not in the list.
 *
 * Wave 1-5 defence bindings all write to `vertex_open_defence_event`
 * only — populated below.
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_bpmn_lexicon_binding ADD COLUMN IF NOT EXISTS write_table_allowlist varchar`.execute(db);

  // Populate for defence cluster (105 bindings)
  await sql`
    UPDATE vertex_bpmn_lexicon_binding
       SET write_table_allowlist = 'vertex_open_defence_event'
     WHERE actor_id LIKE 'sys.bpmn.seed.open-defence%'
       AND write_table_allowlist IS NULL
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Leave column in place; data drop only.
  await sql`UPDATE vertex_bpmn_lexicon_binding SET write_table_allowlist = NULL WHERE actor_id LIKE 'sys.bpmn.seed.open-defence%'`.execute(db);
}
