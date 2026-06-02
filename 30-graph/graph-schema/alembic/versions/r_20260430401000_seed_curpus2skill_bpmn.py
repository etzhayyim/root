"""Captured from Kysely migration 20260430401000_seed_curpus2skill_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430401000_seed_curpus2skill_bpmn"
down_revision = 'r_20260430400000_corpus_skill_extraction'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT $1, $2, $3, 1, $4,\n'
         "           CAST($5 AS integer), $6, 'active', $7,\n"
         '           1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/curpus2skill-extractEvidence-v1',
                 'did:web:recruit.etzhayyim.com',
                 'curpus2skill_extract_evidence',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_curpus2skill_extract_evidence" '
                 'targetNamespace="https://etzhayyim.com/bpmn/curpus2skill" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="curpus2skill_extract_evidence" name="curpus2skill '
                 'extractEvidence" isExecutable="true">\n'
                 '    <bpmn:documentation>{ "taskType": "curpus2skill.extractEvidence", '
                 '"resident": true, "defaultSource": "legal-corpus" }</bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 6 hours">\n'
                 '      <bpmn:outgoing>Flow_Timer_Task</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT6H">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT6H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual">\n'
                 '      <bpmn:outgoing>Flow_Manual_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Timer_Task" sourceRef="Start_Timer" '
                 'targetRef="Task_Extract"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual_Task" sourceRef="Start_Manual" '
                 'targetRef="Task_Extract"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Extract" name="extract corpus skill evidence">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="curpus2skill.extractEvidence" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if source = null then &quot;legal-corpus&quot; '
                 'else source" target="source"/>\n'
                 '          <zeebe:input source="=if limit = null then 10 else limit" '
                 'target="limit"/>\n'
                 '          <zeebe:input source="=if skillLimit = null then 2000 else skillLimit" '
                 'target="skillLimit"/>\n'
                 '          <zeebe:input source="=if minScore = null then 0.97 else minScore" '
                 'target="minScore"/>\n'
                 '          <zeebe:input source="=if topK = null then 5 else topK" '
                 'target="topK"/>\n'
                 '          <zeebe:input source="=if dryRun = null then false else dryRun" '
                 'target="dryRun"/>\n'
                 '          <zeebe:output source="=runId" target="runId"/>\n'
                 '          <zeebe:output source="=source" target="source"/>\n'
                 '          <zeebe:output source="=sourceTable" target="sourceTable"/>\n'
                 '          <zeebe:output source="=documentsScanned" target="documentsScanned"/>\n'
                 '          <zeebe:output source="=skillsLoaded" target="skillsLoaded"/>\n'
                 '          <zeebe:output source="=matchedDocuments" target="matchedDocuments"/>\n'
                 '          <zeebe:output source="=emittedEdges" target="emittedEdges"/>\n'
                 '          <zeebe:output source="=sample" target="sample"/>\n'
                 '          <zeebe:output source="=error" target="error"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Timer_Task</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_Manual_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit result">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="1"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:recruit.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;curpus2skill.extractEvidence&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={runId: runId, source: source, sourceTable: '
                 'sourceTable, documentsScanned: documentsScanned, skillsLoaded: skillsLoaded, '
                 'matchedDocuments: matchedDocuments, emittedEdges: emittedEdges, error: error}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Extract" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3947,
                 '00-contracts/bpmn/com/etzhayyim/curpus2skill/extractEvidence.bpmn',
                 '2026-04-30T12:35:00Z',
                 'did:web:recruit.etzhayyim.com',
                 'did:web:recruit.etzhayyim.com',
                 'sys.bpmn.seed.curpus2skill',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/curpus2skill-extractEvidence-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/curpus2skill-extractEvidence-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
