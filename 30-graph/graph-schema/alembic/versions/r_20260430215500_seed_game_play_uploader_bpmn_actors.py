"""Captured from Kysely migration 20260430215500_seed_game_play_uploader_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430215500_seed_game_play_uploader_bpmn_actors"
down_revision = 'r_20260430215400_vertex_game_play_uploader_record'
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-register-participant-v1',
                 'did:web:game-play-uploader.gftd.ai',
                 'game_play_uploader_register_participant',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_game_play_uploader_register_participant" '
                 'targetNamespace="https://gftd.ai/bpmn/gamePlayUploader"><bpmn:process '
                 'id="game_play_uploader_register_participant" name="gamePlayUploader '
                 'registerParticipant" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gamePlayUploader.registerParticipant", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="register participant"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gamePlayUploader.registerParticipant"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1112,
                 '00-contracts/bpmn/ai/gftd/gamePlayUploader/registerParticipant.bpmn',
                 '2026-04-30T21:55:00+09:00',
                 'did:web:game-play-uploader.gftd.ai',
                 'did:web:game-play-uploader.gftd.ai',
                 'sys.bpmn.seed.game-play-uploader',
                 'did:web:game-play-uploader.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-register-participant-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-register-participant-v1',
                 'did:web:game-play-uploader.gftd.ai',
                 'ai.gftd.apps.gamePlayUploader.registerParticipant',
                 'game_play_uploader_register_participant',
                 'vertex_game_play_participant,vertex_game_play_upload_session,vertex_game_play_upload,vertex_game_play_review,vertex_game_play_reward,edge_game_play_participant_session,edge_game_play_session_upload,edge_game_play_upload_review,edge_game_play_upload_reward',
                 '2026-04-30T21:55:00+09:00',
                 'did:web:game-play-uploader.gftd.ai',
                 'did:web:game-play-uploader.gftd.ai',
                 'sys.bpmn.seed.game-play-uploader',
                 'did:web:game-play-uploader.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-register-participant-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-create-upload-session-v1',
                 'did:web:game-play-uploader.gftd.ai',
                 'game_play_uploader_create_upload_session',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_game_play_uploader_create_upload_session" '
                 'targetNamespace="https://gftd.ai/bpmn/gamePlayUploader"><bpmn:process '
                 'id="game_play_uploader_create_upload_session" name="gamePlayUploader '
                 'createUploadSession" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gamePlayUploader.createUploadSession", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="create upload session"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gamePlayUploader.createUploadSession"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1115,
                 '00-contracts/bpmn/ai/gftd/gamePlayUploader/createUploadSession.bpmn',
                 '2026-04-30T21:55:00+09:00',
                 'did:web:game-play-uploader.gftd.ai',
                 'did:web:game-play-uploader.gftd.ai',
                 'sys.bpmn.seed.game-play-uploader',
                 'did:web:game-play-uploader.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-create-upload-session-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-create-upload-session-v1',
                 'did:web:game-play-uploader.gftd.ai',
                 'ai.gftd.apps.gamePlayUploader.createUploadSession',
                 'game_play_uploader_create_upload_session',
                 'vertex_game_play_participant,vertex_game_play_upload_session,vertex_game_play_upload,vertex_game_play_review,vertex_game_play_reward,edge_game_play_participant_session,edge_game_play_session_upload,edge_game_play_upload_review,edge_game_play_upload_reward',
                 '2026-04-30T21:55:00+09:00',
                 'did:web:game-play-uploader.gftd.ai',
                 'did:web:game-play-uploader.gftd.ai',
                 'sys.bpmn.seed.game-play-uploader',
                 'did:web:game-play-uploader.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-create-upload-session-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-record-gameplay-upload-v1',
                 'did:web:game-play-uploader.gftd.ai',
                 'game_play_uploader_record_gameplay_upload',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_game_play_uploader_record_gameplay_upload" '
                 'targetNamespace="https://gftd.ai/bpmn/gamePlayUploader"><bpmn:process '
                 'id="game_play_uploader_record_gameplay_upload" name="gamePlayUploader '
                 'recordGameplayUpload" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gamePlayUploader.recordGameplayUpload", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="record gameplay upload"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gamePlayUploader.recordGameplayUpload"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1121,
                 '00-contracts/bpmn/ai/gftd/gamePlayUploader/recordGameplayUpload.bpmn',
                 '2026-04-30T21:55:00+09:00',
                 'did:web:game-play-uploader.gftd.ai',
                 'did:web:game-play-uploader.gftd.ai',
                 'sys.bpmn.seed.game-play-uploader',
                 'did:web:game-play-uploader.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-record-gameplay-upload-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-record-gameplay-upload-v1',
                 'did:web:game-play-uploader.gftd.ai',
                 'ai.gftd.apps.gamePlayUploader.recordGameplayUpload',
                 'game_play_uploader_record_gameplay_upload',
                 'vertex_game_play_participant,vertex_game_play_upload_session,vertex_game_play_upload,vertex_game_play_review,vertex_game_play_reward,edge_game_play_participant_session,edge_game_play_session_upload,edge_game_play_upload_review,edge_game_play_upload_reward',
                 '2026-04-30T21:55:00+09:00',
                 'did:web:game-play-uploader.gftd.ai',
                 'did:web:game-play-uploader.gftd.ai',
                 'sys.bpmn.seed.game-play-uploader',
                 'did:web:game-play-uploader.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-record-gameplay-upload-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-review-upload-v1',
                 'did:web:game-play-uploader.gftd.ai',
                 'game_play_uploader_review_upload',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_game_play_uploader_review_upload" '
                 'targetNamespace="https://gftd.ai/bpmn/gamePlayUploader"><bpmn:process '
                 'id="game_play_uploader_review_upload" name="gamePlayUploader reviewUpload" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gamePlayUploader.reviewUpload", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="review upload"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gamePlayUploader.reviewUpload"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1070,
                 '00-contracts/bpmn/ai/gftd/gamePlayUploader/reviewUpload.bpmn',
                 '2026-04-30T21:55:00+09:00',
                 'did:web:game-play-uploader.gftd.ai',
                 'did:web:game-play-uploader.gftd.ai',
                 'sys.bpmn.seed.game-play-uploader',
                 'did:web:game-play-uploader.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-review-upload-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-review-upload-v1',
                 'did:web:game-play-uploader.gftd.ai',
                 'ai.gftd.apps.gamePlayUploader.reviewUpload',
                 'game_play_uploader_review_upload',
                 'vertex_game_play_participant,vertex_game_play_upload_session,vertex_game_play_upload,vertex_game_play_review,vertex_game_play_reward,edge_game_play_participant_session,edge_game_play_session_upload,edge_game_play_upload_review,edge_game_play_upload_reward',
                 '2026-04-30T21:55:00+09:00',
                 'did:web:game-play-uploader.gftd.ai',
                 'did:web:game-play-uploader.gftd.ai',
                 'sys.bpmn.seed.game-play-uploader',
                 'did:web:game-play-uploader.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-review-upload-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-calculate-reward-v1',
                 'did:web:game-play-uploader.gftd.ai',
                 'game_play_uploader_calculate_reward',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_game_play_uploader_calculate_reward" '
                 'targetNamespace="https://gftd.ai/bpmn/gamePlayUploader"><bpmn:process '
                 'id="game_play_uploader_calculate_reward" name="gamePlayUploader calculateReward" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gamePlayUploader.calculateReward", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="calculate reward"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gamePlayUploader.calculateReward"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1088,
                 '00-contracts/bpmn/ai/gftd/gamePlayUploader/calculateReward.bpmn',
                 '2026-04-30T21:55:00+09:00',
                 'did:web:game-play-uploader.gftd.ai',
                 'did:web:game-play-uploader.gftd.ai',
                 'sys.bpmn.seed.game-play-uploader',
                 'did:web:game-play-uploader.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-calculate-reward-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-calculate-reward-v1',
                 'did:web:game-play-uploader.gftd.ai',
                 'ai.gftd.apps.gamePlayUploader.calculateReward',
                 'game_play_uploader_calculate_reward',
                 '',
                 '2026-04-30T21:55:00+09:00',
                 'did:web:game-play-uploader.gftd.ai',
                 'did:web:game-play-uploader.gftd.ai',
                 'sys.bpmn.seed.game-play-uploader',
                 'did:web:game-play-uploader.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-calculate-reward-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-get-campaign-status-v1',
                 'did:web:game-play-uploader.gftd.ai',
                 'game_play_uploader_get_campaign_status',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_game_play_uploader_get_campaign_status" '
                 'targetNamespace="https://gftd.ai/bpmn/gamePlayUploader"><bpmn:process '
                 'id="game_play_uploader_get_campaign_status" name="gamePlayUploader '
                 'getCampaignStatus" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.gamePlayUploader.getCampaignStatus", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="get campaign status"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="gamePlayUploader.getCampaignStatus"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1103,
                 '00-contracts/bpmn/ai/gftd/gamePlayUploader/getCampaignStatus.bpmn',
                 '2026-04-30T21:55:00+09:00',
                 'did:web:game-play-uploader.gftd.ai',
                 'did:web:game-play-uploader.gftd.ai',
                 'sys.bpmn.seed.game-play-uploader',
                 'did:web:game-play-uploader.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-get-campaign-status-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-get-campaign-status-v1',
                 'did:web:game-play-uploader.gftd.ai',
                 'ai.gftd.apps.gamePlayUploader.getCampaignStatus',
                 'game_play_uploader_get_campaign_status',
                 '',
                 '2026-04-30T21:55:00+09:00',
                 'did:web:game-play-uploader.gftd.ai',
                 'did:web:game-play-uploader.gftd.ai',
                 'sys.bpmn.seed.game-play-uploader',
                 'did:web:game-play-uploader.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-get-campaign-status-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-register-participant-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-register-participant-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-create-upload-session-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-create-upload-session-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-record-gameplay-upload-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-record-gameplay-upload-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-review-upload-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-review-upload-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-calculate-reward-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-calculate-reward-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/game-play-uploader-get-campaign-status-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/game-play-uploader-get-campaign-status-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
