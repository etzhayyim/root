"""Captured from Kysely migration 20260427230200_seed_lawfirm_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427230200_seed_lawfirm_bpmn_actors"
down_revision = 'r_20260427230100_seed_telecom_li_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-run-conflict-check-v1',
                 'did:web:lawfirm.gftd.ai',
                 'lawfirm_run_conflict_check',
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
                 '2026-04-27T23:02:00Z',
                 'did:web:lawfirm.gftd.ai',
                 'did:web:lawfirm.gftd.ai',
                 'sys.bpmn.seed.lawfirm',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-run-conflict-check-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-submit-filing-v1',
                 'did:web:lawfirm.gftd.ai',
                 'lawfirm_submit_filing',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_lawfirm_submit_filing" '
                 'targetNamespace="https://gftd.ai/bpmn/lawfirm" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="lawfirm_submit_filing" name="submitFiling" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_Validate"/>\n'
                 '    <bpmn:serviceTask id="Task_Validate" name="validate matter ownership">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT firm_did, status FROM '
                 'vertex_lawfirm_matter WHERE vertex_id = $1 LIMIT 1&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[matterUri]" target="params"/>\n'
                 '          <zeebe:output source="=rows[1]" target="matter"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_W</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_W" sourceRef="Task_Validate" '
                 'targetRef="Task_WriteFiling"/>\n'
                 '    <bpmn:serviceTask id="Task_WriteFiling" name="write filing record">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_lawfirm_filing&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: &quot;at://&quot; + matter.firm_did '
                 '+ &quot;/ai.gftd.apps.lawfirm.filing/&quot; + filingId, matter_uri: matterUri, '
                 'court_did: courtDid, filing_type: filingType, document_uris_csv: documentUris, '
                 'filed_at: now, status: &quot;submitted&quot;, owner_did: matter.firm_did, '
                 'sensitivity_ord: 2, created_at: now}" target="row"/>\n'
                 '          <zeebe:output source="=vertex_id" target="filingVid"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_W</bpmn:incoming><bpmn:outgoing>Flow_T</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_T" sourceRef="Task_WriteFiling" '
                 'targetRef="Task_Transmit"/>\n'
                 '    <bpmn:serviceTask id="Task_Transmit" name="transmit to court endpoint">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.http.fetch" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;POST&quot;" target="method"/>\n'
                 '          <zeebe:input source="=courtEndpointUrl" target="url"/>\n'
                 '          <zeebe:input source="={filingId: filingId, matterUri: matterUri, '
                 'filingType: filingType, documentUris: documentUris}" target="body"/>\n'
                 '          <zeebe:output source="=response.acknowledgmentId" target="ackId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_T</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Transmit" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:lawfirm.gftd.ai&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;lawfirm.submitFiling&quot;" target="action"/><zeebe:input '
                 'source="={filingVid: filingVid, ackId: ackId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3759,
                 '00-contracts/bpmn/ai/gftd/lawfirm/submitFiling.bpmn',
                 '2026-04-27T23:02:00Z',
                 'did:web:lawfirm.gftd.ai',
                 'did:web:lawfirm.gftd.ai',
                 'sys.bpmn.seed.lawfirm',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-submit-filing-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-issue-invoice-v1',
                 'did:web:lawfirm.gftd.ai',
                 'lawfirm_issue_invoice',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_lawfirm_issue_invoice" '
                 'targetNamespace="https://gftd.ai/bpmn/lawfirm" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="lawfirm_issue_invoice" name="issueInvoice" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_AggregateTime"/>\n'
                 '    <bpmn:serviceTask id="Task_AggregateTime" name="aggregate time entries">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT SUM(hours * hourly_rate) AS total, '
                 'COUNT(*) AS entry_count, currency FROM vertex_lawfirm_time_entry WHERE '
                 'matter_uri = $1 AND billed_at IS NULL AND occurred_at &gt;= $2 AND occurred_at '
                 '&lt; $3 GROUP BY currency LIMIT 1&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[matterUri, periodStart, periodEnd]" '
                 'target="params"/>\n'
                 '          <zeebe:output source="=rows[1]" target="agg"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_R</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_R" sourceRef="Task_AggregateTime" '
                 'targetRef="Task_RenderInvoice"/>\n'
                 '    <bpmn:serviceTask id="Task_RenderInvoice" name="render invoice json">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.llm.json" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;Render a legal invoice line summary for '
                 'matter &quot; + matterUri + &quot; covering &quot; + periodStart + &quot; to '
                 '&quot; + periodEnd + &quot;. Total &quot; + agg.total + &quot; &quot; + '
                 'agg.currency + &quot;. Output JSON with fields: lineItems[], subTotal, tax, '
                 'total.&quot;" target="prompt"/>\n'
                 '          <zeebe:output source="=response" target="invoiceJson"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_R</bpmn:incoming><bpmn:outgoing>Flow_W</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_W" sourceRef="Task_RenderInvoice" '
                 'targetRef="Task_WriteInvoice"/>\n'
                 '    <bpmn:serviceTask id="Task_WriteInvoice" name="write invoice record">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_lawfirm_invoice&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: &quot;at://&quot; + firmDid + '
                 '&quot;/ai.gftd.apps.lawfirm.invoice/&quot; + invoiceId, matter_uri: matterUri, '
                 'period_start: periodStart, period_end: periodEnd, total: agg.total, currency: '
                 'agg.currency, body_json: invoiceJson, status: &quot;issued&quot;, issued_at: '
                 'now, owner_did: firmDid, sensitivity_ord: 2, created_at: now}" target="row"/>\n'
                 '          <zeebe:output source="=vertex_id" target="invoiceVid"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_W</bpmn:incoming><bpmn:outgoing>Flow_M</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_M" sourceRef="Task_WriteInvoice" '
                 'targetRef="Task_MarkBilled"/>\n'
                 '    <bpmn:serviceTask id="Task_MarkBilled" name="mark time entries billed">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;UPDATE vertex_lawfirm_time_entry SET '
                 'billed_at = $1, invoice_uri = $2 WHERE matter_uri = $3 AND billed_at IS NULL AND '
                 'occurred_at &gt;= $4 AND occurred_at &lt; $5&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[now, invoiceVid, matterUri, periodStart, '
                 'periodEnd]" target="params"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_M</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_MarkBilled" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4173,
                 '00-contracts/bpmn/ai/gftd/lawfirm/issueInvoice.bpmn',
                 '2026-04-27T23:02:00Z',
                 'did:web:lawfirm.gftd.ai',
                 'did:web:lawfirm.gftd.ai',
                 'sys.bpmn.seed.lawfirm',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-issue-invoice-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-runConflictCheck-v1',
                 'did:web:lawfirm.gftd.ai',
                 'ai.gftd.apps.lawfirm.runConflictCheck',
                 'lawfirm_run_conflict_check',
                 60000,
                 '2026-04-27T23:02:00Z',
                 'did:web:lawfirm.gftd.ai',
                 'did:web:lawfirm.gftd.ai',
                 'sys.bpmn.seed.lawfirm',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-runConflictCheck-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-submitFiling-v1',
                 'did:web:lawfirm.gftd.ai',
                 'ai.gftd.apps.lawfirm.submitFiling',
                 'lawfirm_submit_filing',
                 60000,
                 '2026-04-27T23:02:00Z',
                 'did:web:lawfirm.gftd.ai',
                 'did:web:lawfirm.gftd.ai',
                 'sys.bpmn.seed.lawfirm',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-submitFiling-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-issueInvoice-v1',
                 'did:web:lawfirm.gftd.ai',
                 'ai.gftd.apps.lawfirm.issueInvoice',
                 'lawfirm_issue_invoice',
                 60000,
                 '2026-04-27T23:02:00Z',
                 'did:web:lawfirm.gftd.ai',
                 'did:web:lawfirm.gftd.ai',
                 'sys.bpmn.seed.lawfirm',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-issueInvoice-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-runConflictCheck-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-submitFiling-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-issueInvoice-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-run-conflict-check-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-submit-filing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-issue-invoice-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
