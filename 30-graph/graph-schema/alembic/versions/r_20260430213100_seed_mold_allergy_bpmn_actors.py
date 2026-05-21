"""Captured from Kysely migration 20260430213100_seed_mold_allergy_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430213100_seed_mold_allergy_bpmn_actors"
down_revision = 'r_20260430213000_vertex_mold_allergy'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-seed-allergen-catalog-v1',
                 'did:web:mold-allergy.etzhayyim.com',
                 'mold_allergy_seed_allergen_catalog',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_mold_allergy_seed_allergen_catalog" '
                 'targetNamespace="https://etzhayyim.com/bpmn/moldAllergy"><bpmn:process '
                 'id="mold_allergy_seed_allergen_catalog" name="moldAllergy seedAllergenCatalog" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.moldAllergy.seedAllergenCatalog", "version": 1, "resultTimeoutMs": '
                 '120000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="seed allergen catalog"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="moldAllergy.seedAllergenCatalog"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1084,
                 '00-contracts/bpmn/ai/gftd/moldAllergy/seedAllergenCatalog.bpmn',
                 '2026-04-30T21:31:00+09:00',
                 'did:web:mold-allergy.etzhayyim.com',
                 'did:web:mold-allergy.etzhayyim.com',
                 'sys.bpmn.seed.mold-allergy',
                 'did:web:mold-allergy.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-seed-allergen-catalog-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-seedAllergenCatalog-v1',
                 'did:web:mold-allergy.etzhayyim.com',
                 'ai.gftd.apps.moldAllergy.seedAllergenCatalog',
                 'mold_allergy_seed_allergen_catalog',
                 120000,
                 'vertex_mold_allergen',
                 '2026-04-30T21:31:00+09:00',
                 'did:web:mold-allergy.etzhayyim.com',
                 'did:web:mold-allergy.etzhayyim.com',
                 'sys.bpmn.seed.mold-allergy',
                 'did:web:mold-allergy.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-seedAllergenCatalog-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-record-air-sampling-v1',
                 'did:web:mold-allergy.etzhayyim.com',
                 'mold_allergy_record_air_sampling',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_mold_allergy_record_air_sampling" '
                 'targetNamespace="https://etzhayyim.com/bpmn/moldAllergy"><bpmn:process '
                 'id="mold_allergy_record_air_sampling" name="moldAllergy recordAirSampling" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.moldAllergy.recordAirSampling", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="record air sampling"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="moldAllergy.recordAirSampling"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1071,
                 '00-contracts/bpmn/ai/gftd/moldAllergy/recordAirSampling.bpmn',
                 '2026-04-30T21:31:00+09:00',
                 'did:web:mold-allergy.etzhayyim.com',
                 'did:web:mold-allergy.etzhayyim.com',
                 'sys.bpmn.seed.mold-allergy',
                 'did:web:mold-allergy.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-record-air-sampling-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-recordAirSampling-v1',
                 'did:web:mold-allergy.etzhayyim.com',
                 'ai.gftd.apps.moldAllergy.recordAirSampling',
                 'mold_allergy_record_air_sampling',
                 30000,
                 'vertex_mold_air_sampling',
                 '2026-04-30T21:31:00+09:00',
                 'did:web:mold-allergy.etzhayyim.com',
                 'did:web:mold-allergy.etzhayyim.com',
                 'sys.bpmn.seed.mold-allergy',
                 'did:web:mold-allergy.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-recordAirSampling-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-propose-slit-candidate-v1',
                 'did:web:mold-allergy.etzhayyim.com',
                 'mold_allergy_propose_slit_candidate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_mold_allergy_propose_slit_candidate" '
                 'targetNamespace="https://etzhayyim.com/bpmn/moldAllergy"><bpmn:process '
                 'id="mold_allergy_propose_slit_candidate" name="moldAllergy proposeSlitCandidate" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.moldAllergy.proposeSlitCandidate", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="propose slit candidate"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="moldAllergy.proposeSlitCandidate"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1089,
                 '00-contracts/bpmn/ai/gftd/moldAllergy/proposeSlitCandidate.bpmn',
                 '2026-04-30T21:31:00+09:00',
                 'did:web:mold-allergy.etzhayyim.com',
                 'did:web:mold-allergy.etzhayyim.com',
                 'sys.bpmn.seed.mold-allergy',
                 'did:web:mold-allergy.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-propose-slit-candidate-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-proposeSlitCandidate-v1',
                 'did:web:mold-allergy.etzhayyim.com',
                 'ai.gftd.apps.moldAllergy.proposeSlitCandidate',
                 'mold_allergy_propose_slit_candidate',
                 30000,
                 'vertex_mold_slit_candidate',
                 '2026-04-30T21:31:00+09:00',
                 'did:web:mold-allergy.etzhayyim.com',
                 'did:web:mold-allergy.etzhayyim.com',
                 'sys.bpmn.seed.mold-allergy',
                 'did:web:mold-allergy.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-proposeSlitCandidate-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-list-allergens-v1',
                 'did:web:mold-allergy.etzhayyim.com',
                 'mold_allergy_list_allergens',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_mold_allergy_list_allergens" '
                 'targetNamespace="https://etzhayyim.com/bpmn/moldAllergy"><bpmn:process '
                 'id="mold_allergy_list_allergens" name="moldAllergy listAllergens" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.moldAllergy.listAllergens", "version": 1, "resultTimeoutMs": 30000 '
                 '}</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="list allergens"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="moldAllergy.listAllergens"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1044,
                 '00-contracts/bpmn/ai/gftd/moldAllergy/listAllergens.bpmn',
                 '2026-04-30T21:31:00+09:00',
                 'did:web:mold-allergy.etzhayyim.com',
                 'did:web:mold-allergy.etzhayyim.com',
                 'sys.bpmn.seed.mold-allergy',
                 'did:web:mold-allergy.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-list-allergens-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-listAllergens-v1',
                 'did:web:mold-allergy.etzhayyim.com',
                 'ai.gftd.apps.moldAllergy.listAllergens',
                 'mold_allergy_list_allergens',
                 30000,
                 '',
                 '2026-04-30T21:31:00+09:00',
                 'did:web:mold-allergy.etzhayyim.com',
                 'did:web:mold-allergy.etzhayyim.com',
                 'sys.bpmn.seed.mold-allergy',
                 'did:web:mold-allergy.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-listAllergens-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-list-slit-candidates-v1',
                 'did:web:mold-allergy.etzhayyim.com',
                 'mold_allergy_list_slit_candidates',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_mold_allergy_list_slit_candidates" '
                 'targetNamespace="https://etzhayyim.com/bpmn/moldAllergy"><bpmn:process '
                 'id="mold_allergy_list_slit_candidates" name="moldAllergy listSlitCandidates" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"ai.gftd.apps.moldAllergy.listSlitCandidates", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="list slit candidates"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="moldAllergy.listSlitCandidates"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1077,
                 '00-contracts/bpmn/ai/gftd/moldAllergy/listSlitCandidates.bpmn',
                 '2026-04-30T21:31:00+09:00',
                 'did:web:mold-allergy.etzhayyim.com',
                 'did:web:mold-allergy.etzhayyim.com',
                 'sys.bpmn.seed.mold-allergy',
                 'did:web:mold-allergy.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-list-slit-candidates-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-listSlitCandidates-v1',
                 'did:web:mold-allergy.etzhayyim.com',
                 'ai.gftd.apps.moldAllergy.listSlitCandidates',
                 'mold_allergy_list_slit_candidates',
                 30000,
                 '',
                 '2026-04-30T21:31:00+09:00',
                 'did:web:mold-allergy.etzhayyim.com',
                 'did:web:mold-allergy.etzhayyim.com',
                 'sys.bpmn.seed.mold-allergy',
                 'did:web:mold-allergy.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-listSlitCandidates-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-seedAllergenCatalog-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-seed-allergen-catalog-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-recordAirSampling-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-record-air-sampling-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-proposeSlitCandidate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-propose-slit-candidate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-listAllergens-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-list-allergens-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mold-allergy-listSlitCandidates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mold-allergy-list-slit-candidates-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
