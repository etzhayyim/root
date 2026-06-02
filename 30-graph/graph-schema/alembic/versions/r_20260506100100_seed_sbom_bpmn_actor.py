"""Captured from Kysely migration 20260506100100_seed_sbom_bpmn_actor."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506100100_seed_sbom_bpmn_actor"
down_revision = 'r_20260506100000_vertex_sbom_artifact'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord,\n'
         '      org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT $1, $2, $3, 1, $4,\n'
         "           CAST($5 AS integer), $6, 'active', $7,\n"
         '           1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sbom-register-artifact-v1',
                 'did:web:sbom.etzhayyim.com',
                 'sbom_register_artifact',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
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
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.sbom.registerArtifact"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Persist</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_VulnMatch</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Persist" sourceRef="StartManual" '
                 'targetRef="Task_Persist"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_VulnMatch" name="run vuln-match (purl × CVE)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.apps.sbom.runVulnMatch"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/sbom/registerArtifact.bpmn',
                 '2026-05-06T10:01:00Z',
                 'did:web:sbom.etzhayyim.com',
                 'did:web:sbom.etzhayyim.com',
                 'sys.bpmn.seed.sbom-register-artifact',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sbom-register-artifact-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '      org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT $1, $2, $3, $4, 1,\n'
         "           CAST($5 AS integer), 'active', $6,\n"
         '           1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sbom-registerArtifact-v1',
                 'did:web:sbom.etzhayyim.com',
                 'com.etzhayyim.apps.sbom.registerArtifact',
                 'sbom_register_artifact',
                 300000,
                 '2026-05-06T10:01:00Z',
                 'did:web:sbom.etzhayyim.com',
                 'did:web:sbom.etzhayyim.com',
                 'sys.bpmn.seed.sbom-register-artifact',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sbom-registerArtifact-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/sbom-registerArtifact-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/sbom-register-artifact-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
