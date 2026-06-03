// ADR-0095 P2 — normalize_actor_did() at_did resolution.
//
// RisingWave SQL UDFs are plan-time inlined expressions and cannot reference
// tables. The at_did → actor_did resolution therefore lives in a streaming MV
// (mv_erc725_at_resolution) rather than inside the UDF body itself.
//
// What this migration does:
//   1. Adds idx_erc725_linked_method_at_did index (fast at_did lookup).
//   2. Creates mv_erc725_at_resolution — narrow streaming MV:
//        at_did → actor_did from vertex_erc725_linked_method WHERE revoked_at IS NULL.
//   3. Rebuilds mv_actor_canonical_did to UNION in the new resolution path:
//        - existing: normalize_actor_did(did:web path) for registered actors
//        - new: at_did → ERC725 actor_did for AT Protocol callers (did:plc / did:web federation)
//
// After this migration, any caller that JOINs mv_actor_canonical_did on raw_did
// will resolve AT Protocol DIDs to their ERC725 canonical DID automatically.
// com.etzhayyim.signal.getPrekeyBundle already does an app-layer at_did fallback (ADR-0095 §D4).

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // 1. Index on at_did for O(log n) resolution queries.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_erc725_linked_method_at_did
      ON vertex_erc725_linked_method (at_did)
  `.execute(db);

  // 2. Narrow streaming MV: at_did → actor_did.
  //    Cardinality is bounded by linked-method count with at_did set (small–medium).
  //    revoked_at IS NULL guard excludes revoked links.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_erc725_at_resolution AS
    SELECT at_did, actor_did
    FROM vertex_erc725_linked_method
    WHERE at_did IS NOT NULL
      AND revoked_at IS NULL
  `.execute(db);

  // 3. Rebuild mv_actor_canonical_did with the AT resolution path.
  //    Drop first — no downstream MVs depend on it (verified 2026-04-28).
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_canonical_did`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_actor_canonical_did AS
    SELECT DISTINCT raw_did, canonical_did
    FROM (
      -- Path A: did:web path normalization for registered etzhayyim actors.
      SELECT
        raw_did,
        normalize_actor_did(raw_did) AS canonical_did
      FROM (
        SELECT actor_did AS raw_did FROM mv_actor_social_stats
        UNION ALL
        SELECT actor_did AS raw_did FROM mv_actor_governance_policy
        UNION ALL
        SELECT actor_did AS raw_did FROM mv_actor_tool_grants
      ) AS s
      UNION ALL
      -- Path B: AT Protocol at_did → ERC725 actor_did resolution.
      --         Handles did:plc and non-etzhayyim did:web federation aliases.
      SELECT at_did AS raw_did, actor_did AS canonical_did
      FROM mv_erc725_at_resolution
    ) AS combined
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Restore mv_actor_canonical_did without the AT resolution UNION.
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_canonical_did`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_actor_canonical_did AS
    SELECT DISTINCT raw_did, normalize_actor_did(raw_did) AS canonical_did
    FROM (
      SELECT actor_did AS raw_did FROM mv_actor_social_stats
      UNION ALL
      SELECT actor_did AS raw_did FROM mv_actor_governance_policy
      UNION ALL
      SELECT actor_did AS raw_did FROM mv_actor_tool_grants
    ) AS s
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_erc725_at_resolution`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_erc725_linked_method_at_did`.execute(db);
}
