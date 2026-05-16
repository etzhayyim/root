"""Captured from Kysely migration 20260428090000_seed_m3_infra_cron_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428090000_seed_m3_infra_cron_bpmn_actors"
down_revision = 'r_20260428080100_seed_telecom_mec_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/magatama-cron-tick-v1',
                 'did:web:magatama.gftd.ai',
                 'ai.gftd.magatama.cronTick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '                  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"\n'
                 '                  id="magatama-cron-tick" '
                 'targetNamespace="https://gftd.ai/bpmn">\n'
                 '  <bpmn:process id="ai.gftd.magatama.cronTick" name="Magatama Organizer Cron '
                 'Tick" isExecutable="true">\n'
                 '    <bpmn:startEvent id="start" name="R/PT5M">\n'
                 '      <bpmn:outgoing>to-tick</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT5M">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '          '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:serviceTask id="task-tick" name="POST cronTick">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.http.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&#34;POST&#34;" target="method"/>\n'
                 '          <zeebe:input '
                 'source="=&#34;https://magatama.gftd.ai/xrpc/ai.gftd.apps.magatama.cronTick&#34;" '
                 'target="url"/>\n'
                 '          <zeebe:input source="={}" target="body"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>to-tick</bpmn:incoming>\n'
                 '      <bpmn:outgoing>to-audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:serviceTask id="task-audit" name="Emit audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&#34;ai.gftd.apps.magatama.cronTick&#34;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="=&#34;magatama-organizer&#34;" '
                 'target="actorId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>to-audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>to-end</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:endEvent id="end">\n'
                 '      <bpmn:incoming>to-end</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="to-tick" sourceRef="start" targetRef="task-tick"/>\n'
                 '    <bpmn:sequenceFlow id="to-audit" sourceRef="task-tick" '
                 'targetRef="task-audit"/>\n'
                 '    <bpmn:sequenceFlow id="to-end" sourceRef="task-audit" targetRef="end"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2264,
                 '00-contracts/bpmn/ai/gftd/magatama/cronTick.bpmn',
                 '2026-04-28T09:00:00Z',
                 'did:web:magatama.gftd.ai',
                 'did:web:magatama.gftd.ai',
                 'sys.bpmn.seed.magatama',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/magatama-cron-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, 'active', $5, 1, $6, $7, $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/magatama-cron-tick-v1',
                 'did:web:magatama.gftd.ai',
                 'ai.gftd.apps.magatama.cronTick',
                 'ai.gftd.magatama.cronTick',
                 '2026-04-28T09:00:00Z',
                 'did:web:magatama.gftd.ai',
                 'did:web:magatama.gftd.ai',
                 'sys.bpmn.seed.magatama',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/magatama-cron-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/graph-cron-tick-v1',
                 'did:web:graph.gftd.ai',
                 'ai.gftd.graph.cronTick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '                  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"\n'
                 '                  id="graph-cron-tick" targetNamespace="https://gftd.ai/bpmn">\n'
                 '  <bpmn:process id="ai.gftd.graph.cronTick" name="Graph Consumer Cron Tick" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="start" name="R/PT1M">\n'
                 '      <bpmn:outgoing>to-tick</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT1M">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '          '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT1M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:serviceTask id="task-tick" name="Consume repo commits">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="graph.repo.consumeCommits"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=50" target="batchSize"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>to-tick</bpmn:incoming>\n'
                 '      <bpmn:outgoing>to-audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:serviceTask id="task-audit" name="Emit audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&#34;ai.gftd.apps.graph.cronTick&#34;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="=&#34;graph-consumer&#34;" target="actorId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>to-audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>to-end</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:endEvent id="end">\n'
                 '      <bpmn:incoming>to-end</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="to-tick" sourceRef="start" targetRef="task-tick"/>\n'
                 '    <bpmn:sequenceFlow id="to-audit" sourceRef="task-tick" '
                 'targetRef="task-audit"/>\n'
                 '    <bpmn:sequenceFlow id="to-end" sourceRef="task-audit" targetRef="end"/>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2081,
                 '00-contracts/bpmn/ai/gftd/graph/cronTick.bpmn',
                 '2026-04-28T09:00:00Z',
                 'did:web:graph.gftd.ai',
                 'did:web:graph.gftd.ai',
                 'sys.bpmn.seed.graph',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/graph-cron-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        30000, 'active', $5, 1, $6, $7, $8\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/graph-cron-tick-v1',
                 'did:web:graph.gftd.ai',
                 'ai.gftd.apps.graph.cronTick',
                 'ai.gftd.graph.cronTick',
                 '2026-04-28T09:00:00Z',
                 'did:web:graph.gftd.ai',
                 'did:web:graph.gftd.ai',
                 'sys.bpmn.seed.graph',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/graph-cron-tick-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/magatama-cron-tick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/graph-cron-tick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/magatama-cron-tick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/graph-cron-tick-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
