"""Captured from Kysely migration 20260505140000_seed_aria_market_emotion_influence_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260505140000_seed_aria_market_emotion_influence_bpmn"
down_revision = 'r_20260505130000_activate_llm_classifier_gate_pattern'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, $3, 1, $4,\n'
         "             CAST($5 AS integer), $6, 'active', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-market-ingest-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'aria_market_ingest',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  aria.marketIngest — ADR-2604291800 §ARIA\n'
                 '\n'
                 '  Timer-start (R/PT5M): runs every 5 minutes.\n'
                 '  Fetches market delta signals from CoinGecko (crypto top-10 price/volume).\n'
                 '\n'
                 '  NSID: ai.gftd.apps.aria.marketIngest (BPMN dispatcher T2 tier)\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-market-ingest-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_aria_market_ingest"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/aria"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="aria_market_ingest" name="ARIA Market Ingest" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.aria.marketIngest", "version": 1, "tier": "T2" }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- R/PT5M: fires every 5 minutes indefinitely -->\n'
                 '    <bpmn:startEvent id="Start_Timer" name="R/PT5M">\n'
                 '      <bpmn:outgoing>Flow_ToIngest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToIngest" sourceRef="Start_Timer" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <!-- Fetch market delta signals from CoinGecko top-10 crypto -->\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="Market delta ingest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="aria.market.delta.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=eta"       target="marketEta"/>\n'
                 '          <zeebe:output source="=entropy_h" target="marketH"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToIngest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Ingest" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2150,
                 '00-contracts/bpmn/ai/gftd/aria/marketIngest.bpmn',
                 '2026-05-05T14:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.aria',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-market-ingest-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, $3, 1, $4,\n'
         "             CAST($5 AS integer), $6, 'active', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-emotion-ingest-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'aria_emotion_ingest',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  aria.emotionIngest — ADR-2604291800 §ARIA\n'
                 '\n'
                 '  Timer-start (R/PT5M): runs every 5 minutes.\n'
                 '  Fetches emotion signal from vertex_actor_wellbecoming_profile at-risk actors.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.aria.emotionIngest (BPMN dispatcher T2 tier)\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-emotion-ingest-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_aria_emotion_ingest"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/aria"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="aria_emotion_ingest" name="ARIA Emotion Ingest" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.aria.emotionIngest", "version": 1, "tier": "T2" }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- R/PT5M: fires every 5 minutes indefinitely -->\n'
                 '    <bpmn:startEvent id="Start_Timer" name="R/PT5M">\n'
                 '      <bpmn:outgoing>Flow_ToIngest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToIngest" sourceRef="Start_Timer" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <!-- Fetch emotion signals from at-risk Well-Becoming actor profiles -->\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="Emotion ingest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="aria.emotion.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=eta"       target="emotionEta"/>\n'
                 '          <zeebe:output source="=entropy_h" target="emotionH"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToIngest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Ingest" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2161,
                 '00-contracts/bpmn/ai/gftd/aria/emotionIngest.bpmn',
                 '2026-05-05T14:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.aria',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-emotion-ingest-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '         source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, $3, 1, $4,\n'
         "             CAST($5 AS integer), $6, 'active', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-influence-ingest-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'aria_influence_ingest',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  aria.influenceIngest — ADR-2604291800 §ARIA\n'
                 '\n'
                 '  Timer-start (R/PT5M): runs every 5 minutes.\n'
                 '  Fetches influence signal from edge_follows top-100 follower distribution.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.aria.influenceIngest (BPMN dispatcher T2 tier)\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-influence-ingest-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_aria_influence_ingest"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/aria"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="aria_influence_ingest" name="ARIA Influence Ingest" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.aria.influenceIngest", "version": 1, "tier": "T2" '
                 '}\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- R/PT5M: fires every 5 minutes indefinitely -->\n'
                 '    <bpmn:startEvent id="Start_Timer" name="R/PT5M">\n'
                 '      <bpmn:outgoing>Flow_ToIngest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToIngest" sourceRef="Start_Timer" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <!-- Fetch influence signals from edge_follows top-100 distribution -->\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="Influence ingest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="aria.influence.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=eta"       target="influenceEta"/>\n'
                 '          <zeebe:output source="=entropy_h" target="influenceH"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToIngest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Ingest" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2178,
                 '00-contracts/bpmn/ai/gftd/aria/influenceIngest.bpmn',
                 '2026-05-05T14:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.aria',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-influence-ingest-v1']}]

DOWN = [{'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-market-ingest-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-emotion-ingest-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/aria-influence-ingest-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
