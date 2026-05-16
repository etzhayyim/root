import type { Kysely } from "kysely";
import { sql } from "kysely";

// Phase 12 — cluster-wide actor label resolver (ADR-0074).
//
// The Sankey AppView needs a readable display name for every distinct
// DID it sees in the edge list — both ERC725 root DIDs (canonical actor
// vector keys per ADR-0074 T1) and AT facade DIDs (`did:web:...` or
// `did:plc:...`). We give it a single plain VIEW that:
//
//   1. starts from `vertex_profile` (canonical AT profile),
//   2. left-joins the ERC725 facade ↔ root mapping
//      (`edge_erc725_facade_did` from migration 20260426233000), and
//   3. emits one row per (did, kind) so a single `WHERE did IN (...)`
//      lookup returns labels regardless of whether the caller supplied
//      a root DID or a facade DID.
//
// Plain VIEW (not MV) — query-time evaluation, zero streaming state,
// safe for the high-cardinality `vertex_profile` table.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE VIEW view_resource_flow_actor_label AS
    -- Branch A: facade DID lookup (did:web / did:plc).
    SELECT
      p.did                                                AS did,
      'facade'::VARCHAR                                    AS kind,
      p.did                                                AS facade_did,
      e.root_did                                           AS root_did,
      p.handle                                             AS handle,
      p.display_name                                       AS display_name,
      p.description                                        AS description,
      e.root_identity_addr                                 AS root_identity_addr
    FROM vertex_profile p
    LEFT JOIN edge_erc725_facade_did e ON e.facade_did = p.did
    UNION ALL
    -- Branch B: ERC725 root DID lookup. Resolves through facade for the
    -- display fields; if no facade exists yet, the row still surfaces
    -- the root_did for completeness (display_name = NULL).
    SELECT
      e.root_did                                           AS did,
      'root'::VARCHAR                                      AS kind,
      e.facade_did                                         AS facade_did,
      e.root_did                                           AS root_did,
      p.handle                                             AS handle,
      p.display_name                                       AS display_name,
      p.description                                        AS description,
      e.root_identity_addr                                 AS root_identity_addr
    FROM edge_erc725_facade_did e
    LEFT JOIN vertex_profile p ON p.did = e.facade_did
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_resource_flow_actor_label`.execute(db);
}
