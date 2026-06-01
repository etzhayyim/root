"""Captured from Kysely migration 20260430214100_seed_kami_eng_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430214100_seed_kami_eng_bpmn_actors"
down_revision = 'r_20260430214000_vertex_kami_eng_record'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-eda-create-schematic-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_eda_create_schematic',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_eda_create_schematic" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_eda_create_schematic" name="kamiEng edaCreateSchematic" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.eda.createSchematic", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="eda create schematic"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.eda.createSchematic"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1052,
                 '00-contracts/bpmn/ai/gftd/kamiEng/edaCreateSchematic.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-eda-create-schematic-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-eda-create-schematic-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.eda.createSchematic',
                 'kami_eng_eda_create_schematic',
                 'vertex_kami_eng_eda_schematic,vertex_kami_eng_cad_model,vertex_kami_eng_cad_feature,vertex_kami_eng_cam_job,vertex_kami_eng_rtl_module_ref,vertex_kami_eng_rtl_simulation,vertex_kami_eng_cae_analysis,edge_kami_eng_cad_model_feature,edge_kami_eng_cad_model_cam_job,edge_kami_eng_rtl_module_simulation,edge_kami_eng_cad_model_cae_analysis',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-eda-create-schematic-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-eda-run-erc-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_eda_run_erc',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_eda_run_erc" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_eda_run_erc" name="kamiEng edaRunErc" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.eda.runErc", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="eda run erc"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.eda.runErc"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 998,
                 '00-contracts/bpmn/ai/gftd/kamiEng/edaRunErc.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-eda-run-erc-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-eda-run-erc-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.eda.runErc',
                 'kami_eng_eda_run_erc',
                 '',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-eda-run-erc-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-eda-export-gerber-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_eda_export_gerber',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_eda_export_gerber" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_eda_export_gerber" name="kamiEng edaExportGerber" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.eda.exportGerber", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="eda export gerber"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.eda.exportGerber"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1034,
                 '00-contracts/bpmn/ai/gftd/kamiEng/edaExportGerber.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-eda-export-gerber-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-eda-export-gerber-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.eda.exportGerber',
                 'kami_eng_eda_export_gerber',
                 '',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-eda-export-gerber-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cad-create-model-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_cad_create_model',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_cad_create_model" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_cad_create_model" name="kamiEng cadCreateModel" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.cad.createModel", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="cad create model"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.cad.createModel"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1028,
                 '00-contracts/bpmn/ai/gftd/kamiEng/cadCreateModel.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cad-create-model-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cad-create-model-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.cad.createModel',
                 'kami_eng_cad_create_model',
                 'vertex_kami_eng_eda_schematic,vertex_kami_eng_cad_model,vertex_kami_eng_cad_feature,vertex_kami_eng_cam_job,vertex_kami_eng_rtl_module_ref,vertex_kami_eng_rtl_simulation,vertex_kami_eng_cae_analysis,edge_kami_eng_cad_model_feature,edge_kami_eng_cad_model_cam_job,edge_kami_eng_rtl_module_simulation,edge_kami_eng_cad_model_cae_analysis',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cad-create-model-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cad-add-feature-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_cad_add_feature',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_cad_add_feature" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_cad_add_feature" name="kamiEng cadAddFeature" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.cad.addFeature", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="cad add feature"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.cad.addFeature"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1022,
                 '00-contracts/bpmn/ai/gftd/kamiEng/cadAddFeature.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cad-add-feature-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cad-add-feature-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.cad.addFeature',
                 'kami_eng_cad_add_feature',
                 'vertex_kami_eng_eda_schematic,vertex_kami_eng_cad_model,vertex_kami_eng_cad_feature,vertex_kami_eng_cam_job,vertex_kami_eng_rtl_module_ref,vertex_kami_eng_rtl_simulation,vertex_kami_eng_cae_analysis,edge_kami_eng_cad_model_feature,edge_kami_eng_cad_model_cam_job,edge_kami_eng_rtl_module_simulation,edge_kami_eng_cad_model_cae_analysis',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cad-add-feature-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cad-export-step-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_cad_export_step',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_cad_export_step" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_cad_export_step" name="kamiEng cadExportStep" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.cad.exportStep", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="cad export step"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.cad.exportStep"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1022,
                 '00-contracts/bpmn/ai/gftd/kamiEng/cadExportStep.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cad-export-step-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cad-export-step-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.cad.exportStep',
                 'kami_eng_cad_export_step',
                 '',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cad-export-step-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cam-create-job-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_cam_create_job',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_cam_create_job" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_cam_create_job" name="kamiEng camCreateJob" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.cam.createJob", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="cam create job"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.cam.createJob"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1016,
                 '00-contracts/bpmn/ai/gftd/kamiEng/camCreateJob.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cam-create-job-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cam-create-job-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.cam.createJob',
                 'kami_eng_cam_create_job',
                 'vertex_kami_eng_eda_schematic,vertex_kami_eng_cad_model,vertex_kami_eng_cad_feature,vertex_kami_eng_cam_job,vertex_kami_eng_rtl_module_ref,vertex_kami_eng_rtl_simulation,vertex_kami_eng_cae_analysis,edge_kami_eng_cad_model_feature,edge_kami_eng_cad_model_cam_job,edge_kami_eng_rtl_module_simulation,edge_kami_eng_cad_model_cae_analysis',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cam-create-job-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cam-generate-gcode-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_cam_generate_gcode',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_cam_generate_gcode" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_cam_generate_gcode" name="kamiEng camGenerateGcode" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.cam.generateGcode", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="cam generate gcode"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.cam.generateGcode"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1040,
                 '00-contracts/bpmn/ai/gftd/kamiEng/camGenerateGcode.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cam-generate-gcode-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cam-generate-gcode-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.cam.generateGcode',
                 'kami_eng_cam_generate_gcode',
                 '',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cam-generate-gcode-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-rtl-parse-hdl-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_rtl_parse_hdl',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_rtl_parse_hdl" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_rtl_parse_hdl" name="kamiEng rtlParseHdl" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.rtl.parseHdl", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="rtl parse hdl"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.rtl.parseHdl"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1010,
                 '00-contracts/bpmn/ai/gftd/kamiEng/rtlParseHdl.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-rtl-parse-hdl-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-rtl-parse-hdl-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.rtl.parseHdl',
                 'kami_eng_rtl_parse_hdl',
                 '',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-rtl-parse-hdl-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-rtl-simulate-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_rtl_simulate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_rtl_simulate" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_rtl_simulate" name="kamiEng rtlSimulate" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.rtl.simulate", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="rtl simulate"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.rtl.simulate"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1007,
                 '00-contracts/bpmn/ai/gftd/kamiEng/rtlSimulate.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-rtl-simulate-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-rtl-simulate-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.rtl.simulate',
                 'kami_eng_rtl_simulate',
                 'vertex_kami_eng_eda_schematic,vertex_kami_eng_cad_model,vertex_kami_eng_cad_feature,vertex_kami_eng_cam_job,vertex_kami_eng_rtl_module_ref,vertex_kami_eng_rtl_simulation,vertex_kami_eng_cae_analysis,edge_kami_eng_cad_model_feature,edge_kami_eng_cad_model_cam_job,edge_kami_eng_rtl_module_simulation,edge_kami_eng_cad_model_cae_analysis',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-rtl-simulate-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-rtl-synthesize-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_rtl_synthesize',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_rtl_synthesize" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_rtl_synthesize" name="kamiEng rtlSynthesize" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.rtl.synthesize", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="rtl synthesize"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.rtl.synthesize"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1019,
                 '00-contracts/bpmn/ai/gftd/kamiEng/rtlSynthesize.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-rtl-synthesize-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-rtl-synthesize-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.rtl.synthesize',
                 'kami_eng_rtl_synthesize',
                 '',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-rtl-synthesize-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cae-generate-mesh-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_cae_generate_mesh',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_cae_generate_mesh" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_cae_generate_mesh" name="kamiEng caeGenerateMesh" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.cae.generateMesh", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="cae generate mesh"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.cae.generateMesh"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1034,
                 '00-contracts/bpmn/ai/gftd/kamiEng/caeGenerateMesh.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cae-generate-mesh-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cae-generate-mesh-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.cae.generateMesh',
                 'kami_eng_cae_generate_mesh',
                 '',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cae-generate-mesh-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cae-run-analysis-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_cae_run_analysis',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_cae_run_analysis" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_cae_run_analysis" name="kamiEng caeRunAnalysis" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.cae.runAnalysis", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="cae run analysis"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.cae.runAnalysis"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1028,
                 '00-contracts/bpmn/ai/gftd/kamiEng/caeRunAnalysis.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cae-run-analysis-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cae-run-analysis-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.cae.runAnalysis',
                 'kami_eng_cae_run_analysis',
                 'vertex_kami_eng_eda_schematic,vertex_kami_eng_cad_model,vertex_kami_eng_cad_feature,vertex_kami_eng_cam_job,vertex_kami_eng_rtl_module_ref,vertex_kami_eng_rtl_simulation,vertex_kami_eng_cae_analysis,edge_kami_eng_cad_model_feature,edge_kami_eng_cad_model_cam_job,edge_kami_eng_rtl_module_simulation,edge_kami_eng_cad_model_cae_analysis',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cae-run-analysis-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cae-get-results-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'kami_eng_cae_get_results',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_eng_cae_get_results" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiEng"><bpmn:process '
                 'id="kami_eng_cae_get_results" name="kamiEng caeGetResults" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"app.etzhayyim.apps.kami.cae.getResults", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="cae get results"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiEng.cae.getResults"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1022,
                 '00-contracts/bpmn/ai/gftd/kamiEng/caeGetResults.bpmn',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cae-get-results-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cae-get-results-v1',
                 'did:web:eng-kami.etzhayyim.com',
                 'app.etzhayyim.apps.kami.cae.getResults',
                 'kami_eng_cae_get_results',
                 '',
                 '2026-04-30T21:41:00+09:00',
                 'did:web:eng-kami.etzhayyim.com',
                 'did:web:eng-kami.etzhayyim.com',
                 'sys.bpmn.seed.kami-eng',
                 'did:web:eng-kami.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cae-get-results-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-eda-create-schematic-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-eda-create-schematic-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-eda-run-erc-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-eda-run-erc-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-eda-export-gerber-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-eda-export-gerber-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cad-create-model-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cad-create-model-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cad-add-feature-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cad-add-feature-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cad-export-step-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cad-export-step-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cam-create-job-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cam-create-job-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cam-generate-gcode-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cam-generate-gcode-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-rtl-parse-hdl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-rtl-parse-hdl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-rtl-simulate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-rtl-simulate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-rtl-synthesize-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-rtl-synthesize-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cae-generate-mesh-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cae-generate-mesh-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cae-run-analysis-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cae-run-analysis-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kami-eng-cae-get-results-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kami-eng-cae-get-results-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
