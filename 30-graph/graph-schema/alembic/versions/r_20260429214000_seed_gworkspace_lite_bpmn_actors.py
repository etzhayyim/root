"""Captured from Kysely migration 20260429214000_seed_gworkspace_lite_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429214000_seed_gworkspace_lite_bpmn_actors"
down_revision = 'r_20260429213000_gworkspace_lite_zeebe_support'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tasks-connect-account-v1',
                 'did:web:tasks.gftd.ai',
                 'tasks_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_tasks_connect_account" '
                 'targetNamespace="https://gftd.ai/bpmn/tasks" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="tasks_connect_account" name="tasks '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.tasks.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="tasks.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1094,
                 '00-contracts/bpmn/ai/gftd/tasks/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.gftd.ai',
                 'did:web:tasks.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tasks-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tasks-connect-account-v1',
                 'did:web:tasks.gftd.ai',
                 'ai.gftd.apps.tasks.connectAccount',
                 'tasks_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.gftd.ai',
                 'did:web:tasks.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tasks-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tasks-oauth-callback-v1',
                 'did:web:tasks.gftd.ai',
                 'tasks_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_tasks_oauth_callback" '
                 'targetNamespace="https://gftd.ai/bpmn/tasks" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="tasks_oauth_callback" name="tasks '
                 'oauthCallback" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.tasks.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="tasks.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/ai/gftd/tasks/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.gftd.ai',
                 'did:web:tasks.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tasks-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tasks-oauth-callback-v1',
                 'did:web:tasks.gftd.ai',
                 'ai.gftd.apps.tasks.oauthCallback',
                 'tasks_oauth_callback',
                 120000,
                 'vertex_gtasks_oauth_token,vertex_gtasks_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.gftd.ai',
                 'did:web:tasks.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tasks-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tasks-sync-from-google-v1',
                 'did:web:tasks.gftd.ai',
                 'tasks_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_tasks_sync_from_google" '
                 'targetNamespace="https://gftd.ai/bpmn/tasks" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="tasks_sync_from_google" name="tasks '
                 'syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.tasks.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="tasks.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1098,
                 '00-contracts/bpmn/ai/gftd/tasks/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.gftd.ai',
                 'did:web:tasks.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tasks-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tasks-sync-from-google-v1',
                 'did:web:tasks.gftd.ai',
                 'ai.gftd.apps.tasks.syncFromGoogle',
                 'tasks_sync_from_google',
                 120000,
                 'vertex_gtasks_oauth_token,vertex_gtasks_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.gftd.ai',
                 'did:web:tasks.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tasks-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tasks-cron-tick-v1',
                 'did:web:tasks.gftd.ai',
                 'tasks_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_tasks_cron_tick" targetNamespace="https://gftd.ai/bpmn/tasks" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="tasks_cron_tick" '
                 'name="tasks cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.tasks.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="tasks.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1283,
                 '00-contracts/bpmn/ai/gftd/tasks/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.gftd.ai',
                 'did:web:tasks.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tasks-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_tasks_cron_tick" targetNamespace="https://gftd.ai/bpmn/tasks" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="tasks_cron_tick" '
                 'name="tasks cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.tasks.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="tasks.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1283,
                 '00-contracts/bpmn/ai/gftd/tasks/cronTick.bpmn',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tasks-cron-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tasks-cronTick-v1',
                 'did:web:tasks.gftd.ai',
                 'ai.gftd.apps.tasks.cronTick',
                 'tasks_cron_tick',
                 120000,
                 'vertex_gtasks_oauth_token,vertex_gtasks_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.gftd.ai',
                 'did:web:tasks.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tasks-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gtasks_oauth_token,vertex_gtasks_account',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tasks-cronTick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sheets-connect-account-v1',
                 'did:web:sheets.gftd.ai',
                 'sheets_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_sheets_connect_account" '
                 'targetNamespace="https://gftd.ai/bpmn/sheets" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="sheets_connect_account" name="sheets '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.sheets.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="sheets.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1100,
                 '00-contracts/bpmn/ai/gftd/sheets/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.gftd.ai',
                 'did:web:sheets.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sheets-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sheets-connect-account-v1',
                 'did:web:sheets.gftd.ai',
                 'ai.gftd.apps.sheets.connectAccount',
                 'sheets_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.gftd.ai',
                 'did:web:sheets.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sheets-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sheets-oauth-callback-v1',
                 'did:web:sheets.gftd.ai',
                 'sheets_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_sheets_oauth_callback" '
                 'targetNamespace="https://gftd.ai/bpmn/sheets" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="sheets_oauth_callback" name="sheets '
                 'oauthCallback" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.sheets.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="sheets.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1095,
                 '00-contracts/bpmn/ai/gftd/sheets/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.gftd.ai',
                 'did:web:sheets.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sheets-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sheets-oauth-callback-v1',
                 'did:web:sheets.gftd.ai',
                 'ai.gftd.apps.sheets.oauthCallback',
                 'sheets_oauth_callback',
                 120000,
                 'vertex_gsheets_oauth_token,vertex_gsheets_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.gftd.ai',
                 'did:web:sheets.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sheets-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sheets-sync-from-google-v1',
                 'did:web:sheets.gftd.ai',
                 'sheets_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_sheets_sync_from_google" '
                 'targetNamespace="https://gftd.ai/bpmn/sheets" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="sheets_sync_from_google" name="sheets '
                 'syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.sheets.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="sheets.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1104,
                 '00-contracts/bpmn/ai/gftd/sheets/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.gftd.ai',
                 'did:web:sheets.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sheets-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sheets-sync-from-google-v1',
                 'did:web:sheets.gftd.ai',
                 'ai.gftd.apps.sheets.syncFromGoogle',
                 'sheets_sync_from_google',
                 120000,
                 'vertex_gsheets_oauth_token,vertex_gsheets_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.gftd.ai',
                 'did:web:sheets.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sheets-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sheets-cron-tick-v1',
                 'did:web:sheets.gftd.ai',
                 'sheets_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_sheets_cron_tick" targetNamespace="https://gftd.ai/bpmn/sheets" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="sheets_cron_tick" name="sheets cronTick" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.sheets.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="sheets.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1289,
                 '00-contracts/bpmn/ai/gftd/sheets/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.gftd.ai',
                 'did:web:sheets.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sheets-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_sheets_cron_tick" targetNamespace="https://gftd.ai/bpmn/sheets" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="sheets_cron_tick" name="sheets cronTick" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.sheets.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="sheets.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1289,
                 '00-contracts/bpmn/ai/gftd/sheets/cronTick.bpmn',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sheets-cron-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sheets-cronTick-v1',
                 'did:web:sheets.gftd.ai',
                 'ai.gftd.apps.sheets.cronTick',
                 'sheets_cron_tick',
                 120000,
                 'vertex_gsheets_oauth_token,vertex_gsheets_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.gftd.ai',
                 'did:web:sheets.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sheets-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gsheets_oauth_token,vertex_gsheets_account',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sheets-cronTick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/drive-connect-account-v1',
                 'did:web:drive.gftd.ai',
                 'drive_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_drive_connect_account" '
                 'targetNamespace="https://gftd.ai/bpmn/drive" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="drive_connect_account" name="drive '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.drive.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="drive.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1094,
                 '00-contracts/bpmn/ai/gftd/drive/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.gftd.ai',
                 'did:web:drive.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/drive-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/drive-connect-account-v1',
                 'did:web:drive.gftd.ai',
                 'ai.gftd.apps.drive.connectAccount',
                 'drive_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.gftd.ai',
                 'did:web:drive.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/drive-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/drive-oauth-callback-v1',
                 'did:web:drive.gftd.ai',
                 'drive_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_drive_oauth_callback" '
                 'targetNamespace="https://gftd.ai/bpmn/drive" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="drive_oauth_callback" name="drive '
                 'oauthCallback" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.drive.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="drive.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/ai/gftd/drive/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.gftd.ai',
                 'did:web:drive.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/drive-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/drive-oauth-callback-v1',
                 'did:web:drive.gftd.ai',
                 'ai.gftd.apps.drive.oauthCallback',
                 'drive_oauth_callback',
                 120000,
                 'vertex_gdrive_oauth_token,vertex_gdrive_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.gftd.ai',
                 'did:web:drive.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/drive-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/drive-sync-from-google-v1',
                 'did:web:drive.gftd.ai',
                 'drive_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_drive_sync_from_google" '
                 'targetNamespace="https://gftd.ai/bpmn/drive" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="drive_sync_from_google" name="drive '
                 'syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.drive.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="drive.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1098,
                 '00-contracts/bpmn/ai/gftd/drive/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.gftd.ai',
                 'did:web:drive.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/drive-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/drive-sync-from-google-v1',
                 'did:web:drive.gftd.ai',
                 'ai.gftd.apps.drive.syncFromGoogle',
                 'drive_sync_from_google',
                 120000,
                 'vertex_gdrive_oauth_token,vertex_gdrive_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.gftd.ai',
                 'did:web:drive.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/drive-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/drive-cron-tick-v1',
                 'did:web:drive.gftd.ai',
                 'drive_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_drive_cron_tick" targetNamespace="https://gftd.ai/bpmn/drive" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="drive_cron_tick" '
                 'name="drive cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.drive.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="drive.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1283,
                 '00-contracts/bpmn/ai/gftd/drive/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.gftd.ai',
                 'did:web:drive.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/drive-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_drive_cron_tick" targetNamespace="https://gftd.ai/bpmn/drive" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="drive_cron_tick" '
                 'name="drive cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.drive.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="drive.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1283,
                 '00-contracts/bpmn/ai/gftd/drive/cronTick.bpmn',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/drive-cron-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/drive-cronTick-v1',
                 'did:web:drive.gftd.ai',
                 'ai.gftd.apps.drive.cronTick',
                 'drive_cron_tick',
                 120000,
                 'vertex_gdrive_oauth_token,vertex_gdrive_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.gftd.ai',
                 'did:web:drive.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/drive-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gdrive_oauth_token,vertex_gdrive_account',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/drive-cronTick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contacts-connect-account-v1',
                 'did:web:contacts.gftd.ai',
                 'contacts_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_contacts_connect_account" '
                 'targetNamespace="https://gftd.ai/bpmn/contacts" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="contacts_connect_account" name="contacts '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.contacts.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="contacts.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1112,
                 '00-contracts/bpmn/ai/gftd/contacts/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.gftd.ai',
                 'did:web:contacts.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contacts-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/contacts-connect-account-v1',
                 'did:web:contacts.gftd.ai',
                 'ai.gftd.apps.contacts.connectAccount',
                 'contacts_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.gftd.ai',
                 'did:web:contacts.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/contacts-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contacts-oauth-callback-v1',
                 'did:web:contacts.gftd.ai',
                 'contacts_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_contacts_oauth_callback" '
                 'targetNamespace="https://gftd.ai/bpmn/contacts" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="contacts_oauth_callback" name="contacts '
                 'oauthCallback" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.contacts.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="contacts.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1107,
                 '00-contracts/bpmn/ai/gftd/contacts/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.gftd.ai',
                 'did:web:contacts.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contacts-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/contacts-oauth-callback-v1',
                 'did:web:contacts.gftd.ai',
                 'ai.gftd.apps.contacts.oauthCallback',
                 'contacts_oauth_callback',
                 120000,
                 'vertex_gcontacts_oauth_token,vertex_gcontacts_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.gftd.ai',
                 'did:web:contacts.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/contacts-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contacts-sync-from-google-v1',
                 'did:web:contacts.gftd.ai',
                 'contacts_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_contacts_sync_from_google" '
                 'targetNamespace="https://gftd.ai/bpmn/contacts" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="contacts_sync_from_google" '
                 'name="contacts syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.contacts.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="contacts.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1116,
                 '00-contracts/bpmn/ai/gftd/contacts/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.gftd.ai',
                 'did:web:contacts.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contacts-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/contacts-sync-from-google-v1',
                 'did:web:contacts.gftd.ai',
                 'ai.gftd.apps.contacts.syncFromGoogle',
                 'contacts_sync_from_google',
                 120000,
                 'vertex_gcontacts_oauth_token,vertex_gcontacts_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.gftd.ai',
                 'did:web:contacts.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/contacts-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contacts-cron-tick-v1',
                 'did:web:contacts.gftd.ai',
                 'contacts_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_contacts_cron_tick" '
                 'targetNamespace="https://gftd.ai/bpmn/contacts" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="contacts_cron_tick" name="contacts '
                 'cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.contacts.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="contacts.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1301,
                 '00-contracts/bpmn/ai/gftd/contacts/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.gftd.ai',
                 'did:web:contacts.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contacts-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_contacts_cron_tick" '
                 'targetNamespace="https://gftd.ai/bpmn/contacts" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="contacts_cron_tick" name="contacts '
                 'cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.contacts.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="contacts.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1301,
                 '00-contracts/bpmn/ai/gftd/contacts/cronTick.bpmn',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contacts-cron-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/contacts-cronTick-v1',
                 'did:web:contacts.gftd.ai',
                 'ai.gftd.apps.contacts.cronTick',
                 'contacts_cron_tick',
                 120000,
                 'vertex_gcontacts_oauth_token,vertex_gcontacts_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.gftd.ai',
                 'did:web:contacts.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/contacts-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gcontacts_oauth_token,vertex_gcontacts_account',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/contacts-cronTick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/meet-connect-account-v1',
                 'did:web:meet.gftd.ai',
                 'meet_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_meet_connect_account" '
                 'targetNamespace="https://gftd.ai/bpmn/meet" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="meet_connect_account" name="meet '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.meet.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="meet.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1088,
                 '00-contracts/bpmn/ai/gftd/meet/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.gftd.ai',
                 'did:web:meet.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/meet-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/meet-connect-account-v1',
                 'did:web:meet.gftd.ai',
                 'ai.gftd.apps.meet.connectAccount',
                 'meet_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.gftd.ai',
                 'did:web:meet.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/meet-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/meet-oauth-callback-v1',
                 'did:web:meet.gftd.ai',
                 'meet_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_meet_oauth_callback" targetNamespace="https://gftd.ai/bpmn/meet" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="meet_oauth_callback" name="meet oauthCallback" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.meet.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="meet.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1083,
                 '00-contracts/bpmn/ai/gftd/meet/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.gftd.ai',
                 'did:web:meet.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/meet-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/meet-oauth-callback-v1',
                 'did:web:meet.gftd.ai',
                 'ai.gftd.apps.meet.oauthCallback',
                 'meet_oauth_callback',
                 120000,
                 'vertex_gmeet_oauth_token,vertex_gmeet_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.gftd.ai',
                 'did:web:meet.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/meet-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/meet-sync-from-google-v1',
                 'did:web:meet.gftd.ai',
                 'meet_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_meet_sync_from_google" '
                 'targetNamespace="https://gftd.ai/bpmn/meet" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="meet_sync_from_google" name="meet '
                 'syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.meet.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="meet.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1092,
                 '00-contracts/bpmn/ai/gftd/meet/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.gftd.ai',
                 'did:web:meet.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/meet-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/meet-sync-from-google-v1',
                 'did:web:meet.gftd.ai',
                 'ai.gftd.apps.meet.syncFromGoogle',
                 'meet_sync_from_google',
                 120000,
                 'vertex_gmeet_oauth_token,vertex_gmeet_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.gftd.ai',
                 'did:web:meet.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/meet-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/meet-cron-tick-v1',
                 'did:web:meet.gftd.ai',
                 'meet_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_meet_cron_tick" targetNamespace="https://gftd.ai/bpmn/meet" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="meet_cron_tick" '
                 'name="meet cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.meet.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="meet.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1277,
                 '00-contracts/bpmn/ai/gftd/meet/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.gftd.ai',
                 'did:web:meet.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/meet-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_meet_cron_tick" targetNamespace="https://gftd.ai/bpmn/meet" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="meet_cron_tick" '
                 'name="meet cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.meet.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="meet.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1277,
                 '00-contracts/bpmn/ai/gftd/meet/cronTick.bpmn',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/meet-cron-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/meet-cronTick-v1',
                 'did:web:meet.gftd.ai',
                 'ai.gftd.apps.meet.cronTick',
                 'meet_cron_tick',
                 120000,
                 'vertex_gmeet_oauth_token,vertex_gmeet_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.gftd.ai',
                 'did:web:meet.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/meet-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gmeet_oauth_token,vertex_gmeet_account',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/meet-cronTick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/docs-connect-account-v1',
                 'did:web:docs.gftd.ai',
                 'docs_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_docs_connect_account" '
                 'targetNamespace="https://gftd.ai/bpmn/docs" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="docs_connect_account" name="docs '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.docs.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="docs.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1088,
                 '00-contracts/bpmn/ai/gftd/docs/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.gftd.ai',
                 'did:web:docs.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/docs-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/docs-connect-account-v1',
                 'did:web:docs.gftd.ai',
                 'ai.gftd.apps.docs.connectAccount',
                 'docs_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.gftd.ai',
                 'did:web:docs.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/docs-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/docs-oauth-callback-v1',
                 'did:web:docs.gftd.ai',
                 'docs_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_docs_oauth_callback" targetNamespace="https://gftd.ai/bpmn/docs" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="docs_oauth_callback" name="docs oauthCallback" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.docs.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="docs.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1083,
                 '00-contracts/bpmn/ai/gftd/docs/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.gftd.ai',
                 'did:web:docs.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/docs-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/docs-oauth-callback-v1',
                 'did:web:docs.gftd.ai',
                 'ai.gftd.apps.docs.oauthCallback',
                 'docs_oauth_callback',
                 120000,
                 'vertex_gdocs_oauth_token,vertex_gdocs_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.gftd.ai',
                 'did:web:docs.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/docs-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/docs-sync-from-google-v1',
                 'did:web:docs.gftd.ai',
                 'docs_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_docs_sync_from_google" '
                 'targetNamespace="https://gftd.ai/bpmn/docs" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="docs_sync_from_google" name="docs '
                 'syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.docs.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="docs.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1092,
                 '00-contracts/bpmn/ai/gftd/docs/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.gftd.ai',
                 'did:web:docs.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/docs-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/docs-sync-from-google-v1',
                 'did:web:docs.gftd.ai',
                 'ai.gftd.apps.docs.syncFromGoogle',
                 'docs_sync_from_google',
                 120000,
                 'vertex_gdocs_oauth_token,vertex_gdocs_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.gftd.ai',
                 'did:web:docs.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/docs-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/docs-cron-tick-v1',
                 'did:web:docs.gftd.ai',
                 'docs_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_docs_cron_tick" targetNamespace="https://gftd.ai/bpmn/docs" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="docs_cron_tick" '
                 'name="docs cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.docs.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="docs.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1277,
                 '00-contracts/bpmn/ai/gftd/docs/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.gftd.ai',
                 'did:web:docs.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/docs-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_docs_cron_tick" targetNamespace="https://gftd.ai/bpmn/docs" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="docs_cron_tick" '
                 'name="docs cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.docs.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="docs.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1277,
                 '00-contracts/bpmn/ai/gftd/docs/cronTick.bpmn',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/docs-cron-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/docs-cronTick-v1',
                 'did:web:docs.gftd.ai',
                 'ai.gftd.apps.docs.cronTick',
                 'docs_cron_tick',
                 120000,
                 'vertex_gdocs_oauth_token,vertex_gdocs_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.gftd.ai',
                 'did:web:docs.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/docs-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gdocs_oauth_token,vertex_gdocs_account',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/docs-cronTick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/slides-connect-account-v1',
                 'did:web:slides.gftd.ai',
                 'slides_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_slides_connect_account" '
                 'targetNamespace="https://gftd.ai/bpmn/slides" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="slides_connect_account" name="slides '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.slides.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="slides.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1100,
                 '00-contracts/bpmn/ai/gftd/slides/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.gftd.ai',
                 'did:web:slides.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/slides-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/slides-connect-account-v1',
                 'did:web:slides.gftd.ai',
                 'ai.gftd.apps.slides.connectAccount',
                 'slides_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.gftd.ai',
                 'did:web:slides.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/slides-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/slides-oauth-callback-v1',
                 'did:web:slides.gftd.ai',
                 'slides_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_slides_oauth_callback" '
                 'targetNamespace="https://gftd.ai/bpmn/slides" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="slides_oauth_callback" name="slides '
                 'oauthCallback" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.slides.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="slides.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1095,
                 '00-contracts/bpmn/ai/gftd/slides/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.gftd.ai',
                 'did:web:slides.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/slides-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/slides-oauth-callback-v1',
                 'did:web:slides.gftd.ai',
                 'ai.gftd.apps.slides.oauthCallback',
                 'slides_oauth_callback',
                 120000,
                 'vertex_gslides_oauth_token,vertex_gslides_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.gftd.ai',
                 'did:web:slides.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/slides-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/slides-sync-from-google-v1',
                 'did:web:slides.gftd.ai',
                 'slides_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_slides_sync_from_google" '
                 'targetNamespace="https://gftd.ai/bpmn/slides" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="slides_sync_from_google" name="slides '
                 'syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.slides.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="slides.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1104,
                 '00-contracts/bpmn/ai/gftd/slides/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.gftd.ai',
                 'did:web:slides.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/slides-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/slides-sync-from-google-v1',
                 'did:web:slides.gftd.ai',
                 'ai.gftd.apps.slides.syncFromGoogle',
                 'slides_sync_from_google',
                 120000,
                 'vertex_gslides_oauth_token,vertex_gslides_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.gftd.ai',
                 'did:web:slides.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/slides-sync-from-google-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/slides-cron-tick-v1',
                 'did:web:slides.gftd.ai',
                 'slides_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_slides_cron_tick" targetNamespace="https://gftd.ai/bpmn/slides" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="slides_cron_tick" name="slides cronTick" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.slides.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="slides.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1289,
                 '00-contracts/bpmn/ai/gftd/slides/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.gftd.ai',
                 'did:web:slides.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/slides-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_slides_cron_tick" targetNamespace="https://gftd.ai/bpmn/slides" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="slides_cron_tick" name="slides cronTick" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.slides.cronTick", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 30 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT30M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="slides.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1289,
                 '00-contracts/bpmn/ai/gftd/slides/cronTick.bpmn',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/slides-cron-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/slides-cronTick-v1',
                 'did:web:slides.gftd.ai',
                 'ai.gftd.apps.slides.cronTick',
                 'slides_cron_tick',
                 120000,
                 'vertex_gslides_oauth_token,vertex_gslides_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.gftd.ai',
                 'did:web:slides.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/slides-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gslides_oauth_token,vertex_gslides_account',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/slides-cronTick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-connect-account-v1',
                 'did:web:gmail.gftd.ai',
                 'gmail_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_connect_account" '
                 'targetNamespace="https://gftd.ai/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_connect_account" name="gmail '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gmail.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1094,
                 '00-contracts/bpmn/ai/gftd/gmail/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-connect-account-v1',
                 'did:web:gmail.gftd.ai',
                 'ai.gftd.apps.gmail.connectAccount',
                 'gmail_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-connect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-oauth-callback-v1',
                 'did:web:gmail.gftd.ai',
                 'gmail_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_oauth_callback" '
                 'targetNamespace="https://gftd.ai/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_oauth_callback" name="gmail '
                 'oauthCallback" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gmail.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/ai/gftd/gmail/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-oauth-callback-v1',
                 'did:web:gmail.gftd.ai',
                 'ai.gftd.apps.gmail.oauthCallback',
                 'gmail_oauth_callback',
                 120000,
                 'vertex_gmail_oauth_token,vertex_gmail_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-oauth-callback-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-disconnect-account-v1',
                 'did:web:gmail.gftd.ai',
                 'gmail_disconnect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_disconnect_account" '
                 'targetNamespace="https://gftd.ai/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_disconnect_account" name="gmail '
                 'disconnectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gmail.disconnectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="disconnect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.disconnectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1112,
                 '00-contracts/bpmn/ai/gftd/gmail/disconnectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-disconnect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-disconnect-account-v1',
                 'did:web:gmail.gftd.ai',
                 'ai.gftd.apps.gmail.disconnectAccount',
                 'gmail_disconnect_account',
                 30000,
                 'vertex_gmail_oauth_token,vertex_gmail_account_binding',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-disconnect-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-sync-inbox-v1',
                 'did:web:gmail.gftd.ai',
                 'gmail_sync_inbox',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_sync_inbox" targetNamespace="https://gftd.ai/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="gmail_sync_inbox" name="gmail syncInbox" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gmail.syncInbox", "version": 1, "resultTimeoutMs": 180000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync inbox"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.syncInbox"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1065,
                 '00-contracts/bpmn/ai/gftd/gmail/syncInbox.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-sync-inbox-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-sync-inbox-v1',
                 'did:web:gmail.gftd.ai',
                 'ai.gftd.apps.gmail.syncInbox',
                 'gmail_sync_inbox',
                 180000,
                 'vertex_gmail_oauth_token,vertex_gmail_email,vertex_gmail_sync_job,vertex_gmail_phishing_alert',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-sync-inbox-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-send-email-v1',
                 'did:web:gmail.gftd.ai',
                 'gmail_send_email',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_send_email" targetNamespace="https://gftd.ai/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="gmail_send_email" name="gmail sendEmail" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gmail.sendEmail", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="send email"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.sendEmail"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1065,
                 '00-contracts/bpmn/ai/gftd/gmail/sendEmail.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-send-email-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-send-email-v1',
                 'did:web:gmail.gftd.ai',
                 'ai.gftd.apps.gmail.sendEmail',
                 'gmail_send_email',
                 120000,
                 'vertex_gmail_oauth_token,vertex_gmail_outbound_email',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-send-email-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-reply-to-thread-v1',
                 'did:web:gmail.gftd.ai',
                 'gmail_reply_to_thread',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_reply_to_thread" '
                 'targetNamespace="https://gftd.ai/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_reply_to_thread" name="gmail '
                 'replyToThread" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gmail.replyToThread", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="reply to '
                 'thread"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.replyToThread"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1092,
                 '00-contracts/bpmn/ai/gftd/gmail/replyToThread.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-reply-to-thread-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-reply-to-thread-v1',
                 'did:web:gmail.gftd.ai',
                 'ai.gftd.apps.gmail.replyToThread',
                 'gmail_reply_to_thread',
                 120000,
                 'vertex_gmail_oauth_token,vertex_gmail_outbound_email',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-reply-to-thread-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-list-accounts-v1',
                 'did:web:gmail.gftd.ai',
                 'gmail_list_accounts',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_list_accounts" '
                 'targetNamespace="https://gftd.ai/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_list_accounts" name="gmail '
                 'listAccounts" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gmail.listAccounts", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="list accounts"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.listAccounts"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1082,
                 '00-contracts/bpmn/ai/gftd/gmail/listAccounts.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-list-accounts-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-list-accounts-v1',
                 'did:web:gmail.gftd.ai',
                 'ai.gftd.apps.gmail.listAccounts',
                 'gmail_list_accounts',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-list-accounts-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-list-threads-v1',
                 'did:web:gmail.gftd.ai',
                 'gmail_list_threads',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_list_threads" targetNamespace="https://gftd.ai/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="gmail_list_threads" name="gmail listThreads" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gmail.listThreads", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="list threads"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.listThreads"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1076,
                 '00-contracts/bpmn/ai/gftd/gmail/listThreads.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-list-threads-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-list-threads-v1',
                 'did:web:gmail.gftd.ai',
                 'ai.gftd.apps.gmail.listThreads',
                 'gmail_list_threads',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-list-threads-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-search-emails-v1',
                 'did:web:gmail.gftd.ai',
                 'gmail_search_emails',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_search_emails" '
                 'targetNamespace="https://gftd.ai/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_search_emails" name="gmail '
                 'searchEmails" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gmail.searchEmails", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="search emails"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.searchEmails"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1082,
                 '00-contracts/bpmn/ai/gftd/gmail/searchEmails.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-search-emails-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-search-emails-v1',
                 'did:web:gmail.gftd.ai',
                 'ai.gftd.apps.gmail.searchEmails',
                 'gmail_search_emails',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-search-emails-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-get-thread-v1',
                 'did:web:gmail.gftd.ai',
                 'gmail_get_thread',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_get_thread" targetNamespace="https://gftd.ai/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="gmail_get_thread" name="gmail getThread" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gmail.getThread", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="get thread"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.getThread"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1065,
                 '00-contracts/bpmn/ai/gftd/gmail/getThread.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-get-thread-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-get-thread-v1',
                 'did:web:gmail.gftd.ai',
                 'ai.gftd.apps.gmail.getThread',
                 'gmail_get_thread',
                 120000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-get-thread-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-triage-v1',
                 'did:web:gmail.gftd.ai',
                 'gmail_triage',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_gmail_triage" '
                 'targetNamespace="https://gftd.ai/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_triage" name="gmail triage" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "ai.gftd.apps.gmail.triage", '
                 '"version": 1, "resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="triage"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.triage"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1043,
                 '00-contracts/bpmn/ai/gftd/gmail/triage.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-triage-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-triage-v1',
                 'did:web:gmail.gftd.ai',
                 'ai.gftd.apps.gmail.triage',
                 'gmail_triage',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-triage-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-cron-tick-v1',
                 'did:web:gmail.gftd.ai',
                 'gmail_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_gmail_cron_tick" targetNamespace="https://gftd.ai/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="gmail_cron_tick" '
                 'name="gmail cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gmail.cronTick", "version": 1, "resultTimeoutMs": 180000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 15 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT15M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT15M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1283,
                 '00-contracts/bpmn/ai/gftd/gmail/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_gmail_cron_tick" targetNamespace="https://gftd.ai/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="gmail_cron_tick" '
                 'name="gmail cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gmail.cronTick", "version": 1, "resultTimeoutMs": 180000 '
                 '}</bpmn:documentation><bpmn:startEvent id="Start" name="every 15 '
                 'minutes"><bpmn:outgoing>Flow_1</bpmn:outgoing><bpmn:timerEventDefinition '
                 'id="Timer_PT15M"><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT15M</bpmn:timeCycle></bpmn:timerEventDefinition></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="cron tick"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.cronTick"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1283,
                 '00-contracts/bpmn/ai/gftd/gmail/cronTick.bpmn',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-cron-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-cronTick-v1',
                 'did:web:gmail.gftd.ai',
                 'ai.gftd.apps.gmail.cronTick',
                 'gmail_cron_tick',
                 180000,
                 'vertex_gmail_oauth_token,vertex_gmail_email,vertex_gmail_sync_job,vertex_gmail_phishing_alert',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [180000,
                 'vertex_gmail_oauth_token,vertex_gmail_email,vertex_gmail_sync_job,vertex_gmail_phishing_alert',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-cronTick-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tasks-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tasks-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tasks-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tasks-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tasks-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tasks-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sheets-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sheets-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sheets-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sheets-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sheets-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sheets-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/drive-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/drive-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/drive-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/drive-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/drive-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/drive-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/contacts-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contacts-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/contacts-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contacts-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/contacts-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/contacts-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/meet-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/meet-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/meet-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/meet-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/meet-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/meet-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/docs-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/docs-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/docs-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/docs-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/docs-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/docs-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/slides-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/slides-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/slides-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/slides-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/slides-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/slides-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-disconnect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-disconnect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-sync-inbox-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-sync-inbox-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-send-email-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-send-email-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-reply-to-thread-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-reply-to-thread-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-list-accounts-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-list-accounts-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-list-threads-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-list-threads-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-search-emails-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-search-emails-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-get-thread-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-get-thread-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/gmail-triage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/gmail-triage-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
