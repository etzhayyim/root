/**
 * Migration 20260429200000: Add missing columns to vertex_yukkuri_video
 * and ADR-0095 identity columns to all yukkuri vertex tables.
 *
 * Background: migration 0059 created the yukkuri vertex tables without
 *   - scenes_json / scene_count / line_count / voice_left / voice_right / script_source
 *     (needed by CF Worker VideoRow type and Zeebe persist task)
 *   - actor_did / org_did / at_did (ADR-0095 required for all new vertex tables)
 *
 * The yukkuri generation table also needs owner_did → org_did alias.
 * All ALTERs are IF NOT EXISTS to be idempotent.
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // Add only columns not yet present (RisingWave does not support IF NOT EXISTS on ALTER TABLE ADD COLUMN).
  // State as of 2026-04-29: scenes_json/scene_count/line_count/voice_left/voice_right/script_source/actor_did/org_did
  // already exist on vertex_yukkuri_video; at_did is the only missing column there.
  for (const stmt of [
    `ALTER TABLE vertex_yukkuri_video ADD COLUMN at_did VARCHAR`,
    `ALTER TABLE vertex_yukkuri_scene ADD COLUMN at_did VARCHAR`,
    `ALTER TABLE vertex_yukkuri_line ADD COLUMN at_did VARCHAR`,
    `ALTER TABLE vertex_yukkuri_asset ADD COLUMN org_did VARCHAR`,
    `ALTER TABLE vertex_yukkuri_asset ADD COLUMN at_did VARCHAR`,
    `ALTER TABLE vertex_yukkuri_generation ADD COLUMN org_did VARCHAR`,
    `ALTER TABLE vertex_yukkuri_generation ADD COLUMN at_did VARCHAR`,
  ]) {
    await sql.raw(stmt).execute(db);
  }
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // Column drops are intentionally omitted — data loss risk on rollback.
}
