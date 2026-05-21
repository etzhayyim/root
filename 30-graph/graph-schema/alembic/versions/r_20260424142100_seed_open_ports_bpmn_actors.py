"""Captured from Kysely migration 20260424142100_seed_open_ports_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424142100_seed_open_ports_bpmn_actors"
down_revision = 'r_20260424142000_vertex_open_ports'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-ports-schedule-vessel-call-v1',
                 'did:web:open-ports.etzhayyim.com:ops',
                 'open_ports_schedule_vessel_call',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_ports_schedule_vessel_call"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-ports"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_ports_schedule_vessel_call" name="船舶寄港 登録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="call 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_ports_vessel_call&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, authority_org_id: authorityOrgId,\n'
                 '              port_vid: portVid, vessel_vid: vesselVid, berth_label: '
                 'berthLabel,\n'
                 '              eta: eta, etd: etd, purpose: purpose, status: '
                 '&quot;scheduled&quot;,\n'
                 '              created_at: string(now()), owner_did: callerDid, sensitivity_ord: '
                 '1,\n'
                 '              org_id: authorityOrgId, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-ports&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_EP</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EP" sourceRef="Task_Save" '
                 'targetRef="Task_EdgePort"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EdgePort" name="edge (port)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_ports_call_endpoint&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id: string(vertexId) + &quot;:port&quot;,\n'
                 '              src_vid: vertexId, dst_vid: portVid, role: &quot;port&quot;,\n'
                 '              created_at: string(now()), owner_did: callerDid, sensitivity_ord: '
                 '1,\n'
                 '              org_id: authorityOrgId, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-ports&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_EP</bpmn:incoming><bpmn:outgoing>Flow_EV</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EV" sourceRef="Task_EdgePort" '
                 'targetRef="Task_EdgeVessel"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EdgeVessel" name="edge (vessel)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_ports_call_endpoint&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id: string(vertexId) + &quot;:vessel&quot;,\n'
                 '              src_vid: vertexId, dst_vid: vesselVid, role: &quot;vessel&quot;,\n'
                 '              created_at: string(now()), owner_did: callerDid, sensitivity_ord: '
                 '1,\n'
                 '              org_id: authorityOrgId, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-ports&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_EV</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_EdgeVessel" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit call.schedule">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-ports.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openPorts.call.schedule&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, portVid: portVid, '
                 'vesselVid: vesselVid, eta: eta, etd: etd}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4558,
                 '00-contracts/bpmn/ai/gftd/open-ports/scheduleVesselCall.bpmn',
                 '2026-04-24T14:30:00Z',
                 'did:web:open-ports.etzhayyim.com:ops',
                 'did:web:open-ports.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-ports',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-ports-schedule-vessel-call-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-ports-report-incident-v1',
                 'did:web:open-ports.etzhayyim.com:ops',
                 'open_ports_report_incident',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_ports_report_incident"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-ports"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_ports_report_incident" name="港湾事故 報告" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Classify"/>\n'
                 '\n'
                 '    <!--\n'
                 '      major   : category = collision OR spillVolumeTonnes >= 7 (MARPOL '
                 'notifiable)\n'
                 '      moderate: category = spill OR fire\n'
                 '      minor   : otherwise\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Classify" name="severity 分類">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if category = &quot;collision&quot; or '
                 'spillVolumeTonnes &gt;= 7 then &quot;major&quot;\n'
                 '                                else if list '
                 'contains([&quot;spill&quot;,&quot;fire&quot;], category) then '
                 '&quot;moderate&quot;\n'
                 '                                else &quot;minor&quot;" target="severity"/>\n'
                 '          <zeebe:output source="=category = &quot;collision&quot; or '
                 'spillVolumeTonnes &gt;= 7" target="requirePublicNotice"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="incident 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_ports_incident&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: vertexId, authority_org_id: authorityOrgId,\n'
                 '              port_vid: portVid, vessel_vid: vesselVid, call_vid: callVid,\n'
                 '              category: category, narrative: narrative, spill_volume_tonnes: '
                 'spillVolumeTonnes,\n'
                 '              severity: severity, require_public_notice: requirePublicNotice,\n'
                 '              status: &quot;open&quot;, reported_at: reportedAt, created_at: '
                 'string(now()),\n'
                 '              owner_did: callerDid, sensitivity_ord: 1,\n'
                 '              org_id: authorityOrgId, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-ports&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_Save" targetRef="Gate"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gate" default="Flow_Silent">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Notice</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Silent</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Notice" sourceRef="Gate" '
                 'targetRef="Task_AuditMajor">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=requirePublicNotice = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Silent" sourceRef="Gate" '
                 'targetRef="Task_AuditSilent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditMajor" name="audit incident.major">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-ports.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openPorts.incident.major&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, severity: severity, '
                 'portVid: portVid, category: category}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Notice</bpmn:incoming><bpmn:outgoing>Flow_EM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EM" sourceRef="Task_AuditMajor" '
                 'targetRef="End_M"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditSilent" name="audit incident.log">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-ports.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openPorts.incident.log&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, severity: severity, '
                 'portVid: portVid, category: category}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Silent</bpmn:incoming><bpmn:outgoing>Flow_ES</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ES" sourceRef="Task_AuditSilent" '
                 'targetRef="End_S"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_S"><bpmn:incoming>Flow_ES</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_M"><bpmn:incoming>Flow_EM</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5330,
                 '00-contracts/bpmn/ai/gftd/open-ports/reportIncident.bpmn',
                 '2026-04-24T14:30:00Z',
                 'did:web:open-ports.etzhayyim.com:ops',
                 'did:web:open-ports.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-ports',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-ports-report-incident-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-ports-scheduleVesselCall-v1',
                 'did:web:open-ports.etzhayyim.com:ops',
                 'ai.gftd.apps.openPorts.scheduleVesselCall',
                 'open_ports_schedule_vessel_call',
                 15000,
                 '2026-04-24T14:30:00Z',
                 'did:web:open-ports.etzhayyim.com:ops',
                 'did:web:open-ports.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-ports',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-ports-scheduleVesselCall-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-ports-reportIncident-v1',
                 'did:web:open-ports.etzhayyim.com:ops',
                 'ai.gftd.apps.openPorts.reportIncident',
                 'open_ports_report_incident',
                 30000,
                 '2026-04-24T14:30:00Z',
                 'did:web:open-ports.etzhayyim.com:ops',
                 'did:web:open-ports.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-ports',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-ports-reportIncident-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-ports-scheduleVesselCall-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-ports-reportIncident-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-ports-schedule-vessel-call-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-ports-report-incident-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
