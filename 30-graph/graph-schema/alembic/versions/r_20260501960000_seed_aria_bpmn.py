"""Captured from Kysely migration 20260501960000_seed_aria_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260501960000_seed_aria_bpmn"
down_revision = 'r_20260501950000_vertex_signal_aria'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-attention-ingest-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'aria_attention_ingest',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  aria.attentionIngest — ADR-2604291800 §ARIA\n'
                 '\n'
                 '  Timer-start (R/PT5M): runs every 5 minutes.\n'
                 '  Fetches attention signals (vertex_repo_record collection distribution + Google '
                 'Trends).\n'
                 '\n'
                 '  NSID: app.etzhayyim.apps.aria.attentionIngest (BPMN dispatcher T2 tier)\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-attention-ingest-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_aria_attention_ingest"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/aria"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="aria_attention_ingest" name="ARIA Attention Ingest" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.aria.attentionIngest", "version": 1, "tier": "T2" '
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
                 '    <!-- Fetch attention signals from collection distribution + Google Trends '
                 '-->\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="Attention ingest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="aria.attention.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=topic"     target="topSignal"/>\n'
                 '          <zeebe:output source="=eta"       target="attentionEta"/>\n'
                 '          <zeebe:output source="=entropy_h" target="attentionH"/>\n'
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
                 2263,
                 '00-contracts/bpmn/ai/gftd/aria/attentionIngest.bpmn',
                 '2026-05-01T19:50:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.aria',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-attention-ingest-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-request-ingest-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'aria_request_ingest',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  aria.requestIngest — ADR-2604291800 §ARIA\n'
                 '\n'
                 '  Timer-start (R/PT1H): runs every hour.\n'
                 '  Fetches request intent signals from XRPC call distribution.\n'
                 '\n'
                 '  NSID: app.etzhayyim.apps.aria.requestIngest (BPMN dispatcher T2 tier)\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-request-ingest-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_aria_request_ingest"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/aria"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="aria_request_ingest" name="ARIA Request Ingest" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.aria.requestIngest", "version": 1, "tier": "T2" }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- R/PT1H: fires every hour indefinitely -->\n'
                 '    <bpmn:startEvent id="Start_Timer" name="R/PT1H">\n'
                 '      <bpmn:outgoing>Flow_ToIngest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToIngest" sourceRef="Start_Timer" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <!-- Fetch request intent signals from XRPC call distribution -->\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="Request ingest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="aria.request.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=top_nsid"  target="topNsid"/>\n'
                 '          <zeebe:output source="=eta"       target="requestEta"/>\n'
                 '          <zeebe:output source="=entropy_h" target="requestH"/>\n'
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
                 2189,
                 '00-contracts/bpmn/ai/gftd/aria/requestIngest.bpmn',
                 '2026-05-01T19:50:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.aria',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-request-ingest-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-money-flow-ingest-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'aria_money_flow_ingest',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  aria.moneyFlowIngest — ADR-2604291800 §ARIA\n'
                 '\n'
                 '  Timer-start (R/P1D): runs once per day.\n'
                 '  Fetches on-chain + payment flow signals (blockchain.info stats).\n'
                 '\n'
                 '  NSID: app.etzhayyim.apps.aria.moneyFlowIngest (BPMN dispatcher T2 tier)\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-money-flow-ingest-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_aria_money_flow_ingest"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/aria"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="aria_money_flow_ingest" name="ARIA Money Flow Ingest" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.aria.moneyFlowIngest", "version": 1, "tier": "T2" '
                 '}\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- R/P1D: fires once per day indefinitely -->\n'
                 '    <bpmn:startEvent id="Start_Timer" name="R/P1D">\n'
                 '      <bpmn:outgoing>Flow_ToIngest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToIngest" sourceRef="Start_Timer" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <!-- Fetch on-chain + payment flow signals from blockchain.info stats -->\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="Money flow ingest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="aria.money.flow.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=1"           target="lookback_days"/>\n'
                 '          <zeebe:output source="=volume_usd"  target="tradeVolumeUsd"/>\n'
                 '          <zeebe:output source="=eta"         target="moneyEta"/>\n'
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
                 2242,
                 '00-contracts/bpmn/ai/gftd/aria/moneyFlowIngest.bpmn',
                 '2026-05-01T19:50:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.aria',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-money-flow-ingest-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-minimax-sweep-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'aria_minimax_sweep',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  aria.minimaxSweep — ADR-2604291800 §minimax\n'
                 '\n'
                 '  Timer-start (R/PT5M): runs every 5 minutes.\n'
                 '  Von Neumann minimax sweep over 6-dimensional ARIA signal space.\n'
                 '  Computes A_info = Σ w_k × η_k and selects argmin-regret action.\n'
                 '\n'
                 '  NSID: app.etzhayyim.apps.aria.minimaxSweep (BPMN dispatcher T2 tier)\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-minimax-sweep-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_aria_minimax_sweep"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/aria"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="aria_minimax_sweep" name="ARIA Minimax Sweep" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.aria.minimaxSweep", "version": 1, "tier": "T2" }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- R/PT5M: fires every 5 minutes indefinitely -->\n'
                 '    <bpmn:startEvent id="Start_Timer" name="R/PT5M">\n'
                 '      <bpmn:outgoing>Flow_ToSweep</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSweep" sourceRef="Start_Timer" '
                 'targetRef="Task_Sweep"/>\n'
                 '\n'
                 '    <!-- Run minimax sweep over 6-dim ARIA signal space (batch 3) -->\n'
                 '    <bpmn:serviceTask id="Task_Sweep" name="ARIA minimax sweep (batch 3)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="aria.minimax.sweep"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=3"               target="batch_size"/>\n'
                 '          <zeebe:output source="=a_info"          target="aInfo"/>\n'
                 '          <zeebe:output source="=eta_global"      target="etaGlobal"/>\n'
                 '          <zeebe:output source="=minimax_action"  target="minimaxAction"/>\n'
                 '          <zeebe:output source="=regret"          target="regret"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSweep</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Sweep" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2435,
                 '00-contracts/bpmn/ai/gftd/aria/ariaMinimaxSweep.bpmn',
                 '2026-05-01T19:50:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.aria',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-minimax-sweep-v1']}]

DOWN = [{'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-attention-ingest-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-request-ingest-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-money-flow-ingest-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/aria-minimax-sweep-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
