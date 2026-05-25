"""Captured from Kysely migration 20260430215300_seed_baminiku_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430215300_seed_baminiku_bpmn_actors"
down_revision = 'r_20260430215200_vertex_baminiku_record'
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
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-set-agent-profile-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'baminiku_set_agent_profile',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_baminiku_set_agent_profile" '
                 'targetNamespace="https://etzhayyim.com/bpmn/baminiku"><bpmn:process '
                 'id="baminiku_set_agent_profile" name="baminiku setAgentProfile" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.baminiku.setAgentProfile", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="set agent profile"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="baminiku.setAgentProfile"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1039,
                 '00-contracts/bpmn/ai/gftd/baminiku/setAgentProfile.bpmn',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-set-agent-profile-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-set-agent-profile-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'app.etzhayyim.apps.baminiku.setAgentProfile',
                 'baminiku_set_agent_profile',
                 'vertex_baminiku_agent_profile,vertex_baminiku_stream,vertex_baminiku_stage_patch,vertex_baminiku_chat,vertex_baminiku_tip,vertex_baminiku_track,vertex_baminiku_track_event,edge_baminiku_stream_agent,edge_baminiku_stream_stage_patch,edge_baminiku_stream_chat,edge_baminiku_stream_tip,edge_baminiku_stream_track,edge_baminiku_stream_track_event',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-set-agent-profile-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-create-stream-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'baminiku_create_stream',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_baminiku_create_stream" '
                 'targetNamespace="https://etzhayyim.com/bpmn/baminiku"><bpmn:process '
                 'id="baminiku_create_stream" name="baminiku createStream" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.baminiku.createStream", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="create stream"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="baminiku.createStream"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1018,
                 '00-contracts/bpmn/ai/gftd/baminiku/createStream.bpmn',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-create-stream-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-create-stream-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'app.etzhayyim.apps.baminiku.createStream',
                 'baminiku_create_stream',
                 'vertex_baminiku_agent_profile,vertex_baminiku_stream,vertex_baminiku_stage_patch,vertex_baminiku_chat,vertex_baminiku_tip,vertex_baminiku_track,vertex_baminiku_track_event,edge_baminiku_stream_agent,edge_baminiku_stream_stage_patch,edge_baminiku_stream_chat,edge_baminiku_stream_tip,edge_baminiku_stream_track,edge_baminiku_stream_track_event',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-create-stream-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-update-stage-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'baminiku_update_stage',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_baminiku_update_stage" '
                 'targetNamespace="https://etzhayyim.com/bpmn/baminiku"><bpmn:process '
                 'id="baminiku_update_stage" name="baminiku updateStage" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.baminiku.updateStage", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="update stage"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="baminiku.updateStage"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1012,
                 '00-contracts/bpmn/ai/gftd/baminiku/updateStage.bpmn',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-update-stage-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-update-stage-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'app.etzhayyim.apps.baminiku.updateStage',
                 'baminiku_update_stage',
                 'vertex_baminiku_agent_profile,vertex_baminiku_stream,vertex_baminiku_stage_patch,vertex_baminiku_chat,vertex_baminiku_tip,vertex_baminiku_track,vertex_baminiku_track_event,edge_baminiku_stream_agent,edge_baminiku_stream_stage_patch,edge_baminiku_stream_chat,edge_baminiku_stream_tip,edge_baminiku_stream_track,edge_baminiku_stream_track_event',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-update-stage-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-record-chat-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'baminiku_record_chat',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_baminiku_record_chat" '
                 'targetNamespace="https://etzhayyim.com/bpmn/baminiku"><bpmn:process '
                 'id="baminiku_record_chat" name="baminiku recordChat" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.baminiku.recordChat", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="record chat"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="baminiku.recordChat"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1006,
                 '00-contracts/bpmn/ai/gftd/baminiku/recordChat.bpmn',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-record-chat-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-record-chat-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'app.etzhayyim.apps.baminiku.recordChat',
                 'baminiku_record_chat',
                 'vertex_baminiku_agent_profile,vertex_baminiku_stream,vertex_baminiku_stage_patch,vertex_baminiku_chat,vertex_baminiku_tip,vertex_baminiku_track,vertex_baminiku_track_event,edge_baminiku_stream_agent,edge_baminiku_stream_stage_patch,edge_baminiku_stream_chat,edge_baminiku_stream_tip,edge_baminiku_stream_track,edge_baminiku_stream_track_event',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-record-chat-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-record-tip-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'baminiku_record_tip',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_baminiku_record_tip" '
                 'targetNamespace="https://etzhayyim.com/bpmn/baminiku"><bpmn:process '
                 'id="baminiku_record_tip" name="baminiku recordTip" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.baminiku.recordTip", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="record tip"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="baminiku.recordTip"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1000,
                 '00-contracts/bpmn/ai/gftd/baminiku/recordTip.bpmn',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-record-tip-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-record-tip-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'app.etzhayyim.apps.baminiku.recordTip',
                 'baminiku_record_tip',
                 'vertex_baminiku_agent_profile,vertex_baminiku_stream,vertex_baminiku_stage_patch,vertex_baminiku_chat,vertex_baminiku_tip,vertex_baminiku_track,vertex_baminiku_track_event,edge_baminiku_stream_agent,edge_baminiku_stream_stage_patch,edge_baminiku_stream_chat,edge_baminiku_stream_tip,edge_baminiku_stream_track,edge_baminiku_stream_track_event',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-record-tip-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-enqueue-track-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'baminiku_enqueue_track',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_baminiku_enqueue_track" '
                 'targetNamespace="https://etzhayyim.com/bpmn/baminiku"><bpmn:process '
                 'id="baminiku_enqueue_track" name="baminiku enqueueTrack" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.baminiku.enqueueTrack", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="enqueue track"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="baminiku.enqueueTrack"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1018,
                 '00-contracts/bpmn/ai/gftd/baminiku/enqueueTrack.bpmn',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-enqueue-track-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-enqueue-track-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'app.etzhayyim.apps.baminiku.enqueueTrack',
                 'baminiku_enqueue_track',
                 'vertex_baminiku_agent_profile,vertex_baminiku_stream,vertex_baminiku_stage_patch,vertex_baminiku_chat,vertex_baminiku_tip,vertex_baminiku_track,vertex_baminiku_track_event,edge_baminiku_stream_agent,edge_baminiku_stream_stage_patch,edge_baminiku_stream_chat,edge_baminiku_stream_tip,edge_baminiku_stream_track,edge_baminiku_stream_track_event',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-enqueue-track-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-skip-track-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'baminiku_skip_track',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_baminiku_skip_track" '
                 'targetNamespace="https://etzhayyim.com/bpmn/baminiku"><bpmn:process '
                 'id="baminiku_skip_track" name="baminiku skipTrack" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.baminiku.skipTrack", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="skip track"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="baminiku.skipTrack"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1000,
                 '00-contracts/bpmn/ai/gftd/baminiku/skipTrack.bpmn',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-skip-track-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-skip-track-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'app.etzhayyim.apps.baminiku.skipTrack',
                 'baminiku_skip_track',
                 'vertex_baminiku_agent_profile,vertex_baminiku_stream,vertex_baminiku_stage_patch,vertex_baminiku_chat,vertex_baminiku_tip,vertex_baminiku_track,vertex_baminiku_track_event,edge_baminiku_stream_agent,edge_baminiku_stream_stage_patch,edge_baminiku_stream_chat,edge_baminiku_stream_tip,edge_baminiku_stream_track,edge_baminiku_stream_track_event',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-skip-track-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-get-stream-state-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'baminiku_get_stream_state',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_baminiku_get_stream_state" '
                 'targetNamespace="https://etzhayyim.com/bpmn/baminiku"><bpmn:process '
                 'id="baminiku_get_stream_state" name="baminiku getStreamState" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.baminiku.getStreamState", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="get stream state"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="baminiku.getStreamState"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1033,
                 '00-contracts/bpmn/ai/gftd/baminiku/getStreamState.bpmn',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-get-stream-state-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-get-stream-state-v1',
                 'did:web:baminiku.etzhayyim.com',
                 'app.etzhayyim.apps.baminiku.getStreamState',
                 'baminiku_get_stream_state',
                 '',
                 '2026-04-30T21:53:00+09:00',
                 'did:web:baminiku.etzhayyim.com',
                 'did:web:baminiku.etzhayyim.com',
                 'sys.bpmn.seed.baminiku',
                 'did:web:baminiku.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-get-stream-state-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-set-agent-profile-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-set-agent-profile-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-create-stream-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-create-stream-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-update-stage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-update-stage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-record-chat-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-record-chat-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-record-tip-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-record-tip-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-enqueue-track-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-enqueue-track-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-skip-track-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-skip-track-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/baminiku-get-stream-state-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/baminiku-get-stream-state-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
