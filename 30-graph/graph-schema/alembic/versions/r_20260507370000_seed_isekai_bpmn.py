"""Captured from Kysely migration 20260507370000_seed_isekai_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507370000_seed_isekai_bpmn"
down_revision = 'r_20260507360000_seed_yotei_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-analyze-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_analyze',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_analyze" targetNamespace="https://etzhayyim.com/bpmn/isekai" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_analyze" name="analyze" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_analyze"/>\n'
                 '    <bpmn:serviceTask id="Task_analyze" name="analyze">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.analyze" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_analyze" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/analyze.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-analyze-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1083, 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-analyze-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-analyze-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.analyze',
                 'isekai_analyze',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-analyze-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-browse-worlds-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_browse_worlds',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_browse_worlds" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_browse_worlds" name="browseWorlds" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_browseWorlds"/>\n'
                 '    <bpmn:serviceTask id="Task_browseWorlds" name="browseWorlds">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.browseWorlds" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_browseWorlds" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/browseWorlds.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-browse-worlds-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1125,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-browse-worlds-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-browse-worlds-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.browseWorlds',
                 'isekai_browse_worlds',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-browse-worlds-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-card-home-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_card_home',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_card_home" targetNamespace="https://etzhayyim.com/bpmn/isekai" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_card_home" name="cardHome" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_cardHome"/>\n'
                 '    <bpmn:serviceTask id="Task_cardHome" name="cardHome">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.cardHome" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_cardHome" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/cardHome.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-card-home-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1093,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-card-home-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-card-home-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.cardHome',
                 'isekai_card_home',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-card-home-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-catch-pokoa-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_catch_pokoa',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_catch_pokoa" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_catch_pokoa" name="catchPokoa" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_catchPokoa"/>\n'
                 '    <bpmn:serviceTask id="Task_catchPokoa" name="catchPokoa">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.catchPokoa" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_catchPokoa" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/catchPokoa.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-catch-pokoa-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1109,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-catch-pokoa-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-catch-pokoa-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.catchPokoa',
                 'isekai_catch_pokoa',
                 'vertex_isekai_world_state,vertex_isekai_chunk_data,vertex_isekai_creature_roster,vertex_isekai_inventory_item,vertex_isekai_brainrot_event,vertex_isekai_compliance_dep,vertex_isekai_game_capture,vertex_isekai_game_craft,vertex_isekai_game_brainrot_encounter',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-catch-pokoa-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-craft-item-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_craft_item',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_craft_item" targetNamespace="https://etzhayyim.com/bpmn/isekai" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_craft_item" name="craftItem" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_craftItem"/>\n'
                 '    <bpmn:serviceTask id="Task_craftItem" name="craftItem">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.craftItem" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_craftItem" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/craftItem.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-craft-item-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1101,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-craft-item-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-craft-item-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.craftItem',
                 'isekai_craft_item',
                 'vertex_isekai_world_state,vertex_isekai_chunk_data,vertex_isekai_creature_roster,vertex_isekai_inventory_item,vertex_isekai_brainrot_event,vertex_isekai_compliance_dep,vertex_isekai_game_capture,vertex_isekai_game_craft,vertex_isekai_game_brainrot_encounter',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-craft-item-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-create-world-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_create_world',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_create_world" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_create_world" name="createWorld" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_createWorld"/>\n'
                 '    <bpmn:serviceTask id="Task_createWorld" name="createWorld">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.createWorld" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_createWorld" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/createWorld.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-create-world-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1117,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-create-world-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-create-world-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.createWorld',
                 'isekai_create_world',
                 'vertex_isekai_world_state,vertex_isekai_chunk_data,vertex_isekai_creature_roster,vertex_isekai_inventory_item,vertex_isekai_brainrot_event,vertex_isekai_compliance_dep,vertex_isekai_game_capture,vertex_isekai_game_craft,vertex_isekai_game_brainrot_encounter',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-create-world-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-flee-battle-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_flee_battle',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_flee_battle" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_flee_battle" name="fleeBattle" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_fleeBattle"/>\n'
                 '    <bpmn:serviceTask id="Task_fleeBattle" name="fleeBattle">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.fleeBattle" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_fleeBattle" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/fleeBattle.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-flee-battle-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1109,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-flee-battle-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-flee-battle-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.fleeBattle',
                 'isekai_flee_battle',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-flee-battle-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-chunk-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_get_chunk',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_get_chunk" targetNamespace="https://etzhayyim.com/bpmn/isekai" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_get_chunk" name="getChunk" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getChunk"/>\n'
                 '    <bpmn:serviceTask id="Task_getChunk" name="getChunk">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.getChunk" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getChunk" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/getChunk.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-chunk-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1093,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-chunk-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-chunk-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.getChunk',
                 'isekai_get_chunk',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-chunk-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-compliance-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_get_compliance',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_get_compliance" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_get_compliance" name="getCompliance" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getCompliance"/>\n'
                 '    <bpmn:serviceTask id="Task_getCompliance" name="getCompliance">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.getCompliance" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getCompliance" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/getCompliance.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-compliance-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1133,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-compliance-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-compliance-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.getCompliance',
                 'isekai_get_compliance',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-compliance-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-inventory-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_get_inventory',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_get_inventory" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_get_inventory" name="getInventory" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getInventory"/>\n'
                 '    <bpmn:serviceTask id="Task_getInventory" name="getInventory">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.getInventory" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getInventory" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/getInventory.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-inventory-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1125,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-inventory-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-inventory-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.getInventory',
                 'isekai_get_inventory',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-inventory-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-legendaries-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_get_legendaries',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_get_legendaries" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_get_legendaries" name="getLegendaries" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getLegendaries"/>\n'
                 '    <bpmn:serviceTask id="Task_getLegendaries" name="getLegendaries">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.getLegendaries" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getLegendaries" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/getLegendaries.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-legendaries-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1141,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-legendaries-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-legendaries-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.getLegendaries',
                 'isekai_get_legendaries',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-legendaries-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-portal-state-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_get_portal_state',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_get_portal_state" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_get_portal_state" name="getPortalState" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getPortalState"/>\n'
                 '    <bpmn:serviceTask id="Task_getPortalState" name="getPortalState">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.getPortalState" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getPortalState" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/getPortalState.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-portal-state-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1143,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-portal-state-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-portal-state-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.getPortalState',
                 'isekai_get_portal_state',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-portal-state-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-roster-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_get_roster',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_get_roster" targetNamespace="https://etzhayyim.com/bpmn/isekai" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_get_roster" name="getRoster" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getRoster"/>\n'
                 '    <bpmn:serviceTask id="Task_getRoster" name="getRoster">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.getRoster" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getRoster" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/getRoster.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-roster-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1101,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-roster-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-roster-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.getRoster',
                 'isekai_get_roster',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-roster-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-world-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_get_world',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_get_world" targetNamespace="https://etzhayyim.com/bpmn/isekai" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_get_world" name="getWorld" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_getWorld"/>\n'
                 '    <bpmn:serviceTask id="Task_getWorld" name="getWorld">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.getWorld" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_getWorld" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/getWorld.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-world-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1093,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-world-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-world-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.getWorld',
                 'isekai_get_world',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-world-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-heal-party-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_heal_party',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_heal_party" targetNamespace="https://etzhayyim.com/bpmn/isekai" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_heal_party" name="healParty" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_healParty"/>\n'
                 '    <bpmn:serviceTask id="Task_healParty" name="healParty">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.healParty" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_healParty" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/healParty.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-heal-party-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1101,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-heal-party-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-heal-party-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.healParty',
                 'isekai_heal_party',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-heal-party-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-list-recipes-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_list_recipes',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_list_recipes" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_list_recipes" name="listRecipes" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listRecipes"/>\n'
                 '    <bpmn:serviceTask id="Task_listRecipes" name="listRecipes">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.listRecipes" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listRecipes" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/listRecipes.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-list-recipes-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1117,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-list-recipes-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-list-recipes-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.listRecipes',
                 'isekai_list_recipes',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-list-recipes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-list-scenes-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_list_scenes',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_list_scenes" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_list_scenes" name="listScenes" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_listScenes"/>\n'
                 '    <bpmn:serviceTask id="Task_listScenes" name="listScenes">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.listScenes" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_listScenes" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/listScenes.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-list-scenes-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1109,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-list-scenes-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-list-scenes-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.listScenes',
                 'isekai_list_scenes',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-list-scenes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-mine-block-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_mine_block',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_mine_block" targetNamespace="https://etzhayyim.com/bpmn/isekai" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_mine_block" name="mineBlock" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_mineBlock"/>\n'
                 '    <bpmn:serviceTask id="Task_mineBlock" name="mineBlock">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.mineBlock" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_mineBlock" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/mineBlock.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-mine-block-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1101,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-mine-block-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-mine-block-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.mineBlock',
                 'isekai_mine_block',
                 'vertex_isekai_world_state,vertex_isekai_chunk_data,vertex_isekai_creature_roster,vertex_isekai_inventory_item,vertex_isekai_brainrot_event,vertex_isekai_compliance_dep,vertex_isekai_game_capture,vertex_isekai_game_craft,vertex_isekai_game_brainrot_encounter',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-mine-block-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-place-block-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_place_block',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_place_block" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_place_block" name="placeBlock" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_placeBlock"/>\n'
                 '    <bpmn:serviceTask id="Task_placeBlock" name="placeBlock">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.placeBlock" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_placeBlock" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/placeBlock.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-place-block-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1109,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-place-block-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-place-block-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.placeBlock',
                 'isekai_place_block',
                 'vertex_isekai_world_state,vertex_isekai_chunk_data,vertex_isekai_creature_roster,vertex_isekai_inventory_item,vertex_isekai_brainrot_event,vertex_isekai_compliance_dep,vertex_isekai_game_capture,vertex_isekai_game_craft,vertex_isekai_game_brainrot_encounter',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-place-block-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-register-compliance-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_register_compliance',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_register_compliance" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_register_compliance" name="registerCompliance" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_registerCompliance"/>\n'
                 '    <bpmn:serviceTask id="Task_registerCompliance" name="registerCompliance">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.registerCompliance" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_registerCompliance" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/registerCompliance.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-register-compliance-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1173,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-register-compliance-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-register-compliance-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.registerCompliance',
                 'isekai_register_compliance',
                 'vertex_isekai_world_state,vertex_isekai_chunk_data,vertex_isekai_creature_roster,vertex_isekai_inventory_item,vertex_isekai_brainrot_event,vertex_isekai_compliance_dep,vertex_isekai_game_capture,vertex_isekai_game_craft,vertex_isekai_game_brainrot_encounter',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-register-compliance-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-roll-brainrot-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_roll_brainrot',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_roll_brainrot" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_roll_brainrot" name="rollBrainrot" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_rollBrainrot"/>\n'
                 '    <bpmn:serviceTask id="Task_rollBrainrot" name="rollBrainrot">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.rollBrainrot" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_rollBrainrot" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/rollBrainrot.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-roll-brainrot-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1125,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-roll-brainrot-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-roll-brainrot-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.rollBrainrot',
                 'isekai_roll_brainrot',
                 'vertex_isekai_world_state,vertex_isekai_chunk_data,vertex_isekai_creature_roster,vertex_isekai_inventory_item,vertex_isekai_brainrot_event,vertex_isekai_compliance_dep,vertex_isekai_game_capture,vertex_isekai_game_craft,vertex_isekai_game_brainrot_encounter',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-roll-brainrot-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-roll-encounter-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_roll_encounter',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_roll_encounter" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_roll_encounter" name="rollEncounter" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_rollEncounter"/>\n'
                 '    <bpmn:serviceTask id="Task_rollEncounter" name="rollEncounter">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.rollEncounter" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_rollEncounter" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/rollEncounter.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-roll-encounter-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1133,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-roll-encounter-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-roll-encounter-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.rollEncounter',
                 'isekai_roll_encounter',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-roll-encounter-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-start-battle-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_start_battle',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_start_battle" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_start_battle" name="startBattle" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_startBattle"/>\n'
                 '    <bpmn:serviceTask id="Task_startBattle" name="startBattle">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.startBattle" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_startBattle" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/startBattle.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-start-battle-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1117,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-start-battle-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-start-battle-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.startBattle',
                 'isekai_start_battle',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-start-battle-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-start-ohio-raid-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_start_ohio_raid',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_start_ohio_raid" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_start_ohio_raid" name="startOhioRaid" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_startOhioRaid"/>\n'
                 '    <bpmn:serviceTask id="Task_startOhioRaid" name="startOhioRaid">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.startOhioRaid" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_startOhioRaid" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/startOhioRaid.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-start-ohio-raid-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1135,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-start-ohio-raid-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-start-ohio-raid-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.startOhioRaid',
                 'isekai_start_ohio_raid',
                 'vertex_isekai_world_state,vertex_isekai_chunk_data,vertex_isekai_creature_roster,vertex_isekai_inventory_item,vertex_isekai_brainrot_event,vertex_isekai_compliance_dep,vertex_isekai_game_capture,vertex_isekai_game_craft,vertex_isekai_game_brainrot_encounter',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-start-ohio-raid-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-teleport-biome-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_teleport_biome',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_teleport_biome" '
                 'targetNamespace="https://etzhayyim.com/bpmn/isekai" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_teleport_biome" name="teleportBiome" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_teleportBiome"/>\n'
                 '    <bpmn:serviceTask id="Task_teleportBiome" name="teleportBiome">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.teleportBiome" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_teleportBiome" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/teleportBiome.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-teleport-biome-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1133,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-teleport-biome-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-teleport-biome-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.teleportBiome',
                 'isekai_teleport_biome',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-teleport-biome-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, $5, 'active',\n"
         '        $6, 100, $7, $8, $9,\n'
         "        $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-use-move-v1',
                 'did:web:isekai.etzhayyim.com',
                 'isekai_use_move',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_isekai_use_move" targetNamespace="https://etzhayyim.com/bpmn/isekai" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="isekai_use_move" name="useMove" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Task</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Task" sourceRef="Start" '
                 'targetRef="Task_useMove"/>\n'
                 '    <bpmn:serviceTask id="Task_useMove" name="useMove">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.app.etzhayyim.apps.isekai.useMove" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Task</bpmn:incoming><bpmn:outgoing>Flow_Task_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task_End" sourceRef="Task_useMove" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Task_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 '00-contracts/bpmn/ai/gftd/isekai/useMove.bpmn',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-use-move-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         '      SET xml_byte_size = $1\n'
         '      WHERE vertex_id = $2 AND xml_byte_size IS NULL\n'
         '    ',
  'parameters': [1085,
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-use-move-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-use-move-v1',
                 'did:web:isekai.etzhayyim.com',
                 'app.etzhayyim.apps.isekai.useMove',
                 'isekai_use_move',
                 '',
                 '2026-05-07T00:35:00Z',
                 'did:web:isekai.etzhayyim.com',
                 'did:web:isekai.etzhayyim.com',
                 'sys.bpmn.seed.isekai',
                 'did:web:isekai.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-use-move-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-analyze-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-analyze-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-browse-worlds-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-browse-worlds-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-card-home-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-card-home-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-catch-pokoa-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-catch-pokoa-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-craft-item-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-craft-item-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-create-world-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-create-world-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-flee-battle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-flee-battle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-chunk-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-chunk-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-compliance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-compliance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-inventory-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-inventory-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-legendaries-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-legendaries-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-portal-state-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-portal-state-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-roster-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-roster-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-get-world-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-get-world-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-heal-party-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-heal-party-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-list-recipes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-list-recipes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-list-scenes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-list-scenes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-mine-block-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-mine-block-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-place-block-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-place-block-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-register-compliance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-register-compliance-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-roll-brainrot-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-roll-brainrot-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-roll-encounter-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-roll-encounter-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-start-battle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-start-battle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-start-ohio-raid-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-start-ohio-raid-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-teleport-biome-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-teleport-biome-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/isekai-use-move-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/isekai-use-move-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
