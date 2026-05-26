"""Captured from Kysely migration 20260430182000_seed_natural_person_reconcile_visibility_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430182000_seed_natural_person_reconcile_visibility_bpmn"
down_revision = 'r_20260430170000_seed_chart_bpmn'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/natural-person-reconcile-visibility-v1',
                 'did:web:natural-person.etzhayyim.com',
                 'natural_person_reconcile_visibility_v1',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  naturalPerson.reconcileVisibility — visibility-class reconciliation guard\n'
                 '\n'
                 '  Safe default:\n'
                 '    applyOpenalexPublic is false unless explicitly passed by XRPC/BPMN caller.\n'
                 '    In dry-run mode the workflow only reads counts and emits audit.\n'
                 '\n'
                 '  First apply scope:\n'
                 "    vertex_natural_person rows from OpenAlex with data_classification='open'\n"
                 '    and sensitivity_ord IS NULL can be promoted to sensitivity_ord=0\n'
                 '    public_searchable. Business-person rows remain audit-only until source\n'
                 '    allow-listing is explicit.\n'
                 '\n'
                 '  NSID: app.etzhayyim.apps.naturalPerson.reconcileVisibility\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="naturalPersonReconcileVisibility"\n'
                 '    targetNamespace="http://bpmn.io/schema/bpmn"\n'
                 '    exporter="Camunda Modeler"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="natural_person_reconcile_visibility_v1" '
                 'name="naturalPerson.reconcileVisibility" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Manual" name="XRPC trigger">\n'
                 '      <bpmn:outgoing>Flow_start_to_read_plan</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ReadPlan" name="Read visibility reconciliation '
                 'plan">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT (SELECT COUNT(*)::bigint FROM '
                 'vertex_natural_person WHERE sensitivity_ord IS NULL AND data_classification = '
                 "'open' AND source_app = 'openalex') AS planned_openalex_public, (SELECT "
                 'COUNT(*)::bigint FROM vertex_business_person WHERE sensitivity_ord IS NULL) AS '
                 'business_unclassified, (SELECT COUNT(*)::bigint FROM (SELECT cohort_hash FROM '
                 'vertex_natural_person_cohort_person WHERE cohort_hash IS NOT NULL AND '
                 "cohort_hash &lt;&gt; '' GROUP BY cohort_hash HAVING COUNT(*) &gt; 1) x) AS "
                 'cohort_hash_collision_groups&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:input source="=60000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=rows[1]" target="visibilityPlan"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_start_to_read_plan</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_read_plan_to_apply_openalex</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ApplyOpenalexPublic" name="Apply OpenAlex public '
                 'rows when requested">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;UPDATE vertex_natural_person SET '
                 'sensitivity_ord = 0 WHERE COALESCE($1::boolean, false) = true AND '
                 "sensitivity_ord IS NULL AND data_classification = 'open' AND source_app = "
                 '\'openalex\'&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[applyOpenalexPublic]" target="params"/>\n'
                 '          <zeebe:input source="=300000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=updated" target="updatedOpenalexPublic"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_read_plan_to_apply_openalex</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_apply_openalex_to_audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="OCEL audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={\n'
                 '            &quot;eventType&quot;: '
                 '&quot;naturalPerson.visibilityReconcile.complete&quot;,\n'
                 '            &quot;actorDid&quot;: &quot;did:web:natural-person.etzhayyim.com&quot;,\n'
                 '            &quot;attributes&quot;: {\n'
                 '              &quot;applyOpenalexPublic&quot;: applyOpenalexPublic,\n'
                 '              &quot;plannedOpenalexPublic&quot;: '
                 'visibilityPlan.planned_openalex_public,\n'
                 '              &quot;updatedOpenalexPublic&quot;: updatedOpenalexPublic,\n'
                 '              &quot;businessUnclassified&quot;: '
                 'visibilityPlan.business_unclassified,\n'
                 '              &quot;cohortHashCollisionGroups&quot;: '
                 'visibilityPlan.cohort_hash_collision_groups\n'
                 '            }\n'
                 '          }" target="event"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_apply_openalex_to_audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_audit_to_end</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="Done">\n'
                 '      <bpmn:incoming>Flow_audit_to_end</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_start_to_read_plan" sourceRef="Start_Manual" '
                 'targetRef="Task_ReadPlan"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_read_plan_to_apply_openalex" '
                 'sourceRef="Task_ReadPlan" targetRef="Task_ApplyOpenalexPublic"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_apply_openalex_to_audit" '
                 'sourceRef="Task_ApplyOpenalexPublic" targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_audit_to_end" sourceRef="Task_Audit" '
                 'targetRef="End"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5013,
                 '00-contracts/bpmn/ai/gftd/natural-person/reconcileVisibility.bpmn',
                 '2026-04-30T18:20:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'sys.bpmn.seed.natural-person',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/natural-person-reconcile-visibility-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/natural-person-reconcileVisibility-v1',
                 'did:web:natural-person.etzhayyim.com',
                 'app.etzhayyim.apps.naturalPerson.reconcileVisibility',
                 'natural_person_reconcile_visibility_v1',
                 300000,
                 '2026-04-30T18:20:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'sys.bpmn.seed.natural-person',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/natural-person-reconcileVisibility-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/natural-person-reconcileVisibility-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/natural-person-reconcile-visibility-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
