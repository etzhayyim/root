"""Captured from Kysely migration 20260507764000_seed_saikin_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507764000_seed_saikin_bpmn"
down_revision = 'r_20260507763000_vertex_ki_tables'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         '        $4, CAST($5 AS integer),\n'
         "        $6, 'active', $7,\n"
         "        1, $8, $9, 'sys.bpmn.seed.saikin'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/saikin-horizontal-transfer-cycle-v1',
                 'did:web:bpmn.gftd.ai',
                 'saikin_horizontal_transfer_cycle',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_saikin_horizontal_transfer" '
                 'targetNamespace="https://gftd.ai/bpmn/saikin" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="saikin_horizontal_transfer_cycle" '
                 'name="horizontal-transfer-cycle" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT20M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_ProbeEnvironment"/>\n'
                 '    <bpmn:serviceTask id="Task_ProbeEnvironment" name="probe-environment">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="saikin.probe_environment"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=signalCount" target="signalCount"/>\n'
                 '          <zeebe:output source="=signals" target="signals"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_S</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_GW</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_GW" sourceRef="Task_ProbeEnvironment" '
                 'targetRef="GW_HasSignals"/>\n'
                 '    <bpmn:exclusiveGateway id="GW_HasSignals" name="signals found?">\n'
                 '      <bpmn:incoming>Flow_GW</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_NoSignals</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_HasSignals</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_NoSignals" sourceRef="GW_HasSignals" '
                 'targetRef="End">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=signalCount = '
                 '0</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_HasSignals" sourceRef="GW_HasSignals" '
                 'targetRef="Task_TransferSignal">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=signalCount > '
                 '0</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_TransferSignal" name="transfer-signal">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="saikin.transfer_signal"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=signals" target="signals"/>\n'
                 '          <zeebe:output source="=transferId" target="transferId"/>\n'
                 '          <zeebe:output source="=status" target="transferStatus"/>\n'
                 '          <zeebe:output source="=signalId" target="signalId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_HasSignals</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_GW2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_GW2" sourceRef="Task_TransferSignal" '
                 'targetRef="GW_ColonyOrLyse"/>\n'
                 '    <bpmn:exclusiveGateway id="GW_ColonyOrLyse" name="transfer complete?">\n'
                 '      <bpmn:incoming>Flow_GW2</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_FormColony</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Lyse</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_FormColony" sourceRef="GW_ColonyOrLyse" '
                 'targetRef="Task_FormColony">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=transferStatus = '
                 '"transferred"</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:serviceTask id="Task_FormColony" name="form-colony">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="saikin.form_colony"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=signalId" target="signalId"/>\n'
                 '          <zeebe:input source="=transferId" target="transferId"/>\n'
                 '          <zeebe:output source="=colonyId" target="colonyId"/>\n'
                 '          <zeebe:output source="=memberCount" target="memberCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_FormColony</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_AfterColony</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterColony" sourceRef="Task_FormColony" '
                 'targetRef="Task_HandoffToKi"/>\n'
                 '    <bpmn:serviceTask id="Task_HandoffToKi" name="handoff-to-ki">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="saikin.handoff_to_ki"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=colonyId" target="colonyId"/>\n'
                 '          <zeebe:input source="=signalId" target="signalId"/>\n'
                 '          <zeebe:output source="=kiAbsorbId" target="kiAbsorbId"/>\n'
                 '          <zeebe:output source="=kiAbsorbVertexId" target="kiAbsorbVertexId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_AfterColony</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_AfterKi</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Lyse" sourceRef="GW_ColonyOrLyse" '
                 'targetRef="Task_Lyse">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=transferStatus = '
                 '"completed"</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:serviceTask id="Task_Lyse" name="lyse">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="saikin.lyse"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=signalId" target="signalId"/>\n'
                 '          <zeebe:input source="=&quot;fully-transferred&quot;" '
                 'target="reason"/>\n'
                 '          <zeebe:output source="=lysed" target="lysed"/>\n'
                 '          <zeebe:output source="=releasedAt" target="releasedAt"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Lyse</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_AfterLyse</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterKi" sourceRef="Task_HandoffToKi" '
                 'targetRef="GW_MergeToAudit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterLyse" sourceRef="Task_Lyse" '
                 'targetRef="GW_MergeToAudit"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="GW_MergeToAudit" name="merge">\n'
                 '      <bpmn:incoming>Flow_AfterKi</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_AfterLyse</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="GW_MergeToAudit" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:saikin.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;saikin.horizontal_transfer&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={transferId: transferId, colonyId: colonyId, '
                 'signalId: signalId, kiAbsorbId: kiAbsorbId, lysed: lysed}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_NoSignals</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 7037,
                 '00-contracts/bpmn/ai/gftd/saikin/horizontal-transfer-cycle.bpmn',
                 '2026-05-07T19:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/saikin-horizontal-transfer-cycle-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '         created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 1, $6, $7, 'sys.bpmn.seed.saikin'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/saikin-horizontal-transfer-cycle-v1',
                 'did:web:bpmn.gftd.ai',
                 'saikin_horizontal_transfer_cycle',
                 'ai.gftd.apps.saikin.probeEnvironment',
                 '2026-05-07T19:30:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/saikin-horizontal-transfer-cycle-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/saikin-horizontal-transfer-cycle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/saikin-horizontal-transfer-cycle-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
