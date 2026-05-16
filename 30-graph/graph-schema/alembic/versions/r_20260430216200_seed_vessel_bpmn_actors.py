"""Captured from Kysely migration 20260430216200_seed_vessel_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430216200_seed_vessel_bpmn_actors"
down_revision = 'r_20260430216100_seed_vin_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-register-ship-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_registry_registerShip',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_registry_registerShip" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_registry_registerShip" name="vessel_registry_registerShip" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.registry.registerShip", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerShip"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.registry.registerShip"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1047,
                 '00-contracts/bpmn/ai/gftd/vessel/registry/registerShip.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-register-ship-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-register-ship-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.registry.registerShip',
                 'vessel_registry_registerShip',
                 'vertex_vessel_ship',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-register-ship-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-update-ship-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_registry_updateShip',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_registry_updateShip" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_registry_updateShip" name="vessel_registry_updateShip" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.registry.updateShip", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="updateShip"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.registry.updateShip"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1035,
                 '00-contracts/bpmn/ai/gftd/vessel/registry/updateShip.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-update-ship-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-update-ship-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.registry.updateShip',
                 'vessel_registry_updateShip',
                 'vertex_vessel_ship',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-update-ship-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-register-owner-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_registry_registerOwner',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_registry_registerOwner" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_registry_registerOwner" name="vessel_registry_registerOwner" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.registry.registerOwner", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerOwner"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.registry.registerOwner"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1053,
                 '00-contracts/bpmn/ai/gftd/vessel/registry/registerOwner.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-register-owner-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-register-owner-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.registry.registerOwner',
                 'vessel_registry_registerOwner',
                 'vertex_vessel_shipowner',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-register-owner-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-transfer-ownership-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_registry_transferOwnership',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_registry_transferOwnership" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_registry_transferOwnership" name="vessel_registry_transferOwnership" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.registry.transferOwnership", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="transferOwnership"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.registry.transferOwnership"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1077,
                 '00-contracts/bpmn/ai/gftd/vessel/registry/transferOwnership.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-transfer-ownership-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-transfer-ownership-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.registry.transferOwnership',
                 'vessel_registry_transferOwnership',
                 'vertex_vessel_owner_link,edge_vessel_owner_link',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-transfer-ownership-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-register-registry-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_registry_registerRegistry',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_registry_registerRegistry" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_registry_registerRegistry" name="vessel_registry_registerRegistry" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.registry.registerRegistry", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerRegistry"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.registry.registerRegistry"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1071,
                 '00-contracts/bpmn/ai/gftd/vessel/registry/registerRegistry.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-register-registry-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-register-registry-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.registry.registerRegistry',
                 'vessel_registry_registerRegistry',
                 'vertex_vessel_ship_registry',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-register-registry-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-change-flag-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_registry_changeFlag',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_registry_changeFlag" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_registry_changeFlag" name="vessel_registry_changeFlag" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.registry.changeFlag", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="changeFlag"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.registry.changeFlag"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1035,
                 '00-contracts/bpmn/ai/gftd/vessel/registry/changeFlag.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-change-flag-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-change-flag-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.registry.changeFlag',
                 'vessel_registry_changeFlag',
                 'vertex_vessel_ship',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-change-flag-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-get-ship-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_registry_getShip',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_registry_getShip" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_registry_getShip" name="vessel_registry_getShip" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.registry.getShip", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getShip"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.registry.getShip"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1017,
                 '00-contracts/bpmn/ai/gftd/vessel/registry/getShip.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-get-ship-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-get-ship-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.registry.getShip',
                 'vessel_registry_getShip',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-get-ship-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-list-ships-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_registry_listShips',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_registry_listShips" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_registry_listShips" name="vessel_registry_listShips" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.registry.listShips", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listShips"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.registry.listShips"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1029,
                 '00-contracts/bpmn/ai/gftd/vessel/registry/listShips.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-list-ships-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-list-ships-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.registry.listShips',
                 'vessel_registry_listShips',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-list-ships-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-search-ships-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_registry_searchShips',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_registry_searchShips" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_registry_searchShips" name="vessel_registry_searchShips" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.registry.searchShips", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="searchShips"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.registry.searchShips"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1041,
                 '00-contracts/bpmn/ai/gftd/vessel/registry/searchShips.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-search-ships-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-search-ships-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.registry.searchShips',
                 'vessel_registry_searchShips',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-search-ships-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-get-owner-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_registry_getOwner',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_registry_getOwner" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_registry_getOwner" name="vessel_registry_getOwner" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.registry.getOwner", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getOwner"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.registry.getOwner"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1023,
                 '00-contracts/bpmn/ai/gftd/vessel/registry/getOwner.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-get-owner-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-get-owner-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.registry.getOwner',
                 'vessel_registry_getOwner',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-get-owner-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-get-ship-owner-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_registry_getShipOwner',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_registry_getShipOwner" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_registry_getShipOwner" name="vessel_registry_getShipOwner" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.registry.getShipOwner", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getShipOwner"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.registry.getShipOwner"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1047,
                 '00-contracts/bpmn/ai/gftd/vessel/registry/getShipOwner.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-get-ship-owner-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-get-ship-owner-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.registry.getShipOwner',
                 'vessel_registry_getShipOwner',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-get-ship-owner-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-get-ships-by-flag-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_registry_getShipsByFlag',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_registry_getShipsByFlag" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_registry_getShipsByFlag" name="vessel_registry_getShipsByFlag" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.registry.getShipsByFlag", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getShipsByFlag"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.registry.getShipsByFlag"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1059,
                 '00-contracts/bpmn/ai/gftd/vessel/registry/getShipsByFlag.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-get-ships-by-flag-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-get-ships-by-flag-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.registry.getShipsByFlag',
                 'vessel_registry_getShipsByFlag',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-get-ships-by-flag-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-ingest-positions-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_tracking_ingestPositions',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_tracking_ingestPositions" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_tracking_ingestPositions" name="vessel_tracking_ingestPositions" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.tracking.ingestPositions", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="ingestPositions"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.tracking.ingestPositions"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1065,
                 '00-contracts/bpmn/ai/gftd/vessel/tracking/ingestPositions.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-ingest-positions-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-ingest-positions-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.tracking.ingestPositions',
                 'vessel_tracking_ingestPositions',
                 'vertex_vessel_position',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-ingest-positions-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-get-vessel-position-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_tracking_getVesselPosition',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_tracking_getVesselPosition" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_tracking_getVesselPosition" name="vessel_tracking_getVesselPosition" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.tracking.getVesselPosition", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getVesselPosition"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.tracking.getVesselPosition"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1077,
                 '00-contracts/bpmn/ai/gftd/vessel/tracking/getVesselPosition.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-get-vessel-position-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-get-vessel-position-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.tracking.getVesselPosition',
                 'vessel_tracking_getVesselPosition',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-get-vessel-position-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-get-position-by-mmsi-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_tracking_getPositionByMmsi',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_tracking_getPositionByMmsi" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_tracking_getPositionByMmsi" name="vessel_tracking_getPositionByMmsi" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.tracking.getPositionByMmsi", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getPositionByMmsi"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.tracking.getPositionByMmsi"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1077,
                 '00-contracts/bpmn/ai/gftd/vessel/tracking/getPositionByMmsi.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-get-position-by-mmsi-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-get-position-by-mmsi-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.tracking.getPositionByMmsi',
                 'vessel_tracking_getPositionByMmsi',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-get-position-by-mmsi-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-list-vessels-in-area-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_tracking_listVesselsInArea',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_tracking_listVesselsInArea" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_tracking_listVesselsInArea" name="vessel_tracking_listVesselsInArea" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.tracking.listVesselsInArea", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listVesselsInArea"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.tracking.listVesselsInArea"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1077,
                 '00-contracts/bpmn/ai/gftd/vessel/tracking/listVesselsInArea.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-list-vessels-in-area-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-list-vessels-in-area-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.tracking.listVesselsInArea',
                 'vessel_tracking_listVesselsInArea',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-list-vessels-in-area-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-get-position-history-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_tracking_getPositionHistory',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_tracking_getPositionHistory" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_tracking_getPositionHistory" '
                 'name="vessel_tracking_getPositionHistory" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.tracking.getPositionHistory", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getPositionHistory"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.tracking.getPositionHistory"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1083,
                 '00-contracts/bpmn/ai/gftd/vessel/tracking/getPositionHistory.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-get-position-history-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-get-position-history-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.tracking.getPositionHistory',
                 'vessel_tracking_getPositionHistory',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-get-position-history-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-list-vessels-near-port-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_tracking_listVesselsNearPort',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_tracking_listVesselsNearPort" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_tracking_listVesselsNearPort" '
                 'name="vessel_tracking_listVesselsNearPort" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.tracking.listVesselsNearPort", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listVesselsNearPort"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.tracking.listVesselsNearPort"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/ai/gftd/vessel/tracking/listVesselsNearPort.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-list-vessels-near-port-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-list-vessels-near-port-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.tracking.listVesselsNearPort',
                 'vessel_tracking_listVesselsNearPort',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-list-vessels-near-port-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-register-voyage-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_voyage_registerVoyage',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_voyage_registerVoyage" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_voyage_registerVoyage" name="vessel_voyage_registerVoyage" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.voyage.registerVoyage", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerVoyage"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.voyage.registerVoyage"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1049,
                 '00-contracts/bpmn/ai/gftd/vessel/voyage/registerVoyage.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-register-voyage-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-register-voyage-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.voyage.registerVoyage',
                 'vessel_voyage_registerVoyage',
                 'vertex_vessel_voyage',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-register-voyage-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-update-voyage-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_voyage_updateVoyage',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_voyage_updateVoyage" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_voyage_updateVoyage" name="vessel_voyage_updateVoyage" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.voyage.updateVoyage", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="updateVoyage"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.voyage.updateVoyage"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1037,
                 '00-contracts/bpmn/ai/gftd/vessel/voyage/updateVoyage.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-update-voyage-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-update-voyage-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.voyage.updateVoyage',
                 'vessel_voyage_updateVoyage',
                 'vertex_vessel_voyage',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-update-voyage-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-list-voyages-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_voyage_listVoyages',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_voyage_listVoyages" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_voyage_listVoyages" name="vessel_voyage_listVoyages" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.voyage.listVoyages", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listVoyages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.voyage.listVoyages"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1031,
                 '00-contracts/bpmn/ai/gftd/vessel/voyage/listVoyages.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-list-voyages-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-list-voyages-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.voyage.listVoyages',
                 'vessel_voyage_listVoyages',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-list-voyages-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-record-port-call-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_voyage_recordPortCall',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_voyage_recordPortCall" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_voyage_recordPortCall" name="vessel_voyage_recordPortCall" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.voyage.recordPortCall", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="recordPortCall"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.voyage.recordPortCall"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1049,
                 '00-contracts/bpmn/ai/gftd/vessel/voyage/recordPortCall.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-record-port-call-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-record-port-call-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.voyage.recordPortCall',
                 'vessel_voyage_recordPortCall',
                 'vertex_vessel_port_call,edge_vessel_port_call_endpoint',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-record-port-call-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-list-port-calls-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_voyage_listPortCalls',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_voyage_listPortCalls" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_voyage_listPortCalls" name="vessel_voyage_listPortCalls" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.voyage.listPortCalls", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listPortCalls"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.voyage.listPortCalls"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1043,
                 '00-contracts/bpmn/ai/gftd/vessel/voyage/listPortCalls.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-list-port-calls-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-list-port-calls-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.voyage.listPortCalls',
                 'vessel_voyage_listPortCalls',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-list-port-calls-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-link-owner-entity-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_voyage_linkOwnerEntity',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_voyage_linkOwnerEntity" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_voyage_linkOwnerEntity" name="vessel_voyage_linkOwnerEntity" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.voyage.linkOwnerEntity", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="linkOwnerEntity"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.voyage.linkOwnerEntity"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1055,
                 '00-contracts/bpmn/ai/gftd/vessel/voyage/linkOwnerEntity.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-link-owner-entity-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-link-owner-entity-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.voyage.linkOwnerEntity',
                 'vessel_voyage_linkOwnerEntity',
                 'vertex_vessel_owner_link,edge_vessel_owner_link',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-link-owner-entity-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-get-vessel-chain-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_voyage_getVesselChain',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_voyage_getVesselChain" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_voyage_getVesselChain" name="vessel_voyage_getVesselChain" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.voyage.getVesselChain", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getVesselChain"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.voyage.getVesselChain"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1049,
                 '00-contracts/bpmn/ai/gftd/vessel/voyage/getVesselChain.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-get-vessel-chain-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-get-vessel-chain-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.voyage.getVesselChain',
                 'vessel_voyage_getVesselChain',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-get-vessel-chain-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-seed-maritime-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_seedMaritime',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_seedMaritime" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_seedMaritime" name="vessel_seedMaritime" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.seedMaritime", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="seedMaritime"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.seedMaritime"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1002,
                 '00-contracts/bpmn/ai/gftd/vessel/seedMaritime.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-seed-maritime-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-seed-maritime-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.seedMaritime',
                 'vessel_seedMaritime',
                 'vertex_vessel_ship,vertex_vessel_shipowner,vertex_vessel_ship_registry,vertex_vessel_position,vertex_vessel_voyage,vertex_vessel_port_call,vertex_vessel_owner_link,edge_vessel_owner_link,edge_vessel_port_call_endpoint',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-seed-maritime-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-get-dashboard-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'vessel_getDashboard',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_vessel_getDashboard" '
                 'targetNamespace="https://gftd.ai/bpmn/vessel"><bpmn:process '
                 'id="vessel_getDashboard" name="vessel_getDashboard" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.vessel.getDashboard", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getDashboard"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="vessel.getDashboard"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1002,
                 '00-contracts/bpmn/ai/gftd/vessel/getDashboard.bpmn',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-get-dashboard-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-get-dashboard-v1',
                 'did:web:v3ss3l01.gftd.ai',
                 'ai.gftd.apps.vessel.getDashboard',
                 'vessel_getDashboard',
                 '',
                 '2026-04-30T22:02:00+09:00',
                 'did:web:v3ss3l01.gftd.ai',
                 'did:web:v3ss3l01.gftd.ai',
                 'sys.bpmn.seed.vessel',
                 'did:web:v3ss3l01.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-get-dashboard-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-register-ship-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-register-ship-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-update-ship-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-update-ship-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-register-owner-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-register-owner-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-transfer-ownership-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-transfer-ownership-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-register-registry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-register-registry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-change-flag-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-change-flag-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-get-ship-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-get-ship-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-list-ships-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-list-ships-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-search-ships-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-search-ships-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-get-owner-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-get-owner-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-get-ship-owner-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-get-ship-owner-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-registry-get-ships-by-flag-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-registry-get-ships-by-flag-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-ingest-positions-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-ingest-positions-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-get-vessel-position-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-get-vessel-position-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-get-position-by-mmsi-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-get-position-by-mmsi-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-list-vessels-in-area-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-list-vessels-in-area-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-get-position-history-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-get-position-history-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-tracking-list-vessels-near-port-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-tracking-list-vessels-near-port-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-register-voyage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-register-voyage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-update-voyage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-update-voyage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-list-voyages-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-list-voyages-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-record-port-call-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-record-port-call-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-list-port-calls-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-list-port-calls-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-link-owner-entity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-link-owner-entity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-voyage-get-vessel-chain-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-voyage-get-vessel-chain-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-seed-maritime-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-seed-maritime-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/vessel-get-dashboard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/vessel-get-dashboard-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
