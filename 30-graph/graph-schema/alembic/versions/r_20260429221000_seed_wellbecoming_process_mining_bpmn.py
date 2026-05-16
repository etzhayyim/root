"""Captured from Kysely migration 20260429221000_seed_wellbecoming_process_mining_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429221000_seed_wellbecoming_process_mining_bpmn"
down_revision = 'r_20260429221000_coverage_gap_phase2'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, $3, 1, $4,\n'
         '           CAST($5 AS integer),\n'
         '           $6,\n'
         '           $7, $8, 1, $9, $10, $11\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/wellbecoming-process-mining-v1',
                 'did:web:bpmn.gftd.ai',
                 'wellbecoming_process_mining',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  wellbecoming.processMining — ADR-2604291800.\n'
                 '\n'
                 '  Fires every 6h. Scores recent unscored vertex_wellbecoming_event rows via\n'
                 '  LLM (spirit / wellbecoming / feeling / buffer), detects floor violations,\n'
                 '  and emits a process mining report to vertex_repo_record.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.wellbecoming.processMining\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/wellbecoming-process-mining-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_wellbecoming_process_mining"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/wellbecoming"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="wellbecoming_process_mining" name="Well-Becoming Process '
                 'Mining" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.wellbecoming.processMining", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: every 6h -->\n'
                 '    <bpmn:startEvent id="Start" name="every 6h">\n'
                 '      <bpmn:outgoing>Flow_ToAnalyze</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_6h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT6H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAnalyze" sourceRef="Start" '
                 'targetRef="Task_Analyze"/>\n'
                 '\n'
                 '    <!-- Score unscored events + emit report -->\n'
                 '    <bpmn:serviceTask id="Task_Analyze" name="score events + emit report">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="wellbecoming.processMining.analyze"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=5" target="batch_size"/>\n'
                 '          <zeebe:output source="=scored_count"        target="scoredCount"/>\n'
                 '          <zeebe:output source="=floor_violations"    '
                 'target="floorViolations"/>\n'
                 '          <zeebe:output source="=avg_spirit"          target="avgSpirit"/>\n'
                 '          <zeebe:output source="=avg_separation_delta" '
                 'target="avgSeparationDelta"/>\n'
                 '          <zeebe:output source="=report_uri"          target="reportUri"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAnalyze</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Analyze" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2594,
                 '00-contracts/bpmn/ai/gftd/wellbecoming/processMining.bpmn',
                 'active',
                 '2026-04-29T22:10:00Z',
                 'did:web:bpmn.gftd.ai',
                 'did:web:bpmn.gftd.ai',
                 'sys.bpmn.seed.wellbecoming',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/wellbecoming-process-mining-v1']}]

DOWN = [{'sql': '\n'
         '    DELETE FROM vertex_bpmn_process_def\n'
         "    WHERE bpmn_process_id = 'wellbecoming_process_mining'\n"
         '  ',
  'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
