"""Captured from Kysely migration 20260507765000_seed_ki_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507765000_seed_ki_bpmn"
down_revision = 'r_20260507764000_seed_saikin_bpmn'
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
         "        1, $8, $9, 'sys.bpmn.seed.ki'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/ki-vascular-synthesis-cycle-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'ki_vascular_synthesis_cycle',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_ki_vascular_synthesis" targetNamespace="https://etzhayyim.com/bpmn/ki" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="ki_vascular_synthesis_cycle" name="vascular-synthesis-cycle" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Absorb"/>\n'
                 '    <bpmn:serviceTask id="Task_Absorb" name="absorb">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="ki.absorb"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=absorbId" target="absorbId"/>\n'
                 '          <zeebe:output source="=status" target="absorbStatus"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_S</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_GW</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_GW" sourceRef="Task_Absorb" '
                 'targetRef="GW_HasAbsorb"/>\n'
                 '    <bpmn:exclusiveGateway id="GW_HasAbsorb" name="inputs absorbed?">\n'
                 '      <bpmn:incoming>Flow_GW</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_NoAbsorb</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_HasAbsorb</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_NoAbsorb" sourceRef="GW_HasAbsorb" '
                 'targetRef="End">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=absorbStatus '
                 '= "empty"</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_HasAbsorb" sourceRef="GW_HasAbsorb" '
                 'targetRef="Task_Synthesize">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=absorbStatus '
                 '= "absorbed"</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Synthesize" name="synthesize">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="ki.synthesize"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=absorbId" target="absorbId"/>\n'
                 '          <zeebe:output source="=artifactId" target="artifactId"/>\n'
                 '          <zeebe:output source="=synthesis" target="synthesis"/>\n'
                 '          <zeebe:output source="=confidence" target="confidence"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_HasAbsorb</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_GW2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_GW2" sourceRef="Task_Synthesize" '
                 'targetRef="GW_Confidence"/>\n'
                 '    <bpmn:exclusiveGateway id="GW_Confidence" name="confidence >= 0.7?">\n'
                 '      <bpmn:incoming>Flow_GW2</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Bloom</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_SkipBloom</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Bloom" sourceRef="GW_Confidence" '
                 'targetRef="Task_Bloom">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=confidence >= '
                 '0.7</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:serviceTask id="Task_Bloom" name="bloom">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="ki.bloom"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=artifactId" target="artifactId"/>\n'
                 '          <zeebe:output source="=bloomId" target="bloomId"/>\n'
                 '          <zeebe:output source="=publishedAt" target="publishedAt"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Bloom</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_AfterBloom</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_SkipBloom" sourceRef="GW_Confidence" '
                 'targetRef="GW_MergeToRing">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=confidence '
                 '&lt; 0.7</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_AfterBloom" sourceRef="Task_Bloom" '
                 'targetRef="GW_MergeToRing"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="GW_MergeToRing" name="merge">\n'
                 '      <bpmn:incoming>Flow_AfterBloom</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_SkipBloom</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToRing</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_ToRing" sourceRef="GW_MergeToRing" '
                 'targetRef="Task_Ring"/>\n'
                 '    <bpmn:serviceTask id="Task_Ring" name="ring">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="ki.ring"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;PT60M&quot;" target="period"/>\n'
                 '          <zeebe:output source="=ringId" target="ringId"/>\n'
                 '          <zeebe:output source="=snapshotCount" target="snapshotCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToRing</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Ring" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:ki.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ki.vascular_synthesis&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={absorbId: absorbId, artifactId: artifactId, '
                 'bloomId: bloomId, ringId: ringId, confidence: confidence, snapshotCount: '
                 'snapshotCount}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_NoAbsorb</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 6016,
                 '00-contracts/bpmn/com/etzhayyim/ki/vascular-synthesis-cycle.bpmn',
                 '2026-05-07T19:31:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/ki-vascular-synthesis-cycle-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '         created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 1, $6, $7, 'sys.bpmn.seed.ki'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $8\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/ki-vascular-synthesis-cycle-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'ki_vascular_synthesis_cycle',
                 'com.etzhayyim.apps.ki.absorb',
                 '2026-05-07T19:31:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/ki-vascular-synthesis-cycle-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/ki-vascular-synthesis-cycle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/ki-vascular-synthesis-cycle-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
