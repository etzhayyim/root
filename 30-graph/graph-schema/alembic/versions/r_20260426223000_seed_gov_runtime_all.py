"""Captured from Kysely migration 20260426223000_seed_gov_runtime_all."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260426223000_seed_gov_runtime_all"
down_revision = 'r_20260426220000_schema_index_mv_naming_optimization'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_actor (\n'
         '      vertex_id, owner_did, did, nanoid, handle, display_name,\n'
         '      execution_tier, status, collection, rkey, repo, created_at, name,\n'
         '      project, performer_type, runtime_type, agent_type, classification,\n'
         '      operator, category, agent_tools, agent_invoke, capability_declare,\n'
         '      bpmn_task\n'
         '    )\n'
         '    SELECT\n'
         "      CONCAT('at://', r.actor_did, '/com.etzhayyim.actor.govOrgRuntime/', r.gov_org_key),\n"
         "      'did:web:gov.etzhayyim.com',\n"
         '      r.actor_did,\n'
         '      r.gov_org_key,\n'
         "      CONCAT('gov-org-', r.gov_org_key),\n"
         "      CONCAT('Gov org coverage runtime ', r.gov_org_key),\n"
         "      'prod',\n"
         "      'active',\n"
         "      'com.etzhayyim.actor.govOrgRuntime',\n"
         '      r.gov_org_key,\n'
         "      'did:web:gov.etzhayyim.com',\n"
         '      $1,\n'
         "      CONCAT('gov-org-', r.gov_org_key),\n"
         "      'gov',\n"
         "      'agent',\n"
         "      'mcp',\n"
         "      'gov-org-coverage',\n"
         "      'government organization coverage runtime',\n"
         "      'etzhayyim',\n"
         "      'governance',\n"
         '      r.tool_nsids,\n'
         '      r.mcp_endpoint,\n'
         "      CONCAT('mcp:', r.mcp_id),\n"
         '      r.bpmn_process_id\n'
         '    FROM mv_gov_org_runtime r\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_actor a WHERE a.did = r.actor_did)\n'
         '  ',
  'parameters': ['2026-04-26T22:30:00Z']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      r.bpmn_process_vertex_id,\n'
         '      r.actor_did,\n'
         '      r.bpmn_process_id,\n'
         '      1,\n'
         '      CONCAT(\n'
         '        \'<?xml version="1.0" encoding="UTF-8"?>\',\n'
         '        \'<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
         "',\n"
         '        \'id="defs_\', r.bpmn_process_id, \'" '
         'targetNamespace="https://gov.etzhayyim.com/bpmn">\',\n'
         '        \'<bpmn:process id="\', r.bpmn_process_id, \'" isExecutable="true">\',\n'
         '        \'<bpmn:startEvent id="start"/>\',\n'
         '        \'<bpmn:task id="refresh_coverage" name="Refresh gov organization '
         'coverage"/>\',\n'
         '        \'<bpmn:endEvent id="end"/>\',\n'
         "        '</bpmn:process>',\n"
         "        '</bpmn:definitions>'\n"
         '      ),\n'
         '      CAST(LENGTH(CONCAT(\n'
         '        \'<?xml version="1.0" encoding="UTF-8"?>\',\n'
         '        \'<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
         "',\n"
         '        \'id="defs_\', r.bpmn_process_id, \'" '
         'targetNamespace="https://gov.etzhayyim.com/bpmn">\',\n'
         '        \'<bpmn:process id="\', r.bpmn_process_id, \'" isExecutable="true">\',\n'
         '        \'<bpmn:startEvent id="start"/>\',\n'
         '        \'<bpmn:task id="refresh_coverage" name="Refresh gov organization '
         'coverage"/>\',\n'
         '        \'<bpmn:endEvent id="end"/>\',\n'
         "        '</bpmn:process>',\n"
         "        '</bpmn:definitions>'\n"
         '      )) AS integer),\n'
         "      CONCAT('runtime://gov/org/', r.gov_org_key, '/coverage-refresh.bpmn'),\n"
         "      'active',\n"
         '      $1,\n'
         '      1,\n'
         "      'did:web:gov.etzhayyim.com',\n"
         "      'did:web:gov.etzhayyim.com',\n"
         '      $2\n'
         '    FROM mv_gov_org_runtime r\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def p WHERE p.vertex_id = '
         'r.bpmn_process_vertex_id\n'
         '    )\n'
         '  ',
  'parameters': ['2026-04-26T22:30:00Z', 'sys.gov.runtime.all']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         "      CONCAT('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gov-org-', "
         "r.gov_org_key, '-coverage-refresh-v1'),\n"
         '      r.actor_did,\n'
         "      CONCAT('com.etzhayyim.apps.govOrgRuntime.coverageRefresh', "
         "REPLACE(REPLACE(r.gov_org_key, ':', '-'), '.', '-')),\n"
         '      r.bpmn_process_id,\n'
         '      1,\n'
         '      180000,\n'
         "      'active',\n"
         '      $1,\n'
         '      1,\n'
         "      'did:web:gov.etzhayyim.com',\n"
         "      'did:web:gov.etzhayyim.com',\n"
         '      $2,\n'
         '      '
         "'edge_gov_org_site_dependency,vertex_gov_org,mv_gov_coverage_dedup,mv_gov_org_runtime'\n"
         '    FROM mv_gov_org_runtime r\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding b\n'
         '      WHERE b.vertex_id = '
         "CONCAT('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gov-org-', r.gov_org_key, "
         "'-coverage-refresh-v1')\n"
         '    )\n'
         '  ',
  'parameters': ['2026-04-26T22:30:00Z', 'sys.gov.runtime.all']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         "      CONCAT('at://', t.actor_did, '/com.etzhayyim.mcp.toolDef/', REPLACE(t.nsid, '.', '-')),\n"
         '      t.nsid,\n'
         '      t.actor_did,\n'
         "      'gov.etzhayyim.com',\n"
         '      t.lexicon_type,\n'
         '      t.description,\n'
         '      t.input_schema,\n'
         '      t.output_schema,\n'
         '      t.nsid,\n'
         "      'public',\n"
         '      1,\n'
         '      TRUE,\n'
         "      CONCAT('runtime://gov/org/', t.gov_org_key, '/mcp/', REPLACE(t.nsid, '.', '/'), "
         "'.json'),\n"
         '      NULL,\n'
         "      'did:web:gov.etzhayyim.com',\n"
         '      1,\n'
         "      'did:web:gov.etzhayyim.com',\n"
         "      'did:web:gov.etzhayyim.com',\n"
         '      $1,\n'
         '      $2\n'
         '    FROM (\n'
         '      SELECT\n'
         '        r.gov_org_key,\n'
         '        r.actor_did,\n'
         "        'com.etzhayyim.apps.gov.coverage.get' AS nsid,\n"
         "        'query' AS lexicon_type,\n"
         "        'Read gov organization coverage state.' AS description,\n"
         '        \'{"type":"object","properties":{"govOrgKey":{"type":"string"}}}\' AS '
         'input_schema,\n'
         '        \'{"type":"object"}\' AS output_schema\n'
         '      FROM mv_gov_org_runtime r\n'
         '      UNION ALL\n'
         '      SELECT\n'
         '        r.gov_org_key,\n'
         '        r.actor_did,\n'
         "        'com.etzhayyim.apps.ingest.status' AS nsid,\n"
         "        'query' AS lexicon_type,\n"
         "        'Read ingest status for a gov organization runtime.' AS description,\n"
         '        \'{"type":"object","properties":{"govOrgKey":{"type":"string"}}}\' AS '
         'input_schema,\n'
         '        \'{"type":"object"}\' AS output_schema\n'
         '      FROM mv_gov_org_runtime r\n'
         '      UNION ALL\n'
         '      SELECT\n'
         '        r.gov_org_key,\n'
         '        r.actor_did,\n'
         "        'com.etzhayyim.apps.coverage.refresh' AS nsid,\n"
         "        'procedure' AS lexicon_type,\n"
         "        'Request a gov organization coverage refresh.' AS description,\n"
         '        '
         '\'{"type":"object","properties":{"govOrgKey":{"type":"string"},"force":{"type":"boolean"}}}\' '
         'AS input_schema,\n'
         '        \'{"type":"object"}\' AS output_schema\n'
         '      FROM mv_gov_org_runtime r\n'
         '    ) t\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def m\n'
         "      WHERE m.vertex_id = CONCAT('at://', t.actor_did, '/com.etzhayyim.mcp.toolDef/', "
         "REPLACE(t.nsid, '.', '-'))\n"
         '    )\n'
         '  ',
  'parameters': ['sys.gov.runtime.all', '2026-04-26T22:30:00Z']},
 {'sql': '\n'
         '    UPDATE vertex_actor\n'
         "    SET execution_tier = 'prod',\n"
         "        classification = 'government organization coverage runtime'\n"
         "    WHERE collection = 'com.etzhayyim.actor.govOrgRuntime'\n"
         '      AND did IN (SELECT actor_did FROM mv_gov_org_runtime)\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_process_def\n'
         '    SET actor_id = $1\n'
         "    WHERE source_path LIKE 'runtime://gov/org/%/coverage-refresh.bpmn'\n"
         '      AND bpmn_process_id IN (SELECT bpmn_process_id FROM mv_gov_org_runtime)\n'
         '  ',
  'parameters': ['sys.gov.runtime.all']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET actor_id = $1\n'
         "    WHERE nsid LIKE 'com.etzhayyim.apps.govOrgRuntime.coverageRefresh%'\n"
         '      AND bpmn_process_id IN (SELECT bpmn_process_id FROM mv_gov_org_runtime)\n'
         '  ',
  'parameters': ['sys.gov.runtime.all']},
 {'sql': '\n'
         '    UPDATE vertex_mcp_tool_def\n'
         '    SET actor_id = $1\n'
         "    WHERE source_path LIKE 'runtime://gov/org/%/mcp/%'\n"
         '      AND actor_did IN (SELECT actor_did FROM mv_gov_org_runtime)\n'
         '  ',
  'parameters': ['sys.gov.runtime.all']}]

DOWN = [{'sql': 'DELETE FROM vertex_mcp_tool_def WHERE actor_id = $1',
  'parameters': ['sys.gov.runtime.all']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE actor_id = $1',
  'parameters': ['sys.gov.runtime.all']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE actor_id = $1',
  'parameters': ['sys.gov.runtime.all']},
 {'sql': '\n'
         '    DELETE FROM vertex_actor\n'
         "    WHERE collection = 'com.etzhayyim.actor.govOrgRuntime'\n"
         '      AND did IN (SELECT actor_did FROM mv_gov_org_runtime)\n'
         "      AND classification = 'government organization coverage runtime'\n"
         '  ',
  'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
