"""Captured from Kysely migration 20260429203000_seed_briefing_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429203000_seed_briefing_bpmn_actors"
down_revision = 'r_20260429202000_seed_arb_leaf_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-create-agenda-v1',
                 'did:web:briefing.etzhayyim.com',
                 'briefing_create_agenda',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_briefing_create_agenda" '
                 'targetNamespace="https://etzhayyim.com/bpmn/briefing" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="briefing_create_agenda" name="briefing '
                 'createAgenda" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.briefing.createAgenda", "version": 1, "resultTimeoutMs": 60000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="create agenda"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="briefing.createAgenda"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1100,
                 '00-contracts/bpmn/com/etzhayyim/briefing/createAgenda.bpmn',
                 '2026-04-29T20:30:00+09:00',
                 'did:web:briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'sys.bpmn.seed.briefing',
                 'did:web:briefing.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-create-agenda-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-create-agenda-v1',
                 'did:web:briefing.etzhayyim.com',
                 'com.etzhayyim.apps.briefing.createAgenda',
                 'briefing_create_agenda',
                 60000,
                 'pds:com.etzhayyim.apps.briefing.briefingAgenda',
                 '2026-04-29T20:30:00+09:00',
                 'did:web:briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'sys.bpmn.seed.briefing',
                 'did:web:briefing.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-create-agenda-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['pds:com.etzhayyim.apps.briefing.briefingAgenda',
                 'briefing_create_agenda',
                 'com.etzhayyim.apps.briefing.createAgenda',
                 'pds:com.etzhayyim.apps.briefing.briefingAgenda']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-save-transcript-v1',
                 'did:web:briefing.etzhayyim.com',
                 'briefing_save_transcript',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_briefing_save_transcript" '
                 'targetNamespace="https://etzhayyim.com/bpmn/briefing" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="briefing_save_transcript" name="briefing '
                 'saveTranscript" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.briefing.saveTranscript", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="save '
                 'transcript"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="briefing.saveTranscript"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1113,
                 '00-contracts/bpmn/com/etzhayyim/briefing/saveTranscript.bpmn',
                 '2026-04-29T20:30:00+09:00',
                 'did:web:briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'sys.bpmn.seed.briefing',
                 'did:web:briefing.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-save-transcript-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-save-transcript-v1',
                 'did:web:briefing.etzhayyim.com',
                 'com.etzhayyim.apps.briefing.saveTranscript',
                 'briefing_save_transcript',
                 120000,
                 'pds:com.etzhayyim.apps.briefing.briefingTranscript',
                 '2026-04-29T20:30:00+09:00',
                 'did:web:briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'sys.bpmn.seed.briefing',
                 'did:web:briefing.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-save-transcript-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['pds:com.etzhayyim.apps.briefing.briefingTranscript',
                 'briefing_save_transcript',
                 'com.etzhayyim.apps.briefing.saveTranscript',
                 'pds:com.etzhayyim.apps.briefing.briefingTranscript']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-extract-action-items-v1',
                 'did:web:briefing.etzhayyim.com',
                 'briefing_extract_action_items',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_briefing_extract_action_items" '
                 'targetNamespace="https://etzhayyim.com/bpmn/briefing" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="briefing_extract_action_items" '
                 'name="briefing extractActionItems" isExecutable="true"><bpmn:documentation>{ '
                 '"nsid": "com.etzhayyim.apps.briefing.extractActionItems", "version": 1, '
                 '"resultTimeoutMs": 120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="extract action '
                 'items"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="briefing.extractActionItems"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1140,
                 '00-contracts/bpmn/com/etzhayyim/briefing/extractActionItems.bpmn',
                 '2026-04-29T20:30:00+09:00',
                 'did:web:briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'sys.bpmn.seed.briefing',
                 'did:web:briefing.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-extract-action-items-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-extract-action-items-v1',
                 'did:web:briefing.etzhayyim.com',
                 'com.etzhayyim.apps.briefing.extractActionItems',
                 'briefing_extract_action_items',
                 120000,
                 'pds:com.etzhayyim.apps.briefing.briefingActionItem',
                 '2026-04-29T20:30:00+09:00',
                 'did:web:briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'sys.bpmn.seed.briefing',
                 'did:web:briefing.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-extract-action-items-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['pds:com.etzhayyim.apps.briefing.briefingActionItem',
                 'briefing_extract_action_items',
                 'com.etzhayyim.apps.briefing.extractActionItems',
                 'pds:com.etzhayyim.apps.briefing.briefingActionItem']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-generate-summary-v1',
                 'did:web:briefing.etzhayyim.com',
                 'briefing_generate_summary',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_briefing_generate_summary" '
                 'targetNamespace="https://etzhayyim.com/bpmn/briefing" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="briefing_generate_summary" '
                 'name="briefing generateSummary" isExecutable="true"><bpmn:documentation>{ '
                 '"nsid": "com.etzhayyim.apps.briefing.generateSummary", "version": 1, '
                 '"resultTimeoutMs": 120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="generate '
                 'summary"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="briefing.generateSummary"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1119,
                 '00-contracts/bpmn/com/etzhayyim/briefing/generateSummary.bpmn',
                 '2026-04-29T20:30:00+09:00',
                 'did:web:briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'sys.bpmn.seed.briefing',
                 'did:web:briefing.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-generate-summary-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-generate-summary-v1',
                 'did:web:briefing.etzhayyim.com',
                 'com.etzhayyim.apps.briefing.generateSummary',
                 'briefing_generate_summary',
                 120000,
                 'pds:com.etzhayyim.apps.briefing.briefingSummary',
                 '2026-04-29T20:30:00+09:00',
                 'did:web:briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'sys.bpmn.seed.briefing',
                 'did:web:briefing.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-generate-summary-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['pds:com.etzhayyim.apps.briefing.briefingSummary',
                 'briefing_generate_summary',
                 'com.etzhayyim.apps.briefing.generateSummary',
                 'pds:com.etzhayyim.apps.briefing.briefingSummary']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-record-speaker-turn-v1',
                 'did:web:briefing.etzhayyim.com',
                 'briefing_record_speaker_turn',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_briefing_record_speaker_turn" '
                 'targetNamespace="https://etzhayyim.com/bpmn/briefing" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="briefing_record_speaker_turn" '
                 'name="briefing recordSpeakerTurn" isExecutable="true"><bpmn:documentation>{ '
                 '"nsid": "com.etzhayyim.apps.briefing.recordSpeakerTurn", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="record speaker '
                 'turn"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="briefing.recordSpeakerTurn"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1133,
                 '00-contracts/bpmn/com/etzhayyim/briefing/recordSpeakerTurn.bpmn',
                 '2026-04-29T20:30:00+09:00',
                 'did:web:briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'sys.bpmn.seed.briefing',
                 'did:web:briefing.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-record-speaker-turn-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-record-speaker-turn-v1',
                 'did:web:briefing.etzhayyim.com',
                 'com.etzhayyim.apps.briefing.recordSpeakerTurn',
                 'briefing_record_speaker_turn',
                 30000,
                 'pds:com.etzhayyim.apps.briefing.briefingSpeakerTurn',
                 '2026-04-29T20:30:00+09:00',
                 'did:web:briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'sys.bpmn.seed.briefing',
                 'did:web:briefing.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-record-speaker-turn-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['pds:com.etzhayyim.apps.briefing.briefingSpeakerTurn',
                 'briefing_record_speaker_turn',
                 'com.etzhayyim.apps.briefing.recordSpeakerTurn',
                 'pds:com.etzhayyim.apps.briefing.briefingSpeakerTurn']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-record-decision-v1',
                 'did:web:briefing.etzhayyim.com',
                 'briefing_record_decision',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_briefing_record_decision" '
                 'targetNamespace="https://etzhayyim.com/bpmn/briefing" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="briefing_record_decision" name="briefing '
                 'recordDecision" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.briefing.recordDecision", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="record '
                 'decision"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="briefing.recordDecision"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1112,
                 '00-contracts/bpmn/com/etzhayyim/briefing/recordDecision.bpmn',
                 '2026-04-29T20:30:00+09:00',
                 'did:web:briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'sys.bpmn.seed.briefing',
                 'did:web:briefing.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-record-decision-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-record-decision-v1',
                 'did:web:briefing.etzhayyim.com',
                 'com.etzhayyim.apps.briefing.recordDecision',
                 'briefing_record_decision',
                 30000,
                 'pds:com.etzhayyim.apps.briefing.briefingDecision',
                 '2026-04-29T20:30:00+09:00',
                 'did:web:briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'sys.bpmn.seed.briefing',
                 'did:web:briefing.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-record-decision-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['pds:com.etzhayyim.apps.briefing.briefingDecision',
                 'briefing_record_decision',
                 'com.etzhayyim.apps.briefing.recordDecision',
                 'pds:com.etzhayyim.apps.briefing.briefingDecision']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-create-agenda-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-create-agenda-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-save-transcript-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-save-transcript-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-extract-action-items-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-extract-action-items-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-generate-summary-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-generate-summary-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-record-speaker-turn-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-record-speaker-turn-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/briefing-record-decision-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/briefing-record-decision-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
