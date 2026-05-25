"""Captured from Kysely migration 20260501140100_seed_market_bundle_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260501140100_seed_market_bundle_bpmn"
down_revision = 'r_20260501140000_vertex_owl_reasoner_schema'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, 1, $4,\n'
         "             CAST($5 AS integer), $6, 'active', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/market-settlementBundle-v1',
                 'did:web:market.etzhayyim.com',
                 'market_settlement_bundle',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Settlement bundling — ADR 2605011300 (Q axis, throughput layer).\n'
                 '\n'
                 '  Phase 1.2 mock-bundler: every 60s, scan vertex_market_settlement for\n'
                 '  Mokuteki-passed pending rows and amend each (PK upsert) with status\n'
                 "  = 'settled' and a deterministic SHA-256 anchor over the 5-tuple\n"
                 '  (issuer | lxm | quantity | unit_price | vertex_id). The anchor is\n'
                 '  written by handleSettleInvoice at POST time (settlement_tx_hash\n'
                 "  starts as 'anchor:sha256:...'), so this BPMN's only job is the\n"
                 '  status flip (PK overwrite using INSERT, since RW does not support\n'
                 '  UPDATE on regular tables — record-log semantics, ADR-2604240000).\n'
                 '\n'
                 '  Phase 1.3 will replace this with a real ERC-4337 bundler call that\n'
                 '  produces a userOpHash and submits to a public bundler endpoint.\n'
                 '\n'
                 '  NSID:      app.etzhayyim.market.settlementBundle\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/market-settlementBundle-v1\n'
                 '  binding allowlist: vertex_market_settlement\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_market_settlement_bundle"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/market"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.2">\n'
                 '  <bpmn:process id="market_settlement_bundle" name="market settlement bundle" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.market.settlementBundle", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 60 seconds">\n'
                 '      <bpmn:outgoing>Flow_Timer</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT60S">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '                        '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT60S</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Timer" sourceRef="Start_Timer" '
                 'targetRef="Task_Bundle"/>\n'
                 '\n'
                 '    <!--\n'
                 '      INSERT … SELECT amends N pending rows in one atomic batch. Same\n'
                 '      vertex_id implicitly upserts; settlement_tx_hash already populated\n'
                 "      by handleSettleInvoice at POST time. We only flip status='pending'\n"
                 "      → 'settled' and stamp settled_at. mokuteki_floor_pass=TRUE filter\n"
                 '      prevents floor-violating rows from ever flowing to Q.\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Bundle" name="amend Mokuteki-passed pending → '
                 'settled (PK upsert)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;INSERT INTO vertex_market_settlement '
                 '(vertex_id, created_date, sensitivity_ord, owner_did, invoice_id, listing_id, '
                 'listing_vertex_id, lane, issuer_did, payer_did, lxm, quantity, unit_price, '
                 'total_price, currency, settlement_currency, settlement_tx_hash, status, '
                 'mokuteki_floor_pass, memo, enqueued_at, settled_at, created_at, actor_did, '
                 'at_did, org_id, user_id, actor_id, org_did) SELECT vertex_id, created_date, '
                 'sensitivity_ord, owner_did, invoice_id, listing_id, listing_vertex_id, lane, '
                 'issuer_did, payer_did, lxm, quantity, unit_price, total_price, currency, '
                 "settlement_currency, settlement_tx_hash, 'settled', mokuteki_floor_pass, memo, "
                 'enqueued_at, $1, created_at, actor_did, at_did, org_id, user_id, actor_id, '
                 "org_did FROM vertex_market_settlement WHERE status = 'pending' AND "
                 'mokuteki_floor_pass = TRUE&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[ string(now()) ]" target="params"/>\n'
                 '          <zeebe:output source="=inserted" target="amendedCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Timer</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Bundle_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Bundle_Audit" sourceRef="Task_Bundle" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit market.settlement.bundle '
                 'OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;app.etzhayyim.market.settlement.bundle&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;amendedCount&quot;: amendedCount, '
                 '&quot;phase&quot;: &quot;1.2-mock-bundler&quot; }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Bundle_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit_End" sourceRef="Task_Audit" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_Audit_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4727,
                 '00-contracts/bpmn/ai/gftd/generic/settlementBundle.bpmn',
                 '2026-05-01T13:00:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/market-settlementBundle-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord,\n'
         '         org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1,\n'
         '             CAST($5 AS integer), $6,\n'
         "             'active', $7, 1,\n"
         "             $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/market-settlementBundle-v1',
                 'did:web:market.etzhayyim.com',
                 'app.etzhayyim.market.settlementBundle',
                 'market_settlement_bundle',
                 120000,
                 'vertex_market_settlement',
                 '2026-05-01T13:00:00Z',
                 'did:web:market.etzhayyim.com',
                 'did:web:market.etzhayyim.com',
                 'sys.bpmn.seed.market',
                 'did:web:market.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/market-settlementBundle-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/market-settlementBundle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/market-settlementBundle-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
