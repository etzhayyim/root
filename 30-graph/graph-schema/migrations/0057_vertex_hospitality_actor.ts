/**
 * Migration 0057: Hospitality actor coverage MV (ADR-0028 Phase 1, AT-Protocol-native).
 *
 * Source: `vertex_profile` (canonical projection of `app.bsky.actor.profile` records).
 * Filter: hospitality.etzhayyim.com path-based DIDs only.
 *
 * Path-based DID convention (ADR-0019):
 *   did:web:hospitality.etzhayyim.com:actor:{kind}:{slug}
 *   kind ∈ {assoc, ota, chain, cruise, property}
 *
 * Pre-flight (CLAUDE.md §MV Memory Safety Guardrails):
 *   - GROUP BY kind → 5 buckets max — safe
 *   - Source row count at Iter 18 ≈ 564 — trivial backfill
 *   - No MAX(varchar); COUNT(*) only
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hospitality_actor_coverage AS
    SELECT
      split_part(split_part(did, ':actor:', 2), ':', 1) AS kind,
      COUNT(*) AS actor_cnt
    FROM vertex_profile
    WHERE did LIKE 'did:web:hospitality.etzhayyim.com:actor:%'
    GROUP BY kind
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_hospitality_actor_coverage`.execute(db);
}
