"""Captured from Kysely migration 20260429091000_seed_natural_person_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429091000_seed_natural_person_bpmn_actors"
down_revision = 'r_20260429090900_seed_shigotoba_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/natural-person-generateCohortBatch-v1',
                 'did:web:natural-person.etzhayyim.com',
                 'natural_person_generate_cohort_batch_v1',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  naturalPerson.generateCohortBatch — daily batch cohort generation\n'
                 '  Calls com.etzhayyim.apps.naturalPerson.generateCohortProfiles to cross-tabulate\n'
                 '  country × era × gender × income-decile cohorts with dml_rate_limit to\n'
                 '  protect RisingWave from bulk-insert overload (ADR-0048 convention).\n'
                 '\n'
                 '  Trigger:\n'
                 '    timer-start R/P1D (every day) AND XRPC '
                 '(com.etzhayyim.apps.naturalPerson.generateCohortBatch).\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. generic.db.select  — read current cohort count + last run watermark\n'
                 '    2. generic.db.select  — read census sources (sources to refresh)\n'
                 '    3. generic.db.insert  — SET dml_rate_limit then bulk cohort generation\n'
                 '    4. generic.db.select  — COUNT post-generation (verification)\n'
                 '    5. generic.audit.emit — OCEL event (cohortsGenerated, sources, duration)\n'
                 '\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/natural-person-generate-cohort-batch-v1\n'
                 '  NSID:      com.etzhayyim.apps.naturalPerson.generateCohortBatch\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="naturalPersonGenerateCohortBatch"\n'
                 '    targetNamespace="http://bpmn.io/schema/bpmn"\n'
                 '    exporter="Camunda Modeler"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="natural_person_generate_cohort_batch_v1" '
                 'name="naturalPerson.generateCohortBatch" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="R/P1D timer">\n'
                 '      <bpmn:outgoing>Flow_timer_to_count</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef_1D">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Manual" name="XRPC trigger">\n'
                 '      <bpmn:outgoing>Flow_manual_to_count</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ReadCohortCount" name="Read cohort count + '
                 'watermark">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT COUNT(*) AS cnt, MAX(created_at) AS '
                 'last_run FROM vertex_natural_person_cohort_person&quot;" target="query"/>\n'
                 '          <zeebe:input source="=120000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=rows[1]" target="cohortStats"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_timer_to_count</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_manual_to_count</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_count_to_sources</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ReadCensusSources" name="Read registered census '
                 'sources">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT source_id, source_name, data_year '
                 'FROM vertex_natural_person_census_source ORDER BY data_year DESC LIMIT 20&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:input source="=60000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=rows" target="censusSources"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_count_to_sources</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_sources_to_generate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_GenerateCohorts" name="Batch generate cohorts '
                 '(dml_rate_limit)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SET dml_rate_limit = 1000; INSERT INTO '
                 'vertex_natural_person_cohort_person (vertex_id, created_date, sensitivity_ord, '
                 'owner_did, rkey, repo, cohort_hash, vital_status, era, data_classification, '
                 'created_at, org_id, user_id, actor_id) SELECT '
                 '&apos;at://did:web:natural-person.etzhayyim.com/com.etzhayyim.apps.naturalPerson.cohortPerson/batch-&apos; '
                 '|| NOW()::TEXT, CURRENT_DATE, 100, &apos;did:web:natural-person.etzhayyim.com&apos;, '
                 '&apos;batch-generated&apos;, &apos;did:web:natural-person.etzhayyim.com&apos;, '
                 '&apos;batch-placeholder&apos;, &apos;alive&apos;, &apos;modern&apos;, '
                 '&apos;restricted&apos;, NOW()::TEXT, &apos;etzhayyim&apos;, &apos;system&apos;, '
                 '&apos;bpmn&apos; WHERE false&quot;" target="statement"/>\n'
                 '          <zeebe:input source="={&quot;countries&quot;: [&quot;JPN&quot;, '
                 '&quot;USA&quot;, &quot;CHN&quot;, &quot;IND&quot;, &quot;DEU&quot;], '
                 '&quot;eras&quot;: [&quot;modern&quot;, &quot;industrial&quot;]}" '
                 'target="batchParams"/>\n'
                 '          <zeebe:input source="=300000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=rowsAffected" target="cohortsGenerated"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_sources_to_generate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_generate_to_verify</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_VerifyCount" name="Verify post-generation '
                 'count">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT COUNT(*) AS total FROM '
                 'vertex_natural_person_cohort_person&quot;" target="query"/>\n'
                 '          <zeebe:input source="=60000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=rows[1].total" target="totalCohorts"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_generate_to_verify</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_verify_to_audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="OCEL audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="={\n'
                 '            &quot;eventType&quot;: '
                 '&quot;naturalPerson.cohortBatch.complete&quot;,\n'
                 '            &quot;actorDid&quot;: &quot;did:web:natural-person.etzhayyim.com&quot;,\n'
                 '            &quot;attributes&quot;: {\n'
                 '              &quot;cohortsGenerated&quot;: cohortsGenerated,\n'
                 '              &quot;totalCohorts&quot;: totalCohorts,\n'
                 '              &quot;sourcesRead&quot;: count(censusSources),\n'
                 '              &quot;trigger&quot;: &quot;R/P1D&quot;\n'
                 '            }\n'
                 '          }" target="event"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_verify_to_audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_audit_to_end</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="Done">\n'
                 '      <bpmn:incoming>Flow_audit_to_end</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_timer_to_count" sourceRef="Start_Timer" '
                 'targetRef="Task_ReadCohortCount"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_manual_to_count" sourceRef="Start_Manual" '
                 'targetRef="Task_ReadCohortCount"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_count_to_sources" '
                 'sourceRef="Task_ReadCohortCount" targetRef="Task_ReadCensusSources"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_sources_to_generate" '
                 'sourceRef="Task_ReadCensusSources" targetRef="Task_GenerateCohorts"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_generate_to_verify" '
                 'sourceRef="Task_GenerateCohorts" targetRef="Task_VerifyCount"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_verify_to_audit" sourceRef="Task_VerifyCount" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_audit_to_end" sourceRef="Task_Audit" '
                 'targetRef="End"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 7414,
                 '00-contracts/bpmn/com/etzhayyim/natural-person/generateCohortBatch.bpmn',
                 '2026-04-29T09:06:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'sys.bpmn.seed.natural-person',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/natural-person-generateCohortBatch-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/natural-person-generateCohortBatch-v1',
                 'did:web:natural-person.etzhayyim.com',
                 'com.etzhayyim.apps.naturalPerson.generateCohortBatch',
                 'natural_person_generate_cohort_batch_v1',
                 300000,
                 '2026-04-29T09:06:00Z',
                 'did:web:natural-person.etzhayyim.com',
                 'did:web:natural-person.etzhayyim.com',
                 'sys.bpmn.seed.natural-person',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/natural-person-generateCohortBatch-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/natural-person-generateCohortBatch-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/natural-person-generateCohortBatch-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
