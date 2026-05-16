"""Captured from Kysely migration 20260427230800_seed_lawfirm_search_precedent_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427230800_seed_lawfirm_search_precedent_bpmn"
down_revision = 'r_20260427230700_legal_corpus_native_vector_type'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, CAST($4 AS integer), $5, CAST($6 AS integer), $7, 'active', $8, "
         '1, $9, $10, $11\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-search-precedent-v1',
                 'did:web:lawfirm.gftd.ai',
                 'lawfirm_search_precedent',
                 1,
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_lawfirm_search_precedent" '
                 'targetNamespace="https://gftd.ai/bpmn/lawfirm" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="lawfirm_search_precedent" name="searchPrecedent" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_R</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_R" sourceRef="Start" '
                 'targetRef="Task_ResolveJurisdiction"/>\n'
                 '    <bpmn:serviceTask id="Task_ResolveJurisdiction" name="resolve firm '
                 'jurisdiction">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT primary_jurisdiction FROM '
                 'vertex_lawfirm_profile WHERE firm_did = $1 LIMIT 1&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[firmDid]" target="params"/>\n'
                 '          <zeebe:output source="=if jurisdiction != null then jurisdiction else '
                 '(if rows[1] != null then rows[1].primary_jurisdiction else null)" '
                 'target="effectiveJurisdiction"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_R</bpmn:incoming><bpmn:outgoing>Flow_S</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Task_ResolveJurisdiction" '
                 'targetRef="Task_Search"/>\n'
                 '    <bpmn:callActivity id="Task_Search" name="delegate to legal-corpus '
                 'searchDocument">\n'
                 '      <bpmn:extensionElements><zeebe:calledElement '
                 'processId="legal_corpus_search_document"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=queryText" target="queryText"/>\n'
                 '          <zeebe:input source="=effectiveJurisdiction" target="jurisdiction"/>\n'
                 '          <zeebe:input source="=documentType" target="documentType"/>\n'
                 '          <zeebe:input source="=languageCode" target="languageCode"/>\n'
                 '          <zeebe:input source="=decidedAfter" target="decidedAfter"/>\n'
                 '          <zeebe:input source="=decidedBefore" target="decidedBefore"/>\n'
                 '          <zeebe:input source="=if limit != null then limit else 10" '
                 'target="limit"/>\n'
                 '          <zeebe:output source="=hits" target="hits"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:callActivity>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Search" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2561,
                 '00-contracts/bpmn/ai/gftd/lawfirm/searchPrecedent.bpmn',
                 '2026-04-27T23:08:00Z',
                 'did:web:lawfirm.gftd.ai',
                 'did:web:lawfirm.gftd.ai',
                 'sys.bpmn.seed.lawfirm-search-precedent',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-search-precedent-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, CAST($4 AS integer), $5, CAST($6 AS integer), $7, 'active', $8, "
         '1, $9, $10, $11\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-run-conflict-check-v2',
                 'did:web:lawfirm.gftd.ai',
                 'lawfirm_run_conflict_check',
                 2,
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_lawfirm_run_conflict_check" '
                 'targetNamespace="https://gftd.ai/bpmn/lawfirm" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="lawfirm_run_conflict_check" name="runConflictCheck" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_LoadParties"/>\n'
                 '    <bpmn:serviceTask id="Task_LoadParties" name="load past matters by party">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id, matter_type, opened_at, '
                 'status FROM vertex_lawfirm_matter WHERE firm_did = $1 AND (client_did = ANY($2) '
                 'OR EXISTS (SELECT 1 FROM edge_lawfirm_counterparty e WHERE e.src_vid = '
                 'vertex_lawfirm_matter.vertex_id AND e.dst_vid = ANY($2))) LIMIT 200&quot;" '
                 'target="sql"/>\n'
                 '          <zeebe:input source="=[firmDid, partyDids]" target="params"/>\n'
                 '          <zeebe:output source="=rows" target="pastMatters"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_E</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_E" sourceRef="Task_LoadParties" '
                 'targetRef="Task_Embed"/>\n'
                 '    <bpmn:serviceTask id="Task_Embed" name="embed subject matter">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.http.fetch" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;POST&quot;" target="method"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://api.cloudflare.com/client/v4/accounts/&quot; + '
                 'cfAccountId + &quot;/ai/run/@cf/baai/bge-m3&quot;" target="url"/>\n'
                 '          <zeebe:input source="={Authorization: &quot;Bearer &quot; + '
                 'cfApiToken}" target="headers"/>\n'
                 '          <zeebe:input source="={text: subjectMatter}" target="body"/>\n'
                 '          <zeebe:output source="=response.result.data[1]" '
                 'target="queryEmbedding"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_E</bpmn:incoming><bpmn:outgoing>Flow_C</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_C" sourceRef="Task_Embed" '
                 'targetRef="Task_Precedent"/>\n'
                 '    <bpmn:callActivity id="Task_Precedent" name="search legal-corpus '
                 'precedent">\n'
                 '      <bpmn:extensionElements><zeebe:calledElement '
                 'processId="legal_corpus_search_document"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=subjectMatter" target="queryText"/>\n'
                 '          <zeebe:input source="=firmJurisdiction" target="jurisdiction"/>\n'
                 '          <zeebe:input source="=null" target="documentType"/>\n'
                 '          <zeebe:input source="=null" target="languageCode"/>\n'
                 '          <zeebe:input source="=null" target="decidedAfter"/>\n'
                 '          <zeebe:input source="=null" target="decidedBefore"/>\n'
                 '          <zeebe:input source="=10" target="limit"/>\n'
                 '          <zeebe:output source="=hits" target="precedentHits"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_C</bpmn:incoming><bpmn:outgoing>Flow_D</bpmn:outgoing>\n'
                 '    </bpmn:callActivity>\n'
                 '    <bpmn:sequenceFlow id="Flow_D" sourceRef="Task_Precedent" '
                 'targetRef="Task_Classify"/>\n'
                 '    <bpmn:businessRuleTask id="Task_Classify" name="apply conflict dmn">\n'
                 '      <bpmn:extensionElements><zeebe:calledDecision '
                 'decisionId="lawfirm_conflict_severity" '
                 'resultVariable="conflictResult"/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_D</bpmn:incoming><bpmn:outgoing>Flow_W</bpmn:outgoing>\n'
                 '    </bpmn:businessRuleTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_W" sourceRef="Task_Classify" '
                 'targetRef="Task_Write"/>\n'
                 '    <bpmn:serviceTask id="Task_Write" name="write conflict-check record">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;INSERT INTO vertex_lawfirm_conflict_check '
                 '(vertex_id, firm_did, requested_by_did, party_dids_csv, subject_matter, '
                 'severity, status, past_matter_count, precedent_uris_csv, precedent_top_score, '
                 'checked_at, owner_did, sensitivity_ord, created_at) VALUES ($1, $2, $3, $4, $5, '
                 '$6, $7, $8, $9, $10, $11, $12, $13, $14)&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[&quot;at://&quot; + firmDid + '
                 '&quot;/ai.gftd.apps.lawfirm.conflictCheck/&quot; + checkId, firmDid, callerDid, '
                 'partyDids, subjectMatter, conflictResult.severity, conflictResult.status, '
                 'count(pastMatters), string join([for h in precedentHits return h.canonical_uri], '
                 '&quot;,&quot;), if precedentHits != null and precedentHits[1] != null then '
                 'precedentHits[1].score else null, now, firmDid, 2, now]" target="params"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_W</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Write" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5152,
                 '00-contracts/bpmn/ai/gftd/lawfirm/runConflictCheck.bpmn',
                 '2026-04-27T23:08:00Z',
                 'did:web:lawfirm.gftd.ai',
                 'did:web:lawfirm.gftd.ai',
                 'sys.bpmn.seed.lawfirm-search-precedent',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-run-conflict-check-v2']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, CAST($5 AS integer), CAST($6 AS integer), 'active', $7, 1, "
         '$8, $9, $10\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-searchPrecedent-v1',
                 'did:web:lawfirm.gftd.ai',
                 'ai.gftd.apps.lawfirm.searchPrecedent',
                 'lawfirm_search_precedent',
                 1,
                 30000,
                 '2026-04-27T23:08:00Z',
                 'did:web:lawfirm.gftd.ai',
                 'did:web:lawfirm.gftd.ai',
                 'sys.bpmn.seed.lawfirm-search-precedent',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-searchPrecedent-v1']},
 {'sql': "UPDATE vertex_bpmn_lexicon_binding SET status = 'superseded' WHERE vertex_id = $1",
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-runConflictCheck-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, CAST($5 AS integer), CAST($6 AS integer), 'active', $7, 1, "
         '$8, $9, $10\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-runConflictCheck-v2',
                 'did:web:lawfirm.gftd.ai',
                 'ai.gftd.apps.lawfirm.runConflictCheck',
                 'lawfirm_run_conflict_check',
                 2,
                 60000,
                 '2026-04-27T23:08:00Z',
                 'did:web:lawfirm.gftd.ai',
                 'did:web:lawfirm.gftd.ai',
                 'sys.bpmn.seed.lawfirm-search-precedent',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-runConflictCheck-v2']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-searchPrecedent-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-runConflictCheck-v2']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-search-precedent-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-run-conflict-check-v2']},
 {'sql': "UPDATE vertex_bpmn_lexicon_binding SET status = 'active' WHERE vertex_id = $1",
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-runConflictCheck-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
