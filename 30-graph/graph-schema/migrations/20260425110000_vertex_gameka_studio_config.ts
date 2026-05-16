import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * vertex_gameka_studio_config — single-row dry-run / live gate for
 * tickStudio.bpmn (ADR 2604250900 P7).
 *
 * The autonomous tick fires every R/PT2H. β2 lesson from yoro: ship
 * with a 14-day silent log before any derive. The BPMN reads this
 * row each tick and branches on tick_live_mode:
 *   false (default) → emit audit `gameka.tick.dryRun`, no derive
 *   true            → emit audit + derive proposeGame
 *
 * Operator workflow:
 *   day 0    → migration seeds tick_live_mode=false
 *   day 0–14 → soak. tail audit log; verify briefs are non-degenerate
 *   day 14   → INSERT INTO vertex_gameka_studio_config
 *              (vertex_id, config_id, tick_live_mode, ...) VALUES (...)
 *              with same vertex_id (RW PK-upsert overwrites).
 *
 * Fields beyond tick_live_mode are reserved for future tuning
 * (max_iterations, score_threshold) — not read by P7 BPMN.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gameka_studio_config (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      config_id VARCHAR, tick_live_mode BOOLEAN,
      max_iterations BIGINT, score_threshold DOUBLE PRECISION,
      note VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_gameka_studio_config_id
      ON vertex_gameka_studio_config (config_id)
  `.execute(db);

  // Seed the global config row with tick_live_mode=false. RW PK-upsert
  // semantics make this safe to re-run during dev; in prod the operator
  // flips the flag with a same-vertex_id INSERT.
  await sql`
    INSERT INTO vertex_gameka_studio_config (
      vertex_id, owner_did, rkey, repo,
      config_id, tick_live_mode,
      max_iterations, score_threshold,
      note, created_at
    ) VALUES (
      'at://did:web:gameka.gftd.ai/ai.gftd.apps.gameka.studioConfig/global',
      'did:web:gameka.gftd.ai', 'global', 'did:web:gameka.gftd.ai',
      'global', false,
      3, 0.8,
      'P7 dry-run seed — flip tick_live_mode=true after 14-day soak.',
      '2026-04-25T00:00:00Z'
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_gameka_studio_config_id`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gameka_studio_config`.execute(db);
}
