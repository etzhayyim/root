"""Captured from Kysely migration 20260430215100_seed_i18n_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430215100_seed_i18n_bpmn_actors"
down_revision = 'r_20260430215000_vertex_i18n_record'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-register-project-v1',
                 'did:web:i18n.etzhayyim.com',
                 'i18n_register_project',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_i18n_register_project" '
                 'targetNamespace="https://etzhayyim.com/bpmn/i18n"><bpmn:process '
                 'id="i18n_register_project" name="i18n registerProject" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.i18n.registerProject", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="register project"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="i18n.registerProject"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1012,
                 '00-contracts/bpmn/ai/gftd/i18n/registerProject.bpmn',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-register-project-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-register-project-v1',
                 'did:web:i18n.etzhayyim.com',
                 'app.etzhayyim.apps.i18n.registerProject',
                 'i18n_register_project',
                 'vertex_i18n_project,vertex_i18n_project_translation,vertex_i18n_translation_memory,vertex_i18n_text_node,vertex_i18n_credit_job,edge_i18n_project_translation,edge_i18n_translation_text,edge_i18n_text_language',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-register-project-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-batch-v1',
                 'did:web:i18n.etzhayyim.com',
                 'i18n_translate_batch',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_i18n_translate_batch" '
                 'targetNamespace="https://etzhayyim.com/bpmn/i18n"><bpmn:process '
                 'id="i18n_translate_batch" name="i18n translateBatch" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.i18n.translateBatch", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="translate batch"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="i18n.translateBatch"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1006,
                 '00-contracts/bpmn/ai/gftd/i18n/translateBatch.bpmn',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-batch-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-batch-v1',
                 'did:web:i18n.etzhayyim.com',
                 'app.etzhayyim.apps.i18n.translateBatch',
                 'i18n_translate_batch',
                 'vertex_i18n_project,vertex_i18n_project_translation,vertex_i18n_translation_memory,vertex_i18n_text_node,vertex_i18n_credit_job,edge_i18n_project_translation,edge_i18n_translation_text,edge_i18n_text_language',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-batch-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-export-messages-v1',
                 'did:web:i18n.etzhayyim.com',
                 'i18n_export_messages',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_i18n_export_messages" '
                 'targetNamespace="https://etzhayyim.com/bpmn/i18n"><bpmn:process '
                 'id="i18n_export_messages" name="i18n exportMessages" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.i18n.exportMessages", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="export messages"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="i18n.exportMessages"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1006,
                 '00-contracts/bpmn/ai/gftd/i18n/exportMessages.bpmn',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-export-messages-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-export-messages-v1',
                 'did:web:i18n.etzhayyim.com',
                 'app.etzhayyim.apps.i18n.exportMessages',
                 'i18n_export_messages',
                 '',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-export-messages-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-on-demand-v1',
                 'did:web:i18n.etzhayyim.com',
                 'i18n_translate_on_demand',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_i18n_translate_on_demand" '
                 'targetNamespace="https://etzhayyim.com/bpmn/i18n"><bpmn:process '
                 'id="i18n_translate_on_demand" name="i18n translateOnDemand" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.i18n.translateOnDemand", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="translate on demand"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="i18n.translateOnDemand"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1027,
                 '00-contracts/bpmn/ai/gftd/i18n/translateOnDemand.bpmn',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-on-demand-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-on-demand-v1',
                 'did:web:i18n.etzhayyim.com',
                 'app.etzhayyim.apps.i18n.translateOnDemand',
                 'i18n_translate_on_demand',
                 'vertex_i18n_project,vertex_i18n_project_translation,vertex_i18n_translation_memory,vertex_i18n_text_node,vertex_i18n_credit_job,edge_i18n_project_translation,edge_i18n_translation_text,edge_i18n_text_language',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-on-demand-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-page-v1',
                 'did:web:i18n.etzhayyim.com',
                 'i18n_translate_page',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_i18n_translate_page" '
                 'targetNamespace="https://etzhayyim.com/bpmn/i18n"><bpmn:process '
                 'id="i18n_translate_page" name="i18n translatePage" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.i18n.translatePage", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="translate page"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="i18n.translatePage"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1000,
                 '00-contracts/bpmn/ai/gftd/i18n/translatePage.bpmn',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-page-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-page-v1',
                 'did:web:i18n.etzhayyim.com',
                 'app.etzhayyim.apps.i18n.translatePage',
                 'i18n_translate_page',
                 'vertex_i18n_project,vertex_i18n_project_translation,vertex_i18n_translation_memory,vertex_i18n_text_node,vertex_i18n_credit_job,edge_i18n_project_translation,edge_i18n_translation_text,edge_i18n_text_language',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-page-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-message-v1',
                 'did:web:i18n.etzhayyim.com',
                 'i18n_translate_message',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_i18n_translate_message" '
                 'targetNamespace="https://etzhayyim.com/bpmn/i18n"><bpmn:process '
                 'id="i18n_translate_message" name="i18n translateMessage" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.i18n.translateMessage", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="translate message"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="i18n.translateMessage"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1018,
                 '00-contracts/bpmn/ai/gftd/i18n/translateMessage.bpmn',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-message-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-message-v1',
                 'did:web:i18n.etzhayyim.com',
                 'app.etzhayyim.apps.i18n.translateMessage',
                 'i18n_translate_message',
                 'vertex_i18n_project,vertex_i18n_project_translation,vertex_i18n_translation_memory,vertex_i18n_text_node,vertex_i18n_credit_job,edge_i18n_project_translation,edge_i18n_translation_text,edge_i18n_text_language',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-message-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-signal-v1',
                 'did:web:i18n.etzhayyim.com',
                 'i18n_translate_signal',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_i18n_translate_signal" '
                 'targetNamespace="https://etzhayyim.com/bpmn/i18n"><bpmn:process '
                 'id="i18n_translate_signal" name="i18n translateSignal" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.i18n.translateSignal", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="translate signal"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="i18n.translateSignal"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1012,
                 '00-contracts/bpmn/ai/gftd/i18n/translateSignal.bpmn',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-signal-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-signal-v1',
                 'did:web:i18n.etzhayyim.com',
                 'app.etzhayyim.apps.i18n.translateSignal',
                 'i18n_translate_signal',
                 'vertex_i18n_project,vertex_i18n_project_translation,vertex_i18n_translation_memory,vertex_i18n_text_node,vertex_i18n_credit_job,edge_i18n_project_translation,edge_i18n_translation_text,edge_i18n_text_language',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-signal-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-widget-lookup-v1',
                 'did:web:i18n.etzhayyim.com',
                 'i18n_widget_lookup',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_i18n_widget_lookup" '
                 'targetNamespace="https://etzhayyim.com/bpmn/i18n"><bpmn:process '
                 'id="i18n_widget_lookup" name="i18n widgetLookup" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.i18n.widgetLookup", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="widget lookup"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="i18n.widgetLookup"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 994,
                 '00-contracts/bpmn/ai/gftd/i18n/widgetLookup.bpmn',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-widget-lookup-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-widget-lookup-v1',
                 'did:web:i18n.etzhayyim.com',
                 'app.etzhayyim.apps.i18n.widgetLookup',
                 'i18n_widget_lookup',
                 '',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-widget-lookup-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-widget-suggest-v1',
                 'did:web:i18n.etzhayyim.com',
                 'i18n_widget_suggest',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_i18n_widget_suggest" '
                 'targetNamespace="https://etzhayyim.com/bpmn/i18n"><bpmn:process '
                 'id="i18n_widget_suggest" name="i18n widgetSuggest" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.i18n.widgetSuggest", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="widget suggest"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="i18n.widgetSuggest"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1000,
                 '00-contracts/bpmn/ai/gftd/i18n/widgetSuggest.bpmn',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-widget-suggest-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-widget-suggest-v1',
                 'did:web:i18n.etzhayyim.com',
                 'app.etzhayyim.apps.i18n.widgetSuggest',
                 'i18n_widget_suggest',
                 '',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-widget-suggest-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-widget-approve-v1',
                 'did:web:i18n.etzhayyim.com',
                 'i18n_widget_approve',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_i18n_widget_approve" '
                 'targetNamespace="https://etzhayyim.com/bpmn/i18n"><bpmn:process '
                 'id="i18n_widget_approve" name="i18n widgetApprove" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.i18n.widgetApprove", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="widget approve"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="i18n.widgetApprove"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1000,
                 '00-contracts/bpmn/ai/gftd/i18n/widgetApprove.bpmn',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-widget-approve-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-widget-approve-v1',
                 'did:web:i18n.etzhayyim.com',
                 'app.etzhayyim.apps.i18n.widgetApprove',
                 'i18n_widget_approve',
                 'vertex_i18n_project,vertex_i18n_project_translation,vertex_i18n_translation_memory,vertex_i18n_text_node,vertex_i18n_credit_job,edge_i18n_project_translation,edge_i18n_translation_text,edge_i18n_text_language',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-widget-approve-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-get-language-registry-v1',
                 'did:web:i18n.etzhayyim.com',
                 'i18n_get_language_registry',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_i18n_get_language_registry" '
                 'targetNamespace="https://etzhayyim.com/bpmn/i18n"><bpmn:process '
                 'id="i18n_get_language_registry" name="i18n getLanguageRegistry" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.i18n.getLanguageRegistry", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="get language registry"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="i18n.getLanguageRegistry"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1039,
                 '00-contracts/bpmn/ai/gftd/i18n/getLanguageRegistry.bpmn',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-get-language-registry-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-get-language-registry-v1',
                 'did:web:i18n.etzhayyim.com',
                 'app.etzhayyim.apps.i18n.getLanguageRegistry',
                 'i18n_get_language_registry',
                 '',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-get-language-registry-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-get-translation-status-v1',
                 'did:web:i18n.etzhayyim.com',
                 'i18n_get_translation_status',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_i18n_get_translation_status" '
                 'targetNamespace="https://etzhayyim.com/bpmn/i18n"><bpmn:process '
                 'id="i18n_get_translation_status" name="i18n getTranslationStatus" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.i18n.getTranslationStatus", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="get translation status"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="i18n.getTranslationStatus"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1045,
                 '00-contracts/bpmn/ai/gftd/i18n/getTranslationStatus.bpmn',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-get-translation-status-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, $5, 'active', $6,\n"
         "        100, $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-get-translation-status-v1',
                 'did:web:i18n.etzhayyim.com',
                 'app.etzhayyim.apps.i18n.getTranslationStatus',
                 'i18n_get_translation_status',
                 '',
                 '2026-04-30T21:51:00+09:00',
                 'did:web:i18n.etzhayyim.com',
                 'did:web:i18n.etzhayyim.com',
                 'sys.bpmn.seed.i18n',
                 'did:web:i18n.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-get-translation-status-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-register-project-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-register-project-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-batch-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-batch-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-export-messages-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-export-messages-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-on-demand-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-on-demand-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-page-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-page-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-message-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-message-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-translate-signal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-translate-signal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-widget-lookup-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-widget-lookup-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-widget-suggest-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-widget-suggest-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-widget-approve-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-widget-approve-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-get-language-registry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-get-language-registry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/i18n-get-translation-status-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/i18n-get-translation-status-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
