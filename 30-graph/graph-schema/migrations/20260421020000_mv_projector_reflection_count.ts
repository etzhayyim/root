import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * mv_projector_reflection_count — per-convo Reflexion episodic memory
 * count, sourced from the ADR-0036 vertex_projector_reflection table.
 *
 * Replaces the legacy mv_project_reflection_count (migration
 * 20260416170000_count_rollups_mv.ts) which was keyed on
 * vertex_convo WHERE kind='ai.gftd.projector.reflection' — that path
 * is retired when ai.gftd.projector.reflection AT records stop being
 * created. The legacy MV stays in place (harmless, always 0 rows once
 * the switch completes) and will be dropped in a follow-up once no
 * reader references it.
 *
 * Streaming MV (RisingWave default). Freshness < 100ms.
 * Drives ai.gftd.projector.addReflection response field
 * `totalReflections` and could also drive UI badges in yoro /projects.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_projector_reflection_count AS
    SELECT
      convo_id,
      COUNT(*)::bigint AS cnt
    FROM vertex_projector_reflection
    WHERE convo_id IS NOT NULL
    GROUP BY convo_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_projector_reflection_count`.execute(db);
}
