import { Kysely, sql } from 'kysely';

/**
 * Phase D — lawfirm read-path projection views.
 *
 * Reads off `vertex_etzhayyim_identity` + `mv_etzhayyim_identity_children` only
 * (ADR-0029 recursive DID tree is the single authoritative source). The
 * lexicon-specific `vertex_atrecord_lawfirm_*` tables are PDS-pipeline-
 * generated on first write and do not yet exist on a fresh cluster, so the
 * Phase D projections deliberately do NOT depend on them. A Phase E
 * migration can enrich these views with record-level fields
 * (status enum / matterType / jurisdiction) when those tables appear.
 *
 * ── Implementation note (2026-04-17) ──────────────────────────────────
 * These are plain VIEWs, not MATERIALIZED VIEWs. Both were initially
 * authored as streaming MVs, but applying them to the live cluster
 * (<vendor-rw-host-deprecated>:4566) triggered repeated compute pod recovery loops
 * ("failed to collect barrier", "database 1 unavailable cluster is under
 * recovering") even with `enable_locality_backfill = true` + `background_ddl
 * = true`. Given that `vertex_etzhayyim_identity` is empty at Phase D time
 * (0 matters minted yet), a streaming MV provides no freshness benefit
 * while adding cluster state. Plain VIEWs are cost-free metadata and
 * evaluate on-demand with the same SQL shape.
 *
 * Promote to MATERIALIZED VIEW when either of:
 *   (a) matter_did cardinality exceeds ~1K and read latency matters, or
 *   (b) cluster memory headroom is > 64 GiB and compute is idle.
 * Both were deferred per graph-schema CLAUDE.md §MV Memory Safety Guardrails.
 *
 * Spec: 90-docs/adr/0029-did-etzhayyim-recursive-hash-merkle.md
 * Base: 20260416140100_etzhayyim_did_identity_graph.ts
 *     + 20260417150000_etzhayyim_did_recursive_tree.ts
 */

export async function up(db: Kysely<any>): Promise<void> {
  // ── View 1: view_lawfirm_matter_roster ──────────────────────────────
  // Per-matter summary keyed by matter_did.
  // Joins firm (parent) identity + child counts from mv_etzhayyim_identity_children.

  await sql`CREATE VIEW view_lawfirm_matter_roster AS
    SELECT
      m.did                   AS matter_did,
      m.parent_did            AS firm_did,
      m.controller_did,
      m.handle                AS matter_handle,
      m.status                AS identity_status,
      m.material_hash_proof,
      m.created_at,
      m.updated_at,
      m.revoked_at,
      firm.handle             AS firm_handle,
      firm.display_name       AS firm_display_name,
      firm.actor_score        AS firm_actor_score,
      COALESCE(docs.child_count,         0) AS total_doc_count,
      COALESCE(docs.active_child_count,  0) AS active_doc_count,
      COALESCE(grants.child_count,       0) AS total_grant_count,
      COALESCE(grants.active_child_count,0) AS active_grant_count
    FROM vertex_etzhayyim_identity m
    LEFT JOIN vertex_etzhayyim_identity firm
      ON firm.did = m.parent_did
    LEFT JOIN mv_etzhayyim_identity_children docs
      ON docs.parent_did = m.did AND docs.material_kind = 'doc'
    LEFT JOIN mv_etzhayyim_identity_children grants
      ON grants.parent_did = m.did AND grants.material_kind = 'grant'
    WHERE m.material_kind = 'matter'
      AND m.parent_did IS NOT NULL
      AND m.depth = 2`.execute(db);

  // ── View 2: view_lawfirm_external_counsel_access ────────────────────
  // Per-grant listing with parent-matter revocation cascade flag surfaced.
  // The Worker handler resolves full-chain cascade via ancestor walk when
  // parent_revoked_at IS NOT NULL — this view only surfaces depth-1 parent.

  await sql`CREATE VIEW view_lawfirm_external_counsel_access AS
    SELECT
      g.did                      AS grant_did,
      g.parent_did               AS matter_did,
      g.controller_did           AS inviter_did,
      g.material_hash_proof,
      g.status,
      g.created_at,
      g.updated_at,
      g.revoked_at,
      m.revoked_at               AS parent_revoked_at
    FROM vertex_etzhayyim_identity g
    LEFT JOIN vertex_etzhayyim_identity m
      ON m.did = g.parent_did
    WHERE g.material_kind = 'grant'
      AND g.parent_did IS NOT NULL
      AND g.depth = 3`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_lawfirm_external_counsel_access`.execute(db);
  await sql`DROP VIEW IF EXISTS view_lawfirm_matter_roster`.execute(db);
}
