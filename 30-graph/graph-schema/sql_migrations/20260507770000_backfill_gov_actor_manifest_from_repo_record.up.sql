CREATE TABLE IF NOT EXISTS vertex_gov_actor_manifest (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      record_kind VARCHAR NOT NULL,
      path VARCHAR NOT NULL,
      country VARCHAR NOT NULL,
      display_name VARCHAR,
      description TEXT,
      performer_type VARCHAR,
      agent_type VARCHAR,
      is_bot BOOLEAN NOT NULL DEFAULT true,
      value_json TEXT NOT NULL,
      indexed_at VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2
    );

INSERT INTO vertex_gov_actor_manifest (
      vertex_id, record_key, record_kind, path, country, display_name,
      description, performer_type, agent_type, is_bot, value_json,
      indexed_at, created_at, updated_at, actor_did, org_did, owner_did,
      sensitivity_ord
    )
    SELECT
      repo_record.uri,
      repo_record.rkey,
      'actorManifest',
      COALESCE(NULLIF(repo_record.value_json::jsonb ->> 'path', ''), repo_record.rkey),
      COALESCE(NULLIF(repo_record.value_json::jsonb ->> 'country', ''), ''),
      NULLIF(repo_record.value_json::jsonb ->> 'displayName', ''),
      NULLIF(repo_record.value_json::jsonb ->> 'description', ''),
      NULLIF(repo_record.value_json::jsonb ->> 'performerType', ''),
      NULLIF(repo_record.value_json::jsonb ->> 'agentType', ''),
      CASE
        WHEN LOWER(COALESCE(NULLIF(repo_record.value_json::jsonb ->> 'isBot', ''), 'true')) IN ('true', 't', '1', 'yes') THEN true
        ELSE false
      END,
      repo_record.value_json,
      repo_record.indexed_at,
      repo_record.created_at,
      repo_record.created_at,
      COALESCE(NULLIF(repo_record.value_json::jsonb ->> 'actorDid', ''), repo_record.repo),
      COALESCE(NULLIF(repo_record.value_json::jsonb ->> 'orgDid', ''), repo_record.repo),
      COALESCE(NULLIF(repo_record.value_json::jsonb ->> 'ownerDid', ''), repo_record.repo),
      COALESCE(NULLIF(repo_record.value_json::jsonb ->> 'sensitivityOrd', '')::integer, 2)
    FROM vertex_repo_record AS repo_record
    WHERE repo_record.collection IN (
      'actorManifest',
      'ai.gftd.gov.actorManifest',
      'ai.gftd.apps.states.actorManifest'
    )
      AND NOT EXISTS (
        SELECT 1
        FROM vertex_gov_actor_manifest AS actor_manifest
        WHERE actor_manifest.vertex_id = repo_record.uri
      );

CREATE INDEX IF NOT EXISTS idx_gov_actor_manifest_owner_path
      ON vertex_gov_actor_manifest (owner_did, path);

CREATE INDEX IF NOT EXISTS idx_gov_actor_manifest_actor
      ON vertex_gov_actor_manifest (actor_did, indexed_at DESC);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gov_actor_manifest_coverage AS
    SELECT
      owner_did,
      country,
      COUNT(*) AS actor_count,
      MAX(indexed_at) AS latest_indexed_at
    FROM vertex_gov_actor_manifest
    GROUP BY owner_did, country;
