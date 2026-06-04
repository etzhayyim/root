CREATE TABLE IF NOT EXISTS vertex_etzhayyim_identity (
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
  );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_etzhayyim_org (
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
  );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_etzhayyim_team (
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
  );

FLUSH;

CREATE TABLE IF NOT EXISTS edge_etzhayyim_member_of (
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
  );

FLUSH;

CREATE TABLE IF NOT EXISTS edge_etzhayyim_belongs_to_team (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    created_at      VARCHAR
  );

FLUSH;

CREATE TABLE IF NOT EXISTS edge_etzhayyim_controls (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    relationship    VARCHAR,
    created_at      VARCHAR
  );

FLUSH;

CREATE TABLE IF NOT EXISTS edge_etzhayyim_delegates_to (
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
  );

FLUSH;

CREATE TABLE IF NOT EXISTS edge_etzhayyim_federation (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,
    dst_vid         VARCHAR,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    created_at      VARCHAR
  );

FLUSH;

CREATE TABLE IF NOT EXISTS edge_etzhayyim_authenticates (
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
  );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_did
    ON vertex_etzhayyim_identity(did);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_handle
    ON vertex_etzhayyim_identity(handle);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_controller
    ON vertex_etzhayyim_identity(controller_did);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_member_of_dst
    ON edge_etzhayyim_member_of(dst_vid);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_delegates_to_dst
    ON edge_etzhayyim_delegates_to(dst_vid);

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_org_member_count AS
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
    FROM edge_etzhayyim_member_of
    GROUP BY dst_vid;

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_actor_score AS
    SELECT
      src_vid AS did,
      COUNT(*) FILTER (WHERE verified = 1) AS verified_method_count,
      COUNT(*) AS total_method_count,
      LEAST(COUNT(*) FILTER (WHERE verified = 1) * 25, 100) AS actor_score
    FROM edge_etzhayyim_authenticates
    GROUP BY src_vid;

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_delegation_chain AS
    SELECT
      dst_vid AS delegatee_did,
      src_vid AS delegator_did,
      raci,
      role,
      scope
    FROM edge_etzhayyim_delegates_to;

FLUSH;
