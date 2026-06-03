import { Kysely, sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: A

/**
 * Shannon Redundancy Cleanup — Phase 1 (safe, zero-risk).
 *
 * Goal (Pattern B): consolidate DID / Actor / Profile tables into 3 orthogonal
 * axes (identity / profile / manifest) and drop 4 redundant tables.
 *
 * Baseline η = 0.38 (11 tables, ~160 cols, 13 attributes duplicated ×34 times).
 * Target  η = 0.93 (7 tables,  ~56 cols, 13 attributes stored ×14 times).
 *
 * Phase split (to avoid blast-radius on 21 streaming MVs + PDS worker code):
 *
 *   Phase 1 (THIS FILE)  — additive only, no drops of live tables
 *     - DROP vertex_diddocument  (ghost; zero code refs; never written)
 *     - CREATE vertex_actor_profile (new slim replacement for vertex_actor)
 *     - ALTER vertex_etzhayyim_identity ADD profile_json, capabilities
 *     - CREATE view_actor_unified (read-side facade)
 *
 *   Phase 2 (next PR)    — vertex_actor → vertex_actor_profile cutover
 *     - Backfill vertex_actor_profile from vertex_actor
 *     - DROP + recreate 10 MVs to reference vertex_actor_profile
 *     - Update PDS handler selectFrom('vertex_actor') → view_actor_unified
 *     - DROP vertex_actor
 *
 *   Phase 3 (final)      — drop vertex_did, vertex_profile
 *     - Migrate vertex_did.{display_name,description,controller} → vertex_etzhayyim_identity
 *     - DROP + recreate mv_actor_repo_stats, mv_world_did_per_host,
 *       mv_profile_identity_topology to reference vertex_etzhayyim_identity
 *     - Update PDS server.ts 11 vertex_profile queries → view_actor_unified
 *     - DROP vertex_did, vertex_profile
 *     - Slim vertex_actor_manifest (drop display_name, description,
 *       performer_type, execution_tier — now in vertex_actor_profile)
 *     - Slim vertex_did_document (keep did + doc + owner_did + updated_at)
 *
 * References:
 *   - ADR-0029 did:etzhayyim method spec
 *   - 90-docs/260419-shannon-cleanup-did-actor-topology.md (to be written)
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── 1. DROP ghost duplicate ──────────────────────────────────────────
  // vertex_diddocument: zero code references (confirmed 2026-04-19 audit).
  // Only appears in database.ts type generation + one Iceberg sink
  // (sink_vertex_diddocument in 0003_iceberg_sinks.ts, decommissioned
  // 2026-04-13 — sink is already inert).
  await sql`DROP TABLE IF EXISTS vertex_diddocument`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── 2. CREATE vertex_actor_profile (slim, 12 cols vs vertex_actor's 40+) ─
  // Non-key attributes live here exactly once. vertex_actor is kept running
  // during Phase 1; Phase 2 backfills + cuts over + drops.
  await sql`CREATE TABLE IF NOT EXISTS vertex_actor_profile (
    vertex_id         VARCHAR PRIMARY KEY,
    _seq              BIGINT,
    created_date      DATE,
    sensitivity_ord   BIGINT,
    owner_did         VARCHAR,

    did               VARCHAR,   -- FK → vertex_etzhayyim_identity.did
    handle            VARCHAR,
    display_name      VARCHAR,
    description       VARCHAR,
    avatar_cid        VARCHAR,
    banner_cid        VARCHAR,
    execution_tier    VARCHAR,   -- T0 | T1 | T2 | T3
    performer_type    VARCHAR,   -- service | person | agent | organization
    nanoid            VARCHAR,   -- legacy grandfather (ADR-0019 Phase 4)
    category          VARCHAR,
    country           VARCHAR,
    status            VARCHAR,   -- active | deactivated | draft
    created_at        VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_actor_profile_did
    ON vertex_actor_profile(did)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_actor_profile_handle
    ON vertex_actor_profile(handle)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── 3. Extend vertex_etzhayyim_identity with capability / profile surface ──
  // capabilities: JSON array of MCP tool NSIDs (com.etzhayyim.*.xxx) — replaces
  // vertex_actor.{agent_tools, capability_declare, social_post, ...} (14 bool cols).
  // profile_json: compat surface for actor-manifest.jsonld during cutover.
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN capabilities VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN profile_json VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── 4. Read-side facade VIEW ──────────────────────────────────────────
  // view_actor_unified exposes the Phase-3 target shape TODAY, backed by
  // the existing (pre-cleanup) tables. Workers can migrate their reads to
  // this view immediately and Phase 2/3 swaps the underlying sources
  // without touching worker code.
  //
  // Precedence when the same attribute lives in multiple tables:
  //   display_name:  vertex_actor_profile → vertex_actor → vertex_profile → vertex_etzhayyim_identity
  //   description:   vertex_actor_profile → vertex_actor_manifest → vertex_profile
  //   handle:        vertex_actor_profile → vertex_actor → vertex_etzhayyim_identity
  //   avatar/banner: vertex_actor_profile → vertex_actor → vertex_profile
  //
  // `vertex_actor_profile` wins everywhere so that Phase 2 backfill flips
  // the source without semantic change.
  await sql`CREATE VIEW view_actor_unified AS
    SELECT
      COALESCE(ap.did, a.did, p.did, i.did)                               AS did,
      COALESCE(ap.handle, a.handle, i.handle)                              AS handle,
      COALESCE(ap.display_name, a.display_name, p.display_name, i.display_name) AS display_name,
      COALESCE(ap.description, am.description, p.description, i.description)   AS description,
      COALESCE(ap.avatar_cid, a.avatar_cid, p.avatar_cid)                  AS avatar_cid,
      COALESCE(ap.banner_cid, a.banner_cid, p.banner_cid)                  AS banner_cid,
      COALESCE(ap.execution_tier, a.execution_tier, am.execution_tier)     AS execution_tier,
      COALESCE(ap.performer_type, a.performer_type, am.performer_type, i.performer_type) AS performer_type,
      COALESCE(ap.nanoid, a.nanoid, am.nanoid)                             AS nanoid,
      COALESCE(ap.status, a.status, i.status)                              AS status,
      i.public_key_multibase                                               AS public_key_multibase,
      i.rbac_roles                                                         AS rbac_roles,
      i.capability_scopes                                                  AS capability_scopes,
      i.capabilities                                                       AS capabilities,
      i.parent_did                                                         AS parent_did,
      i.depth                                                              AS depth,
      i.root_did                                                           AS root_did,
      i.pii_tier                                                           AS pii_tier,
      am.pipelines_json                                                    AS pipelines_json,
      am.triggers_json                                                     AS triggers_json,
      am.governance_json                                                   AS governance_json,
      am.capabilities_json                                                 AS capabilities_json_legacy,
      i.profile_json                                                       AS profile_json
    FROM vertex_etzhayyim_identity i
    LEFT JOIN vertex_actor_profile ap ON ap.did = i.did
    LEFT JOIN vertex_actor         a  ON a.did  = i.did
    LEFT JOIN vertex_actor_manifest am ON am.did = i.did
    LEFT JOIN vertex_profile       p  ON p.did  = i.did`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_actor_unified`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN profile_json`.execute(db);
  await sql`FLUSH`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN capabilities`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_actor_profile_handle`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_actor_profile_did`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_actor_profile`.execute(db);
  await sql`FLUSH`.execute(db);

  // vertex_diddocument restore is intentionally omitted — the table was a
  // no-op ghost (zero rows of real data, zero code references). If a
  // rollback truly needs it, recreate by hand with the original 7-col
  // layout from database.ts VertexDiddocumentRow.
}
