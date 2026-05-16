"""Captured from Kysely migration 20260430702000_seed_natural_person_seed_latent_entities_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430702000_seed_natural_person_seed_latent_entities_bpmn"
down_revision = 'r_20260430700100_seed_ir_scrape_bpmn'
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/natural-person-seed-latent-entities-v1',
                 'did:web:natural-person.gftd.ai',
                 'natural_person_seed_latent_entities_v1',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  naturalPerson.seedLatentEntities — always-on frontier latent pointer seeding\n'
                 '\n'
                 '  Timer:\n'
                 '    R/PT5M. Every five minutes, materialize missing RisingWave frontier\n'
                 '    pointers for natural-person cohorts. This does not attempt to create the\n'
                 '    all-human individual universe in RisingWave; it keeps the cohort/latent\n'
                 '    frontier current for later policy review and actor fission.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.naturalPerson.seedLatentEntities\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="naturalPersonSeedLatentEntities"\n'
                 '    targetNamespace="http://bpmn.io/schema/bpmn"\n'
                 '    exporter="Camunda Modeler"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="natural_person_seed_latent_entities_v1" '
                 'name="naturalPerson.seedLatentEntities" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="R/PT5M timer">\n'
                 '      <bpmn:outgoing>Flow_timer_to_plan</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="TimerDef_5M">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Manual" name="XRPC trigger">\n'
                 '      <bpmn:outgoing>Flow_manual_to_plan</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ReadPlan" name="Read missing latent entity '
                 'plan">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT COUNT(*)::bigint AS '
                 'planned_entities FROM vertex_natural_person_cohort_person c WHERE c.cohort_hash '
                 "IS NOT NULL AND c.cohort_hash &lt;&gt; '' AND NOT EXISTS (SELECT 1 FROM "
                 'vertex_latent_entity e WHERE e.vertex_id = '
                 "'at://did:web:coverage.gftd.ai/ai.gftd.apps.coverage.latentEntity/natural-person-cohort-' "
                 '|| c.cohort_hash)&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:input source="=60000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=rows[1]" target="seedPlan"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_timer_to_plan</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_manual_to_plan</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_plan_to_seed_entities</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SeedEntities" name="Seed missing latent '
                 'entities">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;INSERT INTO vertex_latent_entity '
                 '(vertex_id, _seq, sensitivity_ord, owner_did, actor_did, org_did, created_at, '
                 'entity_kind, canonical_label, existence_probability, k_evidence_count, '
                 'viewpoint_consensus, fission_eligible, status, primary_topic_vid, '
                 'individual_did) SELECT '
                 "'at://did:web:coverage.gftd.ai/ai.gftd.apps.coverage.latentEntity/natural-person-cohort-' "
                 "|| c.cohort_hash, 1, 300, 'did:web:coverage.gftd.ai', "
                 "'did:web:coverage.gftd.ai', 'did:web:coverage.gftd.ai', NOW(), "
                 "'natural_person_cohort', 'natural person cohort: ' || c.cohort_hash, 0.99, CASE "
                 'WHEN c.intel_estimated_count &gt; 0 THEN 1 ELSE 0 END, 1, c.vital_status = '
                 "'alive', 'active', c.vertex_id, 'did:web:natural-person.gftd.ai:latent:' || "
                 'c.cohort_hash FROM vertex_natural_person_cohort_person c WHERE c.cohort_hash IS '
                 "NOT NULL AND c.cohort_hash &lt;&gt; '' AND NOT EXISTS (SELECT 1 FROM "
                 'vertex_latent_entity e WHERE e.vertex_id = '
                 "'at://did:web:coverage.gftd.ai/ai.gftd.apps.coverage.latentEntity/natural-person-cohort-' "
                 '|| c.cohort_hash)&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:input source="=300000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=updated" target="insertedEntities"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_plan_to_seed_entities</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_entities_to_seed_cohort_links</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SeedCohortLinks" name="Seed missing entity cohort '
                 'links">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;INSERT INTO edge_entity_cohort_link '
                 '(edge_id, _seq, sensitivity_ord, owner_did, actor_did, org_did, created_at, '
                 'src_vid, dst_vid, link_confidence) SELECT '
                 "'at://did:web:coverage.gftd.ai/ai.gftd.apps.coverage.entityCohortLink/natural-person-cohort-' "
                 "|| c.cohort_hash, 1, 300, 'did:web:coverage.gftd.ai', "
                 "'did:web:coverage.gftd.ai', 'did:web:coverage.gftd.ai', NOW(), "
                 "'at://did:web:coverage.gftd.ai/ai.gftd.apps.coverage.latentEntity/natural-person-cohort-' "
                 '|| c.cohort_hash, c.vertex_id, 0.99 FROM vertex_natural_person_cohort_person c '
                 "WHERE c.cohort_hash IS NOT NULL AND c.cohort_hash &lt;&gt; '' AND NOT EXISTS "
                 '(SELECT 1 FROM edge_entity_cohort_link l WHERE l.edge_id = '
                 "'at://did:web:coverage.gftd.ai/ai.gftd.apps.coverage.entityCohortLink/natural-person-cohort-' "
                 '|| c.cohort_hash)&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:input source="=300000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=updated" target="insertedCohortLinks"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_entities_to_seed_cohort_links</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_cohort_links_to_seed_evidence</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SeedEvidence" name="Seed missing entity evidence '
                 'links">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;INSERT INTO edge_entity_evidence (edge_id, '
                 '_seq, sensitivity_ord, owner_did, actor_did, org_did, created_at, src_vid, '
                 'dst_vid, evidence_weight) SELECT '
                 "'at://did:web:coverage.gftd.ai/ai.gftd.apps.coverage.entityEvidence/natural-person-cohort-' "
                 "|| c.cohort_hash, 1, 300, 'did:web:coverage.gftd.ai', "
                 "'did:web:coverage.gftd.ai', 'did:web:coverage.gftd.ai', NOW(), c.vertex_id, "
                 "'at://did:web:coverage.gftd.ai/ai.gftd.apps.coverage.latentEntity/natural-person-cohort-' "
                 '|| c.cohort_hash, 1.0 FROM vertex_natural_person_cohort_person c WHERE '
                 "c.cohort_hash IS NOT NULL AND c.cohort_hash &lt;&gt; '' AND NOT EXISTS (SELECT 1 "
                 'FROM edge_entity_evidence ev WHERE ev.edge_id = '
                 "'at://did:web:coverage.gftd.ai/ai.gftd.apps.coverage.entityEvidence/natural-person-cohort-' "
                 '|| c.cohort_hash)&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:input source="=300000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=updated" target="insertedEvidenceLinks"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_cohort_links_to_seed_evidence</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_evidence_to_verify</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Verify" name="Verify latent frontier totals">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT COUNT(*)::bigint AS '
                 'total_latent_entities FROM vertex_latent_entity WHERE entity_kind = '
                 '\'natural_person_cohort\'&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:input source="=60000" target="resultTimeoutMs"/>\n'
                 '          <zeebe:output source="=rows[1]" target="seedVerify"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_evidence_to_verify</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_verify_to_audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="OCEL audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:natural-person.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;naturalPerson.seedLatentEntities.complete&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={\n'
                 '              &quot;plannedEntities&quot;: seedPlan.planned_entities,\n'
                 '              &quot;insertedEntities&quot;: insertedEntities,\n'
                 '              &quot;insertedCohortLinks&quot;: insertedCohortLinks,\n'
                 '              &quot;insertedEvidenceLinks&quot;: insertedEvidenceLinks,\n'
                 '              &quot;totalLatentEntities&quot;: seedVerify.total_latent_entities\n'
                 '          }" target="payload"/>\n'
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
                 '    <bpmn:sequenceFlow id="Flow_timer_to_plan" sourceRef="Start_Timer" '
                 'targetRef="Task_ReadPlan"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_manual_to_plan" sourceRef="Start_Manual" '
                 'targetRef="Task_ReadPlan"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_plan_to_seed_entities" sourceRef="Task_ReadPlan" '
                 'targetRef="Task_SeedEntities"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_entities_to_seed_cohort_links" '
                 'sourceRef="Task_SeedEntities" targetRef="Task_SeedCohortLinks"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_cohort_links_to_seed_evidence" '
                 'sourceRef="Task_SeedCohortLinks" targetRef="Task_SeedEvidence"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_evidence_to_verify" '
                 'sourceRef="Task_SeedEvidence" targetRef="Task_Verify"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_verify_to_audit" sourceRef="Task_Verify" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_audit_to_end" sourceRef="Task_Audit" '
                 'targetRef="End"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 9850,
                 '00-contracts/bpmn/ai/gftd/natural-person/seedLatentEntities.bpmn',
                 '2026-04-30T20:20:00Z',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 'sys.bpmn.seed.natural-person',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/natural-person-seed-latent-entities-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/natural-person-seedLatentEntities-v1',
                 'did:web:natural-person.gftd.ai',
                 'ai.gftd.apps.naturalPerson.seedLatentEntities',
                 'natural_person_seed_latent_entities_v1',
                 300000,
                 '2026-04-30T20:20:00Z',
                 'did:web:natural-person.gftd.ai',
                 'did:web:natural-person.gftd.ai',
                 'sys.bpmn.seed.natural-person',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/natural-person-seedLatentEntities-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/natural-person-seedLatentEntities-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/natural-person-seed-latent-entities-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
