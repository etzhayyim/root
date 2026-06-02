CREATE TABLE IF NOT EXISTS edge_gov_org_site_dependency (
      edge_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      from_vertex_id VARCHAR NOT NULL,
      to_vertex_id VARCHAR NOT NULL,
      path VARCHAR NOT NULL,
      site_nanoid VARCHAR,
      site_topic_did VARCHAR,
      site_did VARCHAR NOT NULL,
      value_json TEXT NOT NULL,
      indexed_at VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2
    );

INSERT INTO edge_gov_org_site_dependency (
        edge_id, record_key, from_vertex_id, to_vertex_id, path, site_nanoid,
        site_topic_did, site_did, value_json, indexed_at, created_at,
        updated_at, actor_did, org_did, owner_did, sensitivity_ord
      )
      SELECT
        vertex_id,
        record_key,
        'at://' || owner_did || '/com.etzhayyim.apps.states.govOrg/' || COALESCE(value_json::jsonb ->> 'path', ''),
        COALESCE(value_json::jsonb ->> 'siteDid', ''),
        COALESCE(value_json::jsonb ->> 'path', ''),
        value_json::jsonb ->> 'siteNanoid',
        value_json::jsonb ->> 'siteTopicDid',
        COALESCE(value_json::jsonb ->> 'siteDid', ''),
        value_json,
        indexed_at,
        created_at,
        updated_at,
        actor_did,
        org_did,
        owner_did,
        CAST(sensitivity_ord AS integer)
      FROM vertex_gov_record
      WHERE record_kind = 'com.etzhayyim.apps.states.govOrgSiteDep'
      ON CONFLICT (edge_id) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_gov_org_site_dep_from
      ON edge_gov_org_site_dependency (from_vertex_id, indexed_at DESC);

CREATE INDEX IF NOT EXISTS idx_gov_org_site_dep_site
      ON edge_gov_org_site_dependency (site_did, indexed_at DESC);

CREATE INDEX IF NOT EXISTS idx_gov_org_site_dep_owner_path
      ON edge_gov_org_site_dependency (owner_did, path);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gov_org_site_dependency_coverage AS
    SELECT
      owner_did,
      COUNT(*) AS dependency_count,
      COUNT(DISTINCT path) AS org_count,
      COUNT(DISTINCT site_did) AS site_count,
      MAX(indexed_at) AS latest_indexed_at
    FROM edge_gov_org_site_dependency
    GROUP BY owner_did;

UPDATE vertex_bpmn_lexicon_binding
    SET write_table_allowlist = replace(write_table_allowlist, 'vertex_gov_record', 'edge_gov_org_site_dependency')
    WHERE write_table_allowlist LIKE '%vertex_gov_record%';
