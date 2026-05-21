"""Captured from Kysely migration 20260507210000_seed_rl_policy_dispatch_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507210000_seed_rl_policy_dispatch_bpmn"
down_revision = 'r_20260507200000_vertex_rl_aif_dispatch_log'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'rl_policy_dispatch', 1,\n"
         '      $3, CAST($4 AS integer),\n'
         "      '00-contracts/bpmn/ai/gftd/rl/rlPolicyDispatch.bpmn',\n"
         "      'active', $5, 1, $6, $7, 'sys.bpmn.seed.rl'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $8\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/rl-policy-dispatch-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  rl.rlPolicyDispatch — Phase 2 AIF policy-guided BPMN action selection. '
                 'ADR-2604291800.\n'
                 '\n'
                 '  Fires every 1h. For each actor with live EFE data, ε-greedy samples from\n'
                 '  π(a) = softmax(−γ·G(a)) and dispatches the winning BPMN NSID to the\n'
                 '  bpmn-dispatcher ClusterIP. Logs every attempt to vertex_rl_aif_dispatch_log.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.rl.policyDispatch\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/rl-policy-dispatch-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_rl_policy_dispatch"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/rl"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="rl_policy_dispatch" name="AIF Policy Dispatch" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.rl.policyDispatch", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: every 1h (runs after belief update) -->\n'
                 '    <bpmn:startEvent id="Start" name="every 1h">\n'
                 '      <bpmn:outgoing>Flow_ToDispatch</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_1h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToDispatch" sourceRef="Start" '
                 'targetRef="Task_Dispatch"/>\n'
                 '\n'
                 '    <!-- ε-greedy policy sample + bpmn-dispatcher POST -->\n'
                 '    <bpmn:serviceTask id="Task_Dispatch" name="sample policy and dispatch '
                 'BPMN">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rl.policy.dispatch" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=10"  target="batch_size"/>\n'
                 '          <zeebe:input source="=0.2" target="epsilon"/>\n'
                 '          <zeebe:output source="=ok"             target="ok"/>\n'
                 '          <zeebe:output source="=actors_checked" target="actorsChecked"/>\n'
                 '          <zeebe:output source="=dispatched"     target="dispatched"/>\n'
                 '          <zeebe:output source="=errors"         target="errors"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToDispatch</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Dispatch" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2576,
                 '2026-05-07T20:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/rl-policy-dispatch-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, bpmn_process_id, nsid,\n'
         '       created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'rl_policy_dispatch',\n"
         "      'ai.gftd.apps.rl.policyDispatch',\n"
         "      $3, 1, $4, $5, 'sys.bpmn.seed.rl'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $6\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/rl-policy-dispatch-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '2026-05-07T20:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/rl-policy-dispatch-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/rl-policy-dispatch-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/rl-policy-dispatch-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
