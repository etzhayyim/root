import type { Kysely } from "kysely";
import { sql } from "kysely";

const createdAt = "2026-04-26T21:40:00Z";
const actorTag = "sys.gov.runtime.pilot-100";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    INSERT INTO vertex_actor (
      vertex_id, owner_did, did, nanoid, handle, display_name,
      execution_tier, status, collection, rkey, repo, created_at, name,
      project, performer_type, runtime_type, agent_type, classification,
      operator, category, agent_tools, agent_invoke, capability_declare,
      bpmn_task
    )
    SELECT
      CONCAT('at://', r.actor_did, '/com.etzhayyim.actor.govOrgRuntime/', r.gov_org_key),
      'did:web:gov.etzhayyim.com',
      r.actor_did,
      r.gov_org_key,
      CONCAT('gov-org-', r.gov_org_key),
      CONCAT('Gov org coverage runtime ', r.gov_org_key),
      'pilot',
      'active',
      'com.etzhayyim.actor.govOrgRuntime',
      r.gov_org_key,
      'did:web:gov.etzhayyim.com',
      ${createdAt},
      CONCAT('gov-org-', r.gov_org_key),
      'gov',
      'agent',
      'mcp',
      'gov-org-coverage',
      'government organization coverage runtime pilot',
      'etzhayyim',
      'governance',
      r.tool_nsids,
      r.mcp_endpoint,
      CONCAT('mcp:', r.mcp_id),
      r.bpmn_process_id
    FROM (SELECT * FROM mv_gov_org_runtime ORDER BY gov_org_key LIMIT 100) r
    WHERE NOT EXISTS (SELECT 1 FROM vertex_actor a WHERE a.did = r.actor_did)
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      r.bpmn_process_vertex_id,
      r.actor_did,
      r.bpmn_process_id,
      1,
      CONCAT(
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ',
        'id="defs_', r.bpmn_process_id, '" targetNamespace="https://gov.etzhayyim.com/bpmn">',
        '<bpmn:process id="', r.bpmn_process_id, '" isExecutable="true">',
        '<bpmn:startEvent id="start"/>',
        '<bpmn:task id="refresh_coverage" name="Refresh gov organization coverage"/>',
        '<bpmn:endEvent id="end"/>',
        '</bpmn:process>',
        '</bpmn:definitions>'
      ),
      CAST(LENGTH(CONCAT(
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ',
        'id="defs_', r.bpmn_process_id, '" targetNamespace="https://gov.etzhayyim.com/bpmn">',
        '<bpmn:process id="', r.bpmn_process_id, '" isExecutable="true">',
        '<bpmn:startEvent id="start"/>',
        '<bpmn:task id="refresh_coverage" name="Refresh gov organization coverage"/>',
        '<bpmn:endEvent id="end"/>',
        '</bpmn:process>',
        '</bpmn:definitions>'
      )) AS integer),
      CONCAT('runtime://gov/org/', r.gov_org_key, '/coverage-refresh.bpmn'),
      'active',
      ${createdAt},
      1,
      'did:web:gov.etzhayyim.com',
      'did:web:gov.etzhayyim.com',
      ${actorTag}
    FROM (SELECT * FROM mv_gov_org_runtime ORDER BY gov_org_key LIMIT 100) r
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def p WHERE p.vertex_id = r.bpmn_process_vertex_id
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,
      actor_id, write_table_allowlist
    )
      SELECT
      CONCAT('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gov-org-', r.gov_org_key, '-coverage-refresh-v1'),
      r.actor_did,
      CONCAT('com.etzhayyim.apps.govOrgRuntime.coverageRefresh', REPLACE(REPLACE(r.gov_org_key, ':', '-'), '.', '-')),
      r.bpmn_process_id,
      1,
      180000,
      'active',
      ${createdAt},
      1,
      'did:web:gov.etzhayyim.com',
      'did:web:gov.etzhayyim.com',
      ${actorTag},
      'edge_gov_org_site_dependency,vertex_gov_org,mv_gov_coverage_dedup,mv_gov_org_runtime'
    FROM (SELECT * FROM mv_gov_org_runtime ORDER BY gov_org_key LIMIT 100) r
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding b
      WHERE b.vertex_id = CONCAT('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gov-org-', r.gov_org_key, '-coverage-refresh-v1')
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_mcp_tool_def (
      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,
      input_schema, output_schema, lxm_scope, visibility, version, enabled,
      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,
      actor_id, created_at
    )
    SELECT
      CONCAT('at://', t.actor_did, '/com.etzhayyim.mcp.toolDef/', REPLACE(t.nsid, '.', '-')),
      t.nsid,
      t.actor_did,
      'gov.etzhayyim.com',
      t.lexicon_type,
      t.description,
      t.input_schema,
      t.output_schema,
      t.nsid,
      'public',
      1,
      TRUE,
      CONCAT('runtime://gov/org/', t.gov_org_key, '/mcp/', REPLACE(t.nsid, '.', '/'), '.json'),
      NULL,
      'did:web:gov.etzhayyim.com',
      1,
      'did:web:gov.etzhayyim.com',
      'did:web:gov.etzhayyim.com',
      ${actorTag},
      ${createdAt}
    FROM (
      WITH batch AS (
        SELECT * FROM mv_gov_org_runtime ORDER BY gov_org_key LIMIT 100
      ),
      tools AS (
        SELECT
          b.gov_org_key,
          b.actor_did,
          'com.etzhayyim.apps.gov.coverage.get' AS nsid,
          'query' AS lexicon_type,
          'Read gov organization coverage state.' AS description,
          '{"type":"object","properties":{"govOrgKey":{"type":"string"}}}' AS input_schema,
          '{"type":"object"}' AS output_schema
        FROM batch b
        UNION ALL
        SELECT
          b.gov_org_key,
          b.actor_did,
          'com.etzhayyim.apps.ingest.status' AS nsid,
          'query' AS lexicon_type,
          'Read ingest status for a gov organization runtime.' AS description,
          '{"type":"object","properties":{"govOrgKey":{"type":"string"}}}' AS input_schema,
          '{"type":"object"}' AS output_schema
        FROM batch b
        UNION ALL
        SELECT
          b.gov_org_key,
          b.actor_did,
          'com.etzhayyim.apps.coverage.refresh' AS nsid,
          'procedure' AS lexicon_type,
          'Request a gov organization coverage refresh.' AS description,
          '{"type":"object","properties":{"govOrgKey":{"type":"string"},"force":{"type":"boolean"}}}' AS input_schema,
          '{"type":"object"}' AS output_schema
        FROM batch b
      )
      SELECT * FROM tools
    ) t
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_mcp_tool_def m
      WHERE m.vertex_id = CONCAT('at://', t.actor_did, '/com.etzhayyim.mcp.toolDef/', REPLACE(t.nsid, '.', '-'))
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_mcp_tool_def WHERE actor_id = ${actorTag}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE actor_id = ${actorTag}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE actor_id = ${actorTag}`.execute(db);
  await sql`
    DELETE FROM vertex_actor
    WHERE did IN (SELECT actor_did FROM mv_gov_org_runtime ORDER BY gov_org_key LIMIT 100)
      AND classification = 'government organization coverage runtime pilot'
  `.execute(db);
}
