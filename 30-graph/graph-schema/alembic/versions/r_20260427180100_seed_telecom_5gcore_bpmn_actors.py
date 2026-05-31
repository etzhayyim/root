"""Captured from Kysely migration 20260427180100_seed_telecom_5gcore_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427180100_seed_telecom_5gcore_bpmn_actors"
down_revision = 'r_20260427180000_vertex_telecom_5gcore'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-network-function-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_network_function',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_network_function" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_network_function" '
                 'name="registerNetworkFunction" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register network function">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.nf.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={nfInstanceId: nfInstanceId, nfType: nfType, '
                 'plmnId: plmnId, sNssaiList: sNssaiList, fqdn: fqdn, ipv4Address: ipv4Address, '
                 'capacity: capacity, priority: priority, heartbeatInterval: heartbeatInterval, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=nfInstanceId" target="nfInstanceId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Register" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.nf.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, nfInstanceId: nfInstanceId, status: status}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2231,
                 '00-contracts/bpmn/ai/gftd/telecom/registerNetworkFunction.bpmn',
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-network-function-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-subscriber-profile5g-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_subscriber_profile_5g',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_subscriber_profile_5g" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_subscriber_profile_5g" '
                 'name="registerSubscriberProfile5g" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register subscriber profile 5g">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.subscriberProfile5g.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={profileId: profileId, subscriberId: '
                 'subscriberId, supi: supi, suciSchemeId: suciSchemeId, sliceSubscriptionList: '
                 'sliceSubscriptionList, dnnList: dnnList, ambrUplinkKbps: ambrUplinkKbps, '
                 'ambrDownlinkKbps: ambrDownlinkKbps, akaCredentialRef: akaCredentialRef, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=profileId" target="profileId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Register" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.subscriberProfile5g.register&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, profileId: '
                 'profileId, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2330,
                 '00-contracts/bpmn/ai/gftd/telecom/registerSubscriberProfile5g.bpmn',
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-subscriber-profile5g-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-authenticate-subscriber-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_authenticate_subscriber',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_authenticate_subscriber" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_authenticate_subscriber" '
                 'name="authenticateSubscriber" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Auth"/>\n'
                 '    <bpmn:serviceTask id="Task_Auth" name="authenticate subscriber">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.subscriber.authenticate"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={authEventId: authEventId, profileId: profileId, '
                 'supi: supi, servingNetwork: servingNetwork, authMethod: authMethod, result: '
                 'result, randHash: randHash, ausfNfId: ausfNfId, observedAt: observedAt, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=authEventId" target="authEventId"/><zeebe:output source="=success" '
                 'target="success"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Auth" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.subscriber.authenticate&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, authEventId: '
                 'authEventId, success: success, status: status}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2296,
                 '00-contracts/bpmn/ai/gftd/telecom/authenticateSubscriber.bpmn',
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-authenticate-subscriber-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-to-network-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_to_network',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_to_network" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_to_network" name="registerToNetwork" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register to network">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.amf.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={registrationId: registrationId, profileId: '
                 'profileId, supi: supi, registrationType: registrationType, ranNodeId: ranNodeId, '
                 'amfNfId: amfNfId, taiPlmnId: taiPlmnId, taiTac: taiTac, observedAt: observedAt, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=registrationId" target="registrationId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Register" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.amf.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, registrationId: registrationId, status: status}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2221,
                 '00-contracts/bpmn/ai/gftd/telecom/registerToNetwork.bpmn',
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-to-network-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-select-network-slice-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_select_network_slice',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_select_network_slice" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_select_network_slice" name="selectNetworkSlice" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Select"/>\n'
                 '    <bpmn:serviceTask id="Task_Select" name="select network slice">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.slice.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={selectionId: selectionId, registrationId: '
                 'registrationId, profileId: profileId, requestedNssaiList: requestedNssaiList, '
                 'allowedNssaiList: allowedNssaiList, selectedSnssai: selectedSnssai, nssfNfId: '
                 'nssfNfId, observedAt: observedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=selectionId" target="selectionId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Select" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.slice.select&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, selectionId: selectionId, status: status}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2235,
                 '00-contracts/bpmn/ai/gftd/telecom/selectNetworkSlice.bpmn',
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-select-network-slice-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-apply-policy-decision-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_apply_policy_decision',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_apply_policy_decision" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_apply_policy_decision" name="applyPolicyDecision" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Apply"/>\n'
                 '    <bpmn:serviceTask id="Task_Apply" name="apply policy decision">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.policy.apply"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={decisionId: decisionId, profileId: profileId, '
                 'sessionId: sessionId, snssai: snssai, dnn: dnn, qosFlowList: qosFlowList, '
                 'chargingMethod: chargingMethod, ratingGroup: ratingGroup, sponsorId: sponsorId, '
                 'pcfNfId: pcfNfId, observedAt: observedAt, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=decisionId" target="decisionId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Apply" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.policy.apply&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, decisionId: decisionId, status: status}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2242,
                 '00-contracts/bpmn/ai/gftd/telecom/applyPolicyDecision.bpmn',
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-apply-policy-decision-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-establish-pdu-session-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_establish_pdu_session',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_establish_pdu_session" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_establish_pdu_session" name="establishPduSession" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Establish"/>\n'
                 '    <bpmn:serviceTask id="Task_Establish" name="establish pdu session">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.session.establish"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={sessionId: sessionId, registrationId: '
                 'registrationId, profileId: profileId, snssai: snssai, dnn: dnn, sessionType: '
                 'sessionType, smfNfId: smfNfId, upfNfId: upfNfId, ranNodeId: ranNodeId, '
                 'policyDecisionId: policyDecisionId, ueIpv4: ueIpv4, ueIpv6Prefix: ueIpv6Prefix, '
                 'observedAt: observedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=sessionId" target="sessionId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Establish" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.session.establish&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, sessionId: sessionId, status: status}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2308,
                 '00-contracts/bpmn/ai/gftd/telecom/establishPduSession.bpmn',
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-establish-pdu-session-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-emit-charging-data-record-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_emit_charging_data_record',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_emit_charging_data_record" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_emit_charging_data_record" '
                 'name="emitChargingDataRecord" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Emit"/>\n'
                 '    <bpmn:serviceTask id="Task_Emit" name="emit charging data record">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.charging.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={chargingId: chargingId, sessionId: sessionId, '
                 'profileId: profileId, subscriberId: subscriberId, ratingGroup: ratingGroup, '
                 'units: units, unitOfMeasure: unitOfMeasure, currency: currency, amount: amount, '
                 'chargingMethod: chargingMethod, chfNfId: chfNfId, startedAt: startedAt, endedAt: '
                 'endedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=chargingId" target="chargingId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Emit" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.charging.emit&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, chargingId: chargingId, status: status}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2306,
                 '00-contracts/bpmn/ai/gftd/telecom/emitChargingDataRecord.bpmn',
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-emit-charging-data-record-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerNetworkFunction-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.registerNetworkFunction',
                 'telecom_register_network_function',
                 30000,
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerNetworkFunction-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerSubscriberProfile5g-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.registerSubscriberProfile5g',
                 'telecom_register_subscriber_profile_5g',
                 30000,
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerSubscriberProfile5g-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-authenticateSubscriber-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.authenticateSubscriber',
                 'telecom_authenticate_subscriber',
                 15000,
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-authenticateSubscriber-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerToNetwork-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.registerToNetwork',
                 'telecom_register_to_network',
                 30000,
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerToNetwork-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-selectNetworkSlice-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.selectNetworkSlice',
                 'telecom_select_network_slice',
                 15000,
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-selectNetworkSlice-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-applyPolicyDecision-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.applyPolicyDecision',
                 'telecom_apply_policy_decision',
                 15000,
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-applyPolicyDecision-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-establishPduSession-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.establishPduSession',
                 'telecom_establish_pdu_session',
                 30000,
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-establishPduSession-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-emitChargingDataRecord-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.emitChargingDataRecord',
                 'telecom_emit_charging_data_record',
                 15000,
                 '2026-04-27T18:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-5gcore',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-emitChargingDataRecord-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerNetworkFunction-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerSubscriberProfile5g-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-authenticateSubscriber-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerToNetwork-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-selectNetworkSlice-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-applyPolicyDecision-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-establishPduSession-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-emitChargingDataRecord-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-network-function-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-subscriber-profile5g-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-authenticate-subscriber-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-to-network-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-select-network-slice-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-apply-policy-decision-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-establish-pdu-session-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-emit-charging-data-record-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
