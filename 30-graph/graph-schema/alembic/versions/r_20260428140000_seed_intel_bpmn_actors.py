"""Captured from Kysely migration 20260428140000_seed_intel_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428140000_seed_intel_bpmn_actors"
down_revision = 'r_20260428130000_seed_yadoya_from_accommodation'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-resolve-entity-v1',
                 'did:web:intel.etzhayyim.com',
                 'intel_resolve_entity',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_intel_resolve_entity" '
                 'targetNamespace="https://etzhayyim.com/bpmn/intel" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="intel_resolve_entity" name="resolveEntity" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Run</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Run" sourceRef="Start" '
                 'targetRef="Task_CreateRun"/>\n'
                 '    <bpmn:serviceTask id="Task_CreateRun" name="create inference run">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="intel.run.create"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={query: query, entityKind: entityKind, hints: '
                 'hints}" target="scope"/>\n'
                 '          <zeebe:input source="=&quot;mcp_call&quot;" target="triggerKind"/>\n'
                 '          <zeebe:input source="=true" target="dryRun"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Run</bpmn:incoming><bpmn:outgoing>Flow_Run_Candidates</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Run_Candidates" sourceRef="Task_CreateRun" '
                 'targetRef="Task_Candidates"/>\n'
                 '    <bpmn:serviceTask id="Task_Candidates" name="resolve candidates">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="intel.entity.resolve"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=query" target="query"/>\n'
                 '          <zeebe:input source="=entityKind" target="entityKind"/>\n'
                 '          <zeebe:input source="=hints" target="hints"/>\n'
                 '          <zeebe:input source="=maxCandidates" target="maxCandidates"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Run_Candidates</bpmn:incoming><bpmn:outgoing>Flow_Candidates_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Candidates_Audit" sourceRef="Task_Candidates" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:intel.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;intel.resolveEntity&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={runId: runId, query: query, candidateCount: '
                 'count(candidates)}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Candidates_Audit</bpmn:incoming><bpmn:outgoing>Flow_Audit_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit_End" sourceRef="Task_Audit" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Audit_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2884,
                 '00-contracts/bpmn/ai/gftd/intel/resolveEntity.bpmn',
                 '2026-04-28T14:00:00Z',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-resolve-entity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-list-dependency-candidates-v1',
                 'did:web:intel.etzhayyim.com',
                 'intel_list_dependency_candidates',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_intel_list_dependency_candidates" '
                 'targetNamespace="https://etzhayyim.com/bpmn/intel" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="intel_list_dependency_candidates" '
                 'name="listDependencyCandidates" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Query</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Query" sourceRef="Start" '
                 'targetRef="Task_Query"/>\n'
                 '    <bpmn:serviceTask id="Task_Query" name="list dependency candidates">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="intel.dependency.list"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=status" target="status"/>\n'
                 '          <zeebe:input source="=predicate" target="predicate"/>\n'
                 '          <zeebe:input source="=limit" target="limit"/>\n'
                 '          <zeebe:input source="=offset" target="offset"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Query</bpmn:incoming><bpmn:outgoing>Flow_Query_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Query_End" sourceRef="Task_Query" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Query_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1411,
                 '00-contracts/bpmn/ai/gftd/intel/listDependencyCandidates.bpmn',
                 '2026-04-28T14:00:00Z',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-list-dependency-candidates-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-infer-dependencies-v1',
                 'did:web:intel.etzhayyim.com',
                 'intel_infer_dependencies',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_intel_infer_dependencies" '
                 'targetNamespace="https://etzhayyim.com/bpmn/intel" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="intel_infer_dependencies" name="inferDependencies" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Run</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Run" sourceRef="Start" '
                 'targetRef="Task_CreateRun"/>\n'
                 '    <bpmn:serviceTask id="Task_CreateRun" name="create inference run">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="intel.run.create"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=scope" target="scope"/>\n'
                 '          <zeebe:input source="=triggerKind" target="triggerKind"/>\n'
                 '          <zeebe:input source="=dryRun" target="dryRun"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Run</bpmn:incoming><bpmn:outgoing>Flow_Run_Scan</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Run_Scan" sourceRef="Task_CreateRun" '
                 'targetRef="Task_ScanCandidates"/>\n'
                 '    <bpmn:serviceTask id="Task_ScanCandidates" name="scan SQL candidates">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="intel.candidate.scan"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=scope" target="scope"/>\n'
                 '          <zeebe:input source="=maxCandidates" target="maxCandidates"/>\n'
                 '          <zeebe:output source="=candidates" target="candidates"/>\n'
                 '          <zeebe:output source="=candidateCount" target="candidateCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Run_Scan</bpmn:incoming><bpmn:outgoing>Flow_Scan_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Scan_Gate" sourceRef="Task_ScanCandidates" '
                 'targetRef="Gateway_HasCandidates"/>\n'
                 '    <bpmn:exclusiveGateway id="Gateway_HasCandidates" name="has candidates?">\n'
                 '      <bpmn:incoming>Flow_Scan_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Scan_Validate</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_NoCandidates</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Scan_Validate" sourceRef="Gateway_HasCandidates" '
                 'targetRef="Task_Validate">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=candidateCount &gt; '
                 '0</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_NoCandidates" sourceRef="Gateway_HasCandidates" '
                 'targetRef="Task_AuditNoCandidates"/>\n'
                 '    <bpmn:serviceTask id="Task_Validate" name="OWL/SHACL validate">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="intel.owl.validate"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=candidates" target="candidates"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Scan_Validate</bpmn:incoming><bpmn:outgoing>Flow_Validate_Resolve</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Validate_Resolve" sourceRef="Task_Validate" '
                 'targetRef="Task_Resolve"/>\n'
                 '    <bpmn:serviceTask id="Task_Resolve" name="LangGraph resolve ambiguous '
                 'links">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="intel.langgraph.resolve"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=validCandidates" target="validCandidates"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Validate_Resolve</bpmn:incoming><bpmn:outgoing>Flow_Resolve_Materialize</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Resolve_Materialize" sourceRef="Task_Resolve" '
                 'targetRef="Task_Materialize"/>\n'
                 '    <bpmn:serviceTask id="Task_Materialize" name="materialize or queue review">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="intel.edge.materialize"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=runId" target="runId"/>\n'
                 '          <zeebe:input source="=resolvedEdges" target="resolvedEdges"/>\n'
                 '          <zeebe:input source="=dryRun" target="dryRun"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Resolve_Materialize</bpmn:incoming><bpmn:outgoing>Flow_Materialize_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Materialize_Audit" sourceRef="Task_Materialize" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:intel.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;intel.inferDependencies&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={runId: runId, candidateCount: candidateCount, '
                 'activeCount: activeCount, reviewCount: reviewCount}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Materialize_Audit</bpmn:incoming><bpmn:outgoing>Flow_Audit_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit_End" sourceRef="Task_Audit" '
                 'targetRef="End"/>\n'
                 '    <bpmn:serviceTask id="Task_AuditNoCandidates" name="audit no candidates">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:intel.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;intel.inferDependencies.abort&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={runId: runId, reason: '
                 '&quot;no_candidates&quot;, candidateCount: candidateCount}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_NoCandidates</bpmn:incoming><bpmn:outgoing>Flow_NoCandidatesEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_NoCandidatesEnd" '
                 'sourceRef="Task_AuditNoCandidates" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_Audit_End</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_NoCandidatesEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 6340,
                 '00-contracts/bpmn/ai/gftd/intel/inferDependencies.bpmn',
                 '2026-04-28T14:00:00Z',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-infer-dependencies-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-explain-dependency-v1',
                 'did:web:intel.etzhayyim.com',
                 'intel_explain_dependency',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_intel_explain_dependency" '
                 'targetNamespace="https://etzhayyim.com/bpmn/intel" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="intel_explain_dependency" name="explainDependency" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Query</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Query" sourceRef="Start" '
                 'targetRef="Task_Query"/>\n'
                 '    <bpmn:serviceTask id="Task_Query" name="explain dependency">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="intel.dependency.explain"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=edgeId" target="edgeId"/>\n'
                 '          <zeebe:input source="=fromVertexId" target="fromVertexId"/>\n'
                 '          <zeebe:input source="=toVertexId" target="toVertexId"/>\n'
                 '          <zeebe:input source="=predicate" target="predicate"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Query</bpmn:incoming><bpmn:outgoing>Flow_Query_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Query_End" sourceRef="Task_Query" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Query_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1405,
                 '00-contracts/bpmn/ai/gftd/intel/explainDependency.bpmn',
                 '2026-04-28T14:00:00Z',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-explain-dependency-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-get-counterparty-graph-v1',
                 'did:web:intel.etzhayyim.com',
                 'intel_get_counterparty_graph',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_intel_get_counterparty_graph" '
                 'targetNamespace="https://etzhayyim.com/bpmn/intel" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="intel_get_counterparty_graph" name="getCounterpartyGraph" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Query</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Query" sourceRef="Start" '
                 'targetRef="Task_Query"/>\n'
                 '    <bpmn:serviceTask id="Task_Query" name="get counterparty graph">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="intel.graph.counterparty"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=subjectVertexId" target="subjectVertexId"/>\n'
                 '          <zeebe:input source="=lei" target="lei"/>\n'
                 '          <zeebe:input source="=relationKinds" target="relationKinds"/>\n'
                 '          <zeebe:input source="=limit" target="limit"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Query</bpmn:incoming><bpmn:outgoing>Flow_Query_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Query_End" sourceRef="Task_Query" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Query_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1418,
                 '00-contracts/bpmn/ai/gftd/intel/getCounterpartyGraph.bpmn',
                 '2026-04-28T14:00:00Z',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-get-counterparty-graph-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-get-building-ownership-graph-v1',
                 'did:web:intel.etzhayyim.com',
                 'intel_get_building_ownership_graph',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_intel_get_building_ownership_graph" '
                 'targetNamespace="https://etzhayyim.com/bpmn/intel" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="intel_get_building_ownership_graph" '
                 'name="getBuildingOwnershipGraph" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Start_Query</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Query" sourceRef="Start" '
                 'targetRef="Task_Query"/>\n'
                 '    <bpmn:serviceTask id="Task_Query" name="get building ownership graph">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="intel.graph.buildingOwnership"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=buildingVertexId" target="buildingVertexId"/>\n'
                 '          <zeebe:input source="=lei" target="lei"/>\n'
                 '          <zeebe:input source="=bbox" target="bbox"/>\n'
                 '          <zeebe:input source="=limit" target="limit"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Start_Query</bpmn:incoming><bpmn:outgoing>Flow_Query_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Query_End" sourceRef="Task_Query" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_Query_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1430,
                 '00-contracts/bpmn/ai/gftd/intel/getBuildingOwnershipGraph.bpmn',
                 '2026-04-28T14:00:00Z',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-get-building-ownership-graph-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-resolveEntity-v1',
                 'did:web:intel.etzhayyim.com',
                 'ai.gftd.apps.intel.resolveEntity',
                 'intel_resolve_entity',
                 60000,
                 '2026-04-28T14:00:00Z',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-resolveEntity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-listDependencyCandidates-v1',
                 'did:web:intel.etzhayyim.com',
                 'ai.gftd.apps.intel.listDependencyCandidates',
                 'intel_list_dependency_candidates',
                 30000,
                 '2026-04-28T14:00:00Z',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-listDependencyCandidates-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-inferDependencies-v1',
                 'did:web:intel.etzhayyim.com',
                 'ai.gftd.apps.intel.inferDependencies',
                 'intel_infer_dependencies',
                 60000,
                 '2026-04-28T14:00:00Z',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-inferDependencies-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-explainDependency-v1',
                 'did:web:intel.etzhayyim.com',
                 'ai.gftd.apps.intel.explainDependency',
                 'intel_explain_dependency',
                 60000,
                 '2026-04-28T14:00:00Z',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-explainDependency-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-getCounterpartyGraph-v1',
                 'did:web:intel.etzhayyim.com',
                 'ai.gftd.apps.intel.getCounterpartyGraph',
                 'intel_get_counterparty_graph',
                 60000,
                 '2026-04-28T14:00:00Z',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-getCounterpartyGraph-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-getBuildingOwnershipGraph-v1',
                 'did:web:intel.etzhayyim.com',
                 'ai.gftd.apps.intel.getBuildingOwnershipGraph',
                 'intel_get_building_ownership_graph',
                 60000,
                 '2026-04-28T14:00:00Z',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-getBuildingOwnershipGraph-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-resolveEntity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-listDependencyCandidates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-inferDependencies-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-explainDependency-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-getCounterpartyGraph-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/intel-getBuildingOwnershipGraph-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-resolve-entity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-list-dependency-candidates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-infer-dependencies-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-explain-dependency-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-get-counterparty-graph-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/intel-get-building-ownership-graph-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
