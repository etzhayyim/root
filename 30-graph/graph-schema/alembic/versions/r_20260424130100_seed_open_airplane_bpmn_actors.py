"""Captured from Kysely migration 20260424130100_seed_open_airplane_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424130100_seed_open_airplane_bpmn_actors"
down_revision = 'r_20260424130000_vertex_open_airplane'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-airplane-schedule-flight-v1',
                 'did:web:open-airplane.etzhayyim.com:ops',
                 'open_airplane_schedule_flight',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_airplane_schedule_flight"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-airplane"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_airplane_schedule_flight" name="便 登録" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_SaveFlight"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveFlight" name="flight 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_airplane_flight&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        vertexId,\n'
                 '              operator_org_id:  operatorOrgId,\n'
                 '              aircraft_vid:     aircraftVid,\n'
                 '              origin_vid:       originVid,\n'
                 '              destination_vid:  destinationVid,\n'
                 '              flight_number:    flightNumber,\n'
                 '              scheduled_off:    scheduledOff,\n'
                 '              scheduled_in:     scheduledIn,\n'
                 '              status:           &quot;scheduled&quot;,\n'
                 '              created_at:       string(now()),\n'
                 '              owner_did:        callerDid,\n'
                 '              sensitivity_ord:  1,\n'
                 '              org_id:           operatorOrgId,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-airplane&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_EdgeO</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EdgeO" sourceRef="Task_SaveFlight" '
                 'targetRef="Task_EdgeOrigin"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EdgeOrigin" name="route edge (origin)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_airplane_flight_route&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id:   string(vertexId) + &quot;:origin&quot;,\n'
                 '              src_vid:   vertexId,\n'
                 '              dst_vid:   originVid,\n'
                 '              role:      &quot;origin&quot;,\n'
                 '              created_at: string(now()),\n'
                 '              owner_did: callerDid,\n'
                 '              sensitivity_ord: 1,\n'
                 '              org_id:    operatorOrgId,\n'
                 '              user_id:   callerDid,\n'
                 '              actor_id:  &quot;sys.bpmn.open-airplane&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_EdgeO</bpmn:incoming><bpmn:outgoing>Flow_EdgeD</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EdgeD" sourceRef="Task_EdgeOrigin" '
                 'targetRef="Task_EdgeDest"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EdgeDest" name="route edge (destination)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_airplane_flight_route&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id:   string(vertexId) + &quot;:destination&quot;,\n'
                 '              src_vid:   vertexId,\n'
                 '              dst_vid:   destinationVid,\n'
                 '              role:      &quot;destination&quot;,\n'
                 '              created_at: string(now()),\n'
                 '              owner_did: callerDid,\n'
                 '              sensitivity_ord: 1,\n'
                 '              org_id:    operatorOrgId,\n'
                 '              user_id:   callerDid,\n'
                 '              actor_id:  &quot;sys.bpmn.open-airplane&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_EdgeD</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_EdgeDest" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit flight.schedule">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-airplane.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openAirplane.flight.schedule&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertexId:      vertexId,\n'
                 '              operatorOrgId: operatorOrgId,\n'
                 '              flightNumber:  flightNumber,\n'
                 '              originVid:     originVid,\n'
                 '              destinationVid: destinationVid\n'
                 '          }" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5287,
                 '00-contracts/bpmn/ai/gftd/open-airplane/scheduleFlight.bpmn',
                 '2026-04-24T13:30:00Z',
                 'did:web:open-airplane.etzhayyim.com:ops',
                 'did:web:open-airplane.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-airplane',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-airplane-schedule-flight-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-airplane-report-incident-v1',
                 'did:web:open-airplane.etzhayyim.com:ops',
                 'open_airplane_report_incident',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_airplane_report_incident"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/open-airplane"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_airplane_report_incident" name="事故 報告" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Classify"/>\n'
                 '\n'
                 '    <!--\n'
                 '      severity: fatal (inj>=1 OR category in '
                 '{runway-excursion,collision,hull-loss})\n'
                 '                serious (inj<=0 AND category in '
                 '{bird-strike,engine-failure,turbulence-injury})\n'
                 '                minor (otherwise)\n'
                 '      requirePublicNotice = severity != "minor"\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Classify" name="severity 分類">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT 1 AS ok LIMIT 1&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=if injuries &gt;= 1 or list '
                 'contains([&quot;runway-excursion&quot;,&quot;collision&quot;,&quot;hull-loss&quot;], '
                 'category) then &quot;fatal&quot;\n'
                 '                                else if list '
                 'contains([&quot;bird-strike&quot;,&quot;engine-failure&quot;,&quot;turbulence-injury&quot;], '
                 'category) then &quot;serious&quot;\n'
                 '                                else &quot;minor&quot;" target="severity"/>\n'
                 '          <zeebe:output source="=injuries &gt;= 1 or list '
                 'contains([&quot;runway-excursion&quot;,&quot;collision&quot;,&quot;hull-loss&quot;,&quot;bird-strike&quot;,&quot;engine-failure&quot;,&quot;turbulence-injury&quot;], '
                 'category)" target="requirePublicNotice"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_Save</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Task_Classify" '
                 'targetRef="Task_SaveIncident"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SaveIncident" name="incident 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_airplane_incident&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:             vertexId,\n'
                 '              operator_org_id:       operatorOrgId,\n'
                 '              aircraft_vid:          aircraftVid,\n'
                 '              flight_vid:            flightVid,\n'
                 '              category:              category,\n'
                 '              narrative:             narrative,\n'
                 '              injuries:              injuries,\n'
                 '              severity:              severity,\n'
                 '              require_public_notice: requirePublicNotice,\n'
                 '              status:                &quot;open&quot;,\n'
                 '              reported_at:           reportedAt,\n'
                 '              created_at:            string(now()),\n'
                 '              owner_did:             callerDid,\n'
                 '              sensitivity_ord:       1,\n'
                 '              org_id:                operatorOrgId,\n'
                 '              user_id:               callerDid,\n'
                 '              actor_id:              &quot;sys.bpmn.open-airplane&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Gate" sourceRef="Task_SaveIncident" '
                 'targetRef="Gate"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gate" name="公衆周知?" default="Flow_Silent">\n'
                 '      <bpmn:incoming>Flow_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Notice</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Silent</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Notice" sourceRef="Gate" '
                 'targetRef="Task_Notice">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=requirePublicNotice = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Silent" sourceRef="Gate" '
                 'targetRef="Task_AuditSilent"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Notice" name="公衆周知 post">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.pds.dispatch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;app.bsky.feed.post&quot;" target="type"/>\n'
                 '          <zeebe:input source="={\n'
                 '              text: &quot;[open-airplane] incident: aircraft=&quot; + '
                 'string(aircraftVid)\n'
                 '                    + &quot; severity=&quot; + string(severity)\n'
                 '                    + &quot; category=&quot; + string(category),\n'
                 '              createdAt: string(now())\n'
                 '          }" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Notice</bpmn:incoming><bpmn:outgoing>Flow_AM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AM" sourceRef="Task_Notice" '
                 'targetRef="Task_AuditMajor"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditMajor" name="audit incident.notice">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-airplane.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openAirplane.incident.publicNotice&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, severity: severity, '
                 'aircraftVid: aircraftVid}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_AM</bpmn:incoming><bpmn:outgoing>Flow_EndM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EndM" sourceRef="Task_AuditMajor" '
                 'targetRef="End_M"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditSilent" name="audit incident.log">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-airplane.etzhayyim.com:ops&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openAirplane.incident.log&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, severity: severity, '
                 'aircraftVid: aircraftVid}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Silent</bpmn:incoming><bpmn:outgoing>Flow_EndS</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_EndS" sourceRef="Task_AuditSilent" '
                 'targetRef="End_S"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End_S"><bpmn:incoming>Flow_EndS</bpmn:incoming></bpmn:endEvent>\n'
                 '    <bpmn:endEvent '
                 'id="End_M"><bpmn:incoming>Flow_EndM</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 6882,
                 '00-contracts/bpmn/ai/gftd/open-airplane/reportIncident.bpmn',
                 '2026-04-24T13:30:00Z',
                 'did:web:open-airplane.etzhayyim.com:ops',
                 'did:web:open-airplane.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-airplane',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-airplane-report-incident-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-airplane-scheduleFlight-v1',
                 'did:web:open-airplane.etzhayyim.com:ops',
                 'ai.gftd.apps.openAirplane.scheduleFlight',
                 'open_airplane_schedule_flight',
                 15000,
                 '2026-04-24T13:30:00Z',
                 'did:web:open-airplane.etzhayyim.com:ops',
                 'did:web:open-airplane.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-airplane',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-airplane-scheduleFlight-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-airplane-reportIncident-v1',
                 'did:web:open-airplane.etzhayyim.com:ops',
                 'ai.gftd.apps.openAirplane.reportIncident',
                 'open_airplane_report_incident',
                 30000,
                 '2026-04-24T13:30:00Z',
                 'did:web:open-airplane.etzhayyim.com:ops',
                 'did:web:open-airplane.etzhayyim.com:ops',
                 'sys.bpmn.seed.open-airplane',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-airplane-reportIncident-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-airplane-scheduleFlight-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-airplane-reportIncident-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-airplane-schedule-flight-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-airplane-report-incident-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
