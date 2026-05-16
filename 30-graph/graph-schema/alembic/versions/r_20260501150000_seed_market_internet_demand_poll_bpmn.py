"""Captured from Kysely migration 20260501150000_seed_market_internet_demand_poll_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260501150000_seed_market_internet_demand_poll_bpmn"
down_revision = 'r_20260501140100_seed_market_bundle_bpmn'
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/market-internetDemandPoll-v1',
                 'did:web:market.gftd.ai',
                 'market_internet_demand_poll',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Internet demand polling — ADR 2605011300 (∇φ generation through internet '
                 'space).\n'
                 '\n'
                 '  Every 30 minutes, call the bpmn-dispatcher-resident sidecar at\n'
                 '  market-demand-poll.market.svc.cluster.local:8080/trigger which\n'
                 '  performs the fetch (Bluesky AppView + HN Algolia), classifier-tier\n'
                 '  LLM tagging, and batched INSERT into vertex_market_demand_signal.\n'
                 '  Mirror of maps/bulkRefreshWikipedia.bpmn shape.\n'
                 '\n'
                 '  Standalone CLI fallback while sidecar is not yet provisioned:\n'
                 '    python3 70-tools/scripts/cron/market-demand-poll.py\n'
                 '  This is the script that runs today (1-shot) to drive ∇φ.\n'
                 '\n'
                 '  NSID:      ai.gftd.market.internetDemandPoll\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/market-internetDemandPoll-v1\n'
                 '  binding allowlist: vertex_market_demand_signal\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_market_internet_demand_poll"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/market"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.1">\n'
                 '  <bpmn:process id="market_internet_demand_poll" name="market internet demand '
                 'poll" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.market.internetDemandPoll", "version": 1, '
                 '"resultTimeoutMs": 90000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 30 minutes">\n'
                 '      <bpmn:outgoing>Flow_Timer</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT30M">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '                        '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT30M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Timer" sourceRef="Start_Timer" '
                 'targetRef="Task_Trigger"/>\n'
                 '\n'
                 '    <!--\n'
                 '      Trigger the K8s-resident sidecar that owns the actual fetch + classify + '
                 'INSERT.\n'
                 '      Until the sidecar is provisioned, the python CLI script in '
                 '70-tools/scripts/cron/\n'
                 '      drives the same path on a host cron.\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Trigger" name="trigger market demand poll '
                 'sidecar">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.http.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;http://market-demand-poll.market.svc.cluster.local:8080/trigger&quot;" '
                 'target="url"/>\n'
                 '          <zeebe:input source="=&quot;POST&quot;"             target="method"/>\n'
                 '          <zeebe:input source="=&quot;application/json&quot;" '
                 'target="contentType"/>\n'
                 '          <zeebe:input source="={}"                            target="body"/>\n'
                 '          <zeebe:input source="=60000"                         '
                 'target="timeoutMs"/>\n'
                 '          <zeebe:output source="=ok"   target="triggerOk"/>\n'
                 '          <zeebe:output source="=data" target="triggerData"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Timer</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Trigger_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Trigger_Audit" sourceRef="Task_Trigger" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit market.demand.poll OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.market.demand.poll&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;triggerOk&quot;: triggerOk }" '
                 'target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Trigger_Audit</bpmn:incoming>\n'
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
                 3938,
                 '00-contracts/bpmn/ai/gftd/generic/internetDemandPoll.bpmn',
                 '2026-05-01T14:30:00Z',
                 'did:web:market.gftd.ai',
                 'did:web:market.gftd.ai',
                 'sys.bpmn.seed.market',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/market-internetDemandPoll-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/market-internetDemandPoll-v1',
                 'did:web:market.gftd.ai',
                 'ai.gftd.market.internetDemandPoll',
                 'market_internet_demand_poll',
                 90000,
                 'vertex_market_demand_signal',
                 '2026-05-01T14:30:00Z',
                 'did:web:market.gftd.ai',
                 'did:web:market.gftd.ai',
                 'sys.bpmn.seed.market',
                 'did:web:market.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/market-internetDemandPoll-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/market-internetDemandPoll-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/market-internetDemandPoll-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
