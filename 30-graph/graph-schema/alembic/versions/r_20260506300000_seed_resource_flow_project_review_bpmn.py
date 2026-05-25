"""Captured from Kysely migration 20260506300000_seed_resource_flow_project_review_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506300000_seed_resource_flow_project_review_bpmn"
down_revision = 'r_20260506290000_update_yadoya_confirm_bpmn_adr0036'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    ) VALUES (\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/resource-flow-project-flow-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'resource_flow_project_flow',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  resource-flow projectFlow — ADR-0036/0056 BPMN worker projection.\n'
                 '\n'
                 '  NSID: app.etzhayyim.apps.resourceFlow.projectFlow\n'
                 '  Task type: resource-flow.project.flow\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_resource_flow_project_flow"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/resource-flow"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="resource_flow_project_flow" name="resource-flow projectFlow" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.resourceFlow.projectFlow", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="request">\n'
                 '      <bpmn:outgoing>Flow_Start_Project</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Project" sourceRef="Start" '
                 'targetRef="Task_Project"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Project" name="project resource-flow record">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="resource-flow.project.flow"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=flowClass" target="flowClass"/>\n'
                 '          <zeebe:input source="=recordUri" target="recordUri"/>\n'
                 '          <zeebe:input source="=observedAt" target="observedAt"/>\n'
                 '          <zeebe:input source="=record" target="record"/>\n'
                 '          <zeebe:input source="=primaryDid" target="primaryDid"/>\n'
                 '          <zeebe:input source="=orgId" target="orgId"/>\n'
                 '          <zeebe:input source="=userId" target="userId"/>\n'
                 '          <zeebe:output source="=flowClass" target="flowClass"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/>\n'
                 '          <zeebe:output source="=status" target="status"/>\n'
                 '          <zeebe:output source="=rejectReason" target="rejectReason"/>\n'
                 '          <zeebe:output source="=error" target="error"/>\n'
                 '          <zeebe:output source="=message" target="message"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Project</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Project_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Project_Audit" sourceRef="Task_Project" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:resource-flow.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;resource-flow.project.flow&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={flowClass: flowClass, recordUri: recordUri, '
                 'vertexId: vertexId, status: status, error: error}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Project_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3176,
                 '00-contracts/bpmn/ai/gftd/resource-flow/projectFlow.bpmn',
                 '2026-05-06T03:00:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-project-review']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    ) VALUES (\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/resource-flow-review-anomaly-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'resource_flow_review_anomaly',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  resource-flow reviewAnomaly — ADR-0036/0056 BPMN worker review writer.\n'
                 '\n'
                 '  NSID: app.etzhayyim.apps.resourceFlow.reviewAnomaly\n'
                 '  Task type: resource-flow.review.anomaly\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_resource_flow_review_anomaly"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/resource-flow"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="resource_flow_review_anomaly" name="resource-flow '
                 'reviewAnomaly" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.resourceFlow.reviewAnomaly", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="request">\n'
                 '      <bpmn:outgoing>Flow_Start_Review</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Start_Review" sourceRef="Start" '
                 'targetRef="Task_Review"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Review" name="append anomaly review">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="resource-flow.review.anomaly"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=anomalyId" target="anomalyId"/>\n'
                 '          <zeebe:input source="=action" target="action"/>\n'
                 '          <zeebe:input source="=reason" target="reason"/>\n'
                 '          <zeebe:input source="=reviewerDid" target="reviewerDid"/>\n'
                 '          <zeebe:input source="=primaryDid" target="primaryDid"/>\n'
                 '          <zeebe:input source="=orgId" target="orgId"/>\n'
                 '          <zeebe:input source="=userId" target="userId"/>\n'
                 '          <zeebe:output source="=reviewId" target="reviewId"/>\n'
                 '          <zeebe:output source="=anomalyId" target="anomalyId"/>\n'
                 '          <zeebe:output source="=action" target="action"/>\n'
                 '          <zeebe:output source="=vertexId" target="vertexId"/>\n'
                 '          <zeebe:output source="=error" target="error"/>\n'
                 '          <zeebe:output source="=message" target="message"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Start_Review</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Review_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Review_Audit" sourceRef="Task_Review" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:resource-flow.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;resource-flow.review.anomaly&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={anomalyId: anomalyId, reviewId: reviewId, '
                 'action: action, vertexId: vertexId, error: error}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Review_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3167,
                 '00-contracts/bpmn/ai/gftd/resource-flow/reviewAnomaly.bpmn',
                 '2026-05-06T03:00:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-project-review']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    ) VALUES (\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/resource-flow-projectFlow-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'app.etzhayyim.apps.resourceFlow.projectFlow',
                 'resource_flow_project_flow',
                 60000,
                 '2026-05-06T03:00:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-project-review']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    ) VALUES (\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/resource-flow-reviewAnomaly-v1',
                 'did:web:resource-flow.etzhayyim.com',
                 'app.etzhayyim.apps.resourceFlow.reviewAnomaly',
                 'resource_flow_review_anomaly',
                 60000,
                 '2026-05-06T03:00:00Z',
                 'did:web:resource-flow.etzhayyim.com',
                 'did:web:resource-flow.etzhayyim.com',
                 'sys.bpmn.seed.resource-flow-project-review']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/resource-flow-projectFlow-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/resource-flow-reviewAnomaly-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/resource-flow-project-flow-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/resource-flow-review-anomaly-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
