"""Captured from Kysely migration 20260427210100_seed_telecom_ims_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427210100_seed_telecom_ims_bpmn_actors"
down_revision = 'r_20260427210000_vertex_telecom_ims'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-register-ims-subscription-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_ims_subscription',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_ims_subscription" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_ims_subscription" '
                 'name="registerImsSubscription" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register ims subscription">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.ims.subscription"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={subscriptionId: subscriptionId, profileId: '
                 'profileId, subscriberId: subscriberId, impi: impi, impuList: impuList, '
                 'serviceProfileRef: serviceProfileRef, sCscfFqdn: sCscfFqdn, hssNfId: hssNfId, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=subscriptionId" target="subscriptionId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.ims.subscription&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, subscriptionId: subscriptionId, status: status}" '
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
                 2241,
                 '00-contracts/bpmn/com/etzhayyim/telecom/registerImsSubscription.bpmn',
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-register-ims-subscription-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-register-sip-endpoint-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_sip_endpoint',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_sip_endpoint" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_sip_endpoint" name="registerSipEndpoint" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register sip endpoint">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.sip.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={registrationId: registrationId, subscriptionId: '
                 'subscriptionId, impi: impi, impu: impu, contactUri: contactUri, pCscfFqdn: '
                 'pCscfFqdn, accessNetwork: accessNetwork, sessionId: sessionId, expiresSeconds: '
                 'expiresSeconds, observedAt: observedAt, callerDid: callerDid}" '
                 'target="payload"/>\n'
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
                 'source="=&quot;telecom.sip.register&quot;" target="action"/><zeebe:input '
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
                 2267,
                 '00-contracts/bpmn/com/etzhayyim/telecom/registerSipEndpoint.bpmn',
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-register-sip-endpoint-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-establish-voice-call-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_establish_voice_call',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_establish_voice_call" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_establish_voice_call" name="establishVoiceCall" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Establish"/>\n'
                 '    <bpmn:serviceTask id="Task_Establish" name="establish voice call">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.voice.establish"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={callId: callId, subscriberId: subscriberId, '
                 'callerImpu: callerImpu, calleeImpu: calleeImpu, callerMsisdn: callerMsisdn, '
                 'calleeMsisdn: calleeMsisdn, sessionVoltype: sessionVoltype, codec: codec, '
                 'pduSessionId: pduSessionId, sCscfNfId: sCscfNfId, tasNfId: tasNfId, invitedAt: '
                 'invitedAt, answeredAt: answeredAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=callId" target="callId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.voice.establish&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, callId: callId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/telecom/establishVoiceCall.bpmn',
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-establish-voice-call-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-terminate-voice-call-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_terminate_voice_call',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_terminate_voice_call" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_terminate_voice_call" name="terminateVoiceCall" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Terminate"/>\n'
                 '    <bpmn:serviceTask id="Task_Terminate" name="terminate voice call">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.voice.terminate"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={callId: callId, releaseCause: releaseCause, '
                 'releasedBy: releasedBy, releasedAt: releasedAt, sipResponseCode: '
                 'sipResponseCode, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=callId" target="callId"/><zeebe:output source="=durationSeconds" '
                 'target="durationSeconds"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Terminate" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.voice.terminate&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, callId: callId, durationSeconds: durationSeconds, '
                 'status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2224,
                 '00-contracts/bpmn/com/etzhayyim/telecom/terminateVoiceCall.bpmn',
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-terminate-voice-call-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-apply-supplementary-service-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_apply_supplementary_service',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_apply_supplementary_service" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_apply_supplementary_service" '
                 'name="applySupplementaryService" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Apply"/>\n'
                 '    <bpmn:serviceTask id="Task_Apply" name="apply supplementary service">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.voice.suppService"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={eventId: eventId, callId: callId, '
                 'subscriptionId: subscriptionId, serviceType: serviceType, action: action, '
                 'targetImpu: targetImpu, params: params, tasNfId: tasNfId, observedAt: '
                 'observedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=eventId" target="eventId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.voice.suppService&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, eventId: eventId, status: status}" '
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
                 2212,
                 '00-contracts/bpmn/com/etzhayyim/telecom/applySupplementaryService.bpmn',
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-apply-supplementary-service-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-route-emergency-call-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_route_emergency_call',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_route_emergency_call" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_route_emergency_call" name="routeEmergencyCall" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Route"/>\n'
                 '    <bpmn:serviceTask id="Task_Route" name="route emergency call">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.voice.emergency"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={emergencyId: emergencyId, callId: callId, '
                 'subscriberId: subscriberId, emergencyService: emergencyService, jurisdiction: '
                 'jurisdiction, psapId: psapId, callerLocation: callerLocation, locationMethod: '
                 'locationMethod, eCscfNfId: eCscfNfId, observedAt: observedAt, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=emergencyId" target="emergencyId"/><zeebe:output source="=psapId" '
                 'target="psapId"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Route" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.voice.emergency&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, emergencyId: emergencyId, psapId: psapId, status: '
                 'status}" target="payload"/></zeebe:ioMapping>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/telecom/routeEmergencyCall.bpmn',
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-route-emergency-call-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-bridge-voice-to-interconnect-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_bridge_voice_to_interconnect',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_bridge_voice_to_interconnect" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_bridge_voice_to_interconnect" '
                 'name="bridgeVoiceToInterconnect" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Bridge"/>\n'
                 '    <bpmn:serviceTask id="Task_Bridge" name="bridge voice to interconnect">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.voice.interconnect"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={bridgeId: bridgeId, callId: callId, '
                 'agreementId: agreementId, partnerId: partnerId, peerKind: peerKind, gatewayKind: '
                 'gatewayKind, gatewayNfId: gatewayNfId, peerSipUri: peerSipUri, peerTrunkRef: '
                 'peerTrunkRef, codec: codec, observedAt: observedAt, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=bridgeId" target="bridgeId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Bridge" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.voice.interconnect&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, bridgeId: bridgeId, status: status}" '
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
                 2280,
                 '00-contracts/bpmn/com/etzhayyim/telecom/bridgeVoiceToInterconnect.bpmn',
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-bridge-voice-to-interconnect-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-emit-ims-billing-event-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_emit_ims_billing_event',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_emit_ims_billing_event" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_emit_ims_billing_event" name="emitImsBillingEvent" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Emit"/>\n'
                 '    <bpmn:serviceTask id="Task_Emit" name="emit ims billing event">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.ims.billing"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={billingId: billingId, callId: callId, '
                 'subscriberId: subscriberId, eventKind: eventKind, ratingGroup: ratingGroup, '
                 'units: units, unitOfMeasure: unitOfMeasure, currency: currency, amount: amount, '
                 'chargingMethod: chargingMethod, cdfNfId: cdfNfId, startedAt: startedAt, endedAt: '
                 'endedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=billingId" target="billingId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.ims.billing&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, billingId: billingId, status: status}" '
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
                 2278,
                 '00-contracts/bpmn/com/etzhayyim/telecom/emitImsBillingEvent.bpmn',
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-emit-ims-billing-event-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-registerImsSubscription-v1',
                 'did:web:telecom.etzhayyim.com',
                 'com.etzhayyim.apps.telecom.registerImsSubscription',
                 'telecom_register_ims_subscription',
                 30000,
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-registerImsSubscription-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-registerSipEndpoint-v1',
                 'did:web:telecom.etzhayyim.com',
                 'com.etzhayyim.apps.telecom.registerSipEndpoint',
                 'telecom_register_sip_endpoint',
                 15000,
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-registerSipEndpoint-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-establishVoiceCall-v1',
                 'did:web:telecom.etzhayyim.com',
                 'com.etzhayyim.apps.telecom.establishVoiceCall',
                 'telecom_establish_voice_call',
                 30000,
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-establishVoiceCall-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-terminateVoiceCall-v1',
                 'did:web:telecom.etzhayyim.com',
                 'com.etzhayyim.apps.telecom.terminateVoiceCall',
                 'telecom_terminate_voice_call',
                 15000,
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-terminateVoiceCall-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-applySupplementaryService-v1',
                 'did:web:telecom.etzhayyim.com',
                 'com.etzhayyim.apps.telecom.applySupplementaryService',
                 'telecom_apply_supplementary_service',
                 15000,
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-applySupplementaryService-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-routeEmergencyCall-v1',
                 'did:web:telecom.etzhayyim.com',
                 'com.etzhayyim.apps.telecom.routeEmergencyCall',
                 'telecom_route_emergency_call',
                 15000,
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-routeEmergencyCall-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-bridgeVoiceToInterconnect-v1',
                 'did:web:telecom.etzhayyim.com',
                 'com.etzhayyim.apps.telecom.bridgeVoiceToInterconnect',
                 'telecom_bridge_voice_to_interconnect',
                 15000,
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-bridgeVoiceToInterconnect-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-emitImsBillingEvent-v1',
                 'did:web:telecom.etzhayyim.com',
                 'com.etzhayyim.apps.telecom.emitImsBillingEvent',
                 'telecom_emit_ims_billing_event',
                 15000,
                 '2026-04-27T21:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-ims',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-emitImsBillingEvent-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-registerImsSubscription-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-registerSipEndpoint-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-establishVoiceCall-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-terminateVoiceCall-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-applySupplementaryService-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-routeEmergencyCall-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-bridgeVoiceToInterconnect-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/telecom-emitImsBillingEvent-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-register-ims-subscription-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-register-sip-endpoint-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-establish-voice-call-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-terminate-voice-call-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-apply-supplementary-service-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-route-emergency-call-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-bridge-voice-to-interconnect-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/telecom-emit-ims-billing-event-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
