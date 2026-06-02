"""Captured from Kysely migration 20260429217000_seed_mailer_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429217000_seed_mailer_bpmn_actors"
down_revision = 'r_20260429216100_seed_credits_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-health-v1',
                 'did:web:mailer.etzhayyim.com',
                 'mailer_health',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_mailer_health" '
                 'targetNamespace="https://etzhayyim.com/bpmn/mailer" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="mailer_health" name="mailer health" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.mailer.health", '
                 '"version": 1, "resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="health"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="mailer.health"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1049,
                 '00-contracts/bpmn/com/etzhayyim/mailer/health.bpmn',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-health-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-health-v1',
                 'did:web:mailer.etzhayyim.com',
                 'com.etzhayyim.apps.mailer.health',
                 'mailer_health',
                 30000,
                 '',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-health-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-list-emails-v1',
                 'did:web:mailer.etzhayyim.com',
                 'mailer_list_emails',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_mailer_list_emails" '
                 'targetNamespace="https://etzhayyim.com/bpmn/mailer" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="mailer_list_emails" name="mailer '
                 'listEmails" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.mailer.listEmails", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="list emails"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="mailer.listEmails"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1076,
                 '00-contracts/bpmn/com/etzhayyim/mailer/listEmails.bpmn',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-list-emails-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-listEmails-v1',
                 'did:web:mailer.etzhayyim.com',
                 'com.etzhayyim.apps.mailer.listEmails',
                 'mailer_list_emails',
                 30000,
                 '',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-listEmails-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-list-bindings-v1',
                 'did:web:mailer.etzhayyim.com',
                 'mailer_list_bindings',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_mailer_list_bindings" '
                 'targetNamespace="https://etzhayyim.com/bpmn/mailer" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="mailer_list_bindings" name="mailer '
                 'listBindings" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.mailer.listBindings", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="list bindings"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="mailer.listBindings"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1088,
                 '00-contracts/bpmn/com/etzhayyim/mailer/listBindings.bpmn',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-list-bindings-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-listBindings-v1',
                 'did:web:mailer.etzhayyim.com',
                 'com.etzhayyim.apps.mailer.listBindings',
                 'mailer_list_bindings',
                 30000,
                 '',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-listBindings-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-stats-v1',
                 'did:web:mailer.etzhayyim.com',
                 'mailer_stats',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" id="Definitions_mailer_stats" '
                 'targetNamespace="https://etzhayyim.com/bpmn/mailer" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="mailer_stats" name="mailer stats" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": "com.etzhayyim.apps.mailer.stats", '
                 '"version": 1, "resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="stats"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="mailer.stats"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1043,
                 '00-contracts/bpmn/com/etzhayyim/mailer/stats.bpmn',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-stats-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-stats-v1',
                 'did:web:mailer.etzhayyim.com',
                 'com.etzhayyim.apps.mailer.stats',
                 'mailer_stats',
                 30000,
                 '',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-stats-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-send-email-v1',
                 'did:web:mailer.etzhayyim.com',
                 'mailer_send_email',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_mailer_send_email" targetNamespace="https://etzhayyim.com/bpmn/mailer" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="mailer_send_email" name="mailer sendEmail" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.mailer.sendEmail", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="send email"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="mailer.sendEmail"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1071,
                 '00-contracts/bpmn/com/etzhayyim/mailer/sendEmail.bpmn',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-send-email-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-sendEmail-v1',
                 'did:web:mailer.etzhayyim.com',
                 'com.etzhayyim.apps.mailer.sendEmail',
                 'mailer_send_email',
                 120000,
                 'vertex_mailer_outbound_email',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-sendEmail-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-provision-mailbox-v1',
                 'did:web:mailer.etzhayyim.com',
                 'mailer_provision_mailbox',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_mailer_provision_mailbox" '
                 'targetNamespace="https://etzhayyim.com/bpmn/mailer" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="mailer_provision_mailbox" name="mailer '
                 'provisionMailbox" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.mailer.provisionMailbox", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="provision '
                 'mailbox"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="mailer.provisionMailbox"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1113,
                 '00-contracts/bpmn/com/etzhayyim/mailer/provisionMailbox.bpmn',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-provision-mailbox-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-provisionMailbox-v1',
                 'did:web:mailer.etzhayyim.com',
                 'com.etzhayyim.apps.mailer.provisionMailbox',
                 'mailer_provision_mailbox',
                 120000,
                 'vertex_mailer_email_binding',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-provisionMailbox-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-handle-commit-v1',
                 'did:web:mailer.etzhayyim.com',
                 'mailer_handle_commit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_mailer_handle_commit" '
                 'targetNamespace="https://etzhayyim.com/bpmn/mailer" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="mailer_handle_commit" name="mailer '
                 'handleCommit" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.mailer.handleCommit", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="handle commit"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="mailer.handleCommit"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1088,
                 '00-contracts/bpmn/com/etzhayyim/mailer/handleCommit.bpmn',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-handle-commit-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-handleCommit-v1',
                 'did:web:mailer.etzhayyim.com',
                 'com.etzhayyim.apps.mailer.handleCommit',
                 'mailer_handle_commit',
                 30000,
                 '',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-handleCommit-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-heartbeat-v1',
                 'did:web:mailer.etzhayyim.com',
                 'mailer_heartbeat',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_mailer_heartbeat" targetNamespace="https://etzhayyim.com/bpmn/mailer" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="mailer_heartbeat" name="mailer heartbeat" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.mailer.heartbeat", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="heartbeat"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="mailer.heartbeat"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1067,
                 '00-contracts/bpmn/com/etzhayyim/mailer/heartbeat.bpmn',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-heartbeat-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-heartbeat-v1',
                 'did:web:mailer.etzhayyim.com',
                 'com.etzhayyim.apps.mailer.heartbeat',
                 'mailer_heartbeat',
                 30000,
                 '',
                 '2026-04-29T22:10:00+09:00',
                 'did:web:mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'sys.bpmn.seed.mailer',
                 'did:web:mailer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-heartbeat-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-health-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-health-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-listEmails-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-list-emails-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-listBindings-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-list-bindings-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-sendEmail-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-send-email-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-provisionMailbox-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-provision-mailbox-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-handleCommit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-handle-commit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/mailer-heartbeat-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/mailer-heartbeat-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
