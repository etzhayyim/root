"""Captured from Kysely migration 20260507380000_seed_os_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507380000_seed_os_bpmn"
down_revision = 'r_20260507370000_seed_isekai_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-list-v1',
                 'did:web:os.etzhayyim.com',
                 'os_agent_list',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_os_agent_list" '
                 'targetNamespace="https://etzhayyim.com/bpmn/os" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_agent_list" name="agentList" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_agentList"/>\n'
                 '    <bpmn:serviceTask id="Task_agentList" name="agentList">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.agentList" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_agentList" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/agentList.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-list-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1085, 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-list-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-list-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.agentList',
                 'os_agent_list',
                 '',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-list-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-migrate-v1',
                 'did:web:os.etzhayyim.com',
                 'os_agent_migrate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_agent_migrate" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_agent_migrate" name="agentMigrate" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_agentMigrate"/>\n'
                 '    <bpmn:serviceTask id="Task_agentMigrate" name="agentMigrate">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.agentMigrate" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_agentMigrate" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/agentMigrate.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-migrate-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1109,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-migrate-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-migrate-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.agentMigrate',
                 'os_agent_migrate',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-migrate-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-pause-v1',
                 'did:web:os.etzhayyim.com',
                 'os_agent_pause',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_agent_pause" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_agent_pause" name="agentPause" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_agentPause"/>\n'
                 '    <bpmn:serviceTask id="Task_agentPause" name="agentPause">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.agentPause" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_agentPause" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/agentPause.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-pause-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1093, 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-pause-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-pause-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.agentPause',
                 'os_agent_pause',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-pause-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-resume-v1',
                 'did:web:os.etzhayyim.com',
                 'os_agent_resume',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_agent_resume" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_agent_resume" name="agentResume" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_agentResume"/>\n'
                 '    <bpmn:serviceTask id="Task_agentResume" name="agentResume">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.agentResume" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_agentResume" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/agentResume.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-resume-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1101,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-resume-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-resume-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.agentResume',
                 'os_agent_resume',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-resume-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-spawn-v1',
                 'did:web:os.etzhayyim.com',
                 'os_agent_spawn',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_agent_spawn" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_agent_spawn" name="agentSpawn" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_agentSpawn"/>\n'
                 '    <bpmn:serviceTask id="Task_agentSpawn" name="agentSpawn">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.agentSpawn" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_agentSpawn" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/agentSpawn.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-spawn-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1093, 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-spawn-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-spawn-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.agentSpawn',
                 'os_agent_spawn',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-spawn-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-stop-v1',
                 'did:web:os.etzhayyim.com',
                 'os_agent_stop',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_os_agent_stop" '
                 'targetNamespace="https://etzhayyim.com/bpmn/os" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_agent_stop" name="agentStop" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_agentStop"/>\n'
                 '    <bpmn:serviceTask id="Task_agentStop" name="agentStop">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.agentStop" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_agentStop" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/agentStop.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-stop-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1085, 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-stop-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-stop-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.agentStop',
                 'os_agent_stop',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-stop-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-audit-trail-v1',
                 'did:web:os.etzhayyim.com',
                 'os_audit_trail',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_audit_trail" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_audit_trail" name="auditTrail" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_auditTrail"/>\n'
                 '    <bpmn:serviceTask id="Task_auditTrail" name="auditTrail">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.auditTrail" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_auditTrail" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/auditTrail.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-audit-trail-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1093, 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-audit-trail-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-audit-trail-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.auditTrail',
                 'os_audit_trail',
                 '',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-audit-trail-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-budget-allocate-v1',
                 'did:web:os.etzhayyim.com',
                 'os_budget_allocate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_budget_allocate" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_budget_allocate" name="budgetAllocate" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_budgetAllocate"/>\n'
                 '    <bpmn:serviceTask id="Task_budgetAllocate" name="budgetAllocate">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.budgetAllocate" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_budgetAllocate" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/budgetAllocate.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-budget-allocate-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1125,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-budget-allocate-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-budget-allocate-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.budgetAllocate',
                 'os_budget_allocate',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-budget-allocate-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-budget-balance-v1',
                 'did:web:os.etzhayyim.com',
                 'os_budget_balance',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_budget_balance" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_budget_balance" name="budgetBalance" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_budgetBalance"/>\n'
                 '    <bpmn:serviceTask id="Task_budgetBalance" name="budgetBalance">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.budgetBalance" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_budgetBalance" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/budgetBalance.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-budget-balance-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1117,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-budget-balance-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-budget-balance-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.budgetBalance',
                 'os_budget_balance',
                 '',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-budget-balance-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-approve-v1',
                 'did:web:os.etzhayyim.com',
                 'os_consent_approve',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_consent_approve" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_consent_approve" name="consentApprove" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_consentApprove"/>\n'
                 '    <bpmn:serviceTask id="Task_consentApprove" name="consentApprove">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.consentApprove" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_consentApprove" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/consentApprove.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-approve-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1125,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-approve-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-consent-approve-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.consentApprove',
                 'os_consent_approve',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-consent-approve-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-deny-v1',
                 'did:web:os.etzhayyim.com',
                 'os_consent_deny',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_consent_deny" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_consent_deny" name="consentDeny" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_consentDeny"/>\n'
                 '    <bpmn:serviceTask id="Task_consentDeny" name="consentDeny">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.consentDeny" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_consentDeny" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/consentDeny.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-deny-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1101,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-deny-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-consent-deny-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.consentDeny',
                 'os_consent_deny',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-consent-deny-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-pending-v1',
                 'did:web:os.etzhayyim.com',
                 'os_consent_pending',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_consent_pending" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_consent_pending" name="consentPending" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_consentPending"/>\n'
                 '    <bpmn:serviceTask id="Task_consentPending" name="consentPending">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.consentPending" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_consentPending" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/consentPending.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-pending-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1125,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-pending-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-consent-pending-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.consentPending',
                 'os_consent_pending',
                 '',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-consent-pending-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-submit-v1',
                 'did:web:os.etzhayyim.com',
                 'os_consent_submit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_consent_submit" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_consent_submit" name="consentSubmit" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_consentSubmit"/>\n'
                 '    <bpmn:serviceTask id="Task_consentSubmit" name="consentSubmit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.consentSubmit" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_consentSubmit" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/consentSubmit.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-submit-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1117,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-submit-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-consent-submit-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.consentSubmit',
                 'os_consent_submit',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-consent-submit-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-directory-register-v1',
                 'did:web:os.etzhayyim.com',
                 'os_directory_register',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_directory_register" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_directory_register" name="directoryRegister" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_directoryRegister"/>\n'
                 '    <bpmn:serviceTask id="Task_directoryRegister" name="directoryRegister">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.directoryRegister" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_directoryRegister" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/directoryRegister.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-directory-register-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1149,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-directory-register-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-directory-register-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.directoryRegister',
                 'os_directory_register',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-directory-register-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-directory-search-v1',
                 'did:web:os.etzhayyim.com',
                 'os_directory_search',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_directory_search" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_directory_search" name="directorySearch" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_directorySearch"/>\n'
                 '    <bpmn:serviceTask id="Task_directorySearch" name="directorySearch">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.directorySearch" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_directorySearch" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/directorySearch.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-directory-search-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1133,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-directory-search-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-directory-search-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.directorySearch',
                 'os_directory_search',
                 '',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-directory-search-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-health-v1',
                 'did:web:os.etzhayyim.com',
                 'os_health',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_os_health" '
                 'targetNamespace="https://etzhayyim.com/bpmn/os" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_health" name="health" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_health"/>\n'
                 '    <bpmn:serviceTask id="Task_health" name="health">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.health" retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_health" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/health.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-health-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1059, 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-health-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-health-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.health',
                 'os_health',
                 '',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-health-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-sync-pull-v1',
                 'did:web:os.etzhayyim.com',
                 'os_sync_pull',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_os_sync_pull" '
                 'targetNamespace="https://etzhayyim.com/bpmn/os" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_sync_pull" name="syncPull" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_syncPull"/>\n'
                 '    <bpmn:serviceTask id="Task_syncPull" name="syncPull">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.syncPull" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_syncPull" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/syncPull.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-sync-pull-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1077, 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-sync-pull-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-sync-pull-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.syncPull',
                 'os_sync_pull',
                 '',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-sync-pull-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-sync-push-v1',
                 'did:web:os.etzhayyim.com',
                 'os_sync_push',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_os_sync_push" '
                 'targetNamespace="https://etzhayyim.com/bpmn/os" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_sync_push" name="syncPush" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_syncPush"/>\n'
                 '    <bpmn:serviceTask id="Task_syncPush" name="syncPush">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.syncPush" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_syncPush" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/syncPush.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-sync-push-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1077, 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-sync-push-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-sync-push-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.syncPush',
                 'os_sync_push',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-sync-push-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-window-close-v1',
                 'did:web:os.etzhayyim.com',
                 'os_window_close',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_window_close" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_window_close" name="windowClose" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_windowClose"/>\n'
                 '    <bpmn:serviceTask id="Task_windowClose" name="windowClose">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.windowClose" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_windowClose" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/windowClose.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-window-close-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1101,
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-window-close-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-window-close-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.windowClose',
                 'os_window_close',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-window-close-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-window-open-v1',
                 'did:web:os.etzhayyim.com',
                 'os_window_open',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_os_window_open" targetNamespace="https://etzhayyim.com/bpmn/os" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="os_window_open" name="windowOpen" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_windowOpen"/>\n'
                 '    <bpmn:serviceTask id="Task_windowOpen" name="windowOpen">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.os.windowOpen" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_windowOpen" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/os/windowOpen.bpmn',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-window-open-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1093, 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-window-open-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-window-open-v1',
                 'did:web:os.etzhayyim.com',
                 'ai.gftd.apps.os.windowOpen',
                 'os_window_open',
                 'vertex_os_agent,vertex_os_agent_event,vertex_os_audit_entry,vertex_os_consent_request,vertex_os_consent_response,vertex_os_budget_allocation,vertex_os_directory_entry,vertex_os_sync_event,vertex_os_window_event,edge_os_agent_event,edge_os_agent_audit_entry,edge_os_consent_response,edge_os_budget_agent',
                 '2026-05-07T00:50:00Z',
                 'did:web:os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'sys.bpmn.seed.os',
                 'did:web:os.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-window-open-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-list-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-list-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-migrate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-migrate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-pause-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-pause-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-resume-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-resume-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-spawn-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-spawn-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-agent-stop-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-agent-stop-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-audit-trail-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-audit-trail-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-budget-allocate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-budget-allocate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-budget-balance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-budget-balance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-consent-approve-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-approve-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-consent-deny-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-deny-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-consent-pending-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-pending-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-consent-submit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-consent-submit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-directory-register-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-directory-register-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-directory-search-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-directory-search-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-health-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-health-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-sync-pull-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-sync-pull-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-sync-push-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-sync-push-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-window-close-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-window-close-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-window-open-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-window-open-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
