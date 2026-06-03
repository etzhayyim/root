import { Kysely, sql } from 'kysely';

/**
 * ADR-0029 did:etzhayyim recursive semantic path — schema extension (revised 2026-04-19).
 *
 * Extends vertex_etzhayyim_identity (migration 20260416140100) with recursion columns
 * so that a DID tree rooted at a P-256 actor key can carry capability / entity /
 * grant / session descendants, each identified by a `(sub, id, lexicon)` semantic
 * segment tuple:
 *
 *   did:etzhayyim:{s0}:{s1}:…:{sN}      where sN ∈ [a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*
 *
 * Adds:
 *   vertex_etzhayyim_identity.parent_did           — parent DID (NULL = root)
 *   vertex_etzhayyim_identity.depth                — 1 = root, N+1 = child of depth N
 *   vertex_etzhayyim_identity.segment_kind         — root|sub|id|lexicon|role|pubkey|grant
 *   vertex_etzhayyim_identity.segment_value        — semantic segment value (slug / NSID / TID)
 *   vertex_etzhayyim_identity.pubkey_multibase     — NOT NULL for segment_kind ∈ {root, pubkey}
 *   vertex_etzhayyim_identity.material_kind        — LEGACY (ADR-0029 草案). kept nullable for
 *                                               Phase 1 hex Merkle callers during
 *                                               ADR-0030 Phase 4 migration; dropped in a
 *                                               follow-up migration after all adopters
 *                                               switch to segment_kind/segment_value.
 *   vertex_etzhayyim_identity.material_hash_proof  — LEGACY (same lifecycle as material_kind).
 *                                               Verifiers recompute child hash from
 *                                               hex(materialBytes) until migration completes.
 *   vertex_etzhayyim_identity.revoked_at           — ISO 8601; ancestor revoke cascades
 *
 *   idx_vertex_etzhayyim_identity_parent           ON (parent_did)
 *   idx_vertex_etzhayyim_identity_parent_kind      ON (parent_did, segment_kind)
 *
 *   mv_etzhayyim_identity_children                 — per-parent child counts by kind
 *
 * Backfills existing Phase 1 flat hex rows (depth=1, segment_kind='root',
 * segment_value=<hex slice>) so the flat `did:etzhayyim:{24-hex}` form is preserved
 * as the grandfather special case. New mints use semantic form only.
 *
 * Design: 90-docs/adr/0029-did-etzhayyim-recursive-hash-merkle.md
 * Base:   30-graph/graph-schema/migrations/20260416140100_etzhayyim_did_identity_graph.ts
 */

export async function up(db: Kysely<any>): Promise<void> {
  // ── ALTER: recursion columns ──────────────────────────────────────────

  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN parent_did VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN depth BIGINT`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN segment_kind VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN segment_value VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN pubkey_multibase VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  // Legacy hex Merkle columns — kept nullable during ADR-0030 Phase 4 transition.
  // Dropped in a follow-up migration after all app adopters switch to semantic form.
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN material_kind VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN material_hash_proof VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN revoked_at VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── Backfill: Phase 1 flat hex DIDs → depth=1, segment_kind='root' ────
  // Existing did:etzhayyim:{24-hex} rows become grandfather entries. The 24-hex
  // tail is stored in segment_value so the resolver can address them as
  // root DIDs under the semantic schema without renaming the DID itself.

  await sql`UPDATE vertex_etzhayyim_identity
    SET depth = 1,
        segment_kind = 'root',
        segment_value = SUBSTRING(did FROM 10)
    WHERE depth IS NULL
      AND parent_did IS NULL
      AND did LIKE 'did:etzhayyim:%'`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── Indexes ────────────────────────────────────────────────────────────

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_parent
    ON vertex_etzhayyim_identity(parent_did)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_parent_kind
    ON vertex_etzhayyim_identity(parent_did, segment_kind)`.execute(db);
  await sql`FLUSH`.execute(db);

  // Collision prevention: one (parent, kind, value) tuple per child.
  // Legacy flat hex rows (parent_did IS NULL, kind='root') are unique by did
  // which is already the primary identifier; the partial index still applies.
  await sql`CREATE UNIQUE INDEX IF NOT EXISTS uq_vertex_etzhayyim_identity_parent_kind_value
    ON vertex_etzhayyim_identity(parent_did, segment_kind, segment_value)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── MV: per-parent child distribution (bounded by identity tree size) ─

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_identity_children AS
    SELECT
      parent_did,
      segment_kind,
      COUNT(*) AS child_count,
      COUNT(*) FILTER (WHERE revoked_at IS NULL) AS active_child_count
    FROM vertex_etzhayyim_identity
    WHERE parent_did IS NOT NULL
    GROUP BY parent_did, segment_kind`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_identity_children`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS uq_vertex_etzhayyim_identity_parent_kind_value`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_parent_kind`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_parent`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN revoked_at`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN material_hash_proof`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN material_kind`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN pubkey_multibase`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN segment_value`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN segment_kind`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN depth`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN parent_did`.execute(db);
  await sql`FLUSH`.execute(db);
}
