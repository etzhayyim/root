import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 65 — downgrade priority_weight for under-performing Wikipedia
 * langs. Telemetry from last 30 min showed:
 *   - Wikipedia: 20 picks, 7 productive (35%), 32 rows total, avg 5 rows
 *   - Wikidata:  18 picks, 18 productive (100%), 900 rows, avg 50 rows
 *
 * With 97 Wikipedia targets mostly at collected=0-10, they dominate
 * advance-pick slots (high gap_score from low coverage) but yield tiny
 * rows-per-call because Wikipedia `gsradius=10000` returns few articles
 * for minor langs in rotated JP bboxes.
 *
 * Fix: lower priority_weight 0.6 → 0.35 for langs with collected < 100.
 * Wikidata dispatches (priority 0.6–0.7) now outrank them, reclaiming
 * advance slots for the 50-row-per-pick ones.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_maps_coverage_target
       SET priority_weight = 0.35
     WHERE source_did LIKE 'did:web:maps.gftd.ai:wikipedia:%'
       AND collected_count < 100
  `.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_maps_coverage_target
       SET priority_weight = 0.6
     WHERE source_did LIKE 'did:web:maps.gftd.ai:wikipedia:%'
       AND priority_weight = 0.35
  `.execute(db);
  await sql`FLUSH`.execute(db);
}
