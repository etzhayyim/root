"""Captured from Kysely migration 20260506250000_seed_hf_model_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506250000_seed_hf_model_bpmn"
down_revision = 'r_20260506241000_seed_malak_phishing_traps'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'hf_model_scan', 1,\n"
         '      $3, CAST($4 AS integer),\n'
         "      '00-contracts/bpmn/ai/gftd/hf/modelScan.bpmn',\n"
         "      'active', $5, 1, $6, $7, 'sys.bpmn.seed.hf'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $8\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/hf-model-scan-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  hf.modelScan — daily HuggingFace Hub model catalog scan.\n'
                 '\n'
                 '  Fires every 12h (models update more frequently than datasets).\n'
                 '  Step 1: list enabled model filters → Step 2: scan HF Hub per filter\n'
                 '       → Step 3: fetch full card for unenriched models → Step 4: resolve '
                 'lineage.\n'
                 '\n'
                 '  NSID: app.etzhayyim.apps.hf.modelScan\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/hf-model-scan-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_hf_model_scan"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/hf"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="hf_model_scan" name="HF Model Scan" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.hf.modelScan", "version": 1, "resultTimeoutMs": '
                 '300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="every 12h">\n'
                 '      <bpmn:outgoing>Flow_ToListFilters</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_12h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT12H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToListFilters" sourceRef="Start" '
                 'targetRef="Task_ListFilters"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ListFilters" name="list model filters">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="hf.model.listFilters" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=filter_ids"   target="filterIds"/>\n'
                 '          <zeebe:output source="=filter_count" target="filterCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToListFilters</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToScanAll</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToScanAll" sourceRef="Task_ListFilters" '
                 'targetRef="Task_ScanAll"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ScanAll" name="scan HF Hub per model filter">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="hf.model.scanAll" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=filterIds"      target="filter_ids"/>\n'
                 '          <zeebe:output source="=total_scanned"  target="totalScanned"/>\n'
                 '          <zeebe:output source="=total_matched"  target="totalMatched"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToScanAll</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnrich</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnrich" sourceRef="Task_ScanAll" '
                 'targetRef="Task_Enrich"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Enrich" name="fetch full card for unenriched '
                 'models">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="hf.model.fetchDetailBatch" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=30"         target="batch_size"/>\n'
                 '          <zeebe:output source="=enriched"   target="enriched"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToEnrich</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToLineage</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToLineage" sourceRef="Task_Enrich" '
                 'targetRef="Task_Lineage"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Lineage" name="resolve base model + dataset '
                 'links">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="hf.model.resolveLineage" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=50"           target="batch_size"/>\n'
                 '          <zeebe:output source="=ds_resolved"  target="dsResolved"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToLineage</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Lineage" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4117,
                 '2026-05-06T23:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/hf-model-scan-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '       created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'hf_model_scan',\n"
         "      'app.etzhayyim.apps.hf.modelScan',\n"
         "      $3, 1, $4, $5, 'sys.bpmn.seed.hf'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $6\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/hf-model-scan-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '2026-05-06T23:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/hf-model-scan-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_hfhub_filter\n'
         '      (vertex_id, created_date, slug, display_name, description,\n'
         '       filter_tags, filter_tasks, filter_languages, filter_license,\n'
         '       min_downloads, exclude_private, enabled, entity_type, actor_did, created_at)\n'
         '    SELECT\n'
         "      'hf:filter:llm-popular-models', '2026-05-06'::date,\n"
         "      'llm-popular-models',\n"
         "      'Popular LLM & VLM models',\n"
         "      'text-generation and image-text-to-text models with 1K+ monthly downloads',\n"
         "      '[]',\n"
         '      \'["task_categories:text-generation","task_categories:image-text-to-text"]\',\n'
         "      '[]',\n"
         "      NULL, 1000, TRUE, TRUE, 'model',\n"
         "      $1, '2026-05-06 23:00:00'::timestamp\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_hfhub_filter WHERE vertex_id = '
         "'hf:filter:llm-popular-models')\n"
         '  ',
  'parameters': ['did:web:ingest.etzhayyim.com']},
 {'sql': '\n'
         '    INSERT INTO vertex_hfhub_filter\n'
         '      (vertex_id, created_date, slug, display_name, description,\n'
         '       filter_tags, filter_tasks, filter_languages, filter_license,\n'
         '       min_downloads, exclude_private, enabled, entity_type, actor_did, created_at)\n'
         '    SELECT\n'
         "      'hf:filter:japanese-models', '2026-05-06'::date,\n"
         "      'japanese-models',\n"
         "      'Japanese language models',\n"
         "      'Models tagged with language:ja, any task category',\n"
         '      \'["language:ja"]\',\n'
         "      '[]',\n"
         '      \'["ja"]\',\n'
         "      NULL, 100, TRUE, TRUE, 'model',\n"
         "      $1, '2026-05-06 23:00:00'::timestamp\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_hfhub_filter WHERE vertex_id = '
         "'hf:filter:japanese-models')\n"
         '  ',
  'parameters': ['did:web:ingest.etzhayyim.com']},
 {'sql': '\n'
         '    INSERT INTO vertex_hfhub_filter\n'
         '      (vertex_id, created_date, slug, display_name, description,\n'
         '       filter_tags, filter_tasks, filter_languages, filter_license,\n'
         '       min_downloads, exclude_private, enabled, entity_type, actor_did, created_at)\n'
         '    SELECT\n'
         "      'hf:filter:apache2-models', '2026-05-06'::date,\n"
         "      'apache2-models',\n"
         "      'Apache-2.0 licensed models',\n"
         "      'Models with Apache-2.0 license, 500+ monthly downloads',\n"
         "      '[]', '[]', '[]',\n"
         "      'apache-2.0', 500, TRUE, TRUE, 'model',\n"
         "      $1, '2026-05-06 23:00:00'::timestamp\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_hfhub_filter WHERE vertex_id = '
         "'hf:filter:apache2-models')\n"
         '  ',
  'parameters': ['did:web:ingest.etzhayyim.com']}]

DOWN = [{'sql': 'DELETE FROM vertex_hfhub_filter WHERE vertex_id IN (\n'
         '    '
         "'hf:filter:llm-popular-models','hf:filter:japanese-models','hf:filter:apache2-models'\n"
         '  )',
  'parameters': []},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/hf-model-scan-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/hf-model-scan-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
