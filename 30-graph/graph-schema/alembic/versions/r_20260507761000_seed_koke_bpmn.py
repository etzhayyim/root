"""Captured from Kysely migration 20260507761000_seed_koke_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507761000_seed_koke_bpmn"
down_revision = 'r_20260507760000_vertex_koke_tables'
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
         "        1, $8, $9, 'sys.bpmn.seed.koke'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/koke-photosynthesis-cycle-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'koke_photosynthesis_cycle',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_koke_photosynthesis" targetNamespace="https://etzhayyim.com/bpmn/koke" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="koke_photosynthesis_cycle" name="photosynthesis-cycle" '
                 'isExecutable="true">\n'
                 '    <!-- Timer start: every 30 minutes, scan for unfixed raw signals -->\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '      <bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <!-- Step 1: Scan for unfixed raw signals -->\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_ScanSignals"/>\n'
                 '    <bpmn:serviceTask id="Task_ScanSignals" name="scan-raw-signals">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="koke.scan_raw_signals"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=signalCount" target="signalCount"/>\n'
                 '          <zeebe:output source="=signals" target="signals"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_S</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_GW</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Gateway: any signals to process? -->\n'
                 '    <bpmn:sequenceFlow id="Flow_GW" sourceRef="Task_ScanSignals" '
                 'targetRef="GW_HasSignals"/>\n'
                 '    <bpmn:exclusiveGateway id="GW_HasSignals" name="signals found?">\n'
                 '      <bpmn:incoming>Flow_GW</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_NoSignals</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_HasSignals</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <!-- No signals branch → end -->\n'
                 '    <bpmn:sequenceFlow id="Flow_NoSignals" sourceRef="GW_HasSignals" '
                 'targetRef="End">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=signalCount = '
                 '0</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <!-- Has signals branch → fix signal -->\n'
                 '    <bpmn:sequenceFlow id="Flow_HasSignals" sourceRef="GW_HasSignals" '
                 'targetRef="Task_FixSignal">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=signalCount > '
                 '0</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <!-- Step 2: Primary fixation (CO₂ → glucose) -->\n'
                 '    <bpmn:serviceTask id="Task_FixSignal" name="fix-signal">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="koke.fix_signal"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=signals" target="signals"/>\n'
                 '          <zeebe:output source="=fixationId" target="fixationId"/>\n'
                 '          <zeebe:output source="=signalHash" target="signalHash"/>\n'
                 '          <zeebe:output source="=inputKind" target="inputKind"/>\n'
                 '          <zeebe:output source="=rawRef" target="rawRef"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_HasSignals</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Classify</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Step 3: Classify fixation -->\n'
                 '    <bpmn:sequenceFlow id="Flow_Classify" sourceRef="Task_FixSignal" '
                 'targetRef="Task_ClassifyFixation"/>\n'
                 '    <bpmn:serviceTask id="Task_ClassifyFixation" name="classify-fixation">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="koke.classify_fixation"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=fixationId" target="fixationId"/>\n'
                 '          <zeebe:input source="=inputKind" target="inputKind"/>\n'
                 '          <zeebe:input source="=rawRef" target="rawRef"/>\n'
                 '          <zeebe:output source="=classification" target="classification"/>\n'
                 '          <zeebe:output source="=confidence" target="confidence"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Classify</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_GW2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Gateway: high confidence → handoff to hakkou -->\n'
                 '    <bpmn:sequenceFlow id="Flow_GW2" sourceRef="Task_ClassifyFixation" '
                 'targetRef="GW_Confidence"/>\n'
                 '    <bpmn:exclusiveGateway id="GW_Confidence" name="confidence >= 0.7?">\n'
                 '      <bpmn:incoming>Flow_GW2</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Handoff</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <!-- High confidence → handoff to hakkou -->\n'
                 '    <bpmn:sequenceFlow id="Flow_Handoff" sourceRef="GW_Confidence" '
                 'targetRef="Task_HandoffToHakkou">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=confidence >= '
                 '0.7</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:serviceTask id="Task_HandoffToHakkou" name="handoff-to-hakkou">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="koke.handoff_to_hakkou"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=fixationId" target="fixationId"/>\n'
                 '          <zeebe:input source="=classification" target="classification"/>\n'
                 '          <zeebe:input source="=inputKind" target="inputKind"/>\n'
                 '          <zeebe:input source="=rawRef" target="rawRef"/>\n'
                 '          <zeebe:output source="=fermentId" target="fermentId"/>\n'
                 '          <zeebe:output source="=edgeId" target="edgeId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Handoff</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_AfterHakkou</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Bridge: koke→saikin horizontal-transfer pipeline -->\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterHakkou" sourceRef="Task_HandoffToHakkou" '
                 'targetRef="Task_HandoffToSaikin"/>\n'
                 '    <bpmn:serviceTask id="Task_HandoffToSaikin" name="handoff-to-saikin">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="koke.handoff_to_saikin"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=fixationId" target="fixationId"/>\n'
                 '          <zeebe:input source="=classification" target="classification"/>\n'
                 '          <zeebe:input source="=inputKind" target="inputKind"/>\n'
                 '          <zeebe:input source="=rawRef" target="rawRef"/>\n'
                 '          <zeebe:output source="=saikinSignalId" target="saikinSignalId"/>\n'
                 '          <zeebe:output source="=saikinSignalVertexId" '
                 'target="saikinSignalVertexId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_AfterHakkou</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_AfterSaikin</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterSaikin" sourceRef="Task_HandoffToSaikin" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <!-- Low confidence → skip handoff, go to audit -->\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="GW_Confidence" '
                 'targetRef="Task_Audit">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=confidence '
                 '&lt; 0.7</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <!-- Audit emit -->\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:koke.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;koke.photosynthesize&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={fixationId: fixationId, classification: '
                 'classification, confidence: confidence, saikinSignalId: saikinSignalId}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_AfterSaikin</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
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
                 7765,
                 '00-contracts/bpmn/ai/gftd/koke/photosynthesis-cycle.bpmn',
                 '2026-05-07T19:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/koke-photosynthesis-cycle-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '         created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 1, $6, $7, 'sys.bpmn.seed.koke'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/koke-photosynthesis-cycle-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'koke_photosynthesis_cycle',
                 'app.etzhayyim.apps.koke.photosynthesize',
                 '2026-05-07T19:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/koke-photosynthesis-cycle-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/koke-photosynthesis-cycle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/koke-photosynthesis-cycle-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
