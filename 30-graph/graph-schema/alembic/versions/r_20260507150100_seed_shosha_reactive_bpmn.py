"""Captured from Kysely migration 20260507150100_seed_shosha_reactive_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507150100_seed_shosha_reactive_bpmn"
down_revision = 'r_20260507150100_seed_gov_jam_bpmn_mcp_registry'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/shosha-react-to-upstream-v1',
                 'did:web:shosha.etzhayyim.com',
                 'shosha_react_to_upstream',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  shosha.etzhayyim.com — react to upstream actors (autonomous, R/PT5M).\n'
                 '\n'
                 '  Polls vertex_repo_record for commits from configured upstream actors\n'
                 '  (oil-trading, cargo, port — Phase 2a hard-coded set; table-driven\n'
                 '  subscriptions deferred to Phase 2a-extended). For each new commit\n'
                 '  beyond the consumer cursor, the LLM synthesizes a reaction\n'
                 '  (trade idea / hedge suggestion / risk alert / pass). Reactions land\n'
                 '  in vertex_shosha_reaction; cursor is advanced.\n'
                 '\n'
                 '  Phase 2a (2026-05-07). Pull-based; no upstream actor changes needed.\n'
                 "  AT-Protocol-friendly (we read other actors' AT records via the\n"
                 '  graph-projected vertex_repo_record table, no signed-data exchange).\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_shosha_react_to_upstream"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/shosha"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="shosha_react_to_upstream" name="shosha react to upstream '
                 'actors (5 min)" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="every 5 minutes">\n'
                 '      <bpmn:outgoing>Flow_ToScan</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Scan" name="scan upstream commits + emit '
                 'reactions">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="shosha.reactive.scanUpstream"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=20" target="batchPerUpstream"/>\n'
                 '          <zeebe:output source="=upstreamsScanned" target="upstreamsScanned"/>\n'
                 '          <zeebe:output source="=recordsSeen" target="recordsSeen"/>\n'
                 '          <zeebe:output source="=reactionsEmitted" target="reactionsEmitted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToScan</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToScan" sourceRef="StartTimer" '
                 'targetRef="Task_Scan"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:shosha.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;app.etzhayyim.apps.shosha.reactToUpstream&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;upstreamsScanned&quot;: '
                 'upstreamsScanned, &quot;recordsSeen&quot;: recordsSeen, '
                 '&quot;reactionsEmitted&quot;: reactionsEmitted }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Scan" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3274,
                 '00-contracts/bpmn/ai/gftd/shosha/reactToUpstream.bpmn',
                 '2026-05-07T15:00:00Z',
                 'did:web:shosha.etzhayyim.com',
                 'did:web:shosha.etzhayyim.com',
                 'sys.bpmn.seed.shosha.phase2a',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/shosha-react-to-upstream-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/shosha-react-to-upstream-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
