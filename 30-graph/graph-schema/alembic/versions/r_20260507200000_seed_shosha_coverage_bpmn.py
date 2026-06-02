"""Captured from Kysely migration 20260507200000_seed_shosha_coverage_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507200000_seed_shosha_coverage_bpmn"
down_revision = 'r_20260507180100_seed_shosha_approval_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shosha-coverage-v1',
                 'did:web:shosha.etzhayyim.com',
                 'shosha_coverage',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  shosha.etzhayyim.com — coverage snapshot (XRPC com.etzhayyim.apps.shosha.coverage).\n'
                 '\n'
                 '  Phase 3 step 1: wire the Phase 1 schema-only coverage lexicon to a real\n'
                 '  BPMN + primitive. Returns aggregated metrics over all shosha tables for\n'
                 '  external soak monitors / dashboards / RemoteTrigger probes.\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. shosha.coverage.snapshot   reads count(*) over each vertex_shosha_*\n'
                 '                                   table + max(ts_ms) intel; returns\n'
                 '                                   asOf / tradesOpen / tradesClosed /\n'
                 '                                   counterpartiesActive / atRiskTrades /\n'
                 '                                   lastIntelTsMs (lexicon-required)\n'
                 '                                   plus extras (sanctionsActiveCount /\n'
                 '                                   approvalsTotal / reactionsTotal /\n'
                 '                                   settlementsTotal)\n'
                 '    2. generic.audit.emit         optional but kept for OCEL trail\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_shosha_coverage"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/shosha"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="shosha_coverage" name="shosha coverage snapshot" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.shosha.coverage", "version": 1, "resultTimeoutMs": '
                 '15000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="coverage">\n'
                 '      <bpmn:outgoing>Flow_ToSnap</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <!-- Coverage is a high-frequency probe (soak monitor / dashboards).\n'
                 "         Audit step intentionally OMITTED so we don't pile up\n"
                 '         vertex_repo_commit rows on every probe (would be ~hourly).\n'
                 '         Use the underlying refreshSanctionsList / submitTrade audit\n'
                 '         events to get OCEL traffic; coverage stays stateless. -->\n'
                 '    <bpmn:serviceTask id="Task_Snap" name="snapshot all shosha tables">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="shosha.coverage.snapshot"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=asOf" target="asOf"/>\n'
                 '          <zeebe:output source="=tradesOpen" target="tradesOpen"/>\n'
                 '          <zeebe:output source="=tradesClosed" target="tradesClosed"/>\n'
                 '          <zeebe:output source="=tradesPending" target="tradesPending"/>\n'
                 '          <zeebe:output source="=tradesCancelled" target="tradesCancelled"/>\n'
                 '          <zeebe:output source="=counterpartiesActive" '
                 'target="counterpartiesActive"/>\n'
                 '          <zeebe:output source="=atRiskTrades" target="atRiskTrades"/>\n'
                 '          <zeebe:output source="=lastIntelTsMs" target="lastIntelTsMs"/>\n'
                 '          <zeebe:output source="=sanctionsActiveCount" '
                 'target="sanctionsActiveCount"/>\n'
                 '          <zeebe:output source="=approvalsTotal" target="approvalsTotal"/>\n'
                 '          <zeebe:output source="=reactionsTotal" target="reactionsTotal"/>\n'
                 '          <zeebe:output source="=settlementsTotal" target="settlementsTotal"/>\n'
                 '          <zeebe:output source="=intelRows24h" target="intelRows24h"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSnap</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSnap" sourceRef="Start" '
                 'targetRef="Task_Snap"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Snap" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3633,
                 '00-contracts/bpmn/com/etzhayyim/shosha/coverage.bpmn',
                 '2026-05-07T20:00:00Z',
                 'did:web:shosha.etzhayyim.com',
                 'did:web:shosha.etzhayyim.com',
                 'sys.bpmn.seed.shosha.phase3',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shosha-coverage-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shosha-coverage-v1',
                 'did:web:shosha.etzhayyim.com',
                 'com.etzhayyim.apps.shosha.coverage',
                 'shosha_coverage',
                 15000,
                 '2026-05-07T20:00:00Z',
                 'did:web:shosha.etzhayyim.com',
                 'did:web:shosha.etzhayyim.com',
                 'sys.bpmn.seed.shosha.phase3',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shosha-coverage-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shosha-coverage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shosha-coverage-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
