"""Captured from Kysely migration 20260429090600_seed_livecam_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429090600_seed_livecam_bpmn_actors"
down_revision = 'r_20260429090500_seed_legal_entity_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/livecam-analyzeCamera-v1',
                 'did:web:livecam.gftd.ai',
                 'livecam_analyze_camera',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_livecam_analyze_camera"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/livecam"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="livecam_analyze_camera" name="livecam analyze camera" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="camera frame analysis requested">\n'
                 '      <bpmn:outgoing>Flow_Analyze</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Analyze" sourceRef="Start" '
                 'targetRef="Task_Analyze"/>\n'
                 '    <bpmn:serviceTask id="Task_Analyze" name="analyze frame and commit '
                 'records">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="livecam.vision.analyzeCamera"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=cameraSlug" target="cameraSlug"/>\n'
                 '          <zeebe:input source="=imageUrl" target="imageUrl"/>\n'
                 '          <zeebe:input source="=imageBase64" target="imageBase64"/>\n'
                 '          <zeebe:input source="=zoneSlug" target="zoneSlug"/>\n'
                 '          <zeebe:input source="=country" target="country"/>\n'
                 '          <zeebe:input source="=region" target="region"/>\n'
                 '          <zeebe:output source="=result" target="result"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Analyze</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Analyze" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit livecam vision analysis">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:livecam.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;livecam.analyzeCamera&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ cameraSlug: cameraSlug, zoneSlug: zoneSlug, '
                 'result: result }" target="payload"/>\n'
                 '          <zeebe:output source="=rkey" target="auditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="camera analysis committed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2518,
                 '00-contracts/bpmn/ai/gftd/livecam/analyzeCamera.bpmn',
                 '2026-04-29T09:06:00Z',
                 'did:web:livecam.gftd.ai',
                 'did:web:livecam.gftd.ai',
                 'sys.bpmn.seed.livecam',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/livecam-analyzeCamera-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/livecam-analyzeCamera-v1',
                 'did:web:livecam.gftd.ai',
                 'ai.gftd.apps.livecam.analyzeCamera',
                 'livecam_analyze_camera',
                 120000,
                 '2026-04-29T09:06:00Z',
                 'did:web:livecam.gftd.ai',
                 'did:web:livecam.gftd.ai',
                 'sys.bpmn.seed.livecam',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/livecam-analyzeCamera-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/livecam-analyzeCamera-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/livecam-analyzeCamera-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
