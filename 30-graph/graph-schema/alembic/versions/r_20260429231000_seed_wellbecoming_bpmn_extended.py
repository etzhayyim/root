"""Captured from Kysely migration 20260429231000_seed_wellbecoming_bpmn_extended."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429231000_seed_wellbecoming_bpmn_extended"
down_revision = 'r_20260429230000_vertex_actor_wellbecoming_profile'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-detect-bottleneck-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'wellbecoming_detect_bottleneck',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  wellbecoming.detectBottleneck — ADR-2604291800.\n'
                 '\n'
                 '  Fires every 1h. Reads mv_wellbecoming_bottleneck_caller to detect which\n'
                 '  U axis is the current bottleneck per caller, then upserts\n'
                 '  vertex_actor_wellbecoming_profile with bottleneck_axis + at_risk flag.\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.wellbecoming.detectBottleneck\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-detect-bottleneck-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_wellbecoming_detect_bottleneck"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/wellbecoming"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="wellbecoming_detect_bottleneck" name="Well-Becoming '
                 'Bottleneck Detect" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.wellbecoming.detectBottleneck", "version": 1, '
                 '"resultTimeoutMs": 120000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: every 1h -->\n'
                 '    <bpmn:startEvent id="Start" name="every 1h">\n'
                 '      <bpmn:outgoing>Flow_ToDetect</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_1h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToDetect" sourceRef="Start" '
                 'targetRef="Task_Detect"/>\n'
                 '\n'
                 '    <!-- Detect bottleneck axis per caller + upsert profile -->\n'
                 '    <bpmn:serviceTask id="Task_Detect" name="detect bottleneck per caller">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="wellbecoming.bottleneck.detect"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=50" target="batch_size"/>\n'
                 '          <zeebe:output source="=profiles_updated"   target="profilesUpdated"/>\n'
                 '          <zeebe:output source="=at_risk_count"      target="atRiskCount"/>\n'
                 '          <zeebe:output source="=bottleneck_summary" '
                 'target="bottleneckSummary"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToDetect</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Detect" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2464,
                 '00-contracts/bpmn/com/etzhayyim/wellbecoming/detectBottleneck.bpmn',
                 '2026-04-29T23:10:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.wellbecoming',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-detect-bottleneck-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-proactive-connect-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'wellbecoming_proactive_connect',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  wellbecoming.proactiveConnect — ADR-2604291800.\n'
                 '\n'
                 '  Fires every 2h. Finds callers in mv_wellbecoming_at_risk who have not\n'
                 '  received a proactive message recently, then sends a warm check-in via\n'
                 '  vertex_repo_record (C-path, graph-visible).\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.wellbecoming.proactiveConnect\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-proactive-connect-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_wellbecoming_proactive_connect"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/wellbecoming"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="wellbecoming_proactive_connect" name="Well-Becoming '
                 'Proactive Connect" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.wellbecoming.proactiveConnect", "version": 1, '
                 '"resultTimeoutMs": 180000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: every 2h -->\n'
                 '    <bpmn:startEvent id="Start" name="every 2h">\n'
                 '      <bpmn:outgoing>Flow_ToConnect</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_2h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT2H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToConnect" sourceRef="Start" '
                 'targetRef="Task_Connect"/>\n'
                 '\n'
                 '    <!-- Find at-risk callers + send warm check-in via C-path -->\n'
                 '    <bpmn:serviceTask id="Task_Connect" name="proactive connect at-risk '
                 'callers">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="wellbecoming.proactive.connect"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=10"   target="max_callers"/>\n'
                 '          <zeebe:input source="=7200" target="min_interval_seconds"/>\n'
                 '          <zeebe:output source="=connected_count"  target="connectedCount"/>\n'
                 '          <zeebe:output source="=skipped_count"    target="skippedCount"/>\n'
                 '          <zeebe:output source="=error_count"      target="errorCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToConnect</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Connect" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2520,
                 '00-contracts/bpmn/com/etzhayyim/wellbecoming/proactiveConnect.bpmn',
                 '2026-04-29T23:10:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.wellbecoming',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-proactive-connect-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-floor-violation-alert-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'wellbecoming_floor_violation_alert',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  wellbecoming.floorViolationAlert — ADR-2604291800.\n'
                 '\n'
                 '  Fires every 30 min. Checks for recent floor violations (responses that\n'
                 '  could harm children / future generations). If any new violations found,\n'
                 '  emits an alert record and triggers the alert task.\n'
                 '\n'
                 '  Hard floor = Von Neumann minimax constraint — never negotiable.\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.wellbecoming.floorViolationAlert\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-floor-violation-alert-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_wellbecoming_floor_violation_alert"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/wellbecoming"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="wellbecoming_floor_violation_alert" name="Well-Becoming '
                 'Floor Violation Alert" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.wellbecoming.floorViolationAlert", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- Timer: every 30 min -->\n'
                 '    <bpmn:startEvent id="Start" name="every 30m">\n'
                 '      <bpmn:outgoing>Flow_ToCheck</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_30m">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCheck" sourceRef="Start" '
                 'targetRef="Task_Check"/>\n'
                 '\n'
                 '    <!-- Check for new floor violations in last 30 min -->\n'
                 '    <bpmn:serviceTask id="Task_Check" name="check floor violations">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="wellbecoming.floor.check"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=30" target="lookback_minutes"/>\n'
                 '          <zeebe:output source="=violation_count"    target="violationCount"/>\n'
                 '          <zeebe:output source="=has_violations"     target="hasViolations"/>\n'
                 '          <zeebe:output source="=violation_vertex_ids" '
                 'target="violationVertexIds"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToCheck</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToGateway</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToGateway" sourceRef="Task_Check" '
                 'targetRef="Gateway_HasViolations"/>\n'
                 '\n'
                 '    <!-- Only alert if violations found -->\n'
                 '    <bpmn:exclusiveGateway id="Gateway_HasViolations" name="has violations?">\n'
                 '      <bpmn:incoming>Flow_ToGateway</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAlert</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAlert" sourceRef="Gateway_HasViolations" '
                 'targetRef="Task_Alert">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=hasViolations '
                 '= true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Gateway_HasViolations" '
                 'targetRef="End">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=hasViolations '
                 '= false</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <!-- Emit alert record + log -->\n'
                 '    <bpmn:serviceTask id="Task_Alert" name="emit floor alert">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="wellbecoming.floor.alert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=violationCount"      target="violation_count"/>\n'
                 '          <zeebe:input source="=violationVertexIds"  '
                 'target="violation_vertex_ids"/>\n'
                 '          <zeebe:output source="=alert_uri"          target="alertUri"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAlert</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_AlertToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_AlertToEnd" sourceRef="Task_Alert" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_AlertToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4127,
                 '00-contracts/bpmn/com/etzhayyim/wellbecoming/floorViolationAlert.bpmn',
                 '2026-04-29T23:10:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.wellbecoming',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-floor-violation-alert-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, $3, 1, $4,\n'
         "           CAST($5 AS integer), $6, 'active', $7,\n"
         '           1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-agent-loop-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'wellbecoming_agent_loop',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  wellbecoming.agentLoop — ADR-2604291800.\n'
                 '\n'
                 '  XRPC-triggered (none-start). Called by the infer.ts emitWellBecomingEvent\n'
                 '  path or any actor that wants a Well-Becoming-optimized agent response.\n'
                 '\n'
                 '  LangGraph loop:\n'
                 '    load_profile → generate_response → evaluate_spirit\n'
                 '      → (separating + refinements < 2) → refine → generate_response\n'
                 '      → emit_event → END\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.wellbecoming.agentLoop\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-agent-loop-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_wellbecoming_agent_loop"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/wellbecoming"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="wellbecoming_agent_loop" name="Well-Becoming Agent Loop" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.wellbecoming.agentLoop", "version": 1, '
                 '"resultTimeoutMs": 120000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <!-- None-start: triggered via XRPC / dispatcher POST -->\n'
                 '    <bpmn:startEvent id="Start_Manual" name="XRPC trigger">\n'
                 '      <bpmn:outgoing>Flow_ToLoop</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToLoop" sourceRef="Start_Manual" '
                 'targetRef="Task_AgentLoop"/>\n'
                 '\n'
                 '    <!--\n'
                 '      Single LangGraph task that runs the full loop internally.\n'
                 '      The graph handles: load_profile → generate → evaluate_spirit →\n'
                 '      (conditional refine) → emit_event.\n'
                 '      BPMN is intentionally thin here — the complexity lives in Python.\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_AgentLoop" name="LangGraph Well-Becoming loop">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="wellbecoming.agent.loop"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=response_final"       target="responseFinal"/>\n'
                 '          <zeebe:output source="=spirit_assessment"    '
                 'target="spiritAssessment"/>\n'
                 '          <zeebe:output source="=refinement_count"     '
                 'target="refinementCount"/>\n'
                 '          <zeebe:output source="=wb_event_id"          target="wbEventId"/>\n'
                 '          <zeebe:output source="=bottleneck_axis"      '
                 'target="bottleneckAxis"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToLoop</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_AgentLoop" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2735,
                 '00-contracts/bpmn/com/etzhayyim/wellbecoming/agentLoop.bpmn',
                 '2026-04-29T23:10:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.wellbecoming',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-agent-loop-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '       write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         '    SELECT $1, $2, $3, $4,\n'
         "           1, CAST(120000 AS integer), NULL, 'active', $5,\n"
         '           1, $6, $7, $8\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-apps-wellbecoming-agentLoop-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'com.etzhayyim.apps.wellbecoming.agentLoop',
                 'wellbecoming_agent_loop',
                 '2026-04-29T23:10:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.wellbecoming',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-apps-wellbecoming-agentLoop-v1']}]

DOWN = [{'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-detect-bottleneck-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-proactive-connect-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-floor-violation-alert-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/wellbecoming-agent-loop-v1']},
 {'sql': '\n    DELETE FROM vertex_bpmn_lexicon_binding\n    WHERE nsid = $1\n  ',
  'parameters': ['com.etzhayyim.apps.wellbecoming.agentLoop']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
