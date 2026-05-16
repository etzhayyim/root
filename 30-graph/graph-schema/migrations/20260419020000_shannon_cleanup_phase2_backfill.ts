import { Kysely, sql } from "kysely";

/**
 * Shannon Redundancy Cleanup — Phase 2 (bulk backfill, zero-risk).
 *
 * Scope (intentionally narrow): backfill `vertex_actor_profile` from the
 * existing `vertex_actor` table (787,260 rows as of 2026-04-19), without
 * touching any of the 13 downstream streaming MVs.
 *
 * After this migration, `vertex_actor_profile` holds the same identity
 * surface as `vertex_actor`, exposed through `view_actor_unified` (created
 * in Phase 1). Readers can migrate to the view at their own pace; writers
 * keep writing to `vertex_actor` until Phase 3 flips the dual-write flag.
 *
 * NOT in this migration (deferred to Phase 3):
 *   - Dropping vertex_actor
 *   - Rebuilding 13 MVs (mv_actor_*, mv_profile_*)
 *   - Dropping vertex_did / vertex_profile
 *   - Slimming vertex_actor_manifest duplicate columns
 *
 * Phase 3 prerequisites:
 *   - Graph worker dual-writes to both vertex_actor AND vertex_actor_profile
 *     for at least 24h so no events are lost during cutover
 *   - All PDS XRPC handlers read from view_actor_unified (not vertex_actor)
 *   - MV rebuild script written & tested on a staging replica
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  // Enable locality_backfill for large write — keeps S3 Hummock write
  // pressure manageable on 787K-row INSERT (per 2026-04-16 playbook).
  await sql`SET enable_locality_backfill = true`.execute(db);

  // Idempotent one-shot backfill. WHERE NOT EXISTS guard lets us re-run
  // safely if interrupted. vertex_id is the PK, so dedup by vertex_id.
  //
  // Column mapping (vertex_actor → vertex_actor_profile):
  //   vertex_id, did, handle, display_name, avatar_cid, banner_cid,
  //   execution_tier, performer_type, nanoid, category, country, status,
  //   created_at, _seq, created_date, sensitivity_ord, owner_did
  //
  // `description` is intentionally NOT backfilled — it lives in
  // vertex_actor_manifest in the current schema, not vertex_actor. Readers
  // compose description via view_actor_unified's COALESCE() fallback.
  await sql`
    INSERT INTO vertex_actor_profile (
      vertex_id, did, handle, display_name,
      avatar_cid, banner_cid, execution_tier, performer_type,
      nanoid, category, country, status,
      created_at, _seq, created_date, sensitivity_ord, owner_did
    )
    SELECT
      a.vertex_id, a.did, a.handle, a.display_name,
      a.avatar_cid, a.banner_cid, a.execution_tier, a.performer_type,
      a.nanoid, a.category, a.country, a.status,
      a.created_at, a._seq, a.created_date, a.sensitivity_ord, a.owner_did
    FROM vertex_actor a
    WHERE a.vertex_id IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM vertex_actor_profile p
        WHERE p.vertex_id = a.vertex_id
      )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`SET enable_locality_backfill = false`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Intentionally *not* auto-deleting backfilled rows: down() for a bulk
  // backfill is dangerous (it could delete rows that are now the SSoT
  // because later writes went here). If a true rollback is needed:
  //
  //   TRUNCATE vertex_actor_profile;
  //   -- then rerun Phase 1 down() to drop the table entirely.
  //
  // No-op here. The Phase 1 migration can still be reversed independently.
  void db;
}
