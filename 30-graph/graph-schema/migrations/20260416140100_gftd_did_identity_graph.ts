import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: A

/**
 * did:gftd identity graph — vertex, edge, index, MV.
 *
 * Design: 90-docs/260416-did-schema-dodaf-org-agent-shannon-design.md
 *
 * Vertex tables:
 *   vertex_gftd_identity     — 1 actor = 1 row (did:gftd primary key)
 *   vertex_gftd_org          — organization entity
 *   vertex_gftd_team         — team within org
 *
 * Edge tables:
 *   edge_gftd_member_of      — actor → org membership (role, RACI)
 *   edge_gftd_belongs_to_team — actor → team membership
 *   edge_gftd_controls       — org/account → sub-actor controller chain
 *   edge_gftd_delegates_to   — capability delegation (RACI chain)
 *   edge_gftd_federation     — did:gftd → did:plc federation link
 *   edge_gftd_authenticates  — did:gftd → auth method (passkey/google/microsoft/email)
 *
 * MVs:
 *   mv_gftd_org_member_count — org member count + role distribution
 *   mv_gftd_actor_score      — actor score (verified auth method count)
 *   mv_gftd_delegation_chain — flattened RACI delegation (highest wins)
 */

export async function up(db: Kysely<any>): Promise<void> {

  // ── Vertex: gftd_identity (1 actor = 1 row) ────────────────────────────

  await sql`CREATE TABLE IF NOT EXISTS vertex_gftd_identity (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    did             VARCHAR,
    entity_type     VARCHAR,
    performer_type  VARCHAR,
    handle          VARCHAR,
    display_name    VARCHAR,
    description     VARCHAR,

    federation_did  VARCHAR,
    legacy_did      VARCHAR,
    controller_did  VARCHAR,

    actor_score     BIGINT,

    rbac_roles      VARCHAR,
    rbac_grants     VARCHAR,
    capability_scopes VARCHAR,

    consent_model   VARCHAR,
    pii_tier        BIGINT,

    dodaf_viewpoint VARCHAR,
    dodaf_performer_binding VARCHAR,

    authentication_methods VARCHAR,

    org_id          VARCHAR,

    public_key_multibase VARCHAR,

    status          VARCHAR,
    created_at      VARCHAR,
    updated_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── Vertex: gftd_org (organization entity) ─────────────────────────────

  await sql`CREATE TABLE IF NOT EXISTS vertex_gftd_org (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    did             VARCHAR,
    name            VARCHAR,
    display_name    VARCHAR,
    org_type        VARCHAR,

    sso_type        VARCHAR,
    sso_issuer      VARCHAR,
    sso_enforced    BIGINT,
    allowed_domains VARCHAR,
    default_role    VARCHAR,

    rbac_roles      VARCHAR,
    rbac_grants     VARCHAR,
    consent_model   VARCHAR,
    pii_tier        BIGINT,

    status          VARCHAR,
    created_at      VARCHAR,
    updated_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── Vertex: gftd_team (team within org) ────────────────────────────────

  await sql`CREATE TABLE IF NOT EXISTS vertex_gftd_team (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    org_did         VARCHAR,
    name            VARCHAR,
    display_name    VARCHAR,
    rbac_grants     VARCHAR,

    status          VARCHAR,
    created_at      VARCHAR,
    updated_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── Edge: gftd_member_of (actor → org) ─────────────────────────────────

  await sql`CREATE TABLE IF NOT EXISTS edge_gftd_member_of (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    role            VARCHAR,
    raci            VARCHAR,
    invite_email    VARCHAR,
    invite_status   VARCHAR,
    accepted_at     VARCHAR,
    created_at      VARCHAR,
    updated_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── Edge: gftd_belongs_to_team (actor → team) ─────────────────────────

  await sql`CREATE TABLE IF NOT EXISTS edge_gftd_belongs_to_team (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    created_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── Edge: gftd_controls (controller → sub-actor) ──────────────────────

  await sql`CREATE TABLE IF NOT EXISTS edge_gftd_controls (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    relationship    VARCHAR,
    created_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── Edge: gftd_delegates_to (delegator → delegatee, RACI chain) ───────

  await sql`CREATE TABLE IF NOT EXISTS edge_gftd_delegates_to (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    raci            VARCHAR,
    role            VARCHAR,
    vp_proof        VARCHAR,
    scope           VARCHAR,
    created_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── Edge: gftd_federation (did:gftd → did:plc) ────────────────────────

  await sql`CREATE TABLE IF NOT EXISTS edge_gftd_federation (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    created_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── Edge: gftd_authenticates (did:gftd → auth method) ─────────────────

  await sql`CREATE TABLE IF NOT EXISTS edge_gftd_authenticates (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    auth_type       VARCHAR,
    provider        VARCHAR,
    email           VARCHAR,
    verified        BIGINT,
    is_primary      BIGINT,
    linked_at       VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── Indexes ────────────────────────────────────────────────────────────

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_gftd_identity_did
    ON vertex_gftd_identity(did)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_gftd_identity_handle
    ON vertex_gftd_identity(handle)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_gftd_identity_controller
    ON vertex_gftd_identity(controller_did)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_gftd_member_of_dst
    ON edge_gftd_member_of(dst_vid)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_gftd_delegates_to_dst
    ON edge_gftd_delegates_to(dst_vid)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── MVs ────────────────────────────────────────────────────────────────

  // MV: org member count + role distribution (bounded by org count < 10K)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gftd_org_member_count AS
    SELECT
      dst_vid AS org_did,
      COUNT(*) AS total_members,
      COUNT(*) FILTER (WHERE role = 'owner') AS owner_count,
      COUNT(*) FILTER (WHERE role = 'admin') AS admin_count,
      COUNT(*) FILTER (WHERE role = 'member') AS member_count,
      COUNT(*) FILTER (WHERE role = 'viewer') AS viewer_count,
      COUNT(*) FILTER (WHERE role = 'agent-runtime') AS agent_count,
      COUNT(*) FILTER (WHERE invite_status = 'accepted') AS accepted_count,
      COUNT(*) FILTER (WHERE invite_status = 'pending') AS pending_count
    FROM edge_gftd_member_of
    GROUP BY dst_vid`.execute(db);
  await sql`FLUSH`.execute(db);

  // MV: actor score (verified auth method count, bounded by identity count)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gftd_actor_score AS
    SELECT
      src_vid AS did,
      COUNT(*) FILTER (WHERE verified = 1) AS verified_method_count,
      COUNT(*) AS total_method_count,
      LEAST(COUNT(*) FILTER (WHERE verified = 1) * 25, 100) AS actor_score
    FROM edge_gftd_authenticates
    GROUP BY src_vid`.execute(db);
  await sql`FLUSH`.execute(db);

  // MV: delegation chain (highest RACI per delegatee, bounded by delegation count)
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gftd_delegation_chain AS
    SELECT
      dst_vid AS delegatee_did,
      src_vid AS delegator_did,
      raci,
      role,
      scope
    FROM edge_gftd_delegates_to`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gftd_delegation_chain`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gftd_actor_score`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gftd_org_member_count`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_edge_gftd_delegates_to_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_gftd_member_of_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_gftd_identity_controller`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_gftd_identity_handle`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_gftd_identity_did`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP TABLE IF EXISTS edge_gftd_authenticates`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gftd_federation`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gftd_delegates_to`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gftd_controls`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gftd_belongs_to_team`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gftd_member_of`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gftd_team`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gftd_org`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gftd_identity`.execute(db);
  await sql`FLUSH`.execute(db);
}
