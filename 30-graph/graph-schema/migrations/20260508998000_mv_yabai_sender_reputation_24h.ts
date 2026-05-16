/**
 * Streaming MV: vertex_yabai_evidence rolling 24h sender reputation.
 *
 * Phase 3 of the gmail triage rollout (ADR-0032 §T2 sender reputation).
 * Drives the `_node_t2_reputation` lookup in `gmail.triage.v1` LangGraph:
 * senders with ≥3 evidence rows or any severity≥8 in the last 24h get a
 * score bump that may push them from gray → spam without an LLM call.
 *
 * Cardinality safety (per CLAUDE.md §MV Memory Safety):
 *   - GROUP BY entity_id where entity_id ∈ unique sender addresses
 *     (bounded by unique-actor count in vertex_yabai_evidence, expected
 *     <50K well-becoming over 24h window).
 *   - 4 narrow aggregates (count/max/avg/distinct) only — no MAX(varchar)
 *     fan-out which is the documented OOM trigger.
 *   - 24h tumbling window via occurred_at cast keeps state bounded.
 *
 * Note: occurred_at is VARCHAR (ISO 8601). RW supports timestamptz cast.
 */
import { Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_yabai_sender_reputation_24h`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_yabai_sender_reputation_24h AS
    SELECT
      entity_id,
      COUNT(*)                     AS evidence_count_24h,
      MAX(severity)                AS max_severity_24h,
      AVG(confidence)              AS avg_confidence_24h,
      COUNT(DISTINCT category)     AS distinct_categories_24h,
      MAX(occurred_at)             AS last_occurred_at
    FROM vertex_yabai_evidence
    WHERE occurred_at IS NOT NULL
      AND occurred_at::timestamptz > now() - INTERVAL '24 hours'
    GROUP BY entity_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_yabai_sender_reputation_24h`.execute(db);
}
