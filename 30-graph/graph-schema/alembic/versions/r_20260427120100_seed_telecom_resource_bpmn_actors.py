"""Captured from Kysely migration 20260427120100_seed_telecom_resource_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427120100_seed_telecom_resource_bpmn_actors"
down_revision = 'r_20260427120000_vertex_telecom_resource'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-spectrum-license-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_spectrum_license',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_spectrum_license" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_spectrum_license" '
                 'name="registerSpectrumLicense" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register spectrum license">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.spectrum.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={licenseId: licenseId, jurisdiction: '
                 'jurisdiction, band: band, lowMhz: lowMhz, highMhz: highMhz, holderOrgId: '
                 'holderOrgId, region: region, validFrom: validFrom, validUntil: validUntil, '
                 'technology: technology, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=licenseId" target="licenseId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.spectrum.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, licenseId: licenseId, status: status}" '
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
                 2239,
                 '00-contracts/bpmn/ai/gftd/telecom/registerSpectrumLicense.bpmn',
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-spectrum-license-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-cell-site-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_cell_site',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_cell_site" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_cell_site" name="registerCellSite" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register cell site">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.site.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={siteId: siteId, name: name, latitude: latitude, '
                 'longitude: longitude, towerOwnerOrgId: towerOwnerOrgId, jurisdiction: '
                 'jurisdiction, height: height, powerSource: powerSource, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=siteId" target="siteId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.site.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, siteId: siteId, status: status}" '
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
                 2157,
                 '00-contracts/bpmn/ai/gftd/telecom/registerCellSite.bpmn',
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-cell-site-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-ran-node-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_ran_node',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_ran_node" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_ran_node" name="registerRanNode" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register ran node">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.ranNode.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={nodeId: nodeId, siteId: siteId, nodeType: '
                 'nodeType, vendor: vendor, model: model, generation: generation, '
                 'spectrumLicenseId: spectrumLicenseId, plmnId: plmnId, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=nodeId" target="nodeId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.ranNode.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, nodeId: nodeId, status: status}" '
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
                 2145,
                 '00-contracts/bpmn/ai/gftd/telecom/registerRanNode.bpmn',
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-ran-node-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-network-asset-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_register_network_asset',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_register_network_asset" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_register_network_asset" name="registerNetworkAsset" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register network asset">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.asset.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={assetId: assetId, serialNumber: serialNumber, '
                 'assetKind: assetKind, vendor: vendor, model: model, installedSiteId: '
                 'installedSiteId, installedNodeId: installedNodeId, installedAt: installedAt, '
                 'warrantyUntil: warrantyUntil, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=assetId" target="assetId"/><zeebe:output source="=status" '
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
                 'source="=&quot;telecom.asset.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, assetId: assetId, status: status}" '
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
                 2227,
                 '00-contracts/bpmn/ai/gftd/telecom/registerNetworkAsset.bpmn',
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-network-asset-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-record-site-incident-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_record_site_incident',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_record_site_incident" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_record_site_incident" name="recordSiteIncident" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Record"/>\n'
                 '    <bpmn:serviceTask id="Task_Record" name="record site incident">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.site.incident"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={incidentId: incidentId, siteId: siteId, nodeId: '
                 'nodeId, incidentKind: incidentKind, severity: severity, detectedAt: detectedAt, '
                 'resolvedAt: resolvedAt, summary: summary, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=incidentId" target="incidentId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
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
                 'source="=&quot;telecom.site.incident&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, incidentId: incidentId, status: status}" '
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
                 2171,
                 '00-contracts/bpmn/ai/gftd/telecom/recordSiteIncident.bpmn',
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-record-site-incident-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-schedule-maintenance-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_schedule_maintenance',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_schedule_maintenance" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_schedule_maintenance" name="scheduleMaintenance" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Schedule"/>\n'
                 '    <bpmn:serviceTask id="Task_Schedule" name="schedule maintenance">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.maintenance.schedule"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={windowId: windowId, siteId: siteId, nodeId: '
                 'nodeId, assetId: assetId, maintenanceKind: maintenanceKind, plannedStart: '
                 'plannedStart, plannedEnd: plannedEnd, vendorOrgId: vendorOrgId, summary: '
                 'summary, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=windowId" target="windowId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Schedule" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.maintenance.schedule&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, windowId: windowId, status: status}" '
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
                 2214,
                 '00-contracts/bpmn/ai/gftd/telecom/scheduleMaintenance.bpmn',
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-schedule-maintenance-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-request-rma-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_request_rma',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_request_rma" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_request_rma" name="requestRma" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Request"/>\n'
                 '    <bpmn:serviceTask id="Task_Request" name="request rma">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="telecom.rma.request"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={rmaId: rmaId, assetId: assetId, vendorOrgId: '
                 'vendorOrgId, faultCategory: faultCategory, faultDescription: faultDescription, '
                 'openedAt: openedAt, expectedReturnAt: expectedReturnAt, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=rmaId" target="rmaId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Request" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.rma.request&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, rmaId: rmaId, status: status}" '
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
                 2125,
                 '00-contracts/bpmn/ai/gftd/telecom/requestRma.bpmn',
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-request-rma-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-audit-performance-counters-v1',
                 'did:web:telecom.etzhayyim.com',
                 'telecom_audit_performance_counters',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_telecom_audit_performance_counters" '
                 'targetNamespace="https://etzhayyim.com/bpmn/telecom" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="telecom_audit_performance_counters" '
                 'name="auditPerformanceCounters" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Audit_Counter"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit_Counter" name="audit performance '
                 'counters">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="telecom.kpi.audit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={sampleId: sampleId, nodeId: nodeId, metric: '
                 'metric, value: value, unit: unit, sampledAt: sampledAt, slaThreshold: '
                 'slaThreshold, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=sampleId" target="sampleId"/><zeebe:output source="=breach" '
                 'target="breach"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Audit_Counter" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:telecom.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;telecom.kpi.audit&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, sampleId: sampleId, breach: breach, status: '
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
                 2222,
                 '00-contracts/bpmn/ai/gftd/telecom/auditPerformanceCounters.bpmn',
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-audit-performance-counters-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerSpectrumLicense-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.registerSpectrumLicense',
                 'telecom_register_spectrum_license',
                 30000,
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerSpectrumLicense-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerCellSite-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.registerCellSite',
                 'telecom_register_cell_site',
                 30000,
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerCellSite-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerRanNode-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.registerRanNode',
                 'telecom_register_ran_node',
                 30000,
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerRanNode-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerNetworkAsset-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.registerNetworkAsset',
                 'telecom_register_network_asset',
                 30000,
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerNetworkAsset-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-recordSiteIncident-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.recordSiteIncident',
                 'telecom_record_site_incident',
                 30000,
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-recordSiteIncident-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-scheduleMaintenance-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.scheduleMaintenance',
                 'telecom_schedule_maintenance',
                 30000,
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-scheduleMaintenance-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-requestRma-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.requestRma',
                 'telecom_request_rma',
                 30000,
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-requestRma-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-auditPerformanceCounters-v1',
                 'did:web:telecom.etzhayyim.com',
                 'app.etzhayyim.apps.telecom.auditPerformanceCounters',
                 'telecom_audit_performance_counters',
                 15000,
                 '2026-04-27T12:01:00Z',
                 'did:web:telecom.etzhayyim.com',
                 'did:web:telecom.etzhayyim.com',
                 'sys.bpmn.seed.telecom-resource',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-auditPerformanceCounters-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerSpectrumLicense-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerCellSite-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerRanNode-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-registerNetworkAsset-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-recordSiteIncident-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-scheduleMaintenance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-requestRma-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/telecom-auditPerformanceCounters-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-spectrum-license-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-cell-site-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-ran-node-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-register-network-asset-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-record-site-incident-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-schedule-maintenance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-request-rma-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/telecom-audit-performance-counters-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
