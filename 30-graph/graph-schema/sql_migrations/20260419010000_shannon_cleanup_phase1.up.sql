DROP TABLE IF EXISTS vertex_diddocument;

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_actor_profile (
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
  );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_actor_profile_did
    ON vertex_actor_profile(did);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_actor_profile_handle
    ON vertex_actor_profile(handle);

FLUSH;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN capabilities VARCHAR;

FLUSH;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN profile_json VARCHAR;

FLUSH;

CREATE VIEW view_actor_unified AS
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
    LEFT JOIN vertex_profile       p  ON p.did  = i.did;

FLUSH;
