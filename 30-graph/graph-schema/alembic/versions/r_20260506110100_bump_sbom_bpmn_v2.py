"""Captured from Kysely migration 20260506110100_bump_sbom_bpmn_v2."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506110100_bump_sbom_bpmn_v2"
down_revision = 'r_20260506110000_vertex_shosha_schema'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    UPDATE vertex_bpmn_process_def\n'
         '       SET xml = $1,\n'
         '           xml_byte_size = CAST($2 AS integer),\n'
         '           version = 2,\n'
         '           created_at = $3\n'
         '     WHERE vertex_id = $4\n'
         '  ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  sbom.etzhayyim.com — registerArtifact BPMN (Phase C).\n'
                 '\n'
                 '  Persist the artifact + components, then run vuln-match against\n'
                 '  vertex_cve_entry (yabai feed), then audit-emit.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_sbom_register_artifact"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/sbom"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="sbom_register_artifact" name="sbom registerArtifact" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartManual" name="xrpc">\n'
                 '      <bpmn:outgoing>Flow_Persist</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Persist" name="register SBOM artifact + '
                 'components">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.sbom.registerArtifact"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Persist</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_VulnMatch</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Persist" sourceRef="StartManual" '
                 'targetRef="Task_Persist"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_VulnMatch" name="run vuln-match (purl × CVE)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.sbom.runVulnMatch"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_VulnMatch</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_VulnMatch" sourceRef="Task_Persist" '
                 'targetRef="Task_VulnMatch"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:sb0m001x.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;sbom.registerArtifact&quot;" '
                 'target="action"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_VulnMatch" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2490,
                 '2026-05-06T11:01:00Z',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/sbom-register-artifact-v1']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '       SET bpmn_version = 2,\n'
         '           created_at = $1\n'
         '     WHERE vertex_id = $2\n'
         '  ',
  'parameters': ['2026-05-06T11:01:00Z',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/sbom-registerArtifact-v1']}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
