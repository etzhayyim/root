CREATE TABLE IF NOT EXISTS vertex_yoro_browsing_history (
      vertex_id VARCHAR PRIMARY KEY,
      uri VARCHAR,
      rkey VARCHAR,
      repo VARCHAR NOT NULL,
      path TEXT,
      title TEXT,
      history_type VARCHAR,
      avatar TEXT,
      handle TEXT,
      value_json TEXT,
      created_at VARCHAR,
      indexed_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS vertex_yoro_koji_discovery (
      vertex_id VARCHAR PRIMARY KEY,
      uri VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      actor_did VARCHAR NOT NULL,
      actor_name TEXT,
      source VARCHAR,
      readiness_grade TEXT,
      summary TEXT,
      value_json TEXT,
      created_at VARCHAR,
      indexed_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS vertex_yoro_kyumei_validation (
      vertex_id VARCHAR PRIMARY KEY,
      uri VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      actor_did VARCHAR NOT NULL,
      actor_name TEXT,
      source VARCHAR,
      validation_score TEXT,
      value_json TEXT,
      created_at VARCHAR,
      indexed_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS vertex_yoro_shinka_evolution (
      vertex_id VARCHAR PRIMARY KEY,
      uri VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      actor_did VARCHAR NOT NULL,
      actor_name TEXT,
      source VARCHAR,
      mood TEXT,
      value_json TEXT,
      created_at VARCHAR,
      indexed_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS vertex_yoro_hinshitsu_assessment (
      vertex_id VARCHAR PRIMARY KEY,
      uri VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      actor_did VARCHAR NOT NULL,
      actor_name TEXT,
      source VARCHAR,
      quality_score TEXT,
      grade TEXT,
      value_json TEXT,
      created_at VARCHAR,
      indexed_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS vertex_yoro_shinka_knowledge (
      vertex_id VARCHAR PRIMARY KEY,
      uri VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      actor_did VARCHAR NOT NULL,
      actor_name TEXT,
      source VARCHAR,
      domain_summary TEXT,
      value_json TEXT,
      created_at VARCHAR,
      indexed_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS vertex_dojo_step_completed_event (
      vertex_id VARCHAR PRIMARY KEY,
      uri VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      actor_did VARCHAR NOT NULL,
      value_json TEXT,
      created_at VARCHAR,
      indexed_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS vertex_joucho_review (
      vertex_id VARCHAR PRIMARY KEY,
      uri VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      actor_did VARCHAR NOT NULL,
      value_json TEXT,
      created_at VARCHAR,
      indexed_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS vertex_state_profile (
      vertex_id VARCHAR PRIMARY KEY,
      uri VARCHAR,
      rkey VARCHAR,
      repo VARCHAR NOT NULL,
      iso3 VARCHAR,
      name TEXT,
      region TEXT,
      value_json TEXT,
      created_at VARCHAR,
      indexed_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS vertex_agent_governance_rule (
      vertex_id VARCHAR PRIMARY KEY,
      uri VARCHAR,
      rkey VARCHAR,
      repo VARCHAR NOT NULL,
      command TEXT,
      bpmn_task_id TEXT,
      ocel_event_type TEXT,
      value_json TEXT,
      created_at VARCHAR,
      indexed_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS vertex_agent_role_binding (
      vertex_id VARCHAR PRIMARY KEY,
      uri VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      app_id VARCHAR,
      principal_did VARCHAR,
      role_name TEXT,
      value_json TEXT,
      created_at VARCHAR,
      indexed_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS edge_yoro_actor_evolution (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation VARCHAR NOT NULL,
      created_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS edge_yoro_actor_browsing_history (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation VARCHAR NOT NULL,
      created_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS edge_yoro_actor_score_event (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation VARCHAR NOT NULL,
      created_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS edge_state_profile_repo (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation VARCHAR NOT NULL,
      created_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE TABLE IF NOT EXISTS edge_agent_governance (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation VARCHAR NOT NULL,
      created_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE INDEX IF NOT EXISTS idx_yoro_browsing_history_repo_created ON vertex_yoro_browsing_history (repo, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_yoro_browsing_history_path ON vertex_yoro_browsing_history (path);

CREATE INDEX IF NOT EXISTS idx_yoro_koji_actor_created ON vertex_yoro_koji_discovery (actor_did, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_yoro_kyumei_actor_created ON vertex_yoro_kyumei_validation (actor_did, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_yoro_shinka_actor_created ON vertex_yoro_shinka_evolution (actor_did, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_yoro_hinshitsu_actor_created ON vertex_yoro_hinshitsu_assessment (actor_did, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_yoro_knowledge_actor_created ON vertex_yoro_shinka_knowledge (actor_did, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_yoro_koji_source ON vertex_yoro_koji_discovery (source);

CREATE INDEX IF NOT EXISTS idx_yoro_kyumei_source ON vertex_yoro_kyumei_validation (source);

CREATE INDEX IF NOT EXISTS idx_yoro_shinka_source ON vertex_yoro_shinka_evolution (source);

CREATE INDEX IF NOT EXISTS idx_yoro_hinshitsu_source ON vertex_yoro_hinshitsu_assessment (source);

CREATE INDEX IF NOT EXISTS idx_yoro_knowledge_source ON vertex_yoro_shinka_knowledge (source);

CREATE INDEX IF NOT EXISTS idx_dojo_step_actor_created ON vertex_dojo_step_completed_event (actor_did, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_joucho_review_actor_created ON vertex_joucho_review (actor_did, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_state_profile_repo_rkey ON vertex_state_profile (repo, rkey);

CREATE INDEX IF NOT EXISTS idx_state_profile_iso3 ON vertex_state_profile (iso3);

CREATE INDEX IF NOT EXISTS idx_agent_governance_rule_repo ON vertex_agent_governance_rule (repo);

CREATE INDEX IF NOT EXISTS idx_agent_role_binding_app_id ON vertex_agent_role_binding (app_id);

CREATE INDEX IF NOT EXISTS idx_agent_role_binding_principal ON vertex_agent_role_binding (principal_did);

CREATE INDEX IF NOT EXISTS idx_edge_yoro_actor_evolution_src ON edge_yoro_actor_evolution (src_vid, relation);

CREATE INDEX IF NOT EXISTS idx_edge_yoro_actor_browsing_src ON edge_yoro_actor_browsing_history (src_vid, relation);

CREATE INDEX IF NOT EXISTS idx_edge_yoro_actor_score_src ON edge_yoro_actor_score_event (src_vid, relation);

CREATE INDEX IF NOT EXISTS idx_edge_state_profile_repo_src ON edge_state_profile_repo (src_vid, relation);

CREATE INDEX IF NOT EXISTS idx_edge_agent_governance_src ON edge_agent_governance (src_vid, relation);

INSERT INTO vertex_yoro_browsing_history (
      vertex_id, uri, rkey, repo, path, title, history_type, avatar, handle, value_json,
      created_at, indexed_at, owner_did, actor_id, sensitivity_ord
    )
    SELECT
      uri,
      uri,
      rkey,
      repo,
      coalesce(value_json::jsonb ->> 'path', ''),
      coalesce(value_json::jsonb ->> 'title', ''),
      coalesce(value_json::jsonb ->> 'historyType', 'post'),
      nullif(value_json::jsonb ->> 'avatar', ''),
      nullif(value_json::jsonb ->> 'handle', ''),
      value_json,
      coalesce(value_json::jsonb ->> 'createdAt', created_at::text, indexed_at::text, ''),
      indexed_at::text,
      repo,
      'yoro',
      2
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.yoro.browsingHistory'
    ON CONFLICT (vertex_id) DO NOTHING;

INSERT INTO vertex_yoro_koji_discovery (
      vertex_id, uri, rkey, repo, actor_did, actor_name, source, readiness_grade, summary,
      value_json, created_at, indexed_at, owner_did, actor_id, sensitivity_ord
    )
    SELECT uri, uri, rkey, repo,
      coalesce(value_json::jsonb ->> 'actorDid', ''),
      coalesce(value_json::jsonb ->> 'actorName', ''),
      coalesce(value_json::jsonb ->> 'source', ''),
      nullif(value_json::jsonb ->> 'readinessGrade', ''),
      nullif(value_json::jsonb ->> 'summary', ''),
      value_json,
      coalesce(value_json::jsonb ->> 'createdAt', created_at::text, indexed_at::text, ''),
      indexed_at::text,
      repo,
      'yoro',
      2
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.yoro.kojiDiscovery'
    ON CONFLICT (vertex_id) DO NOTHING;

INSERT INTO vertex_yoro_kyumei_validation (
      vertex_id, uri, rkey, repo, actor_did, actor_name, source, validation_score,
      value_json, created_at, indexed_at, owner_did, actor_id, sensitivity_ord
    )
    SELECT uri, uri, rkey, repo,
      coalesce(value_json::jsonb ->> 'actorDid', ''),
      coalesce(value_json::jsonb ->> 'actorName', ''),
      coalesce(value_json::jsonb ->> 'source', ''),
      nullif(value_json::jsonb ->> 'validationScore', ''),
      value_json,
      coalesce(value_json::jsonb ->> 'createdAt', created_at::text, indexed_at::text, ''),
      indexed_at::text,
      repo,
      'yoro',
      2
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.yoro.kyumeiValidation'
    ON CONFLICT (vertex_id) DO NOTHING;

INSERT INTO vertex_yoro_shinka_evolution (
      vertex_id, uri, rkey, repo, actor_did, actor_name, source, mood,
      value_json, created_at, indexed_at, owner_did, actor_id, sensitivity_ord
    )
    SELECT uri, uri, rkey, repo,
      coalesce(value_json::jsonb ->> 'actorDid', ''),
      coalesce(value_json::jsonb ->> 'actorName', ''),
      coalesce(value_json::jsonb ->> 'source', ''),
      nullif(value_json::jsonb ->> 'mood', ''),
      value_json,
      coalesce(value_json::jsonb ->> 'createdAt', created_at::text, indexed_at::text, ''),
      indexed_at::text,
      repo,
      'yoro',
      2
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.yoro.shinkaEvolution'
    ON CONFLICT (vertex_id) DO NOTHING;

INSERT INTO vertex_yoro_hinshitsu_assessment (
      vertex_id, uri, rkey, repo, actor_did, actor_name, source, quality_score, grade,
      value_json, created_at, indexed_at, owner_did, actor_id, sensitivity_ord
    )
    SELECT uri, uri, rkey, repo,
      coalesce(value_json::jsonb ->> 'actorDid', ''),
      coalesce(value_json::jsonb ->> 'actorName', ''),
      coalesce(value_json::jsonb ->> 'source', ''),
      nullif(value_json::jsonb ->> 'qualityScore', ''),
      nullif(value_json::jsonb ->> 'grade', ''),
      value_json,
      coalesce(value_json::jsonb ->> 'createdAt', created_at::text, indexed_at::text, ''),
      indexed_at::text,
      repo,
      'yoro',
      2
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.yoro.hinshitsuAssessment'
    ON CONFLICT (vertex_id) DO NOTHING;

INSERT INTO vertex_yoro_shinka_knowledge (
      vertex_id, uri, rkey, repo, actor_did, actor_name, source, domain_summary,
      value_json, created_at, indexed_at, owner_did, actor_id, sensitivity_ord
    )
    SELECT uri, uri, rkey, repo,
      coalesce(value_json::jsonb ->> 'actorDid', ''),
      coalesce(value_json::jsonb ->> 'actorName', ''),
      coalesce(value_json::jsonb ->> 'source', ''),
      nullif(value_json::jsonb ->> 'domainSummary', ''),
      value_json,
      coalesce(value_json::jsonb ->> 'createdAt', created_at::text, indexed_at::text, ''),
      indexed_at::text,
      repo,
      'yoro',
      2
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.yoro.shinkaKnowledge'
    ON CONFLICT (vertex_id) DO NOTHING;

INSERT INTO vertex_dojo_step_completed_event (
      vertex_id, uri, rkey, repo, actor_did, value_json, created_at, indexed_at,
      owner_did, actor_id, sensitivity_ord
    )
    SELECT uri, uri, rkey, repo, repo, value_json,
      coalesce(value_json::jsonb ->> 'completedAt', value_json::jsonb ->> 'createdAt', created_at::text, indexed_at::text, ''),
      indexed_at::text,
      repo,
      'dojo',
      2
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.dojo.step_completed_event'
    ON CONFLICT (vertex_id) DO NOTHING;

INSERT INTO vertex_joucho_review (
      vertex_id, uri, rkey, repo, actor_did, value_json, created_at, indexed_at,
      owner_did, actor_id, sensitivity_ord
    )
    SELECT uri, uri, rkey, repo, repo, value_json,
      coalesce(value_json::jsonb ->> 'createdAt', created_at::text, indexed_at::text, ''),
      indexed_at::text,
      repo,
      'joucho',
      2
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.joucho.review'
    ON CONFLICT (vertex_id) DO NOTHING;

INSERT INTO vertex_state_profile (
      vertex_id, uri, rkey, repo, iso3, name, region, value_json, created_at, indexed_at,
      owner_did, actor_id, sensitivity_ord
    )
    SELECT uri, uri, rkey, repo,
      coalesce(value_json::jsonb ->> 'iso3', rkey),
      coalesce(value_json::jsonb ->> 'name', value_json::jsonb ->> 'iso3', rkey),
      coalesce(value_json::jsonb ->> 'region', ''),
      value_json,
      coalesce(value_json::jsonb ->> 'createdAt', created_at::text, indexed_at::text, ''),
      indexed_at::text,
      repo,
      'states',
      1
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.apps.states.stateProfile'
    ON CONFLICT (vertex_id) DO NOTHING;

INSERT INTO vertex_agent_governance_rule (
      vertex_id, uri, rkey, repo, command, bpmn_task_id, ocel_event_type, value_json,
      created_at, indexed_at, owner_did, actor_id, sensitivity_ord
    )
    SELECT uri, uri, rkey, repo,
      nullif(value_json::jsonb ->> 'command', ''),
      nullif(value_json::jsonb ->> 'bpmn_task_id', ''),
      nullif(value_json::jsonb ->> 'ocel_event_type', ''),
      value_json,
      coalesce(value_json::jsonb ->> 'createdAt', created_at::text, indexed_at::text, ''),
      indexed_at::text,
      repo,
      'agent-governance',
      2
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.agent.governanceRule'
    ON CONFLICT (vertex_id) DO NOTHING;

INSERT INTO vertex_agent_role_binding (
      vertex_id, uri, rkey, repo, app_id, principal_did, role_name, value_json,
      created_at, indexed_at, owner_did, actor_id, sensitivity_ord
    )
    SELECT uri, uri, rkey, repo,
      nullif(value_json::jsonb ->> 'appId', ''),
      nullif(coalesce(value_json::jsonb ->> 'principalDid', value_json::jsonb ->> 'did'), ''),
      nullif(coalesce(value_json::jsonb ->> 'role', value_json::jsonb ->> 'roleName'), ''),
      value_json,
      coalesce(value_json::jsonb ->> 'createdAt', created_at::text, indexed_at::text, ''),
      indexed_at::text,
      repo,
      'agent-governance',
      2
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.agent.roleBinding'
    ON CONFLICT (vertex_id) DO NOTHING;

INSERT INTO edge_yoro_actor_browsing_history (edge_id, src_vid, dst_vid, relation, created_at, owner_did, actor_id, sensitivity_ord)
    SELECT concat(repo, '#visited#', vertex_id), repo, vertex_id, 'visited', created_at, owner_did, actor_id, sensitivity_ord
    FROM vertex_yoro_browsing_history
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yoro_actor_evolution (edge_id, src_vid, dst_vid, relation, created_at, owner_did, actor_id, sensitivity_ord)
    SELECT concat(actor_did, '#koji_discovered#', vertex_id), actor_did, vertex_id, 'koji_discovered', created_at, owner_did, actor_id, sensitivity_ord
    FROM vertex_yoro_koji_discovery
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yoro_actor_evolution (edge_id, src_vid, dst_vid, relation, created_at, owner_did, actor_id, sensitivity_ord)
    SELECT concat(actor_did, '#kyumei_validated#', vertex_id), actor_did, vertex_id, 'kyumei_validated', created_at, owner_did, actor_id, sensitivity_ord
    FROM vertex_yoro_kyumei_validation
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yoro_actor_evolution (edge_id, src_vid, dst_vid, relation, created_at, owner_did, actor_id, sensitivity_ord)
    SELECT concat(actor_did, '#shinka_evolved#', vertex_id), actor_did, vertex_id, 'shinka_evolved', created_at, owner_did, actor_id, sensitivity_ord
    FROM vertex_yoro_shinka_evolution
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yoro_actor_evolution (edge_id, src_vid, dst_vid, relation, created_at, owner_did, actor_id, sensitivity_ord)
    SELECT concat(actor_did, '#hinshitsu_assessed#', vertex_id), actor_did, vertex_id, 'hinshitsu_assessed', created_at, owner_did, actor_id, sensitivity_ord
    FROM vertex_yoro_hinshitsu_assessment
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yoro_actor_evolution (edge_id, src_vid, dst_vid, relation, created_at, owner_did, actor_id, sensitivity_ord)
    SELECT concat(actor_did, '#shinka_knowledge#', vertex_id), actor_did, vertex_id, 'shinka_knowledge', created_at, owner_did, actor_id, sensitivity_ord
    FROM vertex_yoro_shinka_knowledge
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yoro_actor_score_event (edge_id, src_vid, dst_vid, relation, created_at, owner_did, actor_id, sensitivity_ord)
    SELECT concat(actor_did, '#completed_dojo_step#', vertex_id), actor_did, vertex_id, 'completed_dojo_step', created_at, owner_did, actor_id, sensitivity_ord
    FROM vertex_dojo_step_completed_event
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_yoro_actor_score_event (edge_id, src_vid, dst_vid, relation, created_at, owner_did, actor_id, sensitivity_ord)
    SELECT concat(actor_did, '#received_joucho_review#', vertex_id), actor_did, vertex_id, 'received_joucho_review', created_at, owner_did, actor_id, sensitivity_ord
    FROM vertex_joucho_review
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_state_profile_repo (edge_id, src_vid, dst_vid, relation, created_at, owner_did, actor_id, sensitivity_ord)
    SELECT concat(repo, '#has_state_profile#', vertex_id), repo, vertex_id, 'has_state_profile', created_at, owner_did, actor_id, sensitivity_ord
    FROM vertex_state_profile
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_agent_governance (edge_id, src_vid, dst_vid, relation, created_at, owner_did, actor_id, sensitivity_ord)
    SELECT concat(repo, '#has_governance_rule#', vertex_id), repo, vertex_id, 'has_governance_rule', created_at, owner_did, actor_id, sensitivity_ord
    FROM vertex_agent_governance_rule
    ON CONFLICT (edge_id) DO NOTHING;

INSERT INTO edge_agent_governance (edge_id, src_vid, dst_vid, relation, created_at, owner_did, actor_id, sensitivity_ord)
    SELECT concat(coalesce(app_id, repo, ''), '#has_role_binding#', vertex_id), coalesce(app_id, repo, ''), vertex_id, 'has_role_binding', created_at, owner_did, actor_id, sensitivity_ord
    FROM vertex_agent_role_binding
    WHERE coalesce(app_id, repo, '') <> ''
    ON CONFLICT (edge_id) DO NOTHING;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yoro_browsing_history_recent AS
    SELECT repo, path, title, history_type, avatar, handle, created_at, rkey
    FROM vertex_yoro_browsing_history
    ORDER BY created_at DESC;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yoro_evolution_stats AS
    SELECT
      (SELECT count(*) FROM vertex_yoro_koji_discovery WHERE source = 'browser') AS koji_count,
      (SELECT count(*) FROM vertex_yoro_kyumei_validation WHERE source = 'browser') AS kyumei_count,
      (SELECT count(*) FROM vertex_yoro_shinka_evolution WHERE source = 'browser') AS shinka_count,
      (SELECT count(*) FROM vertex_yoro_hinshitsu_assessment WHERE source = 'browser') AS hinshitsu_count,
      (SELECT count(*) FROM vertex_yoro_shinka_knowledge WHERE source = 'browser') AS shinka_knowledge_count;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yoro_evolution_recent AS
    SELECT 'KojiDiscovery' AS label, actor_did AS "actorDid", actor_name AS "actorName",
      readiness_grade AS "readinessGrade", summary, null::text AS "validationScore", null::text AS mood,
      null::text AS "qualityScore", null::text AS grade, null::text AS "domainSummary", source, created_at AS "createdAt"
    FROM vertex_yoro_koji_discovery
    UNION ALL
    SELECT 'KyumeiValidation' AS label, actor_did AS "actorDid", actor_name AS "actorName",
      null::text AS "readinessGrade", null::text AS summary, validation_score AS "validationScore", null::text AS mood,
      null::text AS "qualityScore", null::text AS grade, null::text AS "domainSummary", source, created_at AS "createdAt"
    FROM vertex_yoro_kyumei_validation
    UNION ALL
    SELECT 'ShinkaEvolution' AS label, actor_did AS "actorDid", actor_name AS "actorName",
      null::text AS "readinessGrade", null::text AS summary, null::text AS "validationScore", mood,
      null::text AS "qualityScore", null::text AS grade, null::text AS "domainSummary", source, created_at AS "createdAt"
    FROM vertex_yoro_shinka_evolution
    UNION ALL
    SELECT 'HinshitsuAssessment' AS label, actor_did AS "actorDid", actor_name AS "actorName",
      null::text AS "readinessGrade", null::text AS summary, null::text AS "validationScore", null::text AS mood,
      quality_score AS "qualityScore", grade, null::text AS "domainSummary", source, created_at AS "createdAt"
    FROM vertex_yoro_hinshitsu_assessment
    UNION ALL
    SELECT 'ShinkaKnowledge' AS label, actor_did AS "actorDid", actor_name AS "actorName",
      null::text AS "readinessGrade", null::text AS summary, null::text AS "validationScore", null::text AS mood,
      null::text AS "qualityScore", null::text AS grade, domain_summary AS "domainSummary", source, created_at AS "createdAt"
    FROM vertex_yoro_shinka_knowledge;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yoro_actor_evolution_counts AS
    SELECT actor_did,
      count(*) FILTER (WHERE kind = 'kyumei') AS kyumei_count,
      count(*) FILTER (WHERE kind = 'shinka') AS shinka_count,
      count(*) FILTER (WHERE kind = 'hinshitsu') AS hinshitsu_count,
      count(*) FILTER (WHERE kind = 'knowledge') AS knowledge_count
    FROM (
      SELECT actor_did, 'kyumei' AS kind FROM vertex_yoro_kyumei_validation
      UNION ALL SELECT actor_did, 'shinka' AS kind FROM vertex_yoro_shinka_evolution
      UNION ALL SELECT actor_did, 'hinshitsu' AS kind FROM vertex_yoro_hinshitsu_assessment
      UNION ALL SELECT actor_did, 'knowledge' AS kind FROM vertex_yoro_shinka_knowledge
    ) events
    GROUP BY actor_did;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yoro_actor_score_counts AS
    SELECT actor_did,
      count(*) FILTER (WHERE kind = 'dojo') AS drills,
      count(*) FILTER (WHERE kind = 'joucho') AS reviews
    FROM (
      SELECT actor_did, 'dojo' AS kind FROM vertex_dojo_step_completed_event
      UNION ALL SELECT actor_did, 'joucho' AS kind FROM vertex_joucho_review
    ) events
    GROUP BY actor_did;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_state_profile_status AS
    SELECT repo, rkey, iso3, name, region, indexed_at
    FROM vertex_state_profile;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_agent_role_binding_status AS
    SELECT app_id, count(*) AS binding_count, max(created_at) AS latest_created_at
    FROM vertex_agent_role_binding
    GROUP BY app_id;
