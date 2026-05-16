/**
 * Migration 0061: Hospitality tier × kind cross-tab MV (ADR-0028 Phase 1).
 *
 * Source: `vertex_profile`. Tier is derived from the path-based DID kind segment
 * (no per-row tier storage required — kind→tier is a static lookup).
 *
 * kind ∈ {assoc, ota, chain, cruise, property}
 * tier ← assoc:R1 / ota:R2 / chain:R3 / cruise:R3 / property:R4
 *
 * Pre-flight (CLAUDE.md §MV Memory Safety Guardrails):
 *   - GROUP BY (tier, kind) → 5×4 = 20 buckets max — safe
 *   - Backfill ≈ 564 rows at Iter 18 — trivial
 *   - No MAX(varchar); CASE + COUNT only
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hospitality_tier_coverage AS
    SELECT
      CASE split_part(split_part(did, ':actor:', 2), ':', 1)
        WHEN 'assoc'    THEN 'R1'
        WHEN 'ota'      THEN 'R2'
        WHEN 'chain'    THEN 'R3'
        WHEN 'cruise'   THEN 'R3'
        WHEN 'property' THEN 'R4'
        ELSE 'unknown'
      END                                                   AS tier,
      split_part(split_part(did, ':actor:', 2), ':', 1)     AS kind,
      COUNT(*)                                              AS actor_cnt
    FROM vertex_profile
    WHERE did LIKE 'did:web:hospitality.gftd.ai:actor:%'
    GROUP BY tier, kind
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_hospitality_tier_coverage`.execute(db);
}
