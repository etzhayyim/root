/**
 * Migration 0060: Hospitality ownership depth rollup (ADR-0028 Phase 1).
 *
 * Source: `edge_owned_by` (migration 0037 — IP cluster context, but reused here
 * for chain→subbrand / parent→property hospitality relationships).
 *
 * Edges are projected from `vertex_repo_record` rows where collection =
 * `ai.gftd.apps.hospitality.ownedBy`. Hospitality emit pipeline:
 *
 *   data/ownership-edges.jsonl
 *     → app.bsky.* style PDS commit
 *       → vertex_repo_record (collection='ai.gftd.apps.hospitality.ownedBy')
 *         → graph-writer projection (TODO: add ownedBy projector)
 *           → edge_owned_by row (src_vid=parent, dst_vid=child)
 *
 * Pre-flight (CLAUDE.md §MV Memory Safety Guardrails):
 *   - GROUP BY src_vid; cardinality ≤ ~20 hospitality parents — safe
 *   - Backfill ≈ 44 rows at Iter 18 — trivial
 *   - No MAX(varchar); COUNT(*) + MAX(_seq) only
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hospitality_ownership_depth AS
    SELECT
      src_vid           AS parent_did,
      COUNT(*)          AS direct_children,
      MAX(_seq)         AS last_seq
    FROM edge_owned_by
    WHERE src_vid LIKE 'did:web:hospitality.gftd.ai:%'
    GROUP BY src_vid
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_hospitality_ownership_depth`.execute(db);
}
