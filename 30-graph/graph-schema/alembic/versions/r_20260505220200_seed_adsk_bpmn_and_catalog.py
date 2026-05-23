"""Captured from Kysely migration 20260505220200_seed_adsk_bpmn_and_catalog."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260505220200_seed_adsk_bpmn_and_catalog"
down_revision = 'r_20260505220100_v_training_text_with_hf'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/adsk-ingest-dataset-v1',
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
                 '2026-05-05T22:00:00Z',
                 'did:web:adsk.etzhayyim.com',
                 'did:web:adsk.etzhayyim.com',
                 'sys.bpmn.seed.adsk-hf-ingest',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/adsk-ingest-dataset-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_hf_dataset (\n'
         '      vertex_id, owner_did, sensitivity_ord,\n'
         '      slug, org, name, modality, license, hf_url, task_categories, tags,\n'
         '      row_count_expected, row_count_ingested, last_synced_at, status,\n'
         '      created_at, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, CAST(0 AS int),\n'
         '      $3, $4, $5, $6, $7, $8, $9, $10,\n'
         "      CAST($11 AS bigint), CAST(0 AS bigint), CAST(NULL AS varchar), 'active',\n"
         '      $12, $13, $14, $15\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_hf_dataset WHERE vertex_id = $16)\n'
         '  ',
  'parameters': ['at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-Zero-To-CAD-100k',
                 'did:web:adsk.etzhayyim.com',
                 'ADSKAILab/Zero-To-CAD-100k',
                 'ADSKAILab',
                 'Zero-To-CAD-100k',
                 'code+image',
                 'apache-2.0',
                 'https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-100k',
                 'text-to-3d,image-to-3d',
                 'CAD,CadQuery,synthetic-data,construction-sequence,parametric-CAD,curated',
                 101516,
                 '2026-05-05T22:00:00Z',
                 'did:web:adsk.etzhayyim.com',
                 'did:web:adsk.etzhayyim.com',
                 'sys.bpmn.seed.adsk-hf-ingest',
                 'at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-Zero-To-CAD-100k']},
 {'sql': '\n'
         '    INSERT INTO vertex_hf_dataset (\n'
         '      vertex_id, owner_did, sensitivity_ord,\n'
         '      slug, org, name, modality, license, hf_url, task_categories, tags,\n'
         '      row_count_expected, row_count_ingested, last_synced_at, status,\n'
         '      created_at, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, CAST(0 AS int),\n'
         '      $3, $4, $5, $6, $7, $8, $9, $10,\n'
         "      CAST($11 AS bigint), CAST(0 AS bigint), CAST(NULL AS varchar), 'active',\n"
         '      $12, $13, $14, $15\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_hf_dataset WHERE vertex_id = $16)\n'
         '  ',
  'parameters': ['at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-Zero-To-CAD-1m',
                 'did:web:adsk.etzhayyim.com',
                 'ADSKAILab/Zero-To-CAD-1m',
                 'ADSKAILab',
                 'Zero-To-CAD-1m',
                 'code+image',
                 'apache-2.0',
                 'https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m',
                 'text-to-3d,image-to-3d',
                 'CAD,CadQuery,synthetic-data,construction-sequence,parametric-CAD',
                 1000000,
                 '2026-05-05T22:00:00Z',
                 'did:web:adsk.etzhayyim.com',
                 'did:web:adsk.etzhayyim.com',
                 'sys.bpmn.seed.adsk-hf-ingest',
                 'at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-Zero-To-CAD-1m']},
 {'sql': '\n'
         '    INSERT INTO vertex_hf_dataset (\n'
         '      vertex_id, owner_did, sensitivity_ord,\n'
         '      slug, org, name, modality, license, hf_url, task_categories, tags,\n'
         '      row_count_expected, row_count_ingested, last_synced_at, status,\n'
         '      created_at, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, CAST(0 AS int),\n'
         '      $3, $4, $5, $6, $7, $8, $9, $10,\n'
         "      CAST(NULL AS bigint), CAST(0 AS bigint), CAST(NULL AS varchar), 'active',\n"
         '      $11, $12, $13, $14\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_hf_dataset WHERE vertex_id = $15)\n'
         '  ',
  'parameters': ['at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-LLM-narrative-planning-taskset',
                 'did:web:adsk.etzhayyim.com',
                 'ADSKAILab/LLM-narrative-planning-taskset',
                 'ADSKAILab',
                 'LLM-narrative-planning-taskset',
                 'text',
                 'mit',
                 'https://huggingface.co/datasets/ADSKAILab/LLM-narrative-planning-taskset',
                 '',
                 'narrative-planning,story-generation,zip-archive',
                 '2026-05-05T22:00:00Z',
                 'did:web:adsk.etzhayyim.com',
                 'did:web:adsk.etzhayyim.com',
                 'sys.bpmn.seed.adsk-hf-ingest',
                 'at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-LLM-narrative-planning-taskset']},
 {'sql': '\n'
         '    INSERT INTO vertex_hf_dataset (\n'
         '      vertex_id, owner_did, sensitivity_ord,\n'
         '      slug, org, name, modality, license, hf_url, task_categories, tags,\n'
         '      row_count_expected, row_count_ingested, last_synced_at, status,\n'
         '      created_at, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, CAST(0 AS int),\n'
         '      $3, $4, $5, $6, $7, $8, $9, $10,\n'
         "      CAST($11 AS bigint), CAST(0 AS bigint), CAST(NULL AS varchar), 'active',\n"
         '      $12, $13, $14, $15\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_hf_dataset WHERE vertex_id = $16)\n'
         '  ',
  'parameters': ['at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-dsl-icl-eval-2025-01-21-113247-model-anthropic-claude-3-5-sonnet-fewshot-5',
                 'did:web:adsk.etzhayyim.com',
                 'ADSKAILab/dsl_icl_eval-2025_01_21_113247_model-anthropic-claude-3.5-sonnet_fewshot-5',
                 'ADSKAILab',
                 'dsl_icl_eval-claude-3.5-sonnet-fewshot-5',
                 'text',
                 '',
                 'https://huggingface.co/datasets/ADSKAILab/dsl_icl_eval-2025_01_21_113247_model-anthropic-claude-3.5-sonnet_fewshot-5',
                 '',
                 'DSL,IFC,architecture,eval,parquet',
                 10,
                 '2026-05-05T22:00:00Z',
                 'did:web:adsk.etzhayyim.com',
                 'did:web:adsk.etzhayyim.com',
                 'sys.bpmn.seed.adsk-hf-ingest',
                 'at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-dsl-icl-eval-2025-01-21-113247-model-anthropic-claude-3-5-sonnet-fewshot-5']},
 {'sql': '\n'
         '    INSERT INTO vertex_hf_dataset (\n'
         '      vertex_id, owner_did, sensitivity_ord,\n'
         '      slug, org, name, modality, license, hf_url, task_categories, tags,\n'
         '      row_count_expected, row_count_ingested, last_synced_at, status,\n'
         '      created_at, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, CAST(0 AS int),\n'
         '      $3, $4, $5, $6, $7, $8, $9, $10,\n'
         "      CAST($11 AS bigint), CAST(0 AS bigint), CAST(NULL AS varchar), 'active',\n"
         '      $12, $13, $14, $15\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_hf_dataset WHERE vertex_id = $16)\n'
         '  ',
  'parameters': ['at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-dsl-icl-eval-2025-01-21-112645-model-openai-gpt-4o-2024-11-20-fewshot-5',
                 'did:web:adsk.etzhayyim.com',
                 'ADSKAILab/dsl_icl_eval-2025_01_21_112645_model-openai-gpt-4o-2024-11-20_fewshot-5',
                 'ADSKAILab',
                 'dsl_icl_eval-gpt-4o-fewshot-5',
                 'text',
                 '',
                 'https://huggingface.co/datasets/ADSKAILab/dsl_icl_eval-2025_01_21_112645_model-openai-gpt-4o-2024-11-20_fewshot-5',
                 '',
                 'DSL,IFC,architecture,eval,parquet',
                 500,
                 '2026-05-05T22:00:00Z',
                 'did:web:adsk.etzhayyim.com',
                 'did:web:adsk.etzhayyim.com',
                 'sys.bpmn.seed.adsk-hf-ingest',
                 'at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-dsl-icl-eval-2025-01-21-112645-model-openai-gpt-4o-2024-11-20-fewshot-5']}]

DOWN = [{'sql': 'DELETE FROM vertex_hf_dataset WHERE vertex_id = $1',
  'parameters': ['at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-Zero-To-CAD-100k']},
 {'sql': 'DELETE FROM vertex_hf_dataset WHERE vertex_id = $1',
  'parameters': ['at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-Zero-To-CAD-1m']},
 {'sql': 'DELETE FROM vertex_hf_dataset WHERE vertex_id = $1',
  'parameters': ['at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-LLM-narrative-planning-taskset']},
 {'sql': 'DELETE FROM vertex_hf_dataset WHERE vertex_id = $1',
  'parameters': ['at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-dsl-icl-eval-2025-01-21-113247-model-anthropic-claude-3-5-sonnet-fewshot-5']},
 {'sql': 'DELETE FROM vertex_hf_dataset WHERE vertex_id = $1',
  'parameters': ['at://did:web:adsk.etzhayyim.com/ai.gftd.apps.adsk.dataset/ADSKAILab-dsl-icl-eval-2025-01-21-112645-model-openai-gpt-4o-2024-11-20-fewshot-5']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/adsk-ingest-dataset-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
