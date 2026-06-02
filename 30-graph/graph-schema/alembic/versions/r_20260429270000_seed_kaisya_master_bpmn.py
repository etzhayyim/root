"""Captured from Kysely migration 20260429270000_seed_kaisya_master_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429270000_seed_kaisya_master_bpmn"
down_revision = 'r_20260429260000_vertex_kaisya_org_snapshot'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, $3, 1, $4,\n'
         "             CAST($5 AS integer), $6, 'active', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def\n'
         '        WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-master-routine-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'kaisya_master_routine',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_kaisya_master_routine" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kaisya" exporter="hand-written" '
                 'exporterVersion="2.0">\n'
                 '  <bpmn:process id="kaisya_master_routine" name="kaisya Master Routine" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "com.etzhayyim.apps.kaisya.masterRoutine", '
                 '"version": 1, "resultTimeoutMs": 120000 }</bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="Every 30 min">\n'
                 '      <bpmn:outgoing>Flow_start_to_collect</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef_30m">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_start_to_collect" sourceRef="Start_Timer" '
                 'targetRef="Task_collectState"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_collectState" name="Collect Org State">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="kaisya.master.collectState"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=orgState" target="orgState"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_start_to_collect</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_collect_to_evaluate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_collect_to_evaluate" '
                 'sourceRef="Task_collectState" targetRef="Task_evaluateObjective"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_evaluateObjective" name="Evaluate Objective '
                 'Ω(t)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="kaisya.master.evaluateObjective"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=orgState" target="orgState"/>\n'
                 '          <zeebe:output source="=omega" target="omega"/>\n'
                 '          <zeebe:output source="=etaValue" target="etaValue"/>\n'
                 '          <zeebe:output source="=uTotal" target="uTotal"/>\n'
                 '          <zeebe:output source="=spiritScore" target="spiritScore"/>\n'
                 '          <zeebe:output source="=bufferScore" target="bufferScore"/>\n'
                 '          <zeebe:output source="=feelingScore" target="feelingScore"/>\n'
                 '          <zeebe:output source="=wellbecomingScore" '
                 'target="wellbecomingScore"/>\n'
                 '          <zeebe:output source="=separationDelta" target="separationDelta"/>\n'
                 '          <zeebe:output source="=decisions" target="decisions"/>\n'
                 '          <zeebe:output source="=criticalAlerts" target="criticalAlerts"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_collect_to_evaluate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_evaluate_to_execute</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_evaluate_to_execute" '
                 'sourceRef="Task_evaluateObjective" targetRef="Task_executeDecisions"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_executeDecisions" name="Execute Decisions">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="kaisya.master.executeDecisions"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=decisions" target="decisions"/>\n'
                 '          <zeebe:input source="=omega" target="omega"/>\n'
                 '          <zeebe:output source="=actionsExecuted" target="actionsExecuted"/>\n'
                 '          <zeebe:output source="=tasksCreated" target="tasksCreated"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_evaluate_to_execute</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_execute_to_snapshot</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_execute_to_snapshot" '
                 'sourceRef="Task_executeDecisions" targetRef="Task_writeSnapshot"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_writeSnapshot" name="Write Org Snapshot">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="kaisya.master.writeSnapshot"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=omega" target="omega"/>\n'
                 '          <zeebe:input source="=etaValue" target="etaValue"/>\n'
                 '          <zeebe:input source="=uTotal" target="uTotal"/>\n'
                 '          <zeebe:input source="=spiritScore" target="spiritScore"/>\n'
                 '          <zeebe:input source="=bufferScore" target="bufferScore"/>\n'
                 '          <zeebe:input source="=feelingScore" target="feelingScore"/>\n'
                 '          <zeebe:input source="=wellbecomingScore" target="wellbecomingScore"/>\n'
                 '          <zeebe:input source="=separationDelta" target="separationDelta"/>\n'
                 '          <zeebe:input source="=actionsExecuted" target="actionsExecuted"/>\n'
                 '          <zeebe:input source="=tasksCreated" target="tasksCreated"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_execute_to_snapshot</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_snapshot_to_end</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_snapshot_to_end" sourceRef="Task_writeSnapshot" '
                 'targetRef="End_Done"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End_Done" name="Done">\n'
                 '      <bpmn:incoming>Flow_snapshot_to_end</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5024,
                 '00-contracts/bpmn/com/etzhayyim/kaisya/masterRoutine.bpmn',
                 '2026-04-29T23:35:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.kaisya',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-master-routine-v1']}]

DOWN = [{'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kaisya-master-routine-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
