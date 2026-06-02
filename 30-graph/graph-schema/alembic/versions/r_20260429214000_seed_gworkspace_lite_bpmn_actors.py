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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/tasks-connect-account-v1',
                 'did:web:tasks.etzhayyim.com',
                 'tasks_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_tasks_connect_account" '
                 'targetNamespace="https://etzhayyim.com/bpmn/tasks" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="tasks_connect_account" name="tasks '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.tasks.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="tasks.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1094,
                 '00-contracts/bpmn/com/etzhayyim/tasks/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.etzhayyim.com',
                 'did:web:tasks.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/tasks-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/tasks-connect-account-v1',
                 'did:web:tasks.etzhayyim.com',
                 'com.etzhayyim.apps.tasks.connectAccount',
                 'tasks_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.etzhayyim.com',
                 'did:web:tasks.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/tasks-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/tasks-oauth-callback-v1',
                 'did:web:tasks.etzhayyim.com',
                 'tasks_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_tasks_oauth_callback" '
                 'targetNamespace="https://etzhayyim.com/bpmn/tasks" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="tasks_oauth_callback" name="tasks '
                 'oauthCallback" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.tasks.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="tasks.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/com/etzhayyim/tasks/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.etzhayyim.com',
                 'did:web:tasks.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/tasks-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/tasks-oauth-callback-v1',
                 'did:web:tasks.etzhayyim.com',
                 'com.etzhayyim.apps.tasks.oauthCallback',
                 'tasks_oauth_callback',
                 120000,
                 'vertex_gtasks_oauth_token,vertex_gtasks_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.etzhayyim.com',
                 'did:web:tasks.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/tasks-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/tasks-sync-from-google-v1',
                 'did:web:tasks.etzhayyim.com',
                 'tasks_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_tasks_sync_from_google" '
                 'targetNamespace="https://etzhayyim.com/bpmn/tasks" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="tasks_sync_from_google" name="tasks '
                 'syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.tasks.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="tasks.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1098,
                 '00-contracts/bpmn/com/etzhayyim/tasks/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.etzhayyim.com',
                 'did:web:tasks.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/tasks-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/tasks-sync-from-google-v1',
                 'did:web:tasks.etzhayyim.com',
                 'com.etzhayyim.apps.tasks.syncFromGoogle',
                 'tasks_sync_from_google',
                 120000,
                 'vertex_gtasks_oauth_token,vertex_gtasks_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.etzhayyim.com',
                 'did:web:tasks.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/tasks-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/tasks-cron-tick-v1',
                 'did:web:tasks.etzhayyim.com',
                 'tasks_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_tasks_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/tasks" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="tasks_cron_tick" '
                 'name="tasks cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.tasks.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/tasks/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.etzhayyim.com',
                 'did:web:tasks.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/tasks-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_tasks_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/tasks" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="tasks_cron_tick" '
                 'name="tasks cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.tasks.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/tasks/cronTick.bpmn',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/tasks-cron-tick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/tasks-cronTick-v1',
                 'did:web:tasks.etzhayyim.com',
                 'com.etzhayyim.apps.tasks.cronTick',
                 'tasks_cron_tick',
                 120000,
                 'vertex_gtasks_oauth_token,vertex_gtasks_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:tasks.etzhayyim.com',
                 'did:web:tasks.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:tasks.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/tasks-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gtasks_oauth_token,vertex_gtasks_account',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/tasks-cronTick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sheets-connect-account-v1',
                 'did:web:sheets.etzhayyim.com',
                 'sheets_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_sheets_connect_account" '
                 'targetNamespace="https://etzhayyim.com/bpmn/sheets" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="sheets_connect_account" name="sheets '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.sheets.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="sheets.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1100,
                 '00-contracts/bpmn/com/etzhayyim/sheets/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.etzhayyim.com',
                 'did:web:sheets.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sheets-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sheets-connect-account-v1',
                 'did:web:sheets.etzhayyim.com',
                 'com.etzhayyim.apps.sheets.connectAccount',
                 'sheets_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.etzhayyim.com',
                 'did:web:sheets.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sheets-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sheets-oauth-callback-v1',
                 'did:web:sheets.etzhayyim.com',
                 'sheets_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_sheets_oauth_callback" '
                 'targetNamespace="https://etzhayyim.com/bpmn/sheets" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="sheets_oauth_callback" name="sheets '
                 'oauthCallback" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.sheets.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="sheets.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1095,
                 '00-contracts/bpmn/com/etzhayyim/sheets/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.etzhayyim.com',
                 'did:web:sheets.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sheets-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sheets-oauth-callback-v1',
                 'did:web:sheets.etzhayyim.com',
                 'com.etzhayyim.apps.sheets.oauthCallback',
                 'sheets_oauth_callback',
                 120000,
                 'vertex_gsheets_oauth_token,vertex_gsheets_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.etzhayyim.com',
                 'did:web:sheets.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sheets-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sheets-sync-from-google-v1',
                 'did:web:sheets.etzhayyim.com',
                 'sheets_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_sheets_sync_from_google" '
                 'targetNamespace="https://etzhayyim.com/bpmn/sheets" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="sheets_sync_from_google" name="sheets '
                 'syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.sheets.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="sheets.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1104,
                 '00-contracts/bpmn/com/etzhayyim/sheets/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.etzhayyim.com',
                 'did:web:sheets.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sheets-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sheets-sync-from-google-v1',
                 'did:web:sheets.etzhayyim.com',
                 'com.etzhayyim.apps.sheets.syncFromGoogle',
                 'sheets_sync_from_google',
                 120000,
                 'vertex_gsheets_oauth_token,vertex_gsheets_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.etzhayyim.com',
                 'did:web:sheets.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sheets-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sheets-cron-tick-v1',
                 'did:web:sheets.etzhayyim.com',
                 'sheets_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_sheets_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/sheets" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="sheets_cron_tick" name="sheets cronTick" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.sheets.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/sheets/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.etzhayyim.com',
                 'did:web:sheets.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sheets-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_sheets_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/sheets" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="sheets_cron_tick" name="sheets cronTick" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.sheets.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/sheets/cronTick.bpmn',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sheets-cron-tick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sheets-cronTick-v1',
                 'did:web:sheets.etzhayyim.com',
                 'com.etzhayyim.apps.sheets.cronTick',
                 'sheets_cron_tick',
                 120000,
                 'vertex_gsheets_oauth_token,vertex_gsheets_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:sheets.etzhayyim.com',
                 'did:web:sheets.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:sheets.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sheets-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gsheets_oauth_token,vertex_gsheets_account',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sheets-cronTick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/drive-connect-account-v1',
                 'did:web:drive.etzhayyim.com',
                 'drive_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_drive_connect_account" '
                 'targetNamespace="https://etzhayyim.com/bpmn/drive" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="drive_connect_account" name="drive '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.drive.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="drive.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1094,
                 '00-contracts/bpmn/com/etzhayyim/drive/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.etzhayyim.com',
                 'did:web:drive.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/drive-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/drive-connect-account-v1',
                 'did:web:drive.etzhayyim.com',
                 'com.etzhayyim.apps.drive.connectAccount',
                 'drive_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.etzhayyim.com',
                 'did:web:drive.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/drive-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/drive-oauth-callback-v1',
                 'did:web:drive.etzhayyim.com',
                 'drive_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_drive_oauth_callback" '
                 'targetNamespace="https://etzhayyim.com/bpmn/drive" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="drive_oauth_callback" name="drive '
                 'oauthCallback" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.drive.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="drive.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/com/etzhayyim/drive/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.etzhayyim.com',
                 'did:web:drive.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/drive-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/drive-oauth-callback-v1',
                 'did:web:drive.etzhayyim.com',
                 'com.etzhayyim.apps.drive.oauthCallback',
                 'drive_oauth_callback',
                 120000,
                 'vertex_gdrive_oauth_token,vertex_gdrive_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.etzhayyim.com',
                 'did:web:drive.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/drive-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/drive-sync-from-google-v1',
                 'did:web:drive.etzhayyim.com',
                 'drive_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_drive_sync_from_google" '
                 'targetNamespace="https://etzhayyim.com/bpmn/drive" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="drive_sync_from_google" name="drive '
                 'syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.drive.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="drive.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1098,
                 '00-contracts/bpmn/com/etzhayyim/drive/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.etzhayyim.com',
                 'did:web:drive.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/drive-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/drive-sync-from-google-v1',
                 'did:web:drive.etzhayyim.com',
                 'com.etzhayyim.apps.drive.syncFromGoogle',
                 'drive_sync_from_google',
                 120000,
                 'vertex_gdrive_oauth_token,vertex_gdrive_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.etzhayyim.com',
                 'did:web:drive.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/drive-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/drive-cron-tick-v1',
                 'did:web:drive.etzhayyim.com',
                 'drive_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_drive_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/drive" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="drive_cron_tick" '
                 'name="drive cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.drive.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/drive/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.etzhayyim.com',
                 'did:web:drive.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/drive-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_drive_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/drive" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="drive_cron_tick" '
                 'name="drive cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.drive.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/drive/cronTick.bpmn',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/drive-cron-tick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/drive-cronTick-v1',
                 'did:web:drive.etzhayyim.com',
                 'com.etzhayyim.apps.drive.cronTick',
                 'drive_cron_tick',
                 120000,
                 'vertex_gdrive_oauth_token,vertex_gdrive_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:drive.etzhayyim.com',
                 'did:web:drive.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:drive.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/drive-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gdrive_oauth_token,vertex_gdrive_account',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/drive-cronTick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/contacts-connect-account-v1',
                 'did:web:contacts.etzhayyim.com',
                 'contacts_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_contacts_connect_account" '
                 'targetNamespace="https://etzhayyim.com/bpmn/contacts" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="contacts_connect_account" name="contacts '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.contacts.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="contacts.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1112,
                 '00-contracts/bpmn/com/etzhayyim/contacts/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.etzhayyim.com',
                 'did:web:contacts.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/contacts-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/contacts-connect-account-v1',
                 'did:web:contacts.etzhayyim.com',
                 'com.etzhayyim.apps.contacts.connectAccount',
                 'contacts_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.etzhayyim.com',
                 'did:web:contacts.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/contacts-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/contacts-oauth-callback-v1',
                 'did:web:contacts.etzhayyim.com',
                 'contacts_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_contacts_oauth_callback" '
                 'targetNamespace="https://etzhayyim.com/bpmn/contacts" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="contacts_oauth_callback" name="contacts '
                 'oauthCallback" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.contacts.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="contacts.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1107,
                 '00-contracts/bpmn/com/etzhayyim/contacts/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.etzhayyim.com',
                 'did:web:contacts.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/contacts-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/contacts-oauth-callback-v1',
                 'did:web:contacts.etzhayyim.com',
                 'com.etzhayyim.apps.contacts.oauthCallback',
                 'contacts_oauth_callback',
                 120000,
                 'vertex_gcontacts_oauth_token,vertex_gcontacts_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.etzhayyim.com',
                 'did:web:contacts.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/contacts-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/contacts-sync-from-google-v1',
                 'did:web:contacts.etzhayyim.com',
                 'contacts_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_contacts_sync_from_google" '
                 'targetNamespace="https://etzhayyim.com/bpmn/contacts" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="contacts_sync_from_google" '
                 'name="contacts syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.contacts.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="contacts.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1116,
                 '00-contracts/bpmn/com/etzhayyim/contacts/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.etzhayyim.com',
                 'did:web:contacts.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/contacts-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/contacts-sync-from-google-v1',
                 'did:web:contacts.etzhayyim.com',
                 'com.etzhayyim.apps.contacts.syncFromGoogle',
                 'contacts_sync_from_google',
                 120000,
                 'vertex_gcontacts_oauth_token,vertex_gcontacts_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.etzhayyim.com',
                 'did:web:contacts.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/contacts-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/contacts-cron-tick-v1',
                 'did:web:contacts.etzhayyim.com',
                 'contacts_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_contacts_cron_tick" '
                 'targetNamespace="https://etzhayyim.com/bpmn/contacts" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="contacts_cron_tick" name="contacts '
                 'cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.contacts.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/contacts/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.etzhayyim.com',
                 'did:web:contacts.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/contacts-cron-tick-v1']},
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
                 'targetNamespace="https://etzhayyim.com/bpmn/contacts" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="contacts_cron_tick" name="contacts '
                 'cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.contacts.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/contacts/cronTick.bpmn',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/contacts-cron-tick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/contacts-cronTick-v1',
                 'did:web:contacts.etzhayyim.com',
                 'com.etzhayyim.apps.contacts.cronTick',
                 'contacts_cron_tick',
                 120000,
                 'vertex_gcontacts_oauth_token,vertex_gcontacts_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:contacts.etzhayyim.com',
                 'did:web:contacts.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:contacts.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/contacts-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gcontacts_oauth_token,vertex_gcontacts_account',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/contacts-cronTick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/meet-connect-account-v1',
                 'did:web:meet.etzhayyim.com',
                 'meet_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_meet_connect_account" '
                 'targetNamespace="https://etzhayyim.com/bpmn/meet" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="meet_connect_account" name="meet '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.meet.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="meet.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1088,
                 '00-contracts/bpmn/com/etzhayyim/meet/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.etzhayyim.com',
                 'did:web:meet.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/meet-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/meet-connect-account-v1',
                 'did:web:meet.etzhayyim.com',
                 'com.etzhayyim.apps.meet.connectAccount',
                 'meet_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.etzhayyim.com',
                 'did:web:meet.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/meet-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/meet-oauth-callback-v1',
                 'did:web:meet.etzhayyim.com',
                 'meet_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_meet_oauth_callback" targetNamespace="https://etzhayyim.com/bpmn/meet" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="meet_oauth_callback" name="meet oauthCallback" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.meet.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="meet.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1083,
                 '00-contracts/bpmn/com/etzhayyim/meet/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.etzhayyim.com',
                 'did:web:meet.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/meet-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/meet-oauth-callback-v1',
                 'did:web:meet.etzhayyim.com',
                 'com.etzhayyim.apps.meet.oauthCallback',
                 'meet_oauth_callback',
                 120000,
                 'vertex_gmeet_oauth_token,vertex_gmeet_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.etzhayyim.com',
                 'did:web:meet.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/meet-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/meet-sync-from-google-v1',
                 'did:web:meet.etzhayyim.com',
                 'meet_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_meet_sync_from_google" '
                 'targetNamespace="https://etzhayyim.com/bpmn/meet" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="meet_sync_from_google" name="meet '
                 'syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.meet.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="meet.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1092,
                 '00-contracts/bpmn/com/etzhayyim/meet/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.etzhayyim.com',
                 'did:web:meet.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/meet-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/meet-sync-from-google-v1',
                 'did:web:meet.etzhayyim.com',
                 'com.etzhayyim.apps.meet.syncFromGoogle',
                 'meet_sync_from_google',
                 120000,
                 'vertex_gmeet_oauth_token,vertex_gmeet_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.etzhayyim.com',
                 'did:web:meet.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/meet-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/meet-cron-tick-v1',
                 'did:web:meet.etzhayyim.com',
                 'meet_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_meet_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/meet" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="meet_cron_tick" '
                 'name="meet cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.meet.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/meet/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.etzhayyim.com',
                 'did:web:meet.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/meet-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_meet_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/meet" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="meet_cron_tick" '
                 'name="meet cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.meet.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/meet/cronTick.bpmn',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/meet-cron-tick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/meet-cronTick-v1',
                 'did:web:meet.etzhayyim.com',
                 'com.etzhayyim.apps.meet.cronTick',
                 'meet_cron_tick',
                 120000,
                 'vertex_gmeet_oauth_token,vertex_gmeet_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:meet.etzhayyim.com',
                 'did:web:meet.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:meet.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/meet-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gmeet_oauth_token,vertex_gmeet_account',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/meet-cronTick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/docs-connect-account-v1',
                 'did:web:docs.etzhayyim.com',
                 'docs_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_docs_connect_account" '
                 'targetNamespace="https://etzhayyim.com/bpmn/docs" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="docs_connect_account" name="docs '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.docs.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="docs.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1088,
                 '00-contracts/bpmn/com/etzhayyim/docs/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.etzhayyim.com',
                 'did:web:docs.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/docs-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/docs-connect-account-v1',
                 'did:web:docs.etzhayyim.com',
                 'com.etzhayyim.apps.docs.connectAccount',
                 'docs_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.etzhayyim.com',
                 'did:web:docs.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/docs-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/docs-oauth-callback-v1',
                 'did:web:docs.etzhayyim.com',
                 'docs_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_docs_oauth_callback" targetNamespace="https://etzhayyim.com/bpmn/docs" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="docs_oauth_callback" name="docs oauthCallback" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.docs.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="docs.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1083,
                 '00-contracts/bpmn/com/etzhayyim/docs/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.etzhayyim.com',
                 'did:web:docs.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/docs-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/docs-oauth-callback-v1',
                 'did:web:docs.etzhayyim.com',
                 'com.etzhayyim.apps.docs.oauthCallback',
                 'docs_oauth_callback',
                 120000,
                 'vertex_gdocs_oauth_token,vertex_gdocs_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.etzhayyim.com',
                 'did:web:docs.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/docs-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/docs-sync-from-google-v1',
                 'did:web:docs.etzhayyim.com',
                 'docs_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_docs_sync_from_google" '
                 'targetNamespace="https://etzhayyim.com/bpmn/docs" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="docs_sync_from_google" name="docs '
                 'syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.docs.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="docs.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1092,
                 '00-contracts/bpmn/com/etzhayyim/docs/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.etzhayyim.com',
                 'did:web:docs.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/docs-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/docs-sync-from-google-v1',
                 'did:web:docs.etzhayyim.com',
                 'com.etzhayyim.apps.docs.syncFromGoogle',
                 'docs_sync_from_google',
                 120000,
                 'vertex_gdocs_oauth_token,vertex_gdocs_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.etzhayyim.com',
                 'did:web:docs.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/docs-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/docs-cron-tick-v1',
                 'did:web:docs.etzhayyim.com',
                 'docs_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_docs_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/docs" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="docs_cron_tick" '
                 'name="docs cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.docs.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/docs/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.etzhayyim.com',
                 'did:web:docs.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/docs-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_docs_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/docs" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="docs_cron_tick" '
                 'name="docs cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.docs.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/docs/cronTick.bpmn',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/docs-cron-tick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/docs-cronTick-v1',
                 'did:web:docs.etzhayyim.com',
                 'com.etzhayyim.apps.docs.cronTick',
                 'docs_cron_tick',
                 120000,
                 'vertex_gdocs_oauth_token,vertex_gdocs_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:docs.etzhayyim.com',
                 'did:web:docs.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:docs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/docs-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gdocs_oauth_token,vertex_gdocs_account',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/docs-cronTick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/slides-connect-account-v1',
                 'did:web:slides.etzhayyim.com',
                 'slides_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_slides_connect_account" '
                 'targetNamespace="https://etzhayyim.com/bpmn/slides" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="slides_connect_account" name="slides '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.slides.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="slides.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1100,
                 '00-contracts/bpmn/com/etzhayyim/slides/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.etzhayyim.com',
                 'did:web:slides.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/slides-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/slides-connect-account-v1',
                 'did:web:slides.etzhayyim.com',
                 'com.etzhayyim.apps.slides.connectAccount',
                 'slides_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.etzhayyim.com',
                 'did:web:slides.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/slides-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/slides-oauth-callback-v1',
                 'did:web:slides.etzhayyim.com',
                 'slides_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_slides_oauth_callback" '
                 'targetNamespace="https://etzhayyim.com/bpmn/slides" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="slides_oauth_callback" name="slides '
                 'oauthCallback" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.slides.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="slides.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1095,
                 '00-contracts/bpmn/com/etzhayyim/slides/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.etzhayyim.com',
                 'did:web:slides.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/slides-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/slides-oauth-callback-v1',
                 'did:web:slides.etzhayyim.com',
                 'com.etzhayyim.apps.slides.oauthCallback',
                 'slides_oauth_callback',
                 120000,
                 'vertex_gslides_oauth_token,vertex_gslides_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.etzhayyim.com',
                 'did:web:slides.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/slides-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/slides-sync-from-google-v1',
                 'did:web:slides.etzhayyim.com',
                 'slides_sync_from_google',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_slides_sync_from_google" '
                 'targetNamespace="https://etzhayyim.com/bpmn/slides" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="slides_sync_from_google" name="slides '
                 'syncFromGoogle" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.slides.syncFromGoogle", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync from '
                 'Google"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="slides.syncFromGoogle"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1104,
                 '00-contracts/bpmn/com/etzhayyim/slides/syncFromGoogle.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.etzhayyim.com',
                 'did:web:slides.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/slides-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/slides-sync-from-google-v1',
                 'did:web:slides.etzhayyim.com',
                 'com.etzhayyim.apps.slides.syncFromGoogle',
                 'slides_sync_from_google',
                 120000,
                 'vertex_gslides_oauth_token,vertex_gslides_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.etzhayyim.com',
                 'did:web:slides.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/slides-sync-from-google-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/slides-cron-tick-v1',
                 'did:web:slides.etzhayyim.com',
                 'slides_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_slides_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/slides" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="slides_cron_tick" name="slides cronTick" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.slides.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/slides/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.etzhayyim.com',
                 'did:web:slides.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/slides-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_slides_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/slides" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="slides_cron_tick" name="slides cronTick" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.slides.cronTick", "version": 1, "resultTimeoutMs": 120000 '
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
                 '00-contracts/bpmn/com/etzhayyim/slides/cronTick.bpmn',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/slides-cron-tick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/slides-cronTick-v1',
                 'did:web:slides.etzhayyim.com',
                 'com.etzhayyim.apps.slides.cronTick',
                 'slides_cron_tick',
                 120000,
                 'vertex_gslides_oauth_token,vertex_gslides_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:slides.etzhayyim.com',
                 'did:web:slides.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:slides.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/slides-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [120000,
                 'vertex_gslides_oauth_token,vertex_gslides_account',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/slides-cronTick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-connect-account-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_connect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_connect_account" '
                 'targetNamespace="https://etzhayyim.com/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_connect_account" name="gmail '
                 'connectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.gmail.connectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="connect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.connectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1094,
                 '00-contracts/bpmn/com/etzhayyim/gmail/connectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-connect-account-v1',
                 'did:web:gmail.etzhayyim.com',
                 'com.etzhayyim.apps.gmail.connectAccount',
                 'gmail_connect_account',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-connect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-oauth-callback-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_oauth_callback',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_oauth_callback" '
                 'targetNamespace="https://etzhayyim.com/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_oauth_callback" name="gmail '
                 'oauthCallback" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.gmail.oauthCallback", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="oauth '
                 'callback"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.oauthCallback"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/com/etzhayyim/gmail/oauthCallback.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-oauth-callback-v1',
                 'did:web:gmail.etzhayyim.com',
                 'com.etzhayyim.apps.gmail.oauthCallback',
                 'gmail_oauth_callback',
                 120000,
                 'vertex_gmail_oauth_token,vertex_gmail_account',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-oauth-callback-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-disconnect-account-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_disconnect_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_disconnect_account" '
                 'targetNamespace="https://etzhayyim.com/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_disconnect_account" name="gmail '
                 'disconnectAccount" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.gmail.disconnectAccount", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="disconnect '
                 'account"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.disconnectAccount"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1112,
                 '00-contracts/bpmn/com/etzhayyim/gmail/disconnectAccount.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-disconnect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-disconnect-account-v1',
                 'did:web:gmail.etzhayyim.com',
                 'com.etzhayyim.apps.gmail.disconnectAccount',
                 'gmail_disconnect_account',
                 30000,
                 'vertex_gmail_oauth_token,vertex_gmail_account_binding',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-disconnect-account-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-sync-inbox-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_sync_inbox',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_sync_inbox" targetNamespace="https://etzhayyim.com/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="gmail_sync_inbox" name="gmail syncInbox" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.gmail.syncInbox", "version": 1, "resultTimeoutMs": 180000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync inbox"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.syncInbox"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1065,
                 '00-contracts/bpmn/com/etzhayyim/gmail/syncInbox.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-sync-inbox-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-sync-inbox-v1',
                 'did:web:gmail.etzhayyim.com',
                 'com.etzhayyim.apps.gmail.syncInbox',
                 'gmail_sync_inbox',
                 180000,
                 'vertex_gmail_oauth_token,vertex_gmail_email,vertex_gmail_sync_job,vertex_gmail_phishing_alert',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-sync-inbox-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-send-email-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_send_email',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_send_email" targetNamespace="https://etzhayyim.com/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="gmail_send_email" name="gmail sendEmail" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.gmail.sendEmail", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="send email"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.sendEmail"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1065,
                 '00-contracts/bpmn/com/etzhayyim/gmail/sendEmail.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-send-email-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-send-email-v1',
                 'did:web:gmail.etzhayyim.com',
                 'com.etzhayyim.apps.gmail.sendEmail',
                 'gmail_send_email',
                 120000,
                 'vertex_gmail_oauth_token,vertex_gmail_outbound_email',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-send-email-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-reply-to-thread-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_reply_to_thread',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_reply_to_thread" '
                 'targetNamespace="https://etzhayyim.com/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_reply_to_thread" name="gmail '
                 'replyToThread" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.gmail.replyToThread", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="reply to '
                 'thread"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.replyToThread"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1092,
                 '00-contracts/bpmn/com/etzhayyim/gmail/replyToThread.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-reply-to-thread-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-reply-to-thread-v1',
                 'did:web:gmail.etzhayyim.com',
                 'com.etzhayyim.apps.gmail.replyToThread',
                 'gmail_reply_to_thread',
                 120000,
                 'vertex_gmail_oauth_token,vertex_gmail_outbound_email',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-reply-to-thread-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-list-accounts-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_list_accounts',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_list_accounts" '
                 'targetNamespace="https://etzhayyim.com/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_list_accounts" name="gmail '
                 'listAccounts" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.gmail.listAccounts", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="list accounts"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.listAccounts"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1082,
                 '00-contracts/bpmn/com/etzhayyim/gmail/listAccounts.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-list-accounts-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-list-accounts-v1',
                 'did:web:gmail.etzhayyim.com',
                 'com.etzhayyim.apps.gmail.listAccounts',
                 'gmail_list_accounts',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-list-accounts-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-list-threads-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_list_threads',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_list_threads" targetNamespace="https://etzhayyim.com/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="gmail_list_threads" name="gmail listThreads" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.gmail.listThreads", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="list threads"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.listThreads"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1076,
                 '00-contracts/bpmn/com/etzhayyim/gmail/listThreads.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-list-threads-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-list-threads-v1',
                 'did:web:gmail.etzhayyim.com',
                 'com.etzhayyim.apps.gmail.listThreads',
                 'gmail_list_threads',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-list-threads-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-search-emails-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_search_emails',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_search_emails" '
                 'targetNamespace="https://etzhayyim.com/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_search_emails" name="gmail '
                 'searchEmails" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.gmail.searchEmails", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="search emails"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.searchEmails"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1082,
                 '00-contracts/bpmn/com/etzhayyim/gmail/searchEmails.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-search-emails-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-search-emails-v1',
                 'did:web:gmail.etzhayyim.com',
                 'com.etzhayyim.apps.gmail.searchEmails',
                 'gmail_search_emails',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-search-emails-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-get-thread-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_get_thread',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_gmail_get_thread" targetNamespace="https://etzhayyim.com/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="gmail_get_thread" name="gmail getThread" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.gmail.getThread", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="get thread"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.getThread"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1065,
                 '00-contracts/bpmn/com/etzhayyim/gmail/getThread.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-get-thread-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-get-thread-v1',
                 'did:web:gmail.etzhayyim.com',
                 'com.etzhayyim.apps.gmail.getThread',
                 'gmail_get_thread',
                 120000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-get-thread-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-triage-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_triage',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_gmail_triage" '
                 'targetNamespace="https://etzhayyim.com/bpmn/gmail" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="gmail_triage" name="gmail triage" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.gmail.triage", '
                 '"version": 1, "resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="triage"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gmail.triage"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1043,
                 '00-contracts/bpmn/com/etzhayyim/gmail/triage.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-triage-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-triage-v1',
                 'did:web:gmail.etzhayyim.com',
                 'com.etzhayyim.apps.gmail.triage',
                 'gmail_triage',
                 30000,
                 '',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-triage-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-cron-tick-v1',
                 'did:web:gmail.etzhayyim.com',
                 'gmail_cron_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_gmail_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="gmail_cron_tick" '
                 'name="gmail cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.gmail.cronTick", "version": 1, "resultTimeoutMs": 180000 '
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
                 '00-contracts/bpmn/com/etzhayyim/gmail/cronTick.bpmn',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-cron-tick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_process_def\n'
         '        SET xml = $1, xml_byte_size = CAST($2 AS integer), source_path = $3\n'
         '        WHERE vertex_id = $4\n'
         '      ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_gmail_cron_tick" targetNamespace="https://etzhayyim.com/bpmn/gmail" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process id="gmail_cron_tick" '
                 'name="gmail cronTick" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.gmail.cronTick", "version": 1, "resultTimeoutMs": 180000 '
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
                 '00-contracts/bpmn/com/etzhayyim/gmail/cronTick.bpmn',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-cron-tick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-cronTick-v1',
                 'did:web:gmail.etzhayyim.com',
                 'com.etzhayyim.apps.gmail.cronTick',
                 'gmail_cron_tick',
                 180000,
                 'vertex_gmail_oauth_token,vertex_gmail_email,vertex_gmail_sync_job,vertex_gmail_phishing_alert',
                 '2026-04-29T21:40:00+09:00',
                 'did:web:gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'sys.bpmn.seed.gworkspace_lite',
                 'did:web:gmail.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-cronTick-v1']},
 {'sql': '\n'
         '        UPDATE vertex_bpmn_lexicon_binding\n'
         '        SET result_timeout_ms = CAST($1 AS integer),\n'
         '            write_table_allowlist = $2\n'
         '        WHERE vertex_id = $3\n'
         '      ',
  'parameters': [180000,
                 'vertex_gmail_oauth_token,vertex_gmail_email,vertex_gmail_sync_job,vertex_gmail_phishing_alert',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-cronTick-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/tasks-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/tasks-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/tasks-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/tasks-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/tasks-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/tasks-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sheets-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sheets-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sheets-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sheets-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sheets-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sheets-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/drive-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/drive-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/drive-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/drive-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/drive-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/drive-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/contacts-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/contacts-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/contacts-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/contacts-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/contacts-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/contacts-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/meet-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/meet-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/meet-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/meet-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/meet-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/meet-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/docs-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/docs-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/docs-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/docs-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/docs-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/docs-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/slides-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/slides-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/slides-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/slides-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/slides-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/slides-sync-from-google-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-connect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-oauth-callback-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-disconnect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-disconnect-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-sync-inbox-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-sync-inbox-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-send-email-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-send-email-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-reply-to-thread-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-reply-to-thread-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-list-accounts-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-list-accounts-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-list-threads-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-list-threads-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-search-emails-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-search-emails-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-get-thread-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-get-thread-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gmail-triage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gmail-triage-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
