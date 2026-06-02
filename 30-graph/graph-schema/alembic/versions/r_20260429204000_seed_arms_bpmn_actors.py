"""Captured from Kysely migration 20260429204000_seed_arms_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429204000_seed_arms_bpmn_actors"
down_revision = 'r_20260429203000_strategy_dependency_topology_contract'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-register-firearm-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_register_firearm',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arms_register_firearm" '
                 'targetNamespace="https://etzhayyim.com/bpmn/arms" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="arms_register_firearm" name="arms '
                 'registerFirearm" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.arms.registerFirearm", "version": 1, "resultTimeoutMs": 60000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" '
                 'name="registerFirearm"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arms.registerFirearm"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1093,
                 '00-contracts/bpmn/com/etzhayyim/arms/registerFirearm.bpmn',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-register-firearm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-register-firearm-v1',
                 'did:web:arms.etzhayyim.com',
                 'com.etzhayyim.apps.arms.registerFirearm',
                 'arms_register_firearm',
                 60000,
                 'vertex_arms_firearm,vertex_arms_firearm_pii,edge_arms_firearm_to_holder',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-register-firearm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-authenticate-holder-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_authenticate_holder',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arms_authenticate_holder" '
                 'targetNamespace="https://etzhayyim.com/bpmn/arms" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="arms_authenticate_holder" name="arms '
                 'authenticateHolder" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.arms.authenticateHolder", "version": 1, "resultTimeoutMs": 60000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" '
                 'name="authenticateHolder"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arms.authenticateHolder"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1111,
                 '00-contracts/bpmn/com/etzhayyim/arms/authenticateHolder.bpmn',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-authenticate-holder-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-authenticate-holder-v1',
                 'did:web:arms.etzhayyim.com',
                 'com.etzhayyim.apps.arms.authenticateHolder',
                 'arms_authenticate_holder',
                 60000,
                 'vertex_arms_auth_session',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-authenticate-holder-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-verify-auth-challenge-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_verify_auth_challenge',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arms_verify_auth_challenge" '
                 'targetNamespace="https://etzhayyim.com/bpmn/arms" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="arms_verify_auth_challenge" name="arms '
                 'verifyAuthChallenge" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.arms.verifyAuthChallenge", "version": 1, "resultTimeoutMs": 60000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" '
                 'name="verifyAuthChallenge"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arms.verifyAuthChallenge"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1119,
                 '00-contracts/bpmn/com/etzhayyim/arms/verifyAuthChallenge.bpmn',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-verify-auth-challenge-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-verify-auth-challenge-v1',
                 'did:web:arms.etzhayyim.com',
                 'com.etzhayyim.apps.arms.verifyAuthChallenge',
                 'arms_verify_auth_challenge',
                 60000,
                 'vertex_arms_auth_session',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-verify-auth-challenge-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-issue-permit-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_issue_permit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arms_issue_permit" targetNamespace="https://etzhayyim.com/bpmn/arms" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="arms_issue_permit" name="arms issuePermit" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.arms.issuePermit", "version": 1, "resultTimeoutMs": 60000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="issuePermit"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arms.issuePermit"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1069,
                 '00-contracts/bpmn/com/etzhayyim/arms/issuePermit.bpmn',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-issue-permit-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-issue-permit-v1',
                 'did:web:arms.etzhayyim.com',
                 'com.etzhayyim.apps.arms.issuePermit',
                 'arms_issue_permit',
                 60000,
                 'vertex_arms_permit,vertex_arms_permit_pii',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-issue-permit-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-transfer-custody-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_transfer_custody',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arms_transfer_custody" '
                 'targetNamespace="https://etzhayyim.com/bpmn/arms" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="arms_transfer_custody" name="arms '
                 'transferCustody" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.arms.transferCustody", "version": 1, "resultTimeoutMs": 60000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" '
                 'name="transferCustody"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arms.transferCustody"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1093,
                 '00-contracts/bpmn/com/etzhayyim/arms/transferCustody.bpmn',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-transfer-custody-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-transfer-custody-v1',
                 'did:web:arms.etzhayyim.com',
                 'com.etzhayyim.apps.arms.transferCustody',
                 'arms_transfer_custody',
                 60000,
                 'vertex_arms_custody_event,edge_arms_firearm_to_holder,edge_arms_firearm_to_permit',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-transfer-custody-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-check-out-firearm-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_check_out_firearm',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arms_check_out_firearm" '
                 'targetNamespace="https://etzhayyim.com/bpmn/arms" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="arms_check_out_firearm" name="arms '
                 'checkOutFirearm" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.arms.checkOutFirearm", "version": 1, "resultTimeoutMs": 60000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" '
                 'name="checkOutFirearm"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arms.checkOutFirearm"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1095,
                 '00-contracts/bpmn/com/etzhayyim/arms/checkOutFirearm.bpmn',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-check-out-firearm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-check-out-firearm-v1',
                 'did:web:arms.etzhayyim.com',
                 'com.etzhayyim.apps.arms.checkOutFirearm',
                 'arms_check_out_firearm',
                 60000,
                 'vertex_arms_custody_event,vertex_arms_firearm',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-check-out-firearm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-check-in-firearm-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_check_in_firearm',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arms_check_in_firearm" '
                 'targetNamespace="https://etzhayyim.com/bpmn/arms" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="arms_check_in_firearm" name="arms '
                 'checkInFirearm" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.arms.checkInFirearm", "version": 1, "resultTimeoutMs": 60000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" '
                 'name="checkInFirearm"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arms.checkInFirearm"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/com/etzhayyim/arms/checkInFirearm.bpmn',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-check-in-firearm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-check-in-firearm-v1',
                 'did:web:arms.etzhayyim.com',
                 'com.etzhayyim.apps.arms.checkInFirearm',
                 'arms_check_in_firearm',
                 60000,
                 'vertex_arms_custody_event,vertex_arms_firearm',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-check-in-firearm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-report-incident-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_report_incident',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arms_report_incident" '
                 'targetNamespace="https://etzhayyim.com/bpmn/arms" exporter="hand-written" '
                 'exporterVersion="1.0"><bpmn:process id="arms_report_incident" name="arms '
                 'reportIncident" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.arms.reportIncident", "version": 1, "resultTimeoutMs": 60000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" '
                 'name="reportIncident"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arms.reportIncident"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1087,
                 '00-contracts/bpmn/com/etzhayyim/arms/reportIncident.bpmn',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-report-incident-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-report-incident-v1',
                 'did:web:arms.etzhayyim.com',
                 'com.etzhayyim.apps.arms.reportIncident',
                 'arms_report_incident',
                 60000,
                 'vertex_arms_custody_event,vertex_open_defence_event,vertex_arms_firearm',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-report-incident-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-get-firearm-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_get_firearm',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arms_get_firearm" targetNamespace="https://etzhayyim.com/bpmn/arms" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="arms_get_firearm" name="arms getFirearm" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.arms.getFirearm", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="getFirearm"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arms.getFirearm"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1063,
                 '00-contracts/bpmn/com/etzhayyim/arms/getFirearm.bpmn',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-get-firearm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-get-firearm-v1',
                 'did:web:arms.etzhayyim.com',
                 'com.etzhayyim.apps.arms.getFirearm',
                 'arms_get_firearm',
                 30000,
                 '',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-get-firearm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-list-firearms-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_list_firearms',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arms_list_firearms" targetNamespace="https://etzhayyim.com/bpmn/arms" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="arms_list_firearms" name="arms listFirearms" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.arms.listFirearms", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="listFirearms"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arms.listFirearms"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1075,
                 '00-contracts/bpmn/com/etzhayyim/arms/listFirearms.bpmn',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-list-firearms-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-list-firearms-v1',
                 'did:web:arms.etzhayyim.com',
                 'com.etzhayyim.apps.arms.listFirearms',
                 'arms_list_firearms',
                 30000,
                 '',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-list-firearms-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-list-permits-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_list_permits',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arms_list_permits" targetNamespace="https://etzhayyim.com/bpmn/arms" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="arms_list_permits" name="arms listPermits" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.arms.listPermits", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="listPermits"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arms.listPermits"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1069,
                 '00-contracts/bpmn/com/etzhayyim/arms/listPermits.bpmn',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-list-permits-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-list-permits-v1',
                 'did:web:arms.etzhayyim.com',
                 'com.etzhayyim.apps.arms.listPermits',
                 'arms_list_permits',
                 30000,
                 '',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-list-permits-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-get-audit-log-v1',
                 'did:web:arms.etzhayyim.com',
                 'arms_get_audit_log',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arms_get_audit_log" targetNamespace="https://etzhayyim.com/bpmn/arms" '
                 'exporter="hand-written" exporterVersion="1.0"><bpmn:process '
                 'id="arms_get_audit_log" name="arms getAuditLog" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.arms.getAuditLog", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="Flow_1" sourceRef="Start" targetRef="Task_Run"/><bpmn:serviceTask '
                 'id="Task_Run" name="getAuditLog"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arms.getAuditLog"/></bpmn:extensionElements><bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="Flow_2" sourceRef="Task_Run" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1071,
                 '00-contracts/bpmn/com/etzhayyim/arms/getAuditLog.bpmn',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-get-audit-log-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-get-audit-log-v1',
                 'did:web:arms.etzhayyim.com',
                 'com.etzhayyim.apps.arms.getAuditLog',
                 'arms_get_audit_log',
                 30000,
                 '',
                 '2026-04-29T20:40:00+09:00',
                 'did:web:arms.etzhayyim.com',
                 'did:web:arms.etzhayyim.com',
                 'sys.bpmn.seed.arms',
                 'did:web:arms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-get-audit-log-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-register-firearm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-register-firearm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-authenticate-holder-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-authenticate-holder-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-verify-auth-challenge-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-verify-auth-challenge-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-issue-permit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-issue-permit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-transfer-custody-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-transfer-custody-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-check-out-firearm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-check-out-firearm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-check-in-firearm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-check-in-firearm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-report-incident-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-report-incident-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-get-firearm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-get-firearm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-list-firearms-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-list-firearms-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-list-permits-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-list-permits-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arms-get-audit-log-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arms-get-audit-log-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
