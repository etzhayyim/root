"""Captured from Kysely migration 20260506000000_adsk_bpmn_v2_cron_timer."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506000000_adsk_bpmn_v2_cron_timer"
down_revision = 'r_20260505230000_vertex_zeebe_monitor'
branch_labels = None
depends_on = None

UP = [{'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/adsk-ingest-dataset-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, CAST(2 AS int), $4, CAST($5 AS integer), $6, 'active', $7, CAST(1 "
         'AS int), $8, $9, $10\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/adsk-ingest-dataset-v2',
                 'did:web:adsk.etzhayyim.com',
                 'adsk_ingest_dataset',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  adsk.etzhayyim.com — HuggingFace dataset ingest (autonomous, monthly).\n'
                 '\n'
                 '  Timer-start: every 30d. Iterates vertex_hf_dataset rows with\n'
                 "  status='active' and last_synced_at older than 28d, calling the\n"
                 '  pyzeebe primitive task_adsk_dataset_ingest_all (which itself does\n'
                 '  the loop). Phase 1 seed = 5 ADSKAILab text/code datasets.\n'
                 '\n'
                 '  Manual one-shot ingest: see CLAUDE.md "Recent Completion: adsk".\n'
                 '\n'
                 '  No XRPC entry. No CF Worker. Pure BPMN-as-actor + pyzeebe handler.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_adsk_ingest_dataset"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/adsk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="adsk_ingest_dataset" name="adsk HF dataset ingest (monthly)" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="monthly day 6">\n'
                 '      <bpmn:outgoing>Flow_Ingest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0 0 6 * '
                 '?</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_IngestAll" name="ingest all HF datasets in '
                 'catalog">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="adsk.dataset.ingestAll"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=2419200" target="staleSeconds"/>\n'
                 '          <zeebe:input source="=10000" target="perDatasetLimit"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Ingest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Ingest" sourceRef="StartTimer" '
                 'targetRef="Task_IngestAll"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:adsk.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;adsk.dataset.ingestAll&quot;" '
                 'target="action"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_IngestAll" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2674,
                 '00-contracts/bpmn/ai/gftd/adsk/ingestAdskDataset.bpmn',
                 '2026-05-06T00:00:00Z',
                 'did:web:adsk.etzhayyim.com',
                 'did:web:adsk.etzhayyim.com',
                 'sys.bpmn.seed.adsk-cron',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/adsk-ingest-dataset-v2']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/adsk-ingest-dataset-v2']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
