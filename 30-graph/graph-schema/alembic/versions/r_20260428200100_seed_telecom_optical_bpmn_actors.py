"""Captured from Kysely migration 20260428200100_seed_telecom_optical_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428200100_seed_telecom_optical_bpmn_actors"
down_revision = 'r_20260428200100_seed_resource_flow_detect_anomaly'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-optical-domain-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_optical_domain',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_optical_domain" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_optical_domain" '
                 'name="registerOpticalDomain" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register optical domain">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.opt.domain.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={domainId: domainId, ownerOrgId: ownerOrgId, '
                 'displayName: displayName, controllerKind: controllerKind, controllerEndpoint: '
                 'controllerEndpoint, southboundProtocols: southboundProtocols, jurisdiction: '
                 'jurisdiction, observedAt: observedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=domainId" target="domainId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.opt.domain.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, domainId: domainId, status: status}" '
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
                 2259,
                 '00-contracts/bpmn/ai/gftd/telecom/registerOpticalDomain.bpmn',
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-optical-domain-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-optical-line-system-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_optical_line_system',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_optical_line_system" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_optical_line_system" '
                 'name="registerOpticalLineSystem" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register optical line system">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.opt.ols.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={olsId: olsId, domainId: domainId, vendor: '
                 'vendor, model: model, mustSpecVersion: mustSpecVersion, transponderProfile: '
                 'transponderProfile, totalSpectrumGhz: totalSpectrumGhz, channelGridGhz: '
                 'channelGridGhz, supportedModulations: supportedModulations, observedAt: '
                 'observedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=olsId" target="olsId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.opt.ols.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, olsId: olsId, status: status}" '
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
                 2298,
                 '00-contracts/bpmn/ai/gftd/telecom/registerOpticalLineSystem.bpmn',
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-optical-line-system-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-roadm-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_roadm',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_roadm" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_roadm" name="registerRoadm" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register roadm">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.opt.roadm.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={roadmId: roadmId, olsId: olsId, displayName: '
                 'displayName, siteId: siteId, roadmKind: roadmKind, degreeCount: degreeCount, '
                 'addDropPortCount: addDropPortCount, wssVendor: wssVendor, attachedAssetId: '
                 'attachedAssetId, observedAt: observedAt, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=roadmId" target="roadmId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.opt.roadm.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, roadmId: roadmId, status: status}" '
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
                 2220,
                 '00-contracts/bpmn/ai/gftd/telecom/registerRoadm.bpmn',
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-roadm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-fiber-span-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_fiber_span',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_fiber_span" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_fiber_span" name="registerFiberSpan" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register fiber span">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.opt.fiber.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={spanId: spanId, olsId: olsId, sourceRoadmId: '
                 'sourceRoadmId, targetRoadmId: targetRoadmId, fiberType: fiberType, lengthKm: '
                 'lengthKm, attenuationDb: attenuationDb, dispersionPsNmKm: dispersionPsNmKm, '
                 'amplifierKind: amplifierKind, amplifierGainDb: amplifierGainDb, ownerOrgId: '
                 'ownerOrgId, observedAt: observedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=spanId" target="spanId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.opt.fiber.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, spanId: spanId, status: status}" '
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
                 2307,
                 '00-contracts/bpmn/ai/gftd/telecom/registerFiberSpan.bpmn',
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-fiber-span-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-provision-dwdm-channel-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_provision_dwdm_channel',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_provision_dwdm_channel" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_provision_dwdm_channel" name="provisionDwdmChannel" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Provision"/>\n'
                 '    <bpmn:serviceTask id="Task_Provision" name="provision dwdm channel">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.opt.dwdm.provision"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={channelId: channelId, olsId: olsId, '
                 'sourceRoadmId: sourceRoadmId, targetRoadmId: targetRoadmId, pathSpanIds: '
                 'pathSpanIds, centerFrequencyGhz: centerFrequencyGhz, bandwidthGhz: bandwidthGhz, '
                 'modulation: modulation, lineRateGbps: lineRateGbps, fec: fec, oTransparentTo: '
                 'oTransparentTo, callerDid: callerDid, observedAt: observedAt}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=channelId" target="channelId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Provision" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.opt.dwdm.provision&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, channelId: channelId, status: status}" '
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
                 2332,
                 '00-contracts/bpmn/ai/gftd/telecom/provisionDwdmChannel.bpmn',
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-provision-dwdm-channel-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-provision-otn-connection-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_provision_otn_connection',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_provision_otn_connection" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_provision_otn_connection" '
                 'name="provisionOtnConnection" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Provision"/>\n'
                 '    <bpmn:serviceTask id="Task_Provision" name="provision otn connection">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.opt.otn.provision"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={otnId: otnId, channelId: channelId, oduKind: '
                 'oduKind, oduRate: oduRate, sourceRoadmId: sourceRoadmId, targetRoadmId: '
                 'targetRoadmId, clientServiceKind: clientServiceKind, clientServiceVid: '
                 'clientServiceVid, protectionKind: protectionKind, observedAt: observedAt, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=otnId" target="otnId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Provision" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.opt.otn.provision&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, otnId: otnId, status: status}" '
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
                 2276,
                 '00-contracts/bpmn/ai/gftd/telecom/provisionOtnConnection.bpmn',
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-provision-otn-connection-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-record-optical-alarm-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_record_optical_alarm',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_record_optical_alarm" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_record_optical_alarm" name="recordOpticalAlarm" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Record"/>\n'
                 '    <bpmn:serviceTask id="Task_Record" name="record optical alarm">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.opt.alarm.record"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={alarmId: alarmId, sourceKind: sourceKind, '
                 'sourceVid: sourceVid, alarmKind: alarmKind, severity: severity, observedAt: '
                 'observedAt, observedValue: observedValue, observedUnit: observedUnit, ticketId: '
                 'ticketId, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=alarmId" target="alarmId"/><zeebe:output source="=ticketId" '
                 'target="ticketId"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Record" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.opt.alarm.record&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, alarmId: alarmId, ticketId: ticketId, status: '
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
                 2275,
                 '00-contracts/bpmn/ai/gftd/telecom/recordOpticalAlarm.bpmn',
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-record-optical-alarm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-record-pm-event-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_record_pm_event',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_record_pm_event" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_record_pm_event" name="recordPmEvent" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Record"/>\n'
                 '    <bpmn:serviceTask id="Task_Record" name="record pm event">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.opt.pm.record"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={pmId: pmId, sourceKind: sourceKind, sourceVid: '
                 'sourceVid, metric: metric, value: value, unit: unit, binIntervalSeconds: '
                 'binIntervalSeconds, slaThreshold: slaThreshold, observedAt: observedAt, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=pmId" target="pmId"/><zeebe:output source="=breach" '
                 'target="breach"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Record" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.opt.pm.record&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, pmId: pmId, breach: breach, status: status}" '
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
                 2213,
                 '00-contracts/bpmn/ai/gftd/telecom/recordPmEvent.bpmn',
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-record-pm-event-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerOpticalDomain-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.registerOpticalDomain',
                 'telecom_register_optical_domain',
                 30000,
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerOpticalDomain-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerOpticalLineSystem-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.registerOpticalLineSystem',
                 'telecom_register_optical_line_system',
                 30000,
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerOpticalLineSystem-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerRoadm-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.registerRoadm',
                 'telecom_register_roadm',
                 30000,
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerRoadm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerFiberSpan-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.registerFiberSpan',
                 'telecom_register_fiber_span',
                 30000,
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerFiberSpan-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-provisionDwdmChannel-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.provisionDwdmChannel',
                 'telecom_provision_dwdm_channel',
                 30000,
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-provisionDwdmChannel-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-provisionOtnConnection-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.provisionOtnConnection',
                 'telecom_provision_otn_connection',
                 30000,
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-provisionOtnConnection-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-recordOpticalAlarm-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.recordOpticalAlarm',
                 'telecom_record_optical_alarm',
                 15000,
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-recordOpticalAlarm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-recordPmEvent-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.recordPmEvent',
                 'telecom_record_pm_event',
                 15000,
                 '2026-04-28T20:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-optical',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-recordPmEvent-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerOpticalDomain-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerOpticalLineSystem-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerRoadm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerFiberSpan-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-provisionDwdmChannel-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-provisionOtnConnection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-recordOpticalAlarm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-recordPmEvent-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-optical-domain-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-optical-line-system-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-roadm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-fiber-span-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-provision-dwdm-channel-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-provision-otn-connection-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-record-optical-alarm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-record-pm-event-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
