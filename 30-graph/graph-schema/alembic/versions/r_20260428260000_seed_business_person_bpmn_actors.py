"""Captured from Kysely migration 20260428260000_seed_business_person_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428260000_seed_business_person_bpmn_actors"
down_revision = 'r_20260428260000_actor_did_backfill_tier2'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/business-person-score-influence-v1',
                 'did:web:business-person.etzhayyim.com',
                 'business_person_score_influence',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Influence scoring pipeline — pure SQL, no LLM.\n'
                 '\n'
                 '  NSID:       ai.gftd.apps.businessPerson.scoreInfluence\n'
                 '  Owner DID:  did:web:business-person.etzhayyim.com\n'
                 '  Process ID: business_person_score_influence\n'
                 '\n'
                 '  Fires every 24h (R/PT24H).\n'
                 '  Reads mv_influence_centrality, assigns faction_label via hub/bridge '
                 'heuristic,\n'
                 '  writes vertex_influence_score rows.\n'
                 '  Phase 1: pure SQL centrality (hub_score / bridge_score / gov_score).\n'
                 '  Phase 2 (future): enrichCareerLLM adds career events with confidence≥0.6.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_business_person_score_influence"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/business-person"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="business_person_score_influence" name="business person score '
                 'influence" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.businessPerson.scoreInfluence", "version": 1, '
                 '"resultTimeoutMs": 120000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="every 24h">\n'
                 '      <bpmn:outgoing>Flow_ToSelectPersons</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_24h">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT24H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSelectPersons" sourceRef="Start" '
                 'targetRef="Task_SelectPersons"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SelectPersons" name="select persons from '
                 'centrality MV">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition '
                 'type="businessPerson.selectPersonsFromCentralityMv" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=persons" target="persons"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSelectPersons</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToComputeScores</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToComputeScores" sourceRef="Task_SelectPersons" '
                 'targetRef="Task_ComputeScores"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ComputeScores" name="compute influence scores">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="businessPerson.computeInfluenceScores" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=persons" target="persons"/>\n'
                 '          <zeebe:output source="=scores" target="scores"/>\n'
                 '          <zeebe:output source="=scoresCount" target="scoresCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToComputeScores</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToWriteScores</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToWriteScores" sourceRef="Task_ComputeScores" '
                 'targetRef="Task_WriteScores"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_WriteScores" name="write influence scores to '
                 'graph">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="businessPerson.writeInfluenceScores" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=scores" target="scores"/>\n'
                 '          <zeebe:output source="=recordsWritten" target="recordsWritten"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToWriteScores</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_WriteScores" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit influence scoring run">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:business-person.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;businessPerson.scoreInfluence.completed&quot;" target="action"/>\n'
                 '          <zeebe:input source="={scoresCount: scoresCount, recordsWritten: '
                 'recordsWritten}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="scores written">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4483,
                 '00-contracts/bpmn/ai/gftd/business-person/scoreInfluence.bpmn',
                 '2026-04-28T26:00:00Z',
                 'did:web:business-person.etzhayyim.com',
                 'did:web:business-person.etzhayyim.com',
                 'sys.bpmn.seed.business-person',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/business-person-score-influence-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), 'active',\n"
         '        $6, 1, $7, $8, $9\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/business-person-scoreInfluence-v1',
                 'did:web:business-person.etzhayyim.com',
                 'ai.gftd.apps.businessPerson.scoreInfluence',
                 'business_person_score_influence',
                 60000,
                 '2026-04-28T26:00:00Z',
                 'did:web:business-person.etzhayyim.com',
                 'did:web:business-person.etzhayyim.com',
                 'sys.bpmn.seed.business-person',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/business-person-scoreInfluence-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/business-person-enrich-career-l-l-m-v1',
                 'did:web:business-person.etzhayyim.com',
                 'business_person_enrich_career_llm',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  LLM-driven career enrichment pipeline (RunPod Serverless).\n'
                 '\n'
                 '  NSID:       ai.gftd.apps.businessPerson.enrichCareerLLM\n'
                 '  Owner DID:  did:web:business-person.etzhayyim.com\n'
                 '  Process ID: business_person_enrich_career_llm\n'
                 '\n'
                 '  Fires every 7 days (R/PT7D).\n'
                 '  Selects persons whose career data is stale (last_enriched_at older than 7d or '
                 'NULL).\n'
                 '  Fetches news / corporate HP pages, calls RunPod LLM to extract career events,\n'
                 '  writes to vertex_business_person_career_event with:\n'
                 "    confidence = 0.6, verification_status = 'llm_inferred'\n"
                 '  Provenance gate: only writes if rwHealthy and score data already exists in\n'
                 '  vertex_influence_score (Phase 1 scoreInfluence must have run first).\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_business_person_enrich_career_llm"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/business-person"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="business_person_enrich_career_llm" name="business person '
                 'enrich career LLM" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.businessPerson.enrichCareerLLM", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="every 7 days">\n'
                 '      <bpmn:outgoing>Flow_ToSelectStale</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_7d">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT168H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSelectStale" sourceRef="Start" '
                 'targetRef="Task_SelectStale"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_SelectStale" name="select persons needing '
                 'enrichment">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="businessPerson.selectStalePersons" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=persons" target="persons"/>\n'
                 '          <zeebe:output source="=personsCount" target="personsCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSelectStale</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToStaleGate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToStaleGate" sourceRef="Task_SelectStale" '
                 'targetRef="Gateway_HasPersons"/>\n'
                 '    <bpmn:exclusiveGateway id="Gateway_HasPersons" name="has stale persons?">\n'
                 '      <bpmn:incoming>Flow_ToStaleGate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToFetchNews</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_NoPersons</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToFetchNews" sourceRef="Gateway_HasPersons" '
                 'targetRef="Task_FetchNews">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=personsCount '
                 '&gt; 0</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_NoPersons" sourceRef="Gateway_HasPersons" '
                 'targetRef="Task_AuditNoPersons"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_FetchNews" name="fetch news and corporate HP '
                 'pages">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="businessPerson.fetchNewsCareer" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=persons" target="persons"/>\n'
                 '          <zeebe:output source="=pageTexts" target="pageTexts"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToFetchNews</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToExtractLLM</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToExtractLLM" sourceRef="Task_FetchNews" '
                 'targetRef="Task_ExtractLLM"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_ExtractLLM" name="extract career events via '
                 'RunPod LLM">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="businessPerson.extractCareerLLM" '
                 'retries="1"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=pageTexts" target="pageTexts"/>\n'
                 '          <zeebe:input source="=persons" target="persons"/>\n'
                 '          <zeebe:output source="=extractions" target="extractions"/>\n'
                 '          <zeebe:output source="=extractionsCount" target="extractionsCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToExtractLLM</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToWriteCareer</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToWriteCareer" sourceRef="Task_ExtractLLM" '
                 'targetRef="Task_WriteCareer"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_WriteCareer" name="write career enrichment to '
                 'graph">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="businessPerson.writeCareerEnrichment" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=extractions" target="extractions"/>\n'
                 '          <zeebe:output source="=recordsWritten" target="recordsWritten"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToWriteCareer</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_WriteCareer" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit LLM career enrichment run">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:business-person.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;businessPerson.enrichCareerLLM.completed&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={personsCount: personsCount, extractionsCount: '
                 'extractionsCount, recordsWritten: recordsWritten}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditNoPersons" name="audit no stale persons">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:business-person.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;businessPerson.enrichCareerLLM.abort&quot;" target="action"/>\n'
                 '          <zeebe:input source="={reason: &quot;no_stale_persons&quot;, '
                 'personsCount: personsCount}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_NoPersons</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_NoPersonsEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_NoPersonsEnd" sourceRef="Task_AuditNoPersons" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="enrichment written">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_NoPersonsEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 6970,
                 '00-contracts/bpmn/ai/gftd/business-person/enrichCareerLLM.bpmn',
                 '2026-04-28T26:00:00Z',
                 'did:web:business-person.etzhayyim.com',
                 'did:web:business-person.etzhayyim.com',
                 'sys.bpmn.seed.business-person',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/business-person-enrich-career-l-l-m-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), 'active',\n"
         '        $6, 1, $7, $8, $9\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/business-person-enrichCareerLLM-v1',
                 'did:web:business-person.etzhayyim.com',
                 'ai.gftd.apps.businessPerson.enrichCareerLLM',
                 'business_person_enrich_career_llm',
                 120000,
                 '2026-04-28T26:00:00Z',
                 'did:web:business-person.etzhayyim.com',
                 'did:web:business-person.etzhayyim.com',
                 'sys.bpmn.seed.business-person',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/business-person-enrichCareerLLM-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/business-person-scoreInfluence-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/business-person-score-influence-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/business-person-enrichCareerLLM-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/business-person-enrich-career-l-l-m-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
