"""Captured from Kysely migration 20260430205100_seed_demining_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430205100_seed_demining_bpmn_actors"
down_revision = 'r_20260430205000_vertex_atrecord_demining'
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
         '        $7, 300, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-register-hazard-area-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'demining_register_hazard_area',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_demining_register_hazard_area" '
                 'targetNamespace="https://etzhayyim.com/bpmn/demining"><bpmn:process '
                 'id="demining_register_hazard_area" name="demining registerHazardArea" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.demining.registerHazardArea", "version": 1, "resultTimeoutMs": '
                 '120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="register hazard area"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="demining.registerHazardArea"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1058,
                 '00-contracts/bpmn/ai/gftd/demining/registerHazardArea.bpmn',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-register-hazard-area-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        300, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-registerHazardArea-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'ai.gftd.apps.demining.registerHazardArea',
                 'demining_register_hazard_area',
                 120000,
                 'vertex_atrecord_demining_public,vertex_atrecord_demining_tier3_field,vertex_atrecord_demining_tier3_audit',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-registerHazardArea-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 300, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-list-hazard-areas-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'demining_list_hazard_areas',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_demining_list_hazard_areas" '
                 'targetNamespace="https://etzhayyim.com/bpmn/demining"><bpmn:process '
                 'id="demining_list_hazard_areas" name="demining listHazardAreas" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.demining.listHazardAreas", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="list hazard areas"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="demining.listHazardAreas"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1039,
                 '00-contracts/bpmn/ai/gftd/demining/listHazardAreas.bpmn',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-list-hazard-areas-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        300, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-listHazardAreas-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'ai.gftd.apps.demining.listHazardAreas',
                 'demining_list_hazard_areas',
                 30000,
                 '',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-listHazardAreas-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 300, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-record-detection-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'demining_record_detection',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_demining_record_detection" '
                 'targetNamespace="https://etzhayyim.com/bpmn/demining"><bpmn:process '
                 'id="demining_record_detection" name="demining recordDetection" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.demining.recordDetection", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="record detection"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="demining.recordDetection"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1037,
                 '00-contracts/bpmn/ai/gftd/demining/recordDetection.bpmn',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-record-detection-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        300, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-recordDetection-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'ai.gftd.apps.demining.recordDetection',
                 'demining_record_detection',
                 120000,
                 'vertex_atrecord_demining_public,vertex_atrecord_demining_tier3_field,vertex_atrecord_demining_tier3_audit',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-recordDetection-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 300, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-record-clearance-task-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'demining_record_clearance_task',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_demining_record_clearance_task" '
                 'targetNamespace="https://etzhayyim.com/bpmn/demining"><bpmn:process '
                 'id="demining_record_clearance_task" name="demining recordClearanceTask" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.demining.recordClearanceTask", "version": 1, "resultTimeoutMs": '
                 '120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="record clearance task"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="demining.recordClearanceTask"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1064,
                 '00-contracts/bpmn/ai/gftd/demining/recordClearanceTask.bpmn',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-record-clearance-task-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        300, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-recordClearanceTask-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'ai.gftd.apps.demining.recordClearanceTask',
                 'demining_record_clearance_task',
                 120000,
                 'vertex_atrecord_demining_public,vertex_atrecord_demining_tier3_field,vertex_atrecord_demining_tier3_audit',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-recordClearanceTask-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 300, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-release-area-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'demining_release_area',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_demining_release_area" '
                 'targetNamespace="https://etzhayyim.com/bpmn/demining"><bpmn:process '
                 'id="demining_release_area" name="demining releaseArea" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.demining.releaseArea", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="release area"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="demining.releaseArea"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1013,
                 '00-contracts/bpmn/ai/gftd/demining/releaseArea.bpmn',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-release-area-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        300, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-releaseArea-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'ai.gftd.apps.demining.releaseArea',
                 'demining_release_area',
                 120000,
                 'vertex_atrecord_demining_public,vertex_atrecord_demining_tier3_field,vertex_atrecord_demining_tier3_audit',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-releaseArea-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 300, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-record-eore-session-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'demining_record_eore_session',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_demining_record_eore_session" '
                 'targetNamespace="https://etzhayyim.com/bpmn/demining"><bpmn:process '
                 'id="demining_record_eore_session" name="demining recordEoreSession" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.demining.recordEoreSession", "version": 1, "resultTimeoutMs": '
                 '120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="record eore session"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="demining.recordEoreSession"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1052,
                 '00-contracts/bpmn/ai/gftd/demining/recordEoreSession.bpmn',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-record-eore-session-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        300, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-recordEoreSession-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'ai.gftd.apps.demining.recordEoreSession',
                 'demining_record_eore_session',
                 120000,
                 'vertex_atrecord_demining_public',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-recordEoreSession-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 300, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-record-victim-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'demining_record_victim',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_demining_record_victim" '
                 'targetNamespace="https://etzhayyim.com/bpmn/demining"><bpmn:process '
                 'id="demining_record_victim" name="demining recordVictim" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.demining.recordVictim", "version": 1, "resultTimeoutMs": 120000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="record victim"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="demining.recordVictim"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1019,
                 '00-contracts/bpmn/ai/gftd/demining/recordVictim.bpmn',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-record-victim-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        300, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-recordVictim-v1',
                 'did:web:dm1nactz.etzhayyim.com',
                 'ai.gftd.apps.demining.recordVictim',
                 'demining_record_victim',
                 120000,
                 'vertex_atrecord_demining_public,vertex_atrecord_demining_tier3_field,vertex_atrecord_demining_tier3_audit',
                 '2026-04-30T20:51:00+09:00',
                 'did:web:dm1nactz.etzhayyim.com',
                 'did:web:dm1nactz.etzhayyim.com',
                 'sys.bpmn.seed.demining',
                 'did:web:dm1nactz.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-recordVictim-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-registerHazardArea-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-register-hazard-area-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-listHazardAreas-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-list-hazard-areas-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-recordDetection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-record-detection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-recordClearanceTask-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-record-clearance-task-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-releaseArea-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-release-area-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-recordEoreSession-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-record-eore-session-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/demining-recordVictim-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/demining-record-victim-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
