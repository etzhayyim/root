"""Captured from Kysely migration 20260507700000_seed_airline_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507700000_seed_airline_bpmn"
down_revision = 'r_20260507690000_air_ffp_schema'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2188, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-register-schedule-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'air_sched_register_schedule',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sched_register_schedule" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sched" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sched_register_schedule" name="registerSchedule" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="register schedule">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sched.schedule.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, carrierCode: carrierCode, '
                 'origin: origin, dest: dest, depTime: depTime, arrTime: arrTime, aircraftType: '
                 'aircraftType, effectiveDate: effectiveDate, season: season, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=scheduleId" target="scheduleId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sched.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sched.schedule.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, scheduleId: scheduleId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sched/registerSchedule.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-register-schedule-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-register-schedule-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'com.etzhayyim.apps.airSched.registerSchedule',
                 'air_sched_register_schedule',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-register-schedule-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2110, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-request-slot-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'air_sched_request_slot',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sched_request_slot" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sched" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sched_request_slot" name="requestSlot" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="request slot">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sched.slot.request"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={airport: airport, slotDate: slotDate, slotTime: '
                 'slotTime, movementType: movementType, carrierCode: carrierCode, flightNo: '
                 'flightNo, season: season, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=slotRef" target="slotRef"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sched.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sched.slot.request&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, slotRef: slotRef, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sched/requestSlot.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-request-slot-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-request-slot-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'com.etzhayyim.apps.airSched.requestSlot',
                 'air_sched_request_slot',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-request-slot-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2082, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-allocate-slot-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'air_sched_allocate_slot',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sched_allocate_slot" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sched" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sched_allocate_slot" name="allocateSlot" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="allocate slot">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sched.slot.allocate"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={slotRef: slotRef, airport: airport, '
                 'allocatedTime: allocatedTime, status: status, coordinatorRef: coordinatorRef, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=slotRef" target="slotRef"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sched.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sched.slot.allocate&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, slotRef: slotRef, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sched/allocateSlot.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-allocate-slot-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-allocate-slot-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'com.etzhayyim.apps.airSched.allocateSlot',
                 'air_sched_allocate_slot',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-allocate-slot-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2170, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-assign-fleet-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'air_sched_assign_fleet',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sched_assign_fleet" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sched" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sched_assign_fleet" name="assignFleet" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="assign fleet">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sched.fleet.assign"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={scheduleId: scheduleId, aircraftType: '
                 'aircraftType, aircraftReg: aircraftReg, effectiveDate: effectiveDate, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=scheduleId" target="scheduleId"/><zeebe:output source="=aircraftType" '
                 'target="aircraftType"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sched.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sched.fleet.assign&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, scheduleId: scheduleId, aircraftType: '
                 'aircraftType, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-sched/assignFleet.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-assign-fleet-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-assign-fleet-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'com.etzhayyim.apps.airSched.assignFleet',
                 'air_sched_assign_fleet',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-assign-fleet-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2196, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-publish-schedule-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'air_sched_publish_schedule',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sched_publish_schedule" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sched" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sched_publish_schedule" name="publishSchedule" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="publish schedule">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sched.schedule.publish"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={scheduleId: scheduleId, distributeToGds: '
                 'distributeToGds, ssimVersion: ssimVersion, effectiveDate: effectiveDate, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=scheduleId" target="scheduleId"/><zeebe:output source="=publishedAt" '
                 'target="publishedAt"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sched.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sched.schedule.publish&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, scheduleId: scheduleId, publishedAt: publishedAt, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sched/publishSchedule.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-publish-schedule-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-publish-schedule-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'com.etzhayyim.apps.airSched.publishSchedule',
                 'air_sched_publish_schedule',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-publish-schedule-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2134, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-assign-gate-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'air_sched_assign_gate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sched_assign_gate" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sched" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sched_assign_gate" name="assignGate" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="assign gate">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sched.gate.assign"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, depDate: depDate, gate: '
                 'gate, tobt: tobt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=flightNo" target="flightNo"/><zeebe:output source="=gate" '
                 'target="gate"/><zeebe:output source="=tobt" target="tobt"/><zeebe:output '
                 'source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sched.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sched.gate.assign&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, flightNo: flightNo, gate: gate, tobt: tobt, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sched/assignGate.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-assign-gate-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-assign-gate-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'com.etzhayyim.apps.airSched.assignGate',
                 'air_sched_assign_gate',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-assign-gate-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2104, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-change-frequency-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'air_sched_change_frequency',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sched_change_frequency" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sched" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sched_change_frequency" name="changeFrequency" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="change frequency">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sched.frequency.change"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={scheduleId: scheduleId, newFrequencyDays: '
                 'newFrequencyDays, effectiveDate: effectiveDate, season: season, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=scheduleId" target="scheduleId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sched.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sched.frequency.change&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, scheduleId: scheduleId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sched/changeFrequency.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-change-frequency-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-change-frequency-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'com.etzhayyim.apps.airSched.changeFrequency',
                 'air_sched_change_frequency',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-change-frequency-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2192, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-register-codeshare-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'air_sched_register_codeshare',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sched_register_codeshare" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sched" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sched_register_codeshare" name="registerCodeshare" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="register codeshare">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sched.codeshare.register"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={operatingCarrier: operatingCarrier, '
                 'marketingCarrier: marketingCarrier, operatingFlightNo: operatingFlightNo, '
                 'marketingFlightNo: marketingFlightNo, effectiveDate: effectiveDate, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=codeshareId" target="codeshareId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sched.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sched.codeshare.register&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, codeshareId: codeshareId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sched/registerCodeshare.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-register-codeshare-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-register-codeshare-v1',
                 'did:web:air-sched.etzhayyim.com',
                 'com.etzhayyim.apps.airSched.registerCodeshare',
                 'air_sched_register_codeshare',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sched.etzhayyim.com',
                 'did:web:air-sched.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sched.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-register-codeshare-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2102, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-create-pnr-v1',
                 'did:web:air-book.etzhayyim.com',
                 'air_book_create_pnr',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_book_create_pnr" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-book" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_book_create_pnr" name="createPnr" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="create pnr">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.book.pnr.create"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={origin: origin, dest: dest, depDate: depDate, '
                 'paxCount: paxCount, carrierCode: carrierCode, flightNo: flightNo, cabinClass: '
                 'cabinClass, bookingSource: bookingSource, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=pnrId" target="pnrId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-book.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.book.pnr.create&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, pnrId: pnrId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-book/createPnr.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-create-pnr-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-create-pnr-v1',
                 'did:web:air-book.etzhayyim.com',
                 'com.etzhayyim.apps.airBook.createPnr',
                 'air_book_create_pnr',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-create-pnr-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2130, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-confirm-booking-v1',
                 'did:web:air-book.etzhayyim.com',
                 'air_book_confirm_booking',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_book_confirm_booking" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-book" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_book_confirm_booking" name="confirmBooking" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="confirm booking">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.book.booking.confirm"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={pnrId: pnrId, paymentRef: paymentRef, '
                 'totalFare: totalFare, currency: currency, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=pnrId" target="pnrId"/><zeebe:output source="=confirmedAt" '
                 'target="confirmedAt"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-book.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.book.booking.confirm&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, pnrId: pnrId, confirmedAt: confirmedAt, status: '
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
                 '00-contracts/bpmn/com/etzhayyim/air-book/confirmBooking.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-confirm-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-confirm-booking-v1',
                 'did:web:air-book.etzhayyim.com',
                 'com.etzhayyim.apps.airBook.confirmBooking',
                 'air_book_confirm_booking',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-confirm-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2092, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-issue-ticket-v1',
                 'did:web:air-book.etzhayyim.com',
                 'air_book_issue_ticket',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_book_issue_ticket" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-book" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_book_issue_ticket" name="issueTicket" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="issue ticket">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.book.ticket.issue"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={pnrId: pnrId, fareBasis: fareBasis, ticketType: '
                 'ticketType, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=ticketNo" target="ticketNo"/><zeebe:output source="=issuedAt" '
                 'target="issuedAt"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-book.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.book.ticket.issue&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, ticketNo: ticketNo, issuedAt: issuedAt, status: '
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
                 '00-contracts/bpmn/com/etzhayyim/air-book/issueTicket.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-issue-ticket-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-issue-ticket-v1',
                 'did:web:air-book.etzhayyim.com',
                 'com.etzhayyim.apps.airBook.issueTicket',
                 'air_book_issue_ticket',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-issue-ticket-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2060, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-assign-seat-v1',
                 'did:web:air-book.etzhayyim.com',
                 'air_book_assign_seat',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_book_assign_seat" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-book" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_book_assign_seat" name="assignSeat" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="assign seat">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.book.seat.assign"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={pnrId: pnrId, seatNo: seatNo, cabinClass: '
                 'cabinClass, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=pnrId" target="pnrId"/><zeebe:output source="=seatNo" '
                 'target="seatNo"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-book.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.book.seat.assign&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, pnrId: pnrId, seatNo: seatNo, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-book/assignSeat.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-assign-seat-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-assign-seat-v1',
                 'did:web:air-book.etzhayyim.com',
                 'com.etzhayyim.apps.airBook.assignSeat',
                 'air_book_assign_seat',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-assign-seat-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2084, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-add-ancillary-v1',
                 'did:web:air-book.etzhayyim.com',
                 'air_book_add_ancillary',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_book_add_ancillary" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-book" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_book_add_ancillary" name="addAncillary" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="add ancillary">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.book.ancillary.add"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={pnrId: pnrId, ancillaryType: ancillaryType, '
                 'description: description, amount: amount, currency: currency, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=ancillaryId" target="ancillaryId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-book.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.book.ancillary.add&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, ancillaryId: ancillaryId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-book/addAncillary.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-add-ancillary-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-add-ancillary-v1',
                 'did:web:air-book.etzhayyim.com',
                 'com.etzhayyim.apps.airBook.addAncillary',
                 'air_book_add_ancillary',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-add-ancillary-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2134, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-cancel-booking-v1',
                 'did:web:air-book.etzhayyim.com',
                 'air_book_cancel_booking',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_book_cancel_booking" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-book" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_book_cancel_booking" name="cancelBooking" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="cancel booking">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.book.booking.cancel"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={pnrId: pnrId, cancelReason: cancelReason, '
                 'refundAmount: refundAmount, currency: currency, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=pnrId" target="pnrId"/><zeebe:output source="=cancelledAt" '
                 'target="cancelledAt"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-book.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.book.booking.cancel&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, pnrId: pnrId, cancelledAt: cancelledAt, status: '
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
                 '00-contracts/bpmn/com/etzhayyim/air-book/cancelBooking.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-cancel-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-cancel-booking-v1',
                 'did:web:air-book.etzhayyim.com',
                 'com.etzhayyim.apps.airBook.cancelBooking',
                 'air_book_cancel_booking',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-cancel-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2120, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-reprotect-passenger-v1',
                 'did:web:air-book.etzhayyim.com',
                 'air_book_reprotect_passenger',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_book_reprotect_passenger" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-book" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_book_reprotect_passenger" name="reprotectPassenger" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="reprotect passenger">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.book.irrop.reprotect"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={pnrId: pnrId, originalFlightNo: '
                 'originalFlightNo, newFlightNo: newFlightNo, newDepDate: newDepDate, irropReason: '
                 'irropReason, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=newPnrId" target="newPnrId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-book.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.book.irrop.reprotect&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, newPnrId: newPnrId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-book/reprotectPassenger.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-reprotect-passenger-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-reprotect-passenger-v1',
                 'did:web:air-book.etzhayyim.com',
                 'com.etzhayyim.apps.airBook.reprotectPassenger',
                 'air_book_reprotect_passenger',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-reprotect-passenger-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2132, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-settle-bsp-v1',
                 'did:web:air-book.etzhayyim.com',
                 'air_book_settle_bsp',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_book_settle_bsp" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-book" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_book_settle_bsp" name="settleBsp" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="settle bsp">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.book.bsp.settle"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={period: period, carrierCode: carrierCode, '
                 'totalAmount: totalAmount, currency: currency, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=settlementRef" target="settlementRef"/><zeebe:output '
                 'source="=settledAt" target="settledAt"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-book.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.book.bsp.settle&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, settlementRef: settlementRef, settledAt: '
                 'settledAt, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-book/settleBsp.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-settle-bsp-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-settle-bsp-v1',
                 'did:web:air-book.etzhayyim.com',
                 'com.etzhayyim.apps.airBook.settleBsp',
                 'air_book_settle_bsp',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-book.etzhayyim.com',
                 'did:web:air-book.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-book.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-settle-bsp-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2191, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-publish-fare-class-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'air_yield_publish_fare_class',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_yield_publish_fare_class" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-yield" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_yield_publish_fare_class" name="publishFareClass" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="publish fare class">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.yield.fare_class.publish"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, carrierCode: carrierCode, '
                 'depDate: depDate, cabin: cabin, classCode: classCode, seatsAvailable: '
                 'seatsAvailable, protectionLevel: protectionLevel, bidPrice: bidPrice, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=classCode" target="classCode"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-yield.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.yield.fare_class.publish&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, classCode: classCode, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-yield/publishFareClass.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-publish-fare-class-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-publish-fare-class-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'com.etzhayyim.apps.airYield.publishFareClass',
                 'air_yield_publish_fare_class',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-publish-fare-class-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2214, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-adjust-inventory-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'air_yield_adjust_inventory',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_yield_adjust_inventory" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-yield" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_yield_adjust_inventory" name="adjustInventory" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="adjust inventory">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.yield.inventory.adjust"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, carrierCode: carrierCode, '
                 'depDate: depDate, loadFactor: loadFactor, bidPrice: bidPrice, adjustmentReason: '
                 'adjustmentReason, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=flightNo" target="flightNo"/><zeebe:output source="=loadFactor" '
                 'target="loadFactor"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-yield.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.yield.inventory.adjust&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, flightNo: flightNo, loadFactor: loadFactor, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-yield/adjustInventory.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-adjust-inventory-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-adjust-inventory-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'com.etzhayyim.apps.airYield.adjustInventory',
                 'air_yield_adjust_inventory',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-adjust-inventory-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2192, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-file-fare-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'air_yield_file_fare',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_yield_file_fare" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-yield" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_yield_file_fare" name="fileFare" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="file fare">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.yield.fare.file"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={fareBasis: fareBasis, origin: origin, dest: '
                 'dest, carrierCode: carrierCode, amount: amount, currency: currency, cabin: '
                 'cabin, ruleNo: ruleNo, effectiveDate: effectiveDate, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=fareBasis" target="fareBasis"/><zeebe:output source="=filedAt" '
                 'target="filedAt"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-yield.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.yield.fare.file&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, fareBasis: fareBasis, filedAt: filedAt, status: '
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
                 '00-contracts/bpmn/com/etzhayyim/air-yield/fileFare.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-file-fare-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-file-fare-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'com.etzhayyim.apps.airYield.fileFare',
                 'air_yield_file_fare',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-file-fare-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2168, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-set-overbooking-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'air_yield_set_overbooking',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_yield_set_overbooking" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-yield" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_yield_set_overbooking" name="setOverbooking" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="set overbooking">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.yield.overbooking.set"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, carrierCode: carrierCode, '
                 'depDate: depDate, obFactor: obFactor, authorizedBy: authorizedBy, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=flightNo" target="flightNo"/><zeebe:output source="=obFactor" '
                 'target="obFactor"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-yield.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.yield.overbooking.set&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, flightNo: flightNo, obFactor: obFactor, status: '
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
                 '00-contracts/bpmn/com/etzhayyim/air-yield/setOverbooking.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-set-overbooking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-set-overbooking-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'com.etzhayyim.apps.airYield.setOverbooking',
                 'air_yield_set_overbooking',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-set-overbooking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2233, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-process-group-booking-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'air_yield_process_group_booking',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_yield_process_group_booking" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-yield" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_yield_process_group_booking" name="processGroupBooking" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="process group booking">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.yield.group.process"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={origin: origin, dest: dest, depDate: depDate, '
                 'carrierCode: carrierCode, groupSize: groupSize, fareBasis: fareBasis, '
                 'contactName: contactName, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=groupId" target="groupId"/><zeebe:output source="=allotmentCode" '
                 'target="allotmentCode"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-yield.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.yield.group.process&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, groupId: groupId, allotmentCode: allotmentCode, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-yield/processGroupBooking.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-process-group-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-process-group-booking-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'com.etzhayyim.apps.airYield.processGroupBooking',
                 'air_yield_process_group_booking',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-process-group-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2233, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-apply-dynamic-price-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'air_yield_apply_dynamic_price',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_yield_apply_dynamic_price" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-yield" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_yield_apply_dynamic_price" name="applyDynamicPrice" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="apply dynamic price">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.yield.price.dynamic"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, carrierCode: carrierCode, '
                 'depDate: depDate, classCode: classCode, newAmount: newAmount, currency: '
                 'currency, triggerReason: triggerReason, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=classCode" target="classCode"/><zeebe:output source="=newAmount" '
                 'target="newAmount"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-yield.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.yield.price.dynamic&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, classCode: classCode, newAmount: newAmount, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-yield/applyDynamicPrice.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-apply-dynamic-price-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-apply-dynamic-price-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'com.etzhayyim.apps.airYield.applyDynamicPrice',
                 'air_yield_apply_dynamic_price',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-apply-dynamic-price-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2291, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-generate-revenue-report-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'air_yield_generate_revenue_report',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_yield_generate_revenue_report" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-yield" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_yield_generate_revenue_report" '
                 'name="generateRevenueReport" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="generate revenue report">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.yield.revenue.report"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={period: period, carrierCode: carrierCode, '
                 'origin: origin, dest: dest, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=rask" target="rask"/><zeebe:output source="=cask" '
                 'target="cask"/><zeebe:output source="=loadFactor" '
                 'target="loadFactor"/><zeebe:output source="=totalRevenue" '
                 'target="totalRevenue"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-yield.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.yield.revenue.report&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, rask: rask, cask: cask, loadFactor: loadFactor, '
                 'totalRevenue: totalRevenue, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-yield/generateRevenueReport.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-generate-revenue-report-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-generate-revenue-report-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'com.etzhayyim.apps.airYield.generateRevenueReport',
                 'air_yield_generate_revenue_report',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-generate-revenue-report-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2168, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-forecast-demand-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'air_yield_forecast_demand',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_yield_forecast_demand" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-yield" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_yield_forecast_demand" name="forecastDemand" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="forecast demand">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.yield.demand.forecast"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, carrierCode: carrierCode, '
                 'depDate: depDate, modelVersion: modelVersion, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=forecastPax" target="forecastPax"/><zeebe:output source="=confidence" '
                 'target="confidence"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-yield.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.yield.demand.forecast&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, forecastPax: forecastPax, confidence: confidence, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-yield/forecastDemand.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-forecast-demand-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-forecast-demand-v1',
                 'did:web:air-yield.etzhayyim.com',
                 'com.etzhayyim.apps.airYield.forecastDemand',
                 'air_yield_forecast_demand',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-yield.etzhayyim.com',
                 'did:web:air-yield.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-yield.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-forecast-demand-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2143, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-process-check-in-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'air_dcs_process_check_in',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_dcs_process_checkin" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-dcs" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_dcs_process_checkin" name="processCheckIn" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="process check-in">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.dcs.checkin.process"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={pnrIdHash: pnrIdHash, flightNo: flightNo, '
                 'depDate: depDate, channel: channel, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=boardingPassRef" target="boardingPassRef"/><zeebe:output '
                 'source="=seatNo" target="seatNo"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-dcs.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.dcs.checkin.process&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, boardingPassRef: boardingPassRef, seatNo: seatNo, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-dcs/processCheckIn.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-process-check-in-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-process-check-in-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'com.etzhayyim.apps.airDcs.processCheckIn',
                 'air_dcs_process_check_in',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-process-check-in-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2151, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-process-boarding-pass-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'air_dcs_process_boarding_pass',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_dcs_process_boarding_pass" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-dcs" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_dcs_process_boarding_pass" name="processBoardingPass" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="process boarding pass">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.dcs.boarding_pass.process"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={pnrIdHash: pnrIdHash, flightNo: flightNo, '
                 'depDate: depDate, gate: gate, boardingTime: boardingTime, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=boardingPassBarcode" target="boardingPassBarcode"/><zeebe:output '
                 'source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-dcs.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.dcs.boarding_pass.process&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId, boardingPassBarcode: '
                 'boardingPassBarcode, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-dcs/processBoardingPass.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-process-boarding-pass-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-process-boarding-pass-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'com.etzhayyim.apps.airDcs.processBoardingPass',
                 'air_dcs_process_boarding_pass',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-process-boarding-pass-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2060, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-accept-baggage-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'air_dcs_accept_baggage',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_dcs_accept_baggage" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-dcs" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_dcs_accept_baggage" name="acceptBaggage" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="accept baggage">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.dcs.baggage.accept"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={pnrIdHash: pnrIdHash, flightNo: flightNo, '
                 'depDate: depDate, weightKg: weightKg, destination: destination, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=tagNo" target="tagNo"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-dcs.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.dcs.baggage.accept&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, tagNo: tagNo, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-dcs/acceptBaggage.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-accept-baggage-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-accept-baggage-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'com.etzhayyim.apps.airDcs.acceptBaggage',
                 'air_dcs_accept_baggage',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-accept-baggage-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2100, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-reconcile-baggage-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'air_dcs_reconcile_baggage',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_dcs_reconcile_baggage" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-dcs" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_dcs_reconcile_baggage" name="reconcileBaggage" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="reconcile baggage">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.dcs.baggage.reconcile"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, depDate: depDate, tagNo: '
                 'tagNo, status: status, lastSeenAt: lastSeenAt, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=tagNo" target="tagNo"/><zeebe:output source="=reconcileStatus" '
                 'target="reconcileStatus"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-dcs.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.dcs.baggage.reconcile&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, tagNo: tagNo, reconcileStatus: reconcileStatus}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-dcs/reconcileBaggage.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-reconcile-baggage-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-reconcile-baggage-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'com.etzhayyim.apps.airDcs.reconcileBaggage',
                 'air_dcs_reconcile_baggage',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-reconcile-baggage-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2215, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-compute-load-sheet-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'air_dcs_compute_load_sheet',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_dcs_compute_load_sheet" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-dcs" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_dcs_compute_load_sheet" name="computeLoadSheet" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="compute load sheet">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.dcs.load_sheet.compute"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, depDate: depDate, totalPax: '
                 'totalPax, totalCargoKg: totalCargoKg, fuelKg: fuelKg, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=zfwKg" target="zfwKg"/><zeebe:output source="=towKg" '
                 'target="towKg"/><zeebe:output source="=lmcStatus" '
                 'target="lmcStatus"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-dcs.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.dcs.load_sheet.compute&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, zfwKg: zfwKg, towKg: towKg, lmcStatus: lmcStatus, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-dcs/computeLoadSheet.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-compute-load-sheet-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-compute-load-sheet-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'com.etzhayyim.apps.airDcs.computeLoadSheet',
                 'air_dcs_compute_load_sheet',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-compute-load-sheet-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2086, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-transmit-apis-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'air_dcs_transmit_apis',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_dcs_transmit_apis" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-dcs" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_dcs_transmit_apis" name="transmitApis" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="transmit apis">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.dcs.apis.transmit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, depDate: depDate, '
                 'destCountry: destCountry, paxManifestHash: paxManifestHash, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=transmissionRef" target="transmissionRef"/><zeebe:output '
                 'source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-dcs.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.dcs.apis.transmit&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, transmissionRef: transmissionRef, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-dcs/transmitApis.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-transmit-apis-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-transmit-apis-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'com.etzhayyim.apps.airDcs.transmitApis',
                 'air_dcs_transmit_apis',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-transmit-apis-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2224, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-track-turnaround-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'air_dcs_track_turnaround',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_dcs_track_turnaround" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-dcs" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_dcs_track_turnaround" name="trackTurnaround" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="track turnaround">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.dcs.turnaround.track"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, depDate: depDate, '
                 'milestone: milestone, milestoneTime: milestoneTime, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=milestone" target="milestone"/><zeebe:output source="=targetTime" '
                 'target="targetTime"/><zeebe:output source="=variance" '
                 'target="variance"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-dcs.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.dcs.turnaround.track&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, milestone: milestone, targetTime: targetTime, '
                 'variance: variance, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-dcs/trackTurnaround.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-track-turnaround-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-track-turnaround-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'com.etzhayyim.apps.airDcs.trackTurnaround',
                 'air_dcs_track_turnaround',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-track-turnaround-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2167, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-issue-departure-control-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'air_dcs_issue_departure_control',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_dcs_issue_departure_control" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-dcs" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_dcs_issue_departure_control" '
                 'name="issueDepartureControl" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="issue departure control">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.dcs.departure.control"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, depDate: depDate, atd: atd, '
                 'delayReason: delayReason, delayMins: delayMins, gate: gate, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=flightNo" target="flightNo"/><zeebe:output source="=atd" '
                 'target="atd"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-dcs.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.dcs.departure.control&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, flightNo: flightNo, atd: atd, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-dcs/issueDepartureControl.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-issue-departure-control-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-issue-departure-control-v1',
                 'did:web:air-dcs.etzhayyim.com',
                 'com.etzhayyim.apps.airDcs.issueDepartureControl',
                 'air_dcs_issue_departure_control',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-dcs.etzhayyim.com',
                 'did:web:air-dcs.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-dcs.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-issue-departure-control-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2249, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-file-flight-plan-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'air_ops_file_flight_plan',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ops_file_flight_plan" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ops" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ops_file_flight_plan" name="fileFlightPlan" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="file flight plan">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ops.flight_plan.file"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, depDate: depDate, '
                 'carrierCode: carrierCode, origin: origin, dest: dest, route: route, altitude: '
                 'altitude, speed: speed, fuelRequired: fuelRequired, estimatedElapsed: '
                 'estimatedElapsed, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=flightId" target="flightId"/><zeebe:output source="=ifpsRef" '
                 'target="ifpsRef"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ops.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ops.flight_plan.file&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, flightId: flightId, ifpsRef: ifpsRef, status: '
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
                 '00-contracts/bpmn/com/etzhayyim/air-ops/fileFlightPlan.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-file-flight-plan-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-file-flight-plan-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'com.etzhayyim.apps.airOps.fileFlightPlan',
                 'air_ops_file_flight_plan',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-file-flight-plan-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2231, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-create-dispatch-brief-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'air_ops_create_dispatch_brief',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ops_create_dispatch_brief" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ops" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ops_create_dispatch_brief" name="createDispatchBrief" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="create dispatch brief">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ops.dispatch.brief"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, depDate: depDate, '
                 'carrierCode: carrierCode, captainDid: captainDid, fuelPlanned: fuelPlanned, '
                 'alternateAirport: alternateAirport, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=ofpVersion" target="ofpVersion"/><zeebe:output source="=releasedAt" '
                 'target="releasedAt"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ops.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ops.dispatch.brief&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, ofpVersion: ofpVersion, releasedAt: releasedAt, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-ops/createDispatchBrief.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-create-dispatch-brief-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-create-dispatch-brief-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'com.etzhayyim.apps.airOps.createDispatchBrief',
                 'air_ops_create_dispatch_brief',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-create-dispatch-brief-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2054, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-fetch-notam-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'air_ops_fetch_notam',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ops_fetch_notam" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ops" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ops_fetch_notam" name="fetchNotam" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="fetch notam">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ops.notam.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={location: location, effectiveFrom: '
                 'effectiveFrom, effectiveTo: effectiveTo, notamType: notamType, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=notamCount" target="notamCount"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ops.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ops.notam.fetch&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, notamCount: notamCount, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-ops/fetchNotam.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-fetch-notam-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-fetch-notam-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'com.etzhayyim.apps.airOps.fetchNotam',
                 'air_ops_fetch_notam',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-fetch-notam-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2053, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-fetch-weather-brief-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'air_ops_fetch_weather_brief',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ops_fetch_weather" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ops" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ops_fetch_weather" name="fetchWeatherBrief" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="fetch weather brief">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ops.weather.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={icaoCode: icaoCode, briefType: briefType, '
                 'validFrom: validFrom, validTo: validTo, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=briefRef" target="briefRef"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ops.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ops.weather.fetch&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, briefRef: briefRef, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-ops/fetchWeatherBrief.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-fetch-weather-brief-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-fetch-weather-brief-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'com.etzhayyim.apps.airOps.fetchWeatherBrief',
                 'air_ops_fetch_weather_brief',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-fetch-weather-brief-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2109, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-record-tech-log-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'air_ops_record_tech_log',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ops_record_tech_log" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ops" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ops_record_tech_log" name="recordTechLog" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="record tech log">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ops.tech_log.record"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={aircraftReg: aircraftReg, flightNo: flightNo, '
                 'depDate: depDate, defectCode: defectCode, description: description, melRef: '
                 'melRef, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=techLogRef" target="techLogRef"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ops.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ops.tech_log.record&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, techLogRef: techLogRef, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-ops/recordTechLog.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-record-tech-log-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-record-tech-log-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'com.etzhayyim.apps.airOps.recordTechLog',
                 'air_ops_record_tech_log',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-record-tech-log-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2074, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-order-fuel-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'air_ops_order_fuel',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ops_order_fuel" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ops" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ops_order_fuel" name="orderFuel" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="order fuel">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="air.ops.fuel.order"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, depDate: depDate, airport: '
                 'airport, fuelKg: fuelKg, fuelGrade: fuelGrade, tankerRef: tankerRef, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=fuelOrderRef" target="fuelOrderRef"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ops.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ops.fuel.order&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, fuelOrderRef: fuelOrderRef, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-ops/orderFuel.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-order-fuel-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-order-fuel-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'com.etzhayyim.apps.airOps.orderFuel',
                 'air_ops_order_fuel',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-order-fuel-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2098, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-submit-pirep-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'air_ops_submit_pirep',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ops_submit_pirep" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ops" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ops_submit_pirep" name="submitPirep" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="submit pirep">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ops.pirep.submit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, depDate: depDate, position: '
                 'position, altitude: altitude, turbulenceSeverity: turbulenceSeverity, '
                 'icingSeverity: icingSeverity, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=pirepId" target="pirepId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ops.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ops.pirep.submit&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, pirepId: pirepId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-ops/submitPirep.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-submit-pirep-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-submit-pirep-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'com.etzhayyim.apps.airOps.submitPirep',
                 'air_ops_submit_pirep',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-submit-pirep-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2248, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-monitor-flight-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'air_ops_monitor_flight',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ops_monitor_flight" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ops" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ops_monitor_flight" name="monitorFlight" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="monitor flight">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ops.flight.monitor"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, depDate: depDate, '
                 'currentStatus: currentStatus, delayMins: delayMins, position: position, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=flightNo" target="flightNo"/><zeebe:output source="=currentStatus" '
                 'target="currentStatus"/><zeebe:output source="=alertLevel" '
                 'target="alertLevel"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ops.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ops.flight.monitor&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, flightNo: flightNo, currentStatus: currentStatus, '
                 'alertLevel: alertLevel, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-ops/monitorFlight.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-monitor-flight-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-monitor-flight-v1',
                 'did:web:air-ops.etzhayyim.com',
                 'com.etzhayyim.apps.airOps.monitorFlight',
                 'air_ops_monitor_flight',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ops.etzhayyim.com',
                 'did:web:air-ops.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ops.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-monitor-flight-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2092, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-publish-roster-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'air_crew_publish_roster',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_crew_publish_roster" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-crew" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_crew_publish_roster" name="publishRoster" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="publish roster">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.crew.roster.publish"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={crewDid: crewDid, flightNo: flightNo, depDate: '
                 'depDate, role: role, dutyStart: dutyStart, dutyEnd: dutyEnd, base: base, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=rosterId" target="rosterId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-crew.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.crew.roster.publish&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, rosterId: rosterId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-crew/publishRoster.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-publish-roster-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-publish-roster-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'com.etzhayyim.apps.airCrew.publishRoster',
                 'air_crew_publish_roster',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-publish-roster-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2174, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-build-pairing-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'air_crew_build_pairing',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_crew_build_pairing" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-crew" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_crew_build_pairing" name="buildPairing" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="build pairing">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.crew.pairing.build"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={carrierCode: carrierCode, crewBase: crewBase, '
                 'startDate: startDate, endDate: endDate, totalFdtHours: totalFdtHours, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=pairingId" target="pairingId"/><zeebe:output source="=ftlCompliant" '
                 'target="ftlCompliant"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-crew.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.crew.pairing.build&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, pairingId: pairingId, ftlCompliant: ftlCompliant, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-crew/buildPairing.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-build-pairing-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-build-pairing-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'com.etzhayyim.apps.airCrew.buildPairing',
                 'air_crew_build_pairing',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-build-pairing-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2266, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-track-qualification-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'air_crew_track_qualification',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_crew_track_qualification" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-crew" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_crew_track_qualification" name="trackQualification" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="track qualification">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.crew.qualification.track"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={crewDid: crewDid, aircraftType: aircraftType, '
                 'ratingType: ratingType, issuedAt: issuedAt, expiresAt: expiresAt, '
                 'issuingAuthority: issuingAuthority, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=qualificationId" target="qualificationId"/><zeebe:output '
                 'source="=daysToExpiry" target="daysToExpiry"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-crew.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.crew.qualification.track&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, qualificationId: qualificationId, daysToExpiry: '
                 'daysToExpiry, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-crew/trackQualification.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-track-qualification-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-track-qualification-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'com.etzhayyim.apps.airCrew.trackQualification',
                 'air_crew_track_qualification',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-track-qualification-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2310, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-assess-fatigue-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'air_crew_assess_fatigue',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_crew_assess_fatigue" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-crew" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_crew_assess_fatigue" name="assessFatigue" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="assess fatigue">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.crew.fatigue.assess"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={crewDid: crewDid, dutyDate: dutyDate, fdpHours: '
                 'fdpHours, fdtHours: fdtHours, restHours: restHours, cumulative28d: '
                 'cumulative28d, cumulative365d: cumulative365d, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=fatigueScore" target="fatigueScore"/><zeebe:output source="=riskLevel" '
                 'target="riskLevel"/><zeebe:output source="=limitBreach" '
                 'target="limitBreach"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-crew.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.crew.fatigue.assess&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, fatigueScore: fatigueScore, riskLevel: riskLevel, '
                 'limitBreach: limitBreach, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-crew/assessFatigue.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-assess-fatigue-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-assess-fatigue-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'com.etzhayyim.apps.airCrew.assessFatigue',
                 'air_crew_assess_fatigue',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-assess-fatigue-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2070, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-assign-crew-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'air_crew_assign_crew',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_crew_assign_crew" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-crew" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_crew_assign_crew" name="assignCrew" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="assign crew">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.crew.crew.assign"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={crewDid: crewDid, flightNo: flightNo, depDate: '
                 'depDate, role: role, assignmentType: assignmentType, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=assignmentId" target="assignmentId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-crew.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.crew.crew.assign&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, assignmentId: assignmentId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-crew/assignCrew.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-assign-crew-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-assign-crew-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'com.etzhayyim.apps.airCrew.assignCrew',
                 'air_crew_assign_crew',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-assign-crew-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2085, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-book-crew-travel-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'air_crew_book_crew_travel',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_crew_book_travel" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-crew" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_crew_book_travel" name="bookCrewTravel" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="book crew travel">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.crew.travel.book"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={crewDid: crewDid, travelType: travelType, '
                 'origin: origin, dest: dest, depDate: depDate, hotelRequired: hotelRequired, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=travelRef" target="travelRef"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-crew.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.crew.travel.book&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, travelRef: travelRef, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-crew/bookCrewTravel.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-book-crew-travel-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-book-crew-travel-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'com.etzhayyim.apps.airCrew.bookCrewTravel',
                 'air_crew_book_crew_travel',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-book-crew-travel-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2283, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-record-duty-time-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'air_crew_record_duty_time',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_crew_record_duty_time" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-crew" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_crew_record_duty_time" name="recordDutyTime" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="record duty time">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.crew.duty_time.record"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={crewDid: crewDid, dutyDate: dutyDate, fdpHours: '
                 'fdpHours, fdtHours: fdtHours, restHours: restHours, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=cumulative28d" target="cumulative28d"/><zeebe:output '
                 'source="=cumulative365d" target="cumulative365d"/><zeebe:output '
                 'source="=limitBreach" target="limitBreach"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-crew.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.crew.duty_time.record&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, cumulative28d: cumulative28d, cumulative365d: '
                 'cumulative365d, limitBreach: limitBreach, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-crew/recordDutyTime.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-record-duty-time-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-record-duty-time-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'com.etzhayyim.apps.airCrew.recordDutyTime',
                 'air_crew_record_duty_time',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-record-duty-time-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2166, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-notify-crew-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'air_crew_notify_crew',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_crew_notify_crew" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-crew" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_crew_notify_crew" name="notifyCrew" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="notify crew">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.crew.crew.notify"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={crewDid: crewDid, notificationType: '
                 'notificationType, message: message, flightNo: flightNo, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=notificationId" target="notificationId"/><zeebe:output '
                 'source="=acknowledgedAt" target="acknowledgedAt"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-crew.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.crew.crew.notify&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, notificationId: notificationId, acknowledgedAt: '
                 'acknowledgedAt, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-crew/notifyCrew.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-notify-crew-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-notify-crew-v1',
                 'did:web:air-crew.etzhayyim.com',
                 'com.etzhayyim.apps.airCrew.notifyCrew',
                 'air_crew_notify_crew',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-crew.etzhayyim.com',
                 'did:web:air-crew.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-crew.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-notify-crew-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2051, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-create-work-order-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'air_mro_create_work_order',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_mro_create_work_order" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-mro" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_mro_create_work_order" name="createWorkOrder" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="create work order">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.mro.work_order.create"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={aircraftReg: aircraftReg, taskType: taskType, '
                 'station: station, openedAt: openedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=woNo" target="woNo"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-mro.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.mro.work_order.create&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, woNo: woNo, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-mro/createWorkOrder.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-create-work-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-create-work-order-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'com.etzhayyim.apps.airMro.createWorkOrder',
                 'air_mro_create_work_order',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-create-work-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2242, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-track-component-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'air_mro_track_component',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_mro_track_component" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-mro" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_mro_track_component" name="trackComponent" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="track component">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.mro.component.track"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={partNo: partNo, serialNo: serialNo, '
                 'aircraftReg: aircraftReg, mpdTask: mpdTask, ttlHours: ttlHours, ttiHours: '
                 'ttiHours, lastInspAt: lastInspAt, nextDueAt: nextDueAt, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=componentId" target="componentId"/><zeebe:output '
                 'source="=daysToNextDue" target="daysToNextDue"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-mro.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.mro.component.track&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, componentId: componentId, daysToNextDue: '
                 'daysToNextDue, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-mro/trackComponent.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-track-component-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-track-component-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'com.etzhayyim.apps.airMro.trackComponent',
                 'air_mro_track_component',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-track-component-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2332, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-check-airworthiness-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'air_mro_check_airworthiness',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_mro_check_airworthiness" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-mro" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_mro_check_airworthiness" name="checkAirworthiness" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="check airworthiness">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.mro.airworthiness.check"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={adNo: adNo, aircraftReg: aircraftReg, '
                 'complianceMethod: complianceMethod, complianceDate: complianceDate, dueAt: '
                 'dueAt, recurrenceInterval: recurrenceInterval, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=adNo" target="adNo"/><zeebe:output source="=complianceStatus" '
                 'target="complianceStatus"/><zeebe:output source="=daysUntilDue" '
                 'target="daysUntilDue"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-mro.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.mro.airworthiness.check&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, adNo: adNo, complianceStatus: complianceStatus, '
                 'daysUntilDue: daysUntilDue, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-mro/checkAirworthiness.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-check-airworthiness-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-check-airworthiness-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'com.etzhayyim.apps.airMro.checkAirworthiness',
                 'air_mro_check_airworthiness',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-check-airworthiness-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2175, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-report-tech-occurrence-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'air_mro_report_tech_occurrence',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_mro_report_tech_occurrence" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-mro" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_mro_report_tech_occurrence" name="reportTechOccurrence" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="report tech occurrence">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.mro.occurrence.report"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={aircraftReg: aircraftReg, flightNo: flightNo, '
                 'occurrenceType: occurrenceType, ataChapter: ataChapter, description: '
                 'description, reportedBy: reportedBy, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=occurrenceRef" target="occurrenceRef"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-mro.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.mro.occurrence.report&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, occurrenceRef: occurrenceRef, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-mro/reportTechOccurrence.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-report-tech-occurrence-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-report-tech-occurrence-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'com.etzhayyim.apps.airMro.reportTechOccurrence',
                 'air_mro_report_tech_occurrence',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-report-tech-occurrence-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2130, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-schedule-maintenance-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'air_mro_schedule_maintenance',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_mro_schedule_maintenance" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-mro" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_mro_schedule_maintenance" name="scheduleMaintenance" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="schedule maintenance">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.mro.maintenance.schedule"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={aircraftReg: aircraftReg, checkType: checkType, '
                 'station: station, startDate: startDate, endDate: endDate, estimatedManHours: '
                 'estimatedManHours, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=woNo" target="woNo"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-mro.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.mro.maintenance.schedule&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, woNo: woNo, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-mro/scheduleMaintenance.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-schedule-maintenance-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-schedule-maintenance-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'com.etzhayyim.apps.airMro.scheduleMaintenance',
                 'air_mro_schedule_maintenance',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-schedule-maintenance-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2170, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-report-reliability-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'air_mro_report_reliability',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_mro_report_reliability" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-mro" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_mro_report_reliability" name="reportReliability" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="report reliability">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.mro.reliability.report"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={aircraftType: aircraftType, carrierCode: '
                 'carrierCode, period: period, dispatchReliability: dispatchReliability, '
                 'mtbfHours: mtbfHours, pirepRate: pirepRate, ataChapter: ataChapter, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=reportId" target="reportId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-mro.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.mro.reliability.report&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, reportId: reportId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-mro/reportReliability.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-report-reliability-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-report-reliability-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'com.etzhayyim.apps.airMro.reportReliability',
                 'air_mro_report_reliability',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-report-reliability-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2233, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-order-spare-part-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'air_mro_order_spare_part',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_mro_order_spare_part" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-mro" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_mro_order_spare_part" name="orderSparePart" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="order spare part">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.mro.spare_part.order"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={partNo: partNo, serialNo: serialNo, '
                 'aircraftReg: aircraftReg, aogFlag: aogFlag, vendor: vendor, quantity: quantity, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=purchaseOrderRef" target="purchaseOrderRef"/><zeebe:output '
                 'source="=estimatedDelivery" target="estimatedDelivery"/><zeebe:output '
                 'source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-mro.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.mro.spare_part.order&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, purchaseOrderRef: purchaseOrderRef, '
                 'estimatedDelivery: estimatedDelivery, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-mro/orderSparePart.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-order-spare-part-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-order-spare-part-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'com.etzhayyim.apps.airMro.orderSparePart',
                 'air_mro_order_spare_part',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-order-spare-part-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2183, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-record-ground-equipment-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'air_mro_record_ground_equipment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_mro_record_ground_equipment" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-mro" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_mro_record_ground_equipment" '
                 'name="recordGroundEquipment" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="record ground equipment">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="air.mro.gse.record"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={gseId: gseId, gseType: gseType, station: '
                 'station, serviceability: serviceability, lastInspAt: lastInspAt, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=gseId" target="gseId"/><zeebe:output source="=serviceability" '
                 'target="serviceability"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-mro.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.mro.gse.record&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, gseId: gseId, serviceability: serviceability, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-mro/recordGroundEquipment.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-record-ground-equipment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-record-ground-equipment-v1',
                 'did:web:air-mro.etzhayyim.com',
                 'com.etzhayyim.apps.airMro.recordGroundEquipment',
                 'air_mro_record_ground_equipment',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-mro.etzhayyim.com',
                 'did:web:air-mro.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-mro.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-record-ground-equipment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2153, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-submit-safety-report-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'air_sms_submit_safety_report',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sms_submit_safety_report" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sms" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sms_submit_safety_report" name="submitSafetyReport" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="submit safety report">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sms.safety_report.submit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={reporterDidHash: reporterDidHash, category: '
                 'category, severity: severity, descriptionHash: descriptionHash, flightNo: '
                 'flightNo, reportedAt: reportedAt, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=reportId" target="reportId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sms.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sms.safety_report.submit&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, reportId: reportId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sms/submitSafetyReport.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-submit-safety-report-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-submit-safety-report-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'com.etzhayyim.apps.airSms.submitSafetyReport',
                 'air_sms_submit_safety_report',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-submit-safety-report-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2100, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-assess-risk-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'air_sms_assess_risk',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sms_assess_risk" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sms" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sms_assess_risk" name="assessRisk" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="assess risk">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sms.risk.assess"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={hazard: hazard, likelihood: likelihood, '
                 'severity: severity, mitigation: mitigation, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=riskId" target="riskId"/><zeebe:output source="=riskScore" '
                 'target="riskScore"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sms.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sms.risk.assess&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, riskId: riskId, riskScore: riskScore, status: '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sms/assessRisk.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-assess-risk-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-assess-risk-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'com.etzhayyim.apps.airSms.assessRisk',
                 'air_sms_assess_risk',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-assess-risk-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2107, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-record-iosa-finding-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'air_sms_record_iosa_finding',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sms_record_iosa_finding" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sms" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sms_record_iosa_finding" name="recordIosaFinding" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="record IOSA finding">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sms.iosa.finding"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={standardRef: standardRef, category: category, '
                 'descriptionHash: descriptionHash, carDueAt: carDueAt, auditDate: auditDate, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=findingId" target="findingId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sms.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sms.iosa.finding&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, findingId: findingId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sms/recordIosaFinding.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-record-iosa-finding-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-record-iosa-finding-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'com.etzhayyim.apps.airSms.recordIosaFinding',
                 'air_sms_record_iosa_finding',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-record-iosa-finding-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2141, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-file-regulatory-report-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'air_sms_file_regulatory_report',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sms_file_regulatory_report" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sms" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sms_file_regulatory_report" name="fileRegulatoryReport" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="file regulatory report">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sms.regulatory.file"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={authority: authority, reportType: reportType, '
                 'period: period, descriptionHash: descriptionHash, submittedAt: submittedAt, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=submissionRef" target="submissionRef"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sms.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sms.regulatory.file&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, submissionRef: submissionRef, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sms/fileRegulatoryReport.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-file-regulatory-report-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-file-regulatory-report-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'com.etzhayyim.apps.airSms.fileRegulatoryReport',
                 'air_sms_file_regulatory_report',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-file-regulatory-report-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2108, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-report-occurrence-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'air_sms_report_occurrence',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sms_report_occurrence" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sms" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sms_report_occurrence" name="reportOccurrence" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="report occurrence">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sms.occurrence.report"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={flightNo: flightNo, occType: occType, location: '
                 'location, injuries: injuries, damageLevel: damageLevel, stateAuthority: '
                 'stateAuthority, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=occId" target="occId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sms.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sms.occurrence.report&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, occId: occId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sms/reportOccurrence.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-report-occurrence-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-report-occurrence-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'com.etzhayyim.apps.airSms.reportOccurrence',
                 'air_sms_report_occurrence',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-report-occurrence-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2237, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-distribute-safety-bulletin-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'air_sms_distribute_safety_bulletin',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sms_distribute_safety_bulletin" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sms" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sms_distribute_safety_bulletin" '
                 'name="distributeSafetyBulletin" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="distribute safety bulletin">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sms.bulletin.distribute"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={bulletinType: bulletinType, subject: subject, '
                 'recipientGroups: recipientGroups, effectiveDate: effectiveDate, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=bulletinRef" target="bulletinRef"/><zeebe:output '
                 'source="=distributedAt" target="distributedAt"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sms.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sms.bulletin.distribute&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, bulletinRef: bulletinRef, distributedAt: '
                 'distributedAt, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-sms/distributeSafetyBulletin.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-distribute-safety-bulletin-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-distribute-safety-bulletin-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'com.etzhayyim.apps.airSms.distributeSafetyBulletin',
                 'air_sms_distribute_safety_bulletin',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-distribute-safety-bulletin-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2191, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-screen-dangerous-goods-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'air_sms_screen_dangerous_goods',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sms_screen_dangerous_goods" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sms" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sms_screen_dangerous_goods" name="screenDangerousGoods" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="screen dangerous goods">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="air.sms.dg.screen"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={awbNo: awbNo, unNo: unNo, packingGroup: '
                 'packingGroup, netQuantity: netQuantity, acceptanceResult: acceptanceResult, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=screeningRef" target="screeningRef"/><zeebe:output source="=notocRef" '
                 'target="notocRef"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sms.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sms.dg.screen&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, screeningRef: screeningRef, notocRef: notocRef, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sms/screenDangerousGoods.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-screen-dangerous-goods-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-screen-dangerous-goods-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'com.etzhayyim.apps.airSms.screenDangerousGoods',
                 'air_sms_screen_dangerous_goods',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-screen-dangerous-goods-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2185, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-handle-security-alert-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'air_sms_handle_security_alert',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_sms_handle_security_alert" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-sms" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_sms_handle_security_alert" name="handleSecurityAlert" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="handle security alert">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.sms.security.alert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={alertType: alertType, threatLevel: threatLevel, '
                 'affectedFlight: affectedFlight, responseAction: responseAction, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=alertId" target="alertId"/><zeebe:output source="=responseRef" '
                 'target="responseRef"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-sms.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.sms.security.alert&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, alertId: alertId, responseRef: responseRef, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-sms/handleSecurityAlert.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-handle-security-alert-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-handle-security-alert-v1',
                 'did:web:air-sms.etzhayyim.com',
                 'com.etzhayyim.apps.airSms.handleSecurityAlert',
                 'air_sms_handle_security_alert',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-sms.etzhayyim.com',
                 'did:web:air-sms.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-sms.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-handle-security-alert-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2139, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-create-cargo-booking-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'air_cargo_create_cargo_booking',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_cargo_create_booking" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-cargo" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_cargo_create_booking" name="createCargoBooking" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="create cargo booking">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.cargo.booking.create"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={awbNo: awbNo, flightNo: flightNo, depDate: '
                 'depDate, carrierCode: carrierCode, pieces: pieces, weightKg: weightKg, rate: '
                 'rate, currency: currency, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=bookingId" target="bookingId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-cargo.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.cargo.booking.create&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, bookingId: bookingId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-cargo/createCargoBooking.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-create-cargo-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-create-cargo-booking-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'com.etzhayyim.apps.airCargo.createCargoBooking',
                 'air_cargo_create_cargo_booking',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-create-cargo-booking-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2133, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-issue-air-waybill-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'air_cargo_issue_air_waybill',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_cargo_issue_awb" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-cargo" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_cargo_issue_awb" name="issueAirWaybill" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="issue air waybill">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.cargo.awb.issue"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={shipperDid: shipperDid, consigneeDid: '
                 'consigneeDid, origin: origin, dest: dest, weightKg: weightKg, pieces: pieces, '
                 'commodityCode: commodityCode, isDangerousGoods: isDangerousGoods, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=awbNo" target="awbNo"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-cargo.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.cargo.awb.issue&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, awbNo: awbNo, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-cargo/issueAirWaybill.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-issue-air-waybill-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-issue-air-waybill-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'com.etzhayyim.apps.airCargo.issueAirWaybill',
                 'air_cargo_issue_air_waybill',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-issue-air-waybill-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2106, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-accept-cargo-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'air_cargo_accept_cargo',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_cargo_accept_cargo" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-cargo" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_cargo_accept_cargo" name="acceptCargo" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="accept cargo">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.cargo.cargo.accept"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={awbNo: awbNo, flightNo: flightNo, depDate: '
                 'depDate, weightKg: weightKg, pieces: pieces, dgScreeningRef: dgScreeningRef, '
                 'callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=acceptanceRef" target="acceptanceRef"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-cargo.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.cargo.cargo.accept&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, acceptanceRef: acceptanceRef, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-cargo/acceptCargo.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-accept-cargo-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-accept-cargo-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'com.etzhayyim.apps.airCargo.acceptCargo',
                 'air_cargo_accept_cargo',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-accept-cargo-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2134, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-assign-uld-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'air_cargo_assign_uld',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_cargo_assign_uld" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-cargo" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_cargo_assign_uld" name="assignUld" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="assign ULD">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.cargo.uld.assign"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={uldNo: uldNo, aircraftReg: aircraftReg, awbNo: '
                 'awbNo, flightNo: flightNo, depDate: depDate, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=uldNo" target="uldNo"/><zeebe:output source="=loadingPosition" '
                 'target="loadingPosition"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-cargo.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.cargo.uld.assign&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, uldNo: uldNo, loadingPosition: loadingPosition, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-cargo/assignUld.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-assign-uld-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-assign-uld-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'com.etzhayyim.apps.airCargo.assignUld',
                 'air_cargo_assign_uld',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-assign-uld-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2136, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-track-shipment-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'air_cargo_track_shipment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_cargo_track_shipment" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-cargo" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_cargo_track_shipment" name="trackShipment" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="track shipment">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.cargo.shipment.track"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={awbNo: awbNo, location: location, eventType: '
                 'eventType, eventTime: eventTime, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=awbNo" target="awbNo"/><zeebe:output source="=currentStatus" '
                 'target="currentStatus"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-cargo.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.cargo.shipment.track&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, awbNo: awbNo, currentStatus: currentStatus, '
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
                 '00-contracts/bpmn/com/etzhayyim/air-cargo/trackShipment.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-track-shipment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-track-shipment-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'com.etzhayyim.apps.airCargo.trackShipment',
                 'air_cargo_track_shipment',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-track-shipment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2066, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-process-claim-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'air_cargo_process_claim',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_cargo_process_claim" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-cargo" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_cargo_process_claim" name="processClaim" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="process claim">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.cargo.claim.process"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={awbNo: awbNo, claimType: claimType, amount: '
                 'amount, currency: currency, description: description, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=claimId" target="claimId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-cargo.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.cargo.claim.process&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, claimId: claimId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-cargo/processClaim.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-process-claim-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-process-claim-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'com.etzhayyim.apps.airCargo.processClaim',
                 'air_cargo_process_claim',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-process-claim-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2167, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-settle-cargo-account-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'air_cargo_settle_cargo_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_cargo_settle_account" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-cargo" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_cargo_settle_account" name="settleCargoAccount" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="settle cargo account">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.cargo.cass.settle"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={period: period, carrierCode: carrierCode, '
                 'totalAmount: totalAmount, currency: currency, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=settlementRef" target="settlementRef"/><zeebe:output '
                 'source="=settledAt" target="settledAt"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-cargo.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.cargo.cass.settle&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, settlementRef: settlementRef, settledAt: '
                 'settledAt, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-cargo/settleCargoAccount.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-settle-cargo-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-settle-cargo-account-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'com.etzhayyim.apps.airCargo.settleCargoAccount',
                 'air_cargo_settle_cargo_account',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-settle-cargo-account-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2103, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-report-cargo-security-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'air_cargo_report_cargo_security',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_cargo_report_security" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-cargo" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_cargo_report_security" name="reportCargoSecurity" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="report cargo security">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.cargo.security.report"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={awbNo: awbNo, securityScheme: securityScheme, '
                 'screeningMethod: screeningMethod, result: result, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=securityRef" target="securityRef"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-cargo.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.cargo.security.report&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, securityRef: securityRef, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-cargo/reportCargoSecurity.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-report-cargo-security-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-report-cargo-security-v1',
                 'did:web:air-cargo.etzhayyim.com',
                 'com.etzhayyim.apps.airCargo.reportCargoSecurity',
                 'air_cargo_report_cargo_security',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-cargo.etzhayyim.com',
                 'did:web:air-cargo.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-cargo.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-report-cargo-security-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2020, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-enroll-member-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'air_ffp_enroll_member',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ffp_enroll_member" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ffp" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ffp_enroll_member" name="enrollMember" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="enroll member">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ffp.member.enroll"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={memberDid: memberDid, carrierCode: carrierCode, '
                 'tier: tier, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=memberId" target="memberId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ffp.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ffp.member.enroll&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, memberId: memberId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-ffp/enrollMember.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-enroll-member-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-enroll-member-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'com.etzhayyim.apps.airFfp.enrollMember',
                 'air_ffp_enroll_member',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-enroll-member-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2162, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-accrue-points-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'air_ffp_accrue_points',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ffp_accrue_points" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ffp" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ffp_accrue_points" name="accruePoints" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="accrue points">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ffp.miles.accrue"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={memberId: memberId, flightNo: flightNo, '
                 'depDate: depDate, milesEarned: milesEarned, partnerCode: partnerCode, '
                 'accrualType: accrualType, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=txnId" target="txnId"/><zeebe:output source="=totalMiles" '
                 'target="totalMiles"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ffp.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ffp.miles.accrue&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, txnId: txnId, totalMiles: totalMiles, status: '
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
                 '00-contracts/bpmn/com/etzhayyim/air-ffp/accruePoints.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-accrue-points-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-accrue-points-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'com.etzhayyim.apps.airFfp.accruePoints',
                 'air_ffp_accrue_points',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-accrue-points-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2164, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-redeem-reward-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'air_ffp_redeem_reward',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ffp_redeem_reward" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ffp" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ffp_redeem_reward" name="redeemReward" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="redeem reward">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ffp.reward.redeem"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={memberId: memberId, rewardType: rewardType, '
                 'milesUsed: milesUsed, partnerCode: partnerCode, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=redemptionId" target="redemptionId"/><zeebe:output '
                 'source="=remainingMiles" target="remainingMiles"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ffp.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ffp.reward.redeem&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, redemptionId: redemptionId, remainingMiles: '
                 'remainingMiles, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-ffp/redeemReward.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-redeem-reward-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-redeem-reward-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'com.etzhayyim.apps.airFfp.redeemReward',
                 'air_ffp_redeem_reward',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-redeem-reward-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2186, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-update-tier-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'air_ffp_update_tier',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ffp_update_tier" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ffp" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ffp_update_tier" name="updateTier" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="update tier">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ffp.tier.update"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={memberId: memberId, newTier: newTier, '
                 'qualifyingMiles: qualifyingMiles, effectiveDate: effectiveDate, callerDid: '
                 'callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=memberId" target="memberId"/><zeebe:output source="=oldTier" '
                 'target="oldTier"/><zeebe:output source="=newTier" '
                 'target="newTier"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ffp.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ffp.tier.update&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, memberId: memberId, oldTier: oldTier, newTier: '
                 'newTier, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-ffp/updateTier.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-update-tier-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-update-tier-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'com.etzhayyim.apps.airFfp.updateTier',
                 'air_ffp_update_tier',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-update-tier-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2020, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-transfer-miles-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'air_ffp_transfer_miles',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ffp_transfer_miles" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ffp" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ffp_transfer_miles" name="transferMiles" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="transfer miles">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ffp.miles.transfer"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={fromMemberId: fromMemberId, toMemberId: '
                 'toMemberId, miles: miles, callerDid: callerDid}" target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=txnId" target="txnId"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ffp.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ffp.miles.transfer&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, txnId: txnId, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-ffp/transferMiles.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-transfer-miles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-transfer-miles-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'com.etzhayyim.apps.airFfp.transferMiles',
                 'air_ffp_transfer_miles',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-transfer-miles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2138, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-process-purchase-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'air_ffp_process_purchase',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ffp_process_purchase" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ffp" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ffp_process_purchase" name="processPurchase" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="process purchase">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ffp.miles.purchase"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={memberId: memberId, milesAmount: milesAmount, '
                 'paymentAmount: paymentAmount, currency: currency, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=txnId" target="txnId"/><zeebe:output source="=newBalance" '
                 'target="newBalance"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ffp.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ffp.miles.purchase&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, txnId: txnId, newBalance: newBalance, status: '
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
                 '00-contracts/bpmn/com/etzhayyim/air-ffp/processPurchase.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-process-purchase-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-process-purchase-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'com.etzhayyim.apps.airFfp.processPurchase',
                 'air_ffp_process_purchase',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-process-purchase-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2196, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-expire-miles-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'air_ffp_expire_miles',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ffp_expire_miles" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ffp" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ffp_expire_miles" name="expireMiles" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="expire miles">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ffp.miles.expire"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={memberId: memberId, milesExpiring: '
                 'milesExpiring, expiryDate: expiryDate, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=memberId" target="memberId"/><zeebe:output source="=milesExpired" '
                 'target="milesExpired"/><zeebe:output source="=newBalance" '
                 'target="newBalance"/><zeebe:output source="=status" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ffp.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ffp.miles.expire&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, memberId: memberId, milesExpired: milesExpired, '
                 'newBalance: newBalance, status: status}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/com/etzhayyim/air-ffp/expireMiles.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-expire-miles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-expire-miles-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'com.etzhayyim.apps.airFfp.expireMiles',
                 'air_ffp_expire_miles',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-expire-miles-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, 2164, $5, $6,\n'
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-reconcile-partner-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'air_ffp_reconcile_partner',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_air_ffp_reconcile_partner" '
                 'targetNamespace="https://etzhayyim.com/bpmn/air-ffp" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="air_ffp_reconcile_partner" name="reconcilePartner" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Main"/>\n'
                 '    <bpmn:serviceTask id="Task_Main" name="reconcile partner">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="air.ffp.partner.reconcile"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={partnerCode: partnerCode, period: period, '
                 'earnTransactions: earnTransactions, burnTransactions: burnTransactions, '
                 'netSettlement: netSettlement, currency: currency, callerDid: callerDid}" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/><zeebe:output '
                 'source="=reconcileRef" target="reconcileRef"/><zeebe:output source="=status" '
                 'target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Main" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:air-ffp.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;air.ffp.partner.reconcile&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, reconcileRef: reconcileRef, status: status}" '
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
                 '00-contracts/bpmn/com/etzhayyim/air-ffp/reconcilePartner.bpmn',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-reconcile-partner-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         '        15000, $5, $6, 100,\n'
         '        $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-reconcile-partner-v1',
                 'did:web:air-ffp.etzhayyim.com',
                 'com.etzhayyim.apps.airFfp.reconcilePartner',
                 'air_ffp_reconcile_partner',
                 'active',
                 '2026-05-07T12:00:00Z',
                 'did:web:air-ffp.etzhayyim.com',
                 'did:web:air-ffp.etzhayyim.com',
                 'sys.bpmn.seed.airline',
                 'did:web:air-ffp.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-reconcile-partner-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-register-schedule-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-register-schedule-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-request-slot-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-request-slot-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-allocate-slot-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-allocate-slot-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-assign-fleet-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-assign-fleet-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-publish-schedule-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-publish-schedule-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-assign-gate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-assign-gate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-change-frequency-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-change-frequency-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sched-register-codeshare-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sched-register-codeshare-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-create-pnr-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-create-pnr-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-confirm-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-confirm-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-issue-ticket-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-issue-ticket-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-assign-seat-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-assign-seat-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-add-ancillary-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-add-ancillary-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-cancel-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-cancel-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-reprotect-passenger-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-reprotect-passenger-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-book-settle-bsp-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-book-settle-bsp-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-publish-fare-class-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-publish-fare-class-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-adjust-inventory-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-adjust-inventory-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-file-fare-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-file-fare-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-set-overbooking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-set-overbooking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-process-group-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-process-group-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-apply-dynamic-price-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-apply-dynamic-price-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-generate-revenue-report-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-generate-revenue-report-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-yield-forecast-demand-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-yield-forecast-demand-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-process-check-in-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-process-check-in-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-process-boarding-pass-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-process-boarding-pass-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-accept-baggage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-accept-baggage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-reconcile-baggage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-reconcile-baggage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-compute-load-sheet-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-compute-load-sheet-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-transmit-apis-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-transmit-apis-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-track-turnaround-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-track-turnaround-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-dcs-issue-departure-control-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-dcs-issue-departure-control-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-file-flight-plan-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-file-flight-plan-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-create-dispatch-brief-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-create-dispatch-brief-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-fetch-notam-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-fetch-notam-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-fetch-weather-brief-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-fetch-weather-brief-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-record-tech-log-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-record-tech-log-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-order-fuel-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-order-fuel-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-submit-pirep-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-submit-pirep-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ops-monitor-flight-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ops-monitor-flight-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-publish-roster-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-publish-roster-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-build-pairing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-build-pairing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-track-qualification-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-track-qualification-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-assess-fatigue-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-assess-fatigue-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-assign-crew-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-assign-crew-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-book-crew-travel-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-book-crew-travel-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-record-duty-time-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-record-duty-time-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-crew-notify-crew-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-crew-notify-crew-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-create-work-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-create-work-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-track-component-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-track-component-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-check-airworthiness-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-check-airworthiness-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-report-tech-occurrence-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-report-tech-occurrence-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-schedule-maintenance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-schedule-maintenance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-report-reliability-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-report-reliability-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-order-spare-part-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-order-spare-part-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-mro-record-ground-equipment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-mro-record-ground-equipment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-submit-safety-report-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-submit-safety-report-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-assess-risk-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-assess-risk-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-record-iosa-finding-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-record-iosa-finding-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-file-regulatory-report-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-file-regulatory-report-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-report-occurrence-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-report-occurrence-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-distribute-safety-bulletin-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-distribute-safety-bulletin-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-screen-dangerous-goods-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-screen-dangerous-goods-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-sms-handle-security-alert-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-sms-handle-security-alert-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-create-cargo-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-create-cargo-booking-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-issue-air-waybill-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-issue-air-waybill-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-accept-cargo-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-accept-cargo-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-assign-uld-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-assign-uld-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-track-shipment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-track-shipment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-process-claim-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-process-claim-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-settle-cargo-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-settle-cargo-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-cargo-report-cargo-security-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-cargo-report-cargo-security-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-enroll-member-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-enroll-member-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-accrue-points-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-accrue-points-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-redeem-reward-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-redeem-reward-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-update-tier-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-update-tier-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-transfer-miles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-transfer-miles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-process-purchase-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-process-purchase-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-expire-miles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-expire-miles-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/air-ffp-reconcile-partner-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/air-ffp-reconcile-partner-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
