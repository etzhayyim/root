"""Captured from Kysely migration 20260506230000_seed_hf_dataset_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506230000_seed_hf_dataset_bpmn"
down_revision = 'r_20260506220000_vertex_malak_agency_referral_export'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'hf_dataset_scan', 1,\n"
         '      $3, CAST($4 AS integer),\n'
         "      '00-contracts/bpmn/com/etzhayyim/hf/datasetScan.bpmn',\n"
         "      'active', $5, 1, $6, $7, 'sys.bpmn.seed.hf'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $8\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/hf-dataset-scan-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  hf.datasetScan — daily HuggingFace Hub catalog scan per enabled filter.\n'
                 '\n'
                 '  Fires every 24h. Iterates all enabled vertex_hf_filter rows, invokes\n'
                 '  hf.dataset.scan per filter, then fetches splits for newly found datasets.\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.hf.datasetScan\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/hf-dataset-scan-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_hf_dataset_scan"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/hf"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="hf_dataset_scan" name="HF Dataset Scan" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.hf.datasetScan", "version": 1, "resultTimeoutMs": '
                 '300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: every 24h -->\n'
                 '    <bpmn:startEvent id="Start" name="every 24h">\n'
                 '      <bpmn:outgoing>Flow_ToListFilters</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_24h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT24H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToListFilters" sourceRef="Start" '
                 'targetRef="Task_ListFilters"/>\n'
                 '\n'
                 '    <!-- Step 1: fetch enabled filter IDs from RW -->\n'
                 '    <bpmn:serviceTask id="Task_ListFilters" name="list enabled filters">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="hf.dataset.listFilters" retries="3"/>\n'
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
                 '    <!-- Step 2: scan HF Hub per filter (serial, respects rate limits) -->\n'
                 '    <bpmn:serviceTask id="Task_ScanAll" name="scan HF Hub per filter">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="hf.dataset.scanAll" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=filterIds"    target="filter_ids"/>\n'
                 '          <zeebe:output source="=total_scanned" target="totalScanned"/>\n'
                 '          <zeebe:output source="=total_matched" target="totalMatched"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToScanAll</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToFetchSplits</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToFetchSplits" sourceRef="Task_ScanAll" '
                 'targetRef="Task_FetchSplits"/>\n'
                 '\n'
                 '    <!-- Step 3: fetch split/parquet metadata for pending datasets -->\n'
                 '    <bpmn:serviceTask id="Task_FetchSplits" name="fetch splits for new '
                 'datasets">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="hf.dataset.fetchSplitsBatch" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=50"           target="batch_size"/>\n'
                 '          <zeebe:output source="=splits_total" target="splitsTotal"/>\n'
                 '          <zeebe:output source="=files_total"  target="filesTotal"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToFetchSplits</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_FetchSplits" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3758,
                 '2026-05-06T22:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/hf-dataset-scan-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '       created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'hf_dataset_scan',\n"
         "      'com.etzhayyim.apps.hf.datasetScan',\n"
         "      $3, 1, $4, $5, 'sys.bpmn.seed.hf'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $6\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/hf-dataset-scan-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '2026-05-06T22:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/hf-dataset-scan-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_hfhub_filter\n'
         '      (vertex_id, created_date, slug, display_name, description,\n'
         '       filter_tags, filter_tasks, filter_languages,\n'
         '       filter_license, min_downloads, exclude_private, enabled,\n'
         '       actor_did, created_at)\n'
         '    SELECT\n'
         "      'hf:filter:nlp-ja', '2026-05-06'::date,\n"
         "      'nlp-ja',\n"
         "      'Japanese NLP datasets',\n"
         "      'Datasets with language:ja tag for Japanese NLP tasks',\n"
         '      \'["language:ja"]\',\n'
         '      '
         '\'["task_categories:text-classification","task_categories:question-answering","task_categories:summarization"]\',\n'
         '      \'["ja"]\',\n'
         '      NULL, 100, TRUE, TRUE,\n'
         "      $1, '2026-05-06 22:00:00'::timestamp\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_hfhub_filter WHERE vertex_id = '
         "'hf:filter:nlp-ja')\n"
         '  ',
  'parameters': ['did:web:ingest.etzhayyim.com']},
 {'sql': '\n'
         '    INSERT INTO vertex_hfhub_filter\n'
         '      (vertex_id, created_date, slug, display_name, description,\n'
         '       filter_tags, filter_tasks, filter_languages,\n'
         '       filter_license, min_downloads, exclude_private, enabled,\n'
         '       actor_did, created_at)\n'
         '    SELECT\n'
         "      'hf:filter:text-clf-popular', '2026-05-06'::date,\n"
         "      'text-clf-popular',\n"
         "      'Popular text classification datasets',\n"
         "      'Text classification datasets with 1K+ monthly downloads',\n"
         "      '[]',\n"
         '      \'["task_categories:text-classification"]\',\n'
         "      '[]',\n"
         '      NULL, 1000, TRUE, TRUE,\n'
         "      $1, '2026-05-06 22:00:00'::timestamp\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_hfhub_filter WHERE vertex_id = '
         "'hf:filter:text-clf-popular')\n"
         '  ',
  'parameters': ['did:web:ingest.etzhayyim.com']}]

DOWN = [{'sql': 'DELETE FROM vertex_hfhub_filter WHERE vertex_id IN '
         "('hf:filter:nlp-ja','hf:filter:text-clf-popular')",
  'parameters': []},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/hf-dataset-scan-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/hf-dataset-scan-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
