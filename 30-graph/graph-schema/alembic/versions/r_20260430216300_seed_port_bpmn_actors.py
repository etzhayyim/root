"""Captured from Kysely migration 20260430216300_seed_port_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430216300_seed_port_bpmn_actors"
down_revision = 'r_20260430216200_seed_vessel_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-register-port-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_infrastructure_registerPort',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_infrastructure_registerPort" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_infrastructure_registerPort" name="port_infrastructure_registerPort" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.infrastructure.registerPort", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerPort"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.infrastructure.registerPort"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1065,
                 '00-contracts/bpmn/ai/gftd/port/infrastructure/registerPort.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-register-port-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-register-port-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.infrastructure.registerPort',
                 'port_infrastructure_registerPort',
                 'vertex_transport',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-register-port-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-update-port-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_infrastructure_updatePort',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_infrastructure_updatePort" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_infrastructure_updatePort" name="port_infrastructure_updatePort" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.infrastructure.updatePort", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="updatePort"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.infrastructure.updatePort"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1053,
                 '00-contracts/bpmn/ai/gftd/port/infrastructure/updatePort.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-update-port-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-update-port-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.infrastructure.updatePort',
                 'port_infrastructure_updatePort',
                 'vertex_transport',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-update-port-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-register-berth-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_infrastructure_registerBerth',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_infrastructure_registerBerth" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_infrastructure_registerBerth" name="port_infrastructure_registerBerth" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.infrastructure.registerBerth", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerBerth"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.infrastructure.registerBerth"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1071,
                 '00-contracts/bpmn/ai/gftd/port/infrastructure/registerBerth.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-register-berth-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-register-berth-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.infrastructure.registerBerth',
                 'port_infrastructure_registerBerth',
                 'vertex_port_berth,edge_port_infrastructure',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-register-berth-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-register-terminal-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_infrastructure_registerTerminal',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_infrastructure_registerTerminal" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_infrastructure_registerTerminal" '
                 'name="port_infrastructure_registerTerminal" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.infrastructure.registerTerminal", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="registerTerminal"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.infrastructure.registerTerminal"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/ai/gftd/port/infrastructure/registerTerminal.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-register-terminal-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-register-terminal-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.infrastructure.registerTerminal',
                 'port_infrastructure_registerTerminal',
                 'vertex_port_terminal,edge_port_infrastructure',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-register-terminal-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-get-port-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_infrastructure_getPort',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_infrastructure_getPort" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_infrastructure_getPort" name="port_infrastructure_getPort" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.infrastructure.getPort", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getPort"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.infrastructure.getPort"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1035,
                 '00-contracts/bpmn/ai/gftd/port/infrastructure/getPort.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-get-port-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-get-port-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.infrastructure.getPort',
                 'port_infrastructure_getPort',
                 '',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-get-port-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-list-ports-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_infrastructure_listPorts',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_infrastructure_listPorts" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_infrastructure_listPorts" name="port_infrastructure_listPorts" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.infrastructure.listPorts", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listPorts"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.infrastructure.listPorts"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1047,
                 '00-contracts/bpmn/ai/gftd/port/infrastructure/listPorts.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-list-ports-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-list-ports-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.infrastructure.listPorts',
                 'port_infrastructure_listPorts',
                 '',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-list-ports-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-search-ports-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_infrastructure_searchPorts',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_infrastructure_searchPorts" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_infrastructure_searchPorts" name="port_infrastructure_searchPorts" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.infrastructure.searchPorts", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="searchPorts"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.infrastructure.searchPorts"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1059,
                 '00-contracts/bpmn/ai/gftd/port/infrastructure/searchPorts.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-search-ports-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-search-ports-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.infrastructure.searchPorts',
                 'port_infrastructure_searchPorts',
                 '',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-search-ports-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-get-port-berths-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_infrastructure_getPortBerths',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_infrastructure_getPortBerths" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_infrastructure_getPortBerths" name="port_infrastructure_getPortBerths" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.infrastructure.getPortBerths", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getPortBerths"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.infrastructure.getPortBerths"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1071,
                 '00-contracts/bpmn/ai/gftd/port/infrastructure/getPortBerths.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-get-port-berths-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-get-port-berths-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.infrastructure.getPortBerths',
                 'port_infrastructure_getPortBerths',
                 '',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-get-port-berths-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-get-port-terminals-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_infrastructure_getPortTerminals',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_infrastructure_getPortTerminals" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_infrastructure_getPortTerminals" '
                 'name="port_infrastructure_getPortTerminals" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.infrastructure.getPortTerminals", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getPortTerminals"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.infrastructure.getPortTerminals"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/ai/gftd/port/infrastructure/getPortTerminals.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-get-port-terminals-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-get-port-terminals-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.infrastructure.getPortTerminals',
                 'port_infrastructure_getPortTerminals',
                 '',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-get-port-terminals-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-port-call-tracking-receive-port-call-event-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_portCallTracking_receivePortCallEvent',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_portCallTracking_receivePortCallEvent" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_portCallTracking_receivePortCallEvent" '
                 'name="port_portCallTracking_receivePortCallEvent" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.portCallTracking.receivePortCallEvent", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="receivePortCallEvent"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.portCallTracking.receivePortCallEvent"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1123,
                 '00-contracts/bpmn/ai/gftd/port/portCallTracking/receivePortCallEvent.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-port-call-tracking-receive-port-call-event-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-port-call-tracking-receive-port-call-event-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.portCallTracking.receivePortCallEvent',
                 'port_portCallTracking_receivePortCallEvent',
                 'vertex_port_call_event,edge_port_call_event',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-port-call-tracking-receive-port-call-event-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-port-call-tracking-list-port-call-events-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_portCallTracking_listPortCallEvents',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_portCallTracking_listPortCallEvents" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_portCallTracking_listPortCallEvents" '
                 'name="port_portCallTracking_listPortCallEvents" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.portCallTracking.listPortCallEvents", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="listPortCallEvents"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.portCallTracking.listPortCallEvents"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1111,
                 '00-contracts/bpmn/ai/gftd/port/portCallTracking/listPortCallEvents.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-port-call-tracking-list-port-call-events-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-port-call-tracking-list-port-call-events-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.portCallTracking.listPortCallEvents',
                 'port_portCallTracking_listPortCallEvents',
                 '',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-port-call-tracking-list-port-call-events-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-port-call-tracking-get-vessels-at-port-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_portCallTracking_getVesselsAtPort',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_portCallTracking_getVesselsAtPort" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_portCallTracking_getVesselsAtPort" '
                 'name="port_portCallTracking_getVesselsAtPort" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.portCallTracking.getVesselsAtPort", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getVesselsAtPort"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.portCallTracking.getVesselsAtPort"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1099,
                 '00-contracts/bpmn/ai/gftd/port/portCallTracking/getVesselsAtPort.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-port-call-tracking-get-vessels-at-port-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-port-call-tracking-get-vessels-at-port-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.portCallTracking.getVesselsAtPort',
                 'port_portCallTracking_getVesselsAtPort',
                 '',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-port-call-tracking-get-vessels-at-port-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-port-call-tracking-get-port-occupancy-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_portCallTracking_getPortOccupancy',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_portCallTracking_getPortOccupancy" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process '
                 'id="port_portCallTracking_getPortOccupancy" '
                 'name="port_portCallTracking_getPortOccupancy" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.portCallTracking.getPortOccupancy", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getPortOccupancy"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.portCallTracking.getPortOccupancy"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1099,
                 '00-contracts/bpmn/ai/gftd/port/portCallTracking/getPortOccupancy.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-port-call-tracking-get-port-occupancy-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-port-call-tracking-get-port-occupancy-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.portCallTracking.getPortOccupancy',
                 'port_portCallTracking_getPortOccupancy',
                 '',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-port-call-tracking-get-port-occupancy-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-seed-ports-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_seedPorts',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_seedPorts" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process id="port_seedPorts" '
                 'name="port_seedPorts" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.seedPorts", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="seedPorts"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.seedPorts"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 972,
                 '00-contracts/bpmn/ai/gftd/port/seedPorts.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-seed-ports-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-seed-ports-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.seedPorts',
                 'port_seedPorts',
                 'vertex_transport,vertex_port_berth,vertex_port_terminal,vertex_port_call_event,edge_port_infrastructure,edge_port_call_event',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-seed-ports-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id, actor_did, org_did) SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, '
         "'active', $7, 100, $8, $9, $10, $11, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_process_def WHERE vertex_id = $12)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-get-dashboard-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'port_getDashboard',
                 '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions '
                 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_port_getDashboard" '
                 'targetNamespace="https://etzhayyim.com/bpmn/port"><bpmn:process id="port_getDashboard" '
                 'name="port_getDashboard" isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.port.getDashboard", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="getDashboard"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="port.getDashboard"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 990,
                 '00-contracts/bpmn/ai/gftd/port/getDashboard.bpmn',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-get-dashboard-v1']},
 {'sql': 'INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, '
         'bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, '
         'sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT $1, $2, $3, $4, '
         "1, 30000, $5, 'active', $6, 100, $7, $8, $9, $10, 'anon' WHERE NOT EXISTS (SELECT 1 FROM "
         'vertex_bpmn_lexicon_binding WHERE vertex_id = $11)',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-get-dashboard-v1',
                 'did:web:p0rt7890.etzhayyim.com',
                 'ai.gftd.apps.port.getDashboard',
                 'port_getDashboard',
                 '',
                 '2026-04-30T22:03:00+09:00',
                 'did:web:p0rt7890.etzhayyim.com',
                 'did:web:p0rt7890.etzhayyim.com',
                 'sys.bpmn.seed.port',
                 'did:web:p0rt7890.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-get-dashboard-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-register-port-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-register-port-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-update-port-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-update-port-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-register-berth-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-register-berth-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-register-terminal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-register-terminal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-get-port-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-get-port-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-list-ports-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-list-ports-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-search-ports-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-search-ports-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-get-port-berths-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-get-port-berths-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-infrastructure-get-port-terminals-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-infrastructure-get-port-terminals-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-port-call-tracking-receive-port-call-event-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-port-call-tracking-receive-port-call-event-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-port-call-tracking-list-port-call-events-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-port-call-tracking-list-port-call-events-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-port-call-tracking-get-vessels-at-port-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-port-call-tracking-get-vessels-at-port-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-port-call-tracking-get-port-occupancy-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-port-call-tracking-get-port-occupancy-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-seed-ports-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-seed-ports-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/port-get-dashboard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/port-get-dashboard-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
