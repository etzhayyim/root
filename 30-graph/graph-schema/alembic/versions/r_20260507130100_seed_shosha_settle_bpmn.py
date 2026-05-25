"""Captured from Kysely migration 20260507130100_seed_shosha_settle_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507130100_seed_shosha_settle_bpmn"
down_revision = 'r_20260507130000_vertex_shosha_settlement'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/shosha-settle-trade-v1',
                 'did:web:shosha.etzhayyim.com',
                 'shosha_settle_trade',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  shosha.etzhayyim.com — settleTrade workflow (XRPC app.etzhayyim.apps.shosha.settleTrade).\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. shosha.trade.settle           validate (status=open, comply_ok=true)\n'
                 '                                      → INSERT vertex_shosha_settlement\n'
                 '                                      → UPDATE vertex_shosha_trade SET '
                 "status='closed'\n"
                 '                                      → INSERT edge_shosha_trade_settlement\n'
                 '                                      → returns settlementId / tradeStatus / '
                 'amountUsd\n'
                 '    2. generic.audit.emit            OCEL trail\n'
                 '\n'
                 '  XRPC-bound (ADR-0056). Phase 2c (2026-05-07).\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_shosha_settle_trade"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/shosha"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="shosha_settle_trade" name="shosha settle trade" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.shosha.settleTrade", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="settleTrade">\n'
                 '      <bpmn:outgoing>Flow_ToSettle</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Settle" name="settle trade record">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="shosha.trade.settle"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=tradeId" target="tradeId"/>\n'
                 '          <zeebe:input source="=settlementId" target="settlementId"/>\n'
                 '          <zeebe:input source="=method" target="method"/>\n'
                 '          <zeebe:input source="=bankRef" target="bankRef"/>\n'
                 '          <zeebe:input source="=valueDate" target="valueDate"/>\n'
                 '          <zeebe:input source="=amountOverride" target="amountOverride"/>\n'
                 '          <zeebe:input source="=remarks" target="remarks"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=settlementId" target="settlementId"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/>\n'
                 '          <zeebe:output source="=tradeId" target="tradeId"/>\n'
                 '          <zeebe:output source="=tradeStatus" target="tradeStatus"/>\n'
                 '          <zeebe:output source="=amountUsd" target="amountUsd"/>\n'
                 '          <zeebe:output source="=settledAt" target="settledAt"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSettle</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSettle" sourceRef="Start" '
                 'targetRef="Task_Settle"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:shosha.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;app.etzhayyim.apps.shosha.settleTrade&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;settlementId&quot;: settlementId, '
                 '&quot;tradeId&quot;: tradeId, &quot;tradeStatus&quot;: tradeStatus, '
                 '&quot;amountUsd&quot;: amountUsd }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Settle" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3744,
                 '00-contracts/bpmn/ai/gftd/shosha/settleTrade.bpmn',
                 '2026-05-07T13:00:00Z',
                 'did:web:shosha.etzhayyim.com',
                 'did:web:shosha.etzhayyim.com',
                 'sys.bpmn.seed.shosha.phase2c',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/shosha-settle-trade-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/shosha-settleTrade-v1',
                 'did:web:shosha.etzhayyim.com',
                 'app.etzhayyim.apps.shosha.settleTrade',
                 'shosha_settle_trade',
                 30000,
                 '2026-05-07T13:00:00Z',
                 'did:web:shosha.etzhayyim.com',
                 'did:web:shosha.etzhayyim.com',
                 'sys.bpmn.seed.shosha.phase2c',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/shosha-settleTrade-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/shosha-settleTrade-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/shosha-settle-trade-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
