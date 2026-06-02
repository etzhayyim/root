"""Captured from Kysely migration 20260429215100_seed_outlook_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429215100_seed_outlook_bpmn_actors"
down_revision = 'r_20260429215000_outlook_zeebe_support'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-get-oauth-config-v1',
                 'did:web:outlook.etzhayyim.com',
                 'outlook_get_oauth_config',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_outlook_get_oauth_config" '
                 'targetNamespace="https://etzhayyim.com/bpmn/outlook" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="outlook_get_oauth_config" name="outlook '
                 'getOauthConfig" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.outlook.getOauthConfig", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="get oauth '
                 'config"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="outlook.getOauthConfig"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1109,
                 '00-contracts/bpmn/com/etzhayyim/outlook/getOauthConfig.bpmn',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-get-oauth-config-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-getOauthConfig-v1',
                 'did:web:outlook.etzhayyim.com',
                 'com.etzhayyim.apps.outlook.getOauthConfig',
                 'outlook_get_oauth_config',
                 30000,
                 '',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-getOauthConfig-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-get-auth-status-v1',
                 'did:web:outlook.etzhayyim.com',
                 'outlook_get_auth_status',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_outlook_get_auth_status" '
                 'targetNamespace="https://etzhayyim.com/bpmn/outlook" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="outlook_get_auth_status" name="outlook '
                 'getAuthStatus" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.outlook.getAuthStatus", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="get auth '
                 'status"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="outlook.getAuthStatus"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1103,
                 '00-contracts/bpmn/com/etzhayyim/outlook/getAuthStatus.bpmn',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-get-auth-status-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-getAuthStatus-v1',
                 'did:web:outlook.etzhayyim.com',
                 'com.etzhayyim.apps.outlook.getAuthStatus',
                 'outlook_get_auth_status',
                 30000,
                 '',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-getAuthStatus-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-start-auth-v1',
                 'did:web:outlook.etzhayyim.com',
                 'outlook_start_auth',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_outlook_start_auth" '
                 'targetNamespace="https://etzhayyim.com/bpmn/outlook" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="outlook_start_auth" name="outlook '
                 'startAuth" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.outlook.startAuth", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="start auth"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="outlook.startAuth"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1076,
                 '00-contracts/bpmn/com/etzhayyim/outlook/startAuth.bpmn',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-start-auth-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-startAuth-v1',
                 'did:web:outlook.etzhayyim.com',
                 'com.etzhayyim.apps.outlook.startAuth',
                 'outlook_start_auth',
                 30000,
                 'vertex_outlook_pending_oauth',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-startAuth-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-exchange-code-v1',
                 'did:web:outlook.etzhayyim.com',
                 'outlook_exchange_code',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_outlook_exchange_code" '
                 'targetNamespace="https://etzhayyim.com/bpmn/outlook" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="outlook_exchange_code" name="outlook '
                 'exchangeCode" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.outlook.exchangeCode", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="exchange code"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="outlook.exchangeCode"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1095,
                 '00-contracts/bpmn/com/etzhayyim/outlook/exchangeCode.bpmn',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-exchange-code-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-exchangeCode-v1',
                 'did:web:outlook.etzhayyim.com',
                 'com.etzhayyim.apps.outlook.exchangeCode',
                 'outlook_exchange_code',
                 120000,
                 'vertex_outlook_pending_oauth,vertex_outlook_oauth_connection,vertex_outlook_sync_job',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-exchangeCode-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-get-connection-v1',
                 'did:web:outlook.etzhayyim.com',
                 'outlook_get_connection',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_outlook_get_connection" '
                 'targetNamespace="https://etzhayyim.com/bpmn/outlook" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="outlook_get_connection" name="outlook '
                 'getConnection" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.outlook.getConnection", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="get '
                 'connection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="outlook.getConnection"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1100,
                 '00-contracts/bpmn/com/etzhayyim/outlook/getConnection.bpmn',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-get-connection-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-getConnection-v1',
                 'did:web:outlook.etzhayyim.com',
                 'com.etzhayyim.apps.outlook.getConnection',
                 'outlook_get_connection',
                 30000,
                 'vertex_outlook_oauth_connection',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-getConnection-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-sync-mailbox-v1',
                 'did:web:outlook.etzhayyim.com',
                 'outlook_sync_mailbox',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_outlook_sync_mailbox" '
                 'targetNamespace="https://etzhayyim.com/bpmn/outlook" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="outlook_sync_mailbox" name="outlook '
                 'syncMailbox" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.outlook.syncMailbox", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="sync mailbox"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="outlook.syncMailbox"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/com/etzhayyim/outlook/syncMailbox.bpmn',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-sync-mailbox-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-syncMailbox-v1',
                 'did:web:outlook.etzhayyim.com',
                 'com.etzhayyim.apps.outlook.syncMailbox',
                 'outlook_sync_mailbox',
                 120000,
                 'vertex_outlook_oauth_connection,vertex_outlook_sync_job',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-syncMailbox-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-disconnect-v1',
                 'did:web:outlook.etzhayyim.com',
                 'outlook_disconnect',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_outlook_disconnect" '
                 'targetNamespace="https://etzhayyim.com/bpmn/outlook" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="outlook_disconnect" name="outlook '
                 'disconnect" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.outlook.disconnect", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="disconnect"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="outlook.disconnect"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1079,
                 '00-contracts/bpmn/com/etzhayyim/outlook/disconnect.bpmn',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-disconnect-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-disconnect-v1',
                 'did:web:outlook.etzhayyim.com',
                 'com.etzhayyim.apps.outlook.disconnect',
                 'outlook_disconnect',
                 30000,
                 'vertex_outlook_pending_oauth,vertex_outlook_oauth_connection',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-disconnect-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-card-home-v1',
                 'did:web:outlook.etzhayyim.com',
                 'outlook_card_home',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_outlook_card_home" '
                 'targetNamespace="https://etzhayyim.com/bpmn/outlook" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="outlook_card_home" name="outlook '
                 'cardHome" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.outlook.cardHome", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="card home"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="outlook.cardHome"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1070,
                 '00-contracts/bpmn/com/etzhayyim/outlook/cardHome.bpmn',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-card-home-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-cardHome-v1',
                 'did:web:outlook.etzhayyim.com',
                 'com.etzhayyim.apps.outlook.cardHome',
                 'outlook_card_home',
                 30000,
                 '',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-cardHome-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-card-compose-v1',
                 'did:web:outlook.etzhayyim.com',
                 'outlook_card_compose',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_outlook_card_compose" '
                 'targetNamespace="https://etzhayyim.com/bpmn/outlook" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="outlook_card_compose" name="outlook '
                 'cardCompose" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.outlook.cardCompose", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="card compose"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="outlook.cardCompose"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1088,
                 '00-contracts/bpmn/com/etzhayyim/outlook/cardCompose.bpmn',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-card-compose-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-cardCompose-v1',
                 'did:web:outlook.etzhayyim.com',
                 'com.etzhayyim.apps.outlook.cardCompose',
                 'outlook_card_compose',
                 30000,
                 '',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-cardCompose-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-card-action-v1',
                 'did:web:outlook.etzhayyim.com',
                 'outlook_card_action',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_outlook_card_action" '
                 'targetNamespace="https://etzhayyim.com/bpmn/outlook" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="outlook_card_action" name="outlook '
                 'cardAction" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.outlook.cardAction", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="card action"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="outlook.cardAction"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1082,
                 '00-contracts/bpmn/com/etzhayyim/outlook/cardAction.bpmn',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-card-action-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-cardAction-v1',
                 'did:web:outlook.etzhayyim.com',
                 'com.etzhayyim.apps.outlook.cardAction',
                 'outlook_card_action',
                 30000,
                 '',
                 '2026-04-29T21:51:00+09:00',
                 'did:web:outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'sys.bpmn.seed.outlook',
                 'did:web:outlook.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-cardAction-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-getOauthConfig-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-get-oauth-config-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-getAuthStatus-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-get-auth-status-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-startAuth-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-start-auth-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-exchangeCode-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-exchange-code-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-getConnection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-get-connection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-syncMailbox-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-sync-mailbox-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-disconnect-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-disconnect-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-cardHome-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-card-home-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-cardCompose-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-card-compose-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/outlook-cardAction-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/outlook-card-action-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
