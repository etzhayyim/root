"""Captured from Kysely migration 20260429090400_seed_smishing_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429090400_seed_smishing_bpmn_actors"
down_revision = 'r_20260429090200_seed_media_gamers_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/smishing-analyzeMessage-v1',
                 'did:web:smishing.gftd.ai',
                 'smishing_analyze_message',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_smishing_analyze_message"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/smishing"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="smishing_analyze_message" name="smishing analyze message" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="sms analysis requested">\n'
                 '      <bpmn:outgoing>Flow_Classify</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Classify" sourceRef="Start" '
                 'targetRef="Task_Classify"/>\n'
                 '    <bpmn:serviceTask id="Task_Classify" name="classify sms message">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="smishing.message.classify"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=smsId" target="smsId"/>\n'
                 '          <zeebe:input source="=senderAddress" target="senderAddress"/>\n'
                 '          <zeebe:input source="=body" target="body"/>\n'
                 '          <zeebe:input source="=timestamp" target="timestamp"/>\n'
                 '          <zeebe:output source="=classification" target="classification"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Classify</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Analyze</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Analyze" sourceRef="Task_Classify" '
                 'targetRef="Task_Analyze"/>\n'
                 '    <bpmn:serviceTask id="Task_Analyze" name="deep analyze and commit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="smishing.message.deepAnalyze"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=smsId" target="smsId"/>\n'
                 '          <zeebe:input source="=senderAddress" target="senderAddress"/>\n'
                 '          <zeebe:input source="=body" target="body"/>\n'
                 '          <zeebe:input source="=timestamp" target="timestamp"/>\n'
                 '          <zeebe:input source="=publish" target="publish"/>\n'
                 '          <zeebe:input source="=classification" target="classification"/>\n'
                 '          <zeebe:output source="=result" target="result"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Analyze</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Analyze" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit smishing analysis">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:smishing.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;smishing.analyzeMessage&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ smsId: string(smsId), result: result }" '
                 'target="payload"/>\n'
                 '          <zeebe:output source="=rkey" target="auditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="smishing analysis committed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3282,
                 '00-contracts/bpmn/ai/gftd/smishing/analyzeMessage.bpmn',
                 '2026-04-29T09:04:00Z',
                 'did:web:smishing.gftd.ai',
                 'did:web:smishing.gftd.ai',
                 'sys.bpmn.seed.smishing',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/smishing-analyzeMessage-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST(120000 AS integer), 'active',\n"
         '      $5, 1, $6, $7, $8\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/smishing-analyzeMessage-v1',
                 'did:web:smishing.gftd.ai',
                 'ai.gftd.apps.smishing.analyzeMessageProcess',
                 'smishing_analyze_message',
                 '2026-04-29T09:04:00Z',
                 'did:web:smishing.gftd.ai',
                 'did:web:smishing.gftd.ai',
                 'sys.bpmn.seed.smishing',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/smishing-analyzeMessage-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/smishing-analyzeMessage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/smishing-analyzeMessage-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
