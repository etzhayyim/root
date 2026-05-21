"""Captured from Kysely migration 20260428100100_seed_telecom_npn_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428100100_seed_telecom_npn_bpmn_actors"
down_revision = 'r_20260428100000_vertex_telecom_npn'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-register-snpn-deployment-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_snpn_deployment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_snpn_deployment" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_snpn_deployment" '
                 'name="registerSnpnDeployment" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register snpn deployment">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.npn.snpn.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={snpnId: snpnId, enterpriseOrgId: '
                 'enterpriseOrgId, deploymentKind: deploymentKind, plmnId: plmnId, nidValue: '
                 'nidValue, hostingNfIds: hostingNfIds, jurisdiction: jurisdiction, validUntil: '
                 'validUntil, observedAt: observedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=snpnId" target="snpnId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.npn.snpn.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, snpnId: snpnId, status: status}" '
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
                 2237,
                 '00-contracts/bpmn/ai/gftd/telecom/registerSnpnDeployment.bpmn',
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-register-snpn-deployment-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-register-cag-group-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_cag_group',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_cag_group" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_cag_group" name="registerCagGroup" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register cag group">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.npn.cag.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={cagId: cagId, snpnId: snpnId, cagValue: '
                 'cagValue, displayName: displayName, allowedCellSiteIds: allowedCellSiteIds, '
                 'allowedRanNodeIds: allowedRanNodeIds, accessKind: accessKind, observedAt: '
                 'observedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=cagId" target="cagId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.npn.cag.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, cagId: cagId, status: status}" '
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
                 2187,
                 '00-contracts/bpmn/ai/gftd/telecom/registerCagGroup.bpmn',
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-register-cag-group-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-register-nid-allocation-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_nid_allocation',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_nid_allocation" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_nid_allocation" '
                 'name="registerNidAllocation" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register nid allocation">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.npn.nid.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={allocationId: allocationId, snpnId: snpnId, '
                 'nidValue: nidValue, assignmentKind: assignmentKind, ouiPrefix: ouiPrefix, '
                 'ieeeAuthorityRef: ieeeAuthorityRef, allocatedAt: allocatedAt, observedAt: '
                 'observedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=allocationId" target="allocationId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.npn.nid.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, allocationId: allocationId, status: status}" '
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
                 2237,
                 '00-contracts/bpmn/ai/gftd/telecom/registerNidAllocation.bpmn',
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-register-nid-allocation-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-provision-pni-npn-slice-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_provision_pni_npn_slice',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_provision_pni_npn_slice" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_provision_pni_npn_slice" name="provisionPniNpnSlice" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Provision"/>\n'
                 '    <bpmn:serviceTask id="Task_Provision" name="provision pni-npn slice">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.npn.pni.provision"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={pniId: pniId, enterpriseOrgId: enterpriseOrgId, '
                 'hostingPlmnId: hostingPlmnId, snssai: snssai, dnn: dnn, cagId: cagId, '
                 'isolationKind: isolationKind, slaTier: slaTier, validUntil: validUntil, '
                 'observedAt: observedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=pniId" target="pniId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.npn.pni.provision&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, pniId: pniId, status: status}" '
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
                 2223,
                 '00-contracts/bpmn/ai/gftd/telecom/provisionPniNpnSlice.bpmn',
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-provision-pni-npn-slice-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-map-supi-to-gpsi-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_map_supi_to_gpsi',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_map_supi_to_gpsi" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_map_supi_to_gpsi" name="mapSupiToGpsi" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Map"/>\n'
                 '    <bpmn:serviceTask id="Task_Map" name="map supi to gpsi">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.npn.idMap.upsert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={mappingId: mappingId, profileId: profileId, '
                 'supi: supi, gpsiKind: gpsiKind, gpsiValue: gpsiValue, snpnId: snpnId, action: '
                 'action, observedAt: observedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=mappingId" target="mappingId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Map" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.npn.idMap.upsert&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, mappingId: mappingId, status: status}" '
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
                 2131,
                 '00-contracts/bpmn/ai/gftd/telecom/mapSupiToGpsi.bpmn',
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-map-supi-to-gpsi-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-enforce-nsacf-slice-admission-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_enforce_nsacf_slice_admission',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_enforce_nsacf_slice_admission" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_enforce_nsacf_slice_admission" '
                 'name="enforceNsacfSliceAdmission" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Enforce"/>\n'
                 '    <bpmn:serviceTask id="Task_Enforce" name="enforce nsacf slice admission">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.npn.nsacf.enforce"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={decisionId: decisionId, nsacfNfId: nsacfNfId, '
                 'snssai: snssai, snpnId: snpnId, requesterNfId: requesterNfId, profileId: '
                 'profileId, requestKind: requestKind, currentRegisteredUes: currentRegisteredUes, '
                 'currentEstablishedSessions: currentEstablishedSessions, maxRegisteredUes: '
                 'maxRegisteredUes, maxEstablishedSessions: maxEstablishedSessions, decision: '
                 'decision, decisionReason: decisionReason, observedAt: observedAt, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=decisionId" target="decisionId"/><zeebe:output source="=admit" '
                 'target="admit"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Enforce" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.npn.nsacf.enforce&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, decisionId: decisionId, admit: admit, status: '
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
                 2523,
                 '00-contracts/bpmn/ai/gftd/telecom/enforceNsacfSliceAdmission.bpmn',
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-enforce-nsacf-slice-admission-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-provision-prose-direct-comm-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_provision_prose_direct_comm',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_provision_prose_direct_comm" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_provision_prose_direct_comm" '
                 'name="provisionProseDirectComm" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Provision"/>\n'
                 '    <bpmn:serviceTask id="Task_Provision" name="provision prose direct comm">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.npn.prose.provision"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={proseId: proseId, snpnId: snpnId, '
                 'communicationKind: communicationKind, layer2GroupId: layer2GroupId, '
                 'prosePolicyHash: prosePolicyHash, prosePolicyRef: prosePolicyRef, '
                 'sidelinkProfile: sidelinkProfile, allowedRanNodeIds: allowedRanNodeIds, '
                 'validUntil: validUntil, observedAt: observedAt, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=proseId" target="proseId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.npn.prose.provision&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, proseId: proseId, status: status}" '
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
                 2325,
                 '00-contracts/bpmn/ai/gftd/telecom/provisionProseDirectComm.bpmn',
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-provision-prose-direct-comm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-register-non-public-subscriber-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_non_public_subscriber',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_non_public_subscriber" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_non_public_subscriber" '
                 'name="registerNonPublicSubscriber" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register non-public subscriber">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.npn.subscriber.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={enrollmentId: enrollmentId, profileId: '
                 'profileId, snpnId: snpnId, pniId: pniId, cagIds: cagIds, allowedDeviceClass: '
                 'allowedDeviceClass, deviceCount: deviceCount, sponsoredByEnterpriseOrgId: '
                 'sponsoredByEnterpriseOrgId, validUntil: validUntil, observedAt: observedAt, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=enrollmentId" target="enrollmentId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.npn.subscriber.register&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, enrollmentId: '
                 'enrollmentId, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2340,
                 '00-contracts/bpmn/ai/gftd/telecom/registerNonPublicSubscriber.bpmn',
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-register-non-public-subscriber-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-registerSnpnDeployment-v1',
                 'did:web:telecom.etzhayyim.com',
                 'ai.gftd.apps.telecom.registerSnpnDeployment',
                 'telecom_register_snpn_deployment',
                 30000,
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-registerSnpnDeployment-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-registerCagGroup-v1',
                 'did:web:telecom.etzhayyim.com',
                 'ai.gftd.apps.telecom.registerCagGroup',
                 'telecom_register_cag_group',
                 30000,
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-registerCagGroup-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-registerNidAllocation-v1',
                 'did:web:telecom.etzhayyim.com',
                 'ai.gftd.apps.telecom.registerNidAllocation',
                 'telecom_register_nid_allocation',
                 30000,
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-registerNidAllocation-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-provisionPniNpnSlice-v1',
                 'did:web:telecom.etzhayyim.com',
                 'ai.gftd.apps.telecom.provisionPniNpnSlice',
                 'telecom_provision_pni_npn_slice',
                 30000,
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-provisionPniNpnSlice-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-mapSupiToGpsi-v1',
                 'did:web:telecom.etzhayyim.com',
                 'ai.gftd.apps.telecom.mapSupiToGpsi',
                 'telecom_map_supi_to_gpsi',
                 15000,
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-mapSupiToGpsi-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-enforceNsacfSliceAdmission-v1',
                 'did:web:telecom.etzhayyim.com',
                 'ai.gftd.apps.telecom.enforceNsacfSliceAdmission',
                 'telecom_enforce_nsacf_slice_admission',
                 15000,
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-enforceNsacfSliceAdmission-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-provisionProseDirectComm-v1',
                 'did:web:telecom.etzhayyim.com',
                 'ai.gftd.apps.telecom.provisionProseDirectComm',
                 'telecom_provision_prose_direct_comm',
                 30000,
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-provisionProseDirectComm-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-registerNonPublicSubscriber-v1',
                 'did:web:telecom.etzhayyim.com',
                 'ai.gftd.apps.telecom.registerNonPublicSubscriber',
                 'telecom_register_non_public_subscriber',
                 30000,
                 '2026-04-28T10:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-npn',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-registerNonPublicSubscriber-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-registerSnpnDeployment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-registerCagGroup-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-registerNidAllocation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-provisionPniNpnSlice-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-mapSupiToGpsi-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-enforceNsacfSliceAdmission-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-provisionProseDirectComm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/telecom-registerNonPublicSubscriber-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-register-snpn-deployment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-register-cag-group-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-register-nid-allocation-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-provision-pni-npn-slice-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-map-supi-to-gpsi-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-enforce-nsacf-slice-admission-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-provision-prose-direct-comm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/telecom-register-non-public-subscriber-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
