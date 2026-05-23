"""Captured from Kysely migration 20260506120000_seed_sbom_phase_cd_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506120000_seed_sbom_phase_cd_bpmn"
down_revision = 'r_20260506120000_mv_aidesk_job_status'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/sbom-cve-ingest-osv-v1',
                 'did:web:sbom.etzhayyim.com',
                 'sbom_cve_ingest_osv',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  sbom.etzhayyim.com — cveIngestOsv (Phase C feeder).\n'
                 '\n'
                 '  Pull open-source vulnerabilities from osv.dev → vertex_cve_entry.\n'
                 '  XRPC-triggered for ad-hoc refresh; timer-start variant lives in\n'
                 '  cveIngestOsvDaily.bpmn (R/PT24H).\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_sbom_cve_ingest_osv"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/sbom"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="sbom_cve_ingest_osv" name="sbom cveIngest OSV" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartManual" name="xrpc">\n'
                 '      <bpmn:outgoing>Flow_Ingest</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="ingest OSV">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.sbom.cveIngestOsv"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Ingest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Ingest" sourceRef="StartManual" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:sb0m001x.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;sbom.cveIngestOsv&quot;" '
                 'target="action"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Ingest" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2052,
                 '00-contracts/bpmn/ai/gftd/sbom/cveIngestOsv.bpmn',
                 '2026-05-06T12:00:00Z',
                 'did:web:sbom.etzhayyim.com',
                 'did:web:sbom.etzhayyim.com',
                 'sys.bpmn.seed.sbom-phase-cd',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/sbom-cve-ingest-osv-v1']},
 {'sql': '\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/sbom-recall-v1',
                 'did:web:sbom.etzhayyim.com',
                 'sbom_recall',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  sbom.etzhayyim.com — recall (Phase D blast-radius query).\n'
                 '  Single task: pymagatama runs the supplier-scoped JOIN over\n'
                 '  vertex_sbom_component × vertex_sbom_artifact + vuln_match counts,\n'
                 '  returns the affected artifact list. Audit emit closes the trace.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_sbom_recall"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/sbom"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="sbom_recall" name="sbom recall (blast-radius)" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartManual" name="xrpc">\n'
                 '      <bpmn:outgoing>Flow_Run</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Run" name="run blast-radius query">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.ai.gftd.apps.sbom.recall"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Run</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Run" sourceRef="StartManual" '
                 'targetRef="Task_Run"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:sb0m001x.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;sbom.recall&quot;" target="action"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Run" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2056,
                 '00-contracts/bpmn/ai/gftd/sbom/recall.bpmn',
                 '2026-05-06T12:00:00Z',
                 'did:web:sbom.etzhayyim.com',
                 'did:web:sbom.etzhayyim.com',
                 'sys.bpmn.seed.sbom-phase-cd',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/sbom-recall-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/sbom-cveIngestOsv-v1',
                 'did:web:sbom.etzhayyim.com',
                 'ai.gftd.apps.sbom.cveIngestOsv',
                 'sbom_cve_ingest_osv',
                 3600000,
                 '2026-05-06T12:00:00Z',
                 'did:web:sbom.etzhayyim.com',
                 'did:web:sbom.etzhayyim.com',
                 'sys.bpmn.seed.sbom-phase-cd',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/sbom-cveIngestOsv-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/sbom-recall-v1',
                 'did:web:sbom.etzhayyim.com',
                 'ai.gftd.apps.sbom.recall',
                 'sbom_recall',
                 60000,
                 '2026-05-06T12:00:00Z',
                 'did:web:sbom.etzhayyim.com',
                 'did:web:sbom.etzhayyim.com',
                 'sys.bpmn.seed.sbom-phase-cd',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/sbom-recall-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/sbom-cveIngestOsv-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/sbom-recall-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/sbom-cve-ingest-osv-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/sbom-recall-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
