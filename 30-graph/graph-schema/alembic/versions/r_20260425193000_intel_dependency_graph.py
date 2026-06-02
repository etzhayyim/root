"""Captured from Kysely migration 20260425193000_intel_dependency_graph."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425193000_intel_dependency_graph"
down_revision = 'r_20260425190000_medical_data_source_ingest_spine'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_intel_subject (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      _seq BIGINT,\n'
         '      created_date DATE,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did VARCHAR,\n'
         '      subject_kind VARCHAR NOT NULL,\n'
         '      canonical_key VARCHAR,\n'
         '      label VARCHAR,\n'
         '      source_did VARCHAR,\n'
         '      source_vertex_id VARCHAR,\n'
         '      lei VARCHAR,\n'
         '      registration_number VARCHAR,\n'
         '      jurisdiction VARCHAR,\n'
         '      attributes_json VARCHAR,\n'
         '      status VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_intel_inference_run (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      _seq BIGINT,\n'
         '      created_date DATE,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did VARCHAR,\n'
         '      run_id VARCHAR NOT NULL,\n'
         '      trigger_kind VARCHAR NOT NULL,\n'
         '      scope_json VARCHAR,\n'
         '      model VARCHAR,\n'
         '      workflow_instance_key VARCHAR,\n'
         '      candidate_count BIGINT,\n'
         '      active_count BIGINT,\n'
         '      review_count BIGINT,\n'
         '      status VARCHAR,\n'
         '      started_at VARCHAR,\n'
         '      completed_at VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_intel_evidence (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      _seq BIGINT,\n'
         '      created_date DATE,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did VARCHAR,\n'
         '      evidence_id VARCHAR NOT NULL,\n'
         '      subject_vertex_id VARCHAR,\n'
         '      source_uri VARCHAR,\n'
         '      source_did VARCHAR,\n'
         '      extractor VARCHAR,\n'
         '      observed_at VARCHAR,\n'
         '      hash VARCHAR,\n'
         '      payload_json VARCHAR,\n'
         '      status VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_intel_dependency (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      _seq BIGINT,\n'
         '      created_date DATE,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did VARCHAR,\n'
         '      src_vid VARCHAR NOT NULL,\n'
         '      dst_vid VARCHAR NOT NULL,\n'
         '      predicate VARCHAR NOT NULL,\n'
         '      dependency_kind VARCHAR,\n'
         '      confidence DOUBLE PRECISION,\n'
         '      evidence_count BIGINT,\n'
         '      evidence_json VARCHAR,\n'
         '      inference_run_id VARCHAR,\n'
         '      valid_from VARCHAR,\n'
         '      valid_to VARCHAR,\n'
         '      reason VARCHAR,\n'
         '      model_version VARCHAR,\n'
         '      status VARCHAR,\n'
         '      reviewed_by VARCHAR,\n'
         '      reviewed_at VARCHAR,\n'
         '      review_note VARCHAR,\n'
         '      created_at VARCHAR,\n'
         '      org_id VARCHAR,\n'
         '      user_id VARCHAR,\n'
         '      actor_id VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_intel_subject_kind ON vertex_intel_subject (subject_kind)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_intel_subject_lei ON vertex_intel_subject (lei)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_intel_dependency_src ON edge_intel_dependency (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_intel_dependency_dst ON edge_intel_dependency (dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_intel_dependency_status ON edge_intel_dependency (status)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_intel_dependency_predicate ON edge_intel_dependency '
         '(predicate)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_intel_dependency_status AS\n'
         '    SELECT predicate, status, COUNT(*) AS edge_count, AVG(confidence) AS avg_confidence\n'
         '    FROM edge_intel_dependency\n'
         '    GROUP BY predicate, status\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_intel_building_owner_lei AS\n'
         '    SELECT\n'
         '      d.edge_id,\n'
         '      d.src_vid AS building_vid,\n'
         '      d.dst_vid AS owner_vid,\n'
         '      s.lei,\n'
         '      s.label AS owner_label,\n'
         '      d.confidence,\n'
         '      d.status\n'
         '    FROM edge_intel_dependency d\n'
         '    LEFT JOIN vertex_intel_subject s ON s.vertex_id = d.dst_vid\n'
         "    WHERE d.predicate IN ('owned_by', 'constructed_by', 'operated_by')\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-infer-dependencies-v1',
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
                 '00-contracts/bpmn/com/etzhayyim/intel/inferDependencies.bpmn',
                 '2026-04-25T19:30:00+09:00',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-infer-dependencies-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-resolve-entity-v1',
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
                 '00-contracts/bpmn/com/etzhayyim/intel/resolveEntity.bpmn',
                 '2026-04-25T19:30:00+09:00',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-resolve-entity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-explain-dependency-v1',
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
                 '00-contracts/bpmn/com/etzhayyim/intel/explainDependency.bpmn',
                 '2026-04-25T19:30:00+09:00',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-explain-dependency-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-list-dependency-candidates-v1',
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
                 '00-contracts/bpmn/com/etzhayyim/intel/listDependencyCandidates.bpmn',
                 '2026-04-25T19:30:00+09:00',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-list-dependency-candidates-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-get-building-ownership-graph-v1',
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
                 '00-contracts/bpmn/com/etzhayyim/intel/getBuildingOwnershipGraph.bpmn',
                 '2026-04-25T19:30:00+09:00',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-get-building-ownership-graph-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-get-counterparty-graph-v1',
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
                 '00-contracts/bpmn/com/etzhayyim/intel/getCounterpartyGraph.bpmn',
                 '2026-04-25T19:30:00+09:00',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-get-counterparty-graph-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-inferDependencies-v1',
                 'did:web:intel.etzhayyim.com',
                 'com.etzhayyim.apps.intel.inferDependencies',
                 'intel_infer_dependencies',
                 180000,
                 '2026-04-25T19:30:00+09:00',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-inferDependencies-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-resolveEntity-v1',
                 'did:web:intel.etzhayyim.com',
                 'com.etzhayyim.apps.intel.resolveEntity',
                 'intel_resolve_entity',
                 60000,
                 '2026-04-25T19:30:00+09:00',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-resolveEntity-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-explainDependency-v1',
                 'did:web:intel.etzhayyim.com',
                 'com.etzhayyim.apps.intel.explainDependency',
                 'intel_explain_dependency',
                 15000,
                 '2026-04-25T19:30:00+09:00',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-explainDependency-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-listDependencyCandidates-v1',
                 'did:web:intel.etzhayyim.com',
                 'com.etzhayyim.apps.intel.listDependencyCandidates',
                 'intel_list_dependency_candidates',
                 15000,
                 '2026-04-25T19:30:00+09:00',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-listDependencyCandidates-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-getBuildingOwnershipGraph-v1',
                 'did:web:intel.etzhayyim.com',
                 'com.etzhayyim.apps.intel.getBuildingOwnershipGraph',
                 'intel_get_building_ownership_graph',
                 20000,
                 '2026-04-25T19:30:00+09:00',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-getBuildingOwnershipGraph-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-getCounterpartyGraph-v1',
                 'did:web:intel.etzhayyim.com',
                 'com.etzhayyim.apps.intel.getCounterpartyGraph',
                 'intel_get_counterparty_graph',
                 20000,
                 '2026-04-25T19:30:00+09:00',
                 'did:web:intel.etzhayyim.com',
                 'did:web:intel.etzhayyim.com',
                 'sys.bpmn.seed.intel',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-getCounterpartyGraph-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-inferDependencies-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-resolveEntity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-explainDependency-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-listDependencyCandidates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-getBuildingOwnershipGraph-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/intel-getCounterpartyGraph-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-infer-dependencies-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-resolve-entity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-explain-dependency-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-list-dependency-candidates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-get-building-ownership-graph-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/intel-get-counterparty-graph-v1']},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_intel_building_owner_lei', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_intel_dependency_status', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_intel_dependency_predicate', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_intel_dependency_status', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_intel_dependency_dst', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_intel_dependency_src', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_intel_subject_lei', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_intel_subject_kind', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_intel_dependency', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_intel_evidence', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_intel_inference_run', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_intel_subject', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
