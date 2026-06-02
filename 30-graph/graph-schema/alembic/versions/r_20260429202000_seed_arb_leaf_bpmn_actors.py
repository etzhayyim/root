"""Captured from Kysely migration 20260429202000_seed_arb_leaf_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429202000_seed_arb_leaf_bpmn_actors"
down_revision = 'r_20260429201000_seed_bluesky_bpmn_actors'
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
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-scout-quotes-v1',
                 'did:web:arb.etzhayyim.com',
                 'arb_scout_quotes',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arb_scout_quotes" targetNamespace="https://etzhayyim.com/bpmn/arb" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="arb_scout_quotes" name="arb scoutQuotes" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "com.etzhayyim.apps.arb.scoutQuotes", "version": 1, '
                 '"resultTimeoutMs": 120000 }</bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="scout quotes">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arb.scoutQuotes"/><zeebe:ioMapping><zeebe:input source="=assetClass" '
                 'target="assetClass"/></zeebe:ioMapping></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1211,
                 '00-contracts/bpmn/com/etzhayyim/arb/scoutQuotes.bpmn',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-scout-quotes-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-scout-quotes-v1',
                 'did:web:arb.etzhayyim.com',
                 'com.etzhayyim.apps.arb.scoutQuotes',
                 'arb_scout_quotes',
                 120000,
                 'vertex_arb_quote',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-scout-quotes-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['vertex_arb_quote',
                 'arb_scout_quotes',
                 'com.etzhayyim.apps.arb.scoutQuotes',
                 'vertex_arb_quote']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-ingest-quote-v1',
                 'did:web:arb.etzhayyim.com',
                 'arb_ingest_quote',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arb_ingest_quote" targetNamespace="https://etzhayyim.com/bpmn/arb" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="arb_ingest_quote" name="arb ingestQuote" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "com.etzhayyim.apps.arb.ingestQuote", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="ingest quote">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arb.ingestQuote"/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1120,
                 '00-contracts/bpmn/com/etzhayyim/arb/ingestQuote.bpmn',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-ingest-quote-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-ingest-quote-v1',
                 'did:web:arb.etzhayyim.com',
                 'com.etzhayyim.apps.arb.ingestQuote',
                 'arb_ingest_quote',
                 30000,
                 'vertex_arb_quote',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-ingest-quote-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['vertex_arb_quote',
                 'arb_ingest_quote',
                 'com.etzhayyim.apps.arb.ingestQuote',
                 'vertex_arb_quote']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-detect-spread-v1',
                 'did:web:arb.etzhayyim.com',
                 'arb_detect_spread',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arb_detect_spread" targetNamespace="https://etzhayyim.com/bpmn/arb" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="arb_detect_spread" name="arb detectSpread" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "com.etzhayyim.apps.arb.detectSpread", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="detect spread">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arb.detectSpread"/><zeebe:ioMapping><zeebe:input source="=assetClass" '
                 'target="assetClass"/><zeebe:input source="=if minSpreadBps = null then 20 else '
                 'minSpreadBps" '
                 'target="minSpreadBps"/></zeebe:ioMapping></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1311,
                 '00-contracts/bpmn/com/etzhayyim/arb/detectSpread.bpmn',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-detect-spread-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-detect-spread-v1',
                 'did:web:arb.etzhayyim.com',
                 'com.etzhayyim.apps.arb.detectSpread',
                 'arb_detect_spread',
                 30000,
                 '',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-detect-spread-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['', 'arb_detect_spread', 'com.etzhayyim.apps.arb.detectSpread', '']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-propose-trade-v1',
                 'did:web:arb.etzhayyim.com',
                 'arb_propose_trade',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arb_propose_trade" targetNamespace="https://etzhayyim.com/bpmn/arb" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="arb_propose_trade" name="arb proposeTrade" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "com.etzhayyim.apps.arb.proposeTrade", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="propose trade">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arb.proposeTrade"/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1126,
                 '00-contracts/bpmn/com/etzhayyim/arb/proposeTrade.bpmn',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-propose-trade-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-propose-trade-v1',
                 'did:web:arb.etzhayyim.com',
                 'com.etzhayyim.apps.arb.proposeTrade',
                 'arb_propose_trade',
                 30000,
                 'vertex_arb_proposal,edge_arb_proposal_leg',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-propose-trade-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['vertex_arb_proposal,edge_arb_proposal_leg',
                 'arb_propose_trade',
                 'com.etzhayyim.apps.arb.proposeTrade',
                 'vertex_arb_proposal,edge_arb_proposal_leg']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-score-proposal-v1',
                 'did:web:arb.etzhayyim.com',
                 'arb_score_proposal',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arb_score_proposal" targetNamespace="https://etzhayyim.com/bpmn/arb" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="arb_score_proposal" name="arb scoreProposal" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "com.etzhayyim.apps.arb.scoreProposal", "version": '
                 '1, "resultTimeoutMs": 30000 }</bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="score proposal">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arb.scoreProposal"/><zeebe:ioMapping><zeebe:input source="=proposalId" '
                 'target="proposalId"/><zeebe:input source="=if model = null then '
                 '&quot;heuristic-v1&quot; else model" '
                 'target="model"/></zeebe:ioMapping></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1318,
                 '00-contracts/bpmn/com/etzhayyim/arb/scoreProposal.bpmn',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-score-proposal-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-score-proposal-v1',
                 'did:web:arb.etzhayyim.com',
                 'com.etzhayyim.apps.arb.scoreProposal',
                 'arb_score_proposal',
                 30000,
                 'vertex_arb_score',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-score-proposal-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['vertex_arb_score',
                 'arb_score_proposal',
                 'com.etzhayyim.apps.arb.scoreProposal',
                 'vertex_arb_score']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-publish-proposal-v1',
                 'did:web:arb.etzhayyim.com',
                 'arb_publish_proposal',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arb_publish_proposal" targetNamespace="https://etzhayyim.com/bpmn/arb" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="arb_publish_proposal" name="arb publishProposal" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "com.etzhayyim.apps.arb.publishProposal", "version": '
                 '1, "resultTimeoutMs": 120000 }</bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="publish proposal">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arb.publishProposal"/><zeebe:ioMapping><zeebe:input source="=proposalId" '
                 'target="proposalId"/><zeebe:input source="=if mentionCohort = null then '
                 '&quot;trader.etzhayyim.com&quot; else mentionCohort" '
                 'target="mentionCohort"/></zeebe:ioMapping></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1357,
                 '00-contracts/bpmn/com/etzhayyim/arb/publishProposal.bpmn',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-publish-proposal-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-publish-proposal-v1',
                 'did:web:arb.etzhayyim.com',
                 'com.etzhayyim.apps.arb.publishProposal',
                 'arb_publish_proposal',
                 120000,
                 'vertex_arb_publication',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-publish-proposal-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['vertex_arb_publication',
                 'arb_publish_proposal',
                 'com.etzhayyim.apps.arb.publishProposal',
                 'vertex_arb_publication']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-list-proposals-v1',
                 'did:web:arb.etzhayyim.com',
                 'arb_list_proposals',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arb_list_proposals" targetNamespace="https://etzhayyim.com/bpmn/arb" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="arb_list_proposals" name="arb listProposals" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "com.etzhayyim.apps.arb.listProposals", "version": '
                 '1, "resultTimeoutMs": 30000 }</bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="list proposals">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arb.listProposals"/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1132,
                 '00-contracts/bpmn/com/etzhayyim/arb/listProposals.bpmn',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-list-proposals-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-list-proposals-v1',
                 'did:web:arb.etzhayyim.com',
                 'com.etzhayyim.apps.arb.listProposals',
                 'arb_list_proposals',
                 30000,
                 '',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-list-proposals-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['', 'arb_list_proposals', 'com.etzhayyim.apps.arb.listProposals', '']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-get-proposal-v1',
                 'did:web:arb.etzhayyim.com',
                 'arb_get_proposal',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_arb_get_proposal" targetNamespace="https://etzhayyim.com/bpmn/arb" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="arb_get_proposal" name="arb getProposal" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "com.etzhayyim.apps.arb.getProposal", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="get proposal">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="arb.getProposal"/><zeebe:ioMapping><zeebe:input source="=proposalId" '
                 'target="proposalId"/></zeebe:ioMapping></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1210,
                 '00-contracts/bpmn/com/etzhayyim/arb/getProposal.bpmn',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-get-proposal-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-get-proposal-v1',
                 'did:web:arb.etzhayyim.com',
                 'com.etzhayyim.apps.arb.getProposal',
                 'arb_get_proposal',
                 30000,
                 '',
                 '2026-04-29T20:20:00+09:00',
                 'did:web:arb.etzhayyim.com',
                 'did:web:arb.etzhayyim.com',
                 'sys.bpmn.seed.arb',
                 'did:web:arb.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-get-proposal-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['', 'arb_get_proposal', 'com.etzhayyim.apps.arb.getProposal', '']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-scout-quotes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-scout-quotes-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-ingest-quote-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-ingest-quote-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-detect-spread-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-detect-spread-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-propose-trade-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-propose-trade-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-score-proposal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-score-proposal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-publish-proposal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-publish-proposal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-list-proposals-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-list-proposals-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/arb-get-proposal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/arb-get-proposal-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
