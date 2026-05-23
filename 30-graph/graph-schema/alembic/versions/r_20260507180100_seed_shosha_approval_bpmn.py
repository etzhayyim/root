"""Captured from Kysely migration 20260507180100_seed_shosha_approval_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507180100_seed_shosha_approval_bpmn"
down_revision = 'r_20260507180000_vertex_shosha_approval'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/shosha-approve-trade-v1',
                 'did:web:shosha.etzhayyim.com',
                 'shosha_approve_trade',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  shosha.etzhayyim.com — approveTrade workflow (XRPC '
                 'ai.gftd.apps.shosha.approveTrade).\n'
                 '\n'
                 '  Phase 2d simplified — single-step XRPC. Multi-day message-event BPMN\n'
                 '  (waiting on approval signal from inside submitTrade) deferred to\n'
                 '  Phase 3.\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. shosha.trade.approve   validate pending state + INSERT\n'
                 '                               vertex_shosha_approval + UPDATE\n'
                 "                               vertex_shosha_trade.approval_state='approved'\n"
                 '    2. generic.audit.emit     OCEL trail\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_shosha_approve_trade"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/shosha"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="shosha_approve_trade" name="shosha approve trade" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.shosha.approveTrade", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="approveTrade">\n'
                 '      <bpmn:outgoing>Flow_ToApprove</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Approve" name="approve trade decision">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="shosha.trade.approve"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=tradeId" target="tradeId"/>\n'
                 '          <zeebe:input source="=approverDid" target="approverDid"/>\n'
                 '          <zeebe:input source="=approverRole" target="approverRole"/>\n'
                 '          <zeebe:input source="=rationale" target="rationale"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=approvalId" target="approvalId"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/>\n'
                 '          <zeebe:output source="=tradeId" target="tradeId"/>\n'
                 '          <zeebe:output source="=approvalState" target="approvalState"/>\n'
                 '          <zeebe:output source="=decidedAt" target="decidedAt"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToApprove</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToApprove" sourceRef="Start" '
                 'targetRef="Task_Approve"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:shosha.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.shosha.approveTrade&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;approvalId&quot;: approvalId, '
                 '&quot;tradeId&quot;: tradeId, &quot;approvalState&quot;: approvalState, '
                 '&quot;approverDid&quot;: approverDid }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Approve" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3409,
                 '00-contracts/bpmn/ai/gftd/shosha/approveTrade.bpmn',
                 '2026-05-07T18:00:00Z',
                 'did:web:shosha.etzhayyim.com',
                 'did:web:shosha.etzhayyim.com',
                 'sys.bpmn.seed.shosha.phase2d',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/shosha-approve-trade-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/shosha-reject-trade-v1',
                 'did:web:shosha.etzhayyim.com',
                 'shosha_reject_trade',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  shosha.etzhayyim.com — rejectTrade workflow (XRPC ai.gftd.apps.shosha.rejectTrade).\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. shosha.trade.reject    validate pending + INSERT vertex_shosha_approval\n'
                 '                               (decision=reject) + UPDATE vertex_shosha_trade\n'
                 "                               approval_state='rejected', status='cancelled'.\n"
                 '                               Trade becomes terminal.\n'
                 '    2. generic.audit.emit     OCEL trail\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_shosha_reject_trade"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/shosha"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="shosha_reject_trade" name="shosha reject trade" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.shosha.rejectTrade", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="rejectTrade">\n'
                 '      <bpmn:outgoing>Flow_ToReject</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Reject" name="reject trade decision">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="shosha.trade.reject"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=tradeId" target="tradeId"/>\n'
                 '          <zeebe:input source="=approverDid" target="approverDid"/>\n'
                 '          <zeebe:input source="=approverRole" target="approverRole"/>\n'
                 '          <zeebe:input source="=rationale" target="rationale"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=approvalId" target="approvalId"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/>\n'
                 '          <zeebe:output source="=tradeId" target="tradeId"/>\n'
                 '          <zeebe:output source="=approvalState" target="approvalState"/>\n'
                 '          <zeebe:output source="=tradeStatus" target="tradeStatus"/>\n'
                 '          <zeebe:output source="=decidedAt" target="decidedAt"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToReject</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToReject" sourceRef="Start" '
                 'targetRef="Task_Reject"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:shosha.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.shosha.rejectTrade&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;approvalId&quot;: approvalId, '
                 '&quot;tradeId&quot;: tradeId, &quot;approvalState&quot;: approvalState, '
                 '&quot;tradeStatus&quot;: tradeStatus, &quot;approverDid&quot;: approverDid }" '
                 'target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Reject" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3436,
                 '00-contracts/bpmn/ai/gftd/shosha/rejectTrade.bpmn',
                 '2026-05-07T18:00:00Z',
                 'did:web:shosha.etzhayyim.com',
                 'did:web:shosha.etzhayyim.com',
                 'sys.bpmn.seed.shosha.phase2d',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/shosha-reject-trade-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/shosha-approveTrade-v1',
                 'did:web:shosha.etzhayyim.com',
                 'ai.gftd.apps.shosha.approveTrade',
                 'shosha_approve_trade',
                 30000,
                 '2026-05-07T18:00:00Z',
                 'did:web:shosha.etzhayyim.com',
                 'did:web:shosha.etzhayyim.com',
                 'sys.bpmn.seed.shosha.phase2d',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/shosha-approveTrade-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/shosha-rejectTrade-v1',
                 'did:web:shosha.etzhayyim.com',
                 'ai.gftd.apps.shosha.rejectTrade',
                 'shosha_reject_trade',
                 30000,
                 '2026-05-07T18:00:00Z',
                 'did:web:shosha.etzhayyim.com',
                 'did:web:shosha.etzhayyim.com',
                 'sys.bpmn.seed.shosha.phase2d',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/shosha-rejectTrade-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/shosha-approveTrade-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/shosha-rejectTrade-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/shosha-approve-trade-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/shosha-reject-trade-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
