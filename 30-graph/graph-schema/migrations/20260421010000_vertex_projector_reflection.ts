import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_projector_reflection — dedicated table for Shinn et al.
 * Reflexion episodic memory (per-convo lesson buffer).
 *
 * Design A Phase 2 (2026-04-21): reflections don't fit
 * vertex_projector_flow_step cleanly — they are convo-scoped episodic
 * memory, not run/node/step-scoped execution log. Splitting them out
 * keeps flow_step cohesive and makes the reflexion load path a single
 * indexed lookup (convo_id + _seq DESC, limit 5 for system prompt
 * injection).
 *
 * Columns mirror the retired AT record shape
 * (`app.etzhayyim.projector.reflection`):
 *   convoId / attempt / outcome / reflection / createdBy / createdAt
 *
 * Call sites it replaces (per Phase 2 handler rewrite):
 *   - app.etzhayyim.projector.addReflection (XRPC)
 *   - /reflect slash command in sendProjectMessage
 *   - auto-reflexion failure detection in sendProjectMessage
 *   - reflexion buffer load in sendProjectMessage system prompt
 *   - app.etzhayyim.projector.listReflections (XRPC)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_projector_reflection (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      convo_id VARCHAR, attempt VARCHAR, outcome VARCHAR, reflection VARCHAR,
      created_by VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  // Per-convo ordered lookup: reflexion system prompt injection reads
  // the most recent N lessons (ORDER BY _seq DESC LIMIT 5).
  await sql`CREATE INDEX IF NOT EXISTS idx_projector_reflection_convo
            ON vertex_projector_reflection (convo_id, _seq)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_projector_reflection_convo`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_projector_reflection`.execute(db);
}
