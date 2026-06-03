"""Captured from Kysely migration 20260427230100_seed_legal_corpus_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427230100_seed_legal_corpus_bpmn_actors"
down_revision = 'r_20260427230000_vertex_telecom_li'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-ingest-document-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_ingest_document',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_ingest_document" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_corpus_ingest_document" name="ingestDocument" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Dedupe"/>\n'
                 '    <bpmn:serviceTask id="Task_Dedupe" name="dedupe by canonical uri">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id FROM '
                 'vertex_legal_corpus_document WHERE source_id = $1 AND canonical_uri = $2 LIMIT '
                 '1&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[sourceId, canonicalUri]" target="params"/>\n'
                 '          <zeebe:output source="=rows" target="dedupeRows"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_I</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_I" sourceRef="Task_Dedupe" '
                 'targetRef="Task_Insert"/>\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="insert document">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_legal_corpus_document&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:legal-corpus.etzhayyim.com/com.etzhayyim.apps.legal-corpus.document/&quot; '
                 '+ sourceId + &quot;:&quot; + canonicalUri, source_id: sourceId, canonical_uri: '
                 'canonicalUri, document_type: documentType, jurisdiction: jurisdiction, court: '
                 'court, court_did: courtDid, language_code: languageCode, title: title, citation: '
                 'citation, decided_at: decidedAt, published_at: publishedAt, fetched_at: '
                 'fetchedAt, body_text: bodyText, body_uri: bodyUri, topic_tags_csv: topicTags, '
                 'sensitivity_ord: sensitivityOrd, owner_did: '
                 '&quot;did:web:legal-corpus.etzhayyim.com&quot;, created_at: fetchedAt}" '
                 'target="row"/>\n'
                 '          <zeebe:input source="=&quot;skip&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=vertex_id" target="vertexId"/>\n'
                 '          <zeebe:output source="=already_known" target="alreadyKnown"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_I</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Insert" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:legal-corpus.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;legal-corpus.ingestDocument&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, sourceId: sourceId, canonicalUri: canonicalUri, '
                 'alreadyKnown: alreadyKnown}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3485,
                 '00-contracts/bpmn/com/etzhayyim/legal-corpus/ingestDocument.bpmn',
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-ingest-document-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-embed-document-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_embed_document',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_embed_document" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="2.0">\n'
                 '  <bpmn:process id="legal_corpus_embed_document" name="embedDocument" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Load"/>\n'
                 '    <bpmn:serviceTask id="Task_Load" name="load doc body">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id, body_text FROM '
                 'vertex_legal_corpus_document WHERE vertex_id = $1 LIMIT 1&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[vertexId]" target="params"/>\n'
                 '          <zeebe:output source="=rows[1]" target="doc"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_E</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_E" sourceRef="Task_Load" '
                 'targetRef="Task_Embed"/>\n'
                 '    <bpmn:serviceTask id="Task_Embed" name="bge-m3 embed (local CPU)">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legal.corpus.embedText" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=doc.body_text" target="text"/>\n'
                 '          <zeebe:output source="=embedding" target="embedding"/>\n'
                 '          <zeebe:output source="=dim" target="embeddingDim"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_E</bpmn:incoming><bpmn:outgoing>Flow_U</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_U" sourceRef="Task_Embed" '
                 'targetRef="Task_Update"/>\n'
                 '    <bpmn:serviceTask id="Task_Update" name="write embedding">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;UPDATE vertex_legal_corpus_document SET '
                 'embedding_vec = $1::vector(1024), embedding_dim = $2, embedding_model = '
                 '\'BAAI/bge-m3\', embedding_at = now() WHERE vertex_id = $3&quot;" '
                 'target="sql"/>\n'
                 '          <zeebe:input source="=[embedding, embeddingDim, vertexId]" '
                 'target="params"/>\n'
                 '          <zeebe:output source="=updated" target="updated"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_U</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Update" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2811,
                 '00-contracts/bpmn/com/etzhayyim/legal-corpus/embedDocument.bpmn',
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-embed-document-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-register-source-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_register_source',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_register_source" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_corpus_register_source" name="registerSource" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Insert"/>\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="upsert source row">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_legal_corpus_source&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:legal-corpus.etzhayyim.com/com.etzhayyim.apps.legal-corpus.source/&quot; '
                 '+ sourceId, source_id: sourceId, display_name: displayName, base_url: baseUrl, '
                 'jurisdictions_csv: jurisdictions, cadence_iso8601: cadenceIso8601, '
                 'auth_strategy: authStrategy, secret_ref: secretRef, license: license, status: '
                 '&quot;active&quot;, sensitivity_ord: 1, owner_did: '
                 '&quot;did:web:legal-corpus.etzhayyim.com&quot;, created_at: now}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=vertex_id" target="vertexId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Insert" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1822,
                 '00-contracts/bpmn/com/etzhayyim/legal-corpus/registerSource.bpmn',
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-register-source-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-court-listener-delta-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_fetch_courtlistener_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_fetch_courtlistener_delta" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_corpus_fetch_courtlistener_delta" '
                 'name="fetchCourtListenerDelta" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="every 24h">\n'
                 '      <bpmn:outgoing>Flow_C</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT24H</bpmn:timeCycle></bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" '
                 'name="manual"><bpmn:outgoing>Flow_CM</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_CM" sourceRef="Start_Manual" '
                 'targetRef="Task_Cursor"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_C" sourceRef="Start" targetRef="Task_Cursor"/>\n'
                 '    <bpmn:serviceTask id="Task_Cursor" name="load cursor">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT last_cursor, secret_ref FROM '
                 'vertex_legal_corpus_source WHERE source_id = \'courtlistener\' LIMIT 1&quot;" '
                 'target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=rows[1].last_cursor" target="cursor"/>\n'
                 '          <zeebe:output source="=rows[1].secret_ref" target="secretRef"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_C</bpmn:incoming><bpmn:outgoing>Flow_F</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_F" sourceRef="Task_Cursor" '
                 'targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch opinions delta">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.http.fetch" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;GET&quot;" target="method"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://www.courtlistener.com/api/rest/v3/opinions/?date_modified__gt=&quot; '
                 '+ (if cursor != null then cursor else &quot;1970-01-01&quot;) + '
                 '&quot;&amp;order_by=date_modified&amp;page_size=100&quot;" target="url"/>\n'
                 '          <zeebe:input source="={Authorization: &quot;Token &quot; + secretRef}" '
                 'target="headers"/>\n'
                 '          <zeebe:output source="=bodyJson.results" target="items"/>\n'
                 '          <zeebe:output source="=bodyJson.next" target="nextCursor"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_F</bpmn:incoming><bpmn:outgoing>Flow_L</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_L" sourceRef="Task_Fetch" '
                 'targetRef="Task_Loop"/>\n'
                 '    <bpmn:callActivity id="Task_Loop" name="ingest each opinion" '
                 'calledElement="legal_corpus_ingest_document">\n'
                 '      <bpmn:extensionElements><zeebe:calledElement '
                 'processId="legal_corpus_ingest_document"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;courtlistener&quot;" target="sourceId"/>\n'
                 '          <zeebe:input source="=item.absolute_url" target="canonicalUri"/>\n'
                 '          <zeebe:input source="=&quot;opinion&quot;" target="documentType"/>\n'
                 '          <zeebe:input source="=&quot;USA&quot;" target="jurisdiction"/>\n'
                 '          <zeebe:input source="=item.cluster.docket.court_id" target="court"/>\n'
                 '          <zeebe:input source="=&quot;en&quot;" target="languageCode"/>\n'
                 '          <zeebe:input source="=item.cluster.case_name" target="title"/>\n'
                 '          <zeebe:input source="=item.cluster.citation_string" '
                 'target="citation"/>\n'
                 '          <zeebe:input source="=item.date_filed" target="decidedAt"/>\n'
                 '          <zeebe:input source="=item.date_modified" target="publishedAt"/>\n'
                 '          <zeebe:input source="=now" target="fetchedAt"/>\n'
                 '          <zeebe:input source="=item.plain_text" target="bodyText"/>\n'
                 '          <zeebe:input source="=1" target="sensitivityOrd"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_L</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '      <bpmn:multiInstanceLoopCharacteristics isSequential="false">\n'
                 '        <bpmn:extensionElements><zeebe:loopCharacteristics '
                 'inputCollection="=items" inputElement="item"/></bpmn:extensionElements>\n'
                 '      </bpmn:multiInstanceLoopCharacteristics>\n'
                 '    </bpmn:callActivity>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Loop" '
                 'targetRef="Task_Advance"/>\n'
                 '    <bpmn:serviceTask id="Task_Advance" name="advance cursor">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;UPDATE vertex_legal_corpus_source SET '
                 'last_cursor = $1, last_fetched_at = $2 WHERE source_id = '
                 '\'courtlistener\'&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[nextCursor, now]" target="params"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Advance" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5248,
                 '00-contracts/bpmn/com/etzhayyim/legal-corpus/fetchCourtListenerDelta.bpmn',
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-court-listener-delta-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-eur-lex-delta-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_fetch_eur_lex_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_fetch_eur_lex_delta" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="2.0">\n'
                 '  <bpmn:process id="legal_corpus_fetch_eur_lex_delta" name="fetchEurLexDelta" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 24h">\n'
                 '      <bpmn:outgoing>Flow_F</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT24H</bpmn:timeCycle></bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" '
                 'name="manual"><bpmn:outgoing>Flow_FM</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_F" sourceRef="Start_Timer" '
                 'targetRef="Task_Fetch"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_FM" sourceRef="Start_Manual" '
                 'targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="SPARQL: recent EN directives+regs">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.http.fetch" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;POST&quot;" target="method"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://publications.europa.eu/webapi/rdf/sparql&quot;" '
                 'target="url"/>\n'
                 '          <zeebe:input source="={&quot;Content-Type&quot;: '
                 '&quot;application/sparql-query&quot;, &quot;Accept&quot;: '
                 '&quot;application/sparql-results+json&quot;, &quot;User-Agent&quot;: '
                 '&quot;etzhayyim-legal-corpus/1.0&quot;}" target="headers"/>\n'
                 '          <zeebe:input source="=&quot;PREFIX cdm: '
                 '&lt;http://publications.europa.eu/ontology/cdm#&gt; SELECT DISTINCT ?work ?title '
                 '?date WHERE { ?work cdm:work_has_resource-type ?rtype ; cdm:work_date_document '
                 '?date . ?expr cdm:expression_belongs_to_work ?work ; '
                 'cdm:expression_uses_language '
                 '&lt;http://publications.europa.eu/resource/authority/language/ENG&gt; ; '
                 'cdm:expression_title ?title . VALUES ?rtype { '
                 '&lt;http://publications.europa.eu/resource/authority/resource-type/DIR&gt; '
                 '&lt;http://publications.europa.eu/resource/authority/resource-type/REG&gt; '
                 '&lt;http://publications.europa.eu/resource/authority/resource-type/DEC_IMPL&gt; '
                 '} FILTER(str(?date) &gt;= str(sinceDate)) } ORDER BY DESC(?date) LIMIT 50&quot;" '
                 'target="body"/>\n'
                 '          <zeebe:output source="=response.results.bindings" target="items"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_F</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_FM</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_L</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_L" sourceRef="Task_Fetch" '
                 'targetRef="Task_Loop"/>\n'
                 '    <bpmn:callActivity id="Task_Loop" name="ingest each document" '
                 'calledElement="legal_corpus_ingest_document">\n'
                 '      <bpmn:extensionElements><zeebe:calledElement '
                 'processId="legal_corpus_ingest_document"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;eur-lex&quot;" target="sourceId"/>\n'
                 '          <zeebe:input source="=item.work.value" target="canonicalUri"/>\n'
                 '          <zeebe:input source="=&quot;regulation&quot;" target="documentType"/>\n'
                 '          <zeebe:input source="=&quot;EU&quot;" target="jurisdiction"/>\n'
                 '          <zeebe:input source="=item.title.value" target="title"/>\n'
                 '          <zeebe:input source="=&quot;eng&quot;" target="languageCode"/>\n'
                 '          <zeebe:input source="=item.date.value" target="decidedAt"/>\n'
                 '          <zeebe:input source="=now" target="fetchedAt"/>\n'
                 '          <zeebe:input source="=3" target="sensitivityOrd"/>\n'
                 '          <zeebe:input source="=null" target="court"/>\n'
                 '          <zeebe:input source="=null" target="courtDid"/>\n'
                 '          <zeebe:input source="=null" target="citation"/>\n'
                 '          <zeebe:input source="=null" target="publishedAt"/>\n'
                 '          <zeebe:input source="=null" target="bodyText"/>\n'
                 '          <zeebe:input source="=null" target="bodyUri"/>\n'
                 '          <zeebe:input source="=null" target="topicTags"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_L</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '      <bpmn:multiInstanceLoopCharacteristics isSequential="true">\n'
                 '        <bpmn:extensionElements><zeebe:loopCharacteristics '
                 'inputCollection="=items" inputElement="item"/></bpmn:extensionElements>\n'
                 '      </bpmn:multiInstanceLoopCharacteristics>\n'
                 '    </bpmn:callActivity>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Loop" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4608,
                 '00-contracts/bpmn/com/etzhayyim/legal-corpus/fetchEurLexDelta.bpmn',
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-eur-lex-delta-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-bailii-delta-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_fetch_bailii_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_fetch_bailii_delta" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_corpus_fetch_bailii_delta" name="fetchBailiiDelta" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="every '
                 '24h"><bpmn:outgoing>Flow_F</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT24H</bpmn:timeCycle></bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" '
                 'name="manual"><bpmn:outgoing>Flow_FM</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_FM" sourceRef="Start_Manual" '
                 'targetRef="Task_Fetch"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_F" sourceRef="Start" targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="atom feed">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.http.fetch" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;GET&quot;" target="method"/>\n'
                 '          <zeebe:input source="=&quot;https://www.bailii.org/atom.xml&quot;" '
                 'target="url"/>\n'
                 '          <zeebe:input source="=&quot;atom&quot;" target="parse"/>\n'
                 '          <zeebe:input source="={&quot;Accept&quot;: &quot;application/atom+xml, '
                 'application/xml;q=0.9, */*;q=0.8&quot;, &quot;Accept-Language&quot;: '
                 '&quot;en-GB,en;q=0.9&quot;, &quot;Accept-Encoding&quot;: &quot;gzip, deflate, '
                 'br&quot;}" target="headers"/>\n'
                 '          <zeebe:output source="=entries" target="items"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_F</bpmn:incoming><bpmn:outgoing>Flow_L</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_L" sourceRef="Task_Fetch" '
                 'targetRef="Task_Loop"/>\n'
                 '    <bpmn:callActivity id="Task_Loop" name="ingest each entry" '
                 'calledElement="legal_corpus_ingest_document">\n'
                 '      <bpmn:extensionElements><zeebe:calledElement '
                 'processId="legal_corpus_ingest_document"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;bailii&quot;" target="sourceId"/>\n'
                 '          <zeebe:input source="=item.link" target="canonicalUri"/>\n'
                 '          <zeebe:input source="=&quot;opinion&quot;" target="documentType"/>\n'
                 '          <zeebe:input source="=if contains(item.link, &quot;/uk/&quot;) then '
                 '&quot;GBR&quot; else (if contains(item.link, &quot;/ie/&quot;) then '
                 '&quot;IRL&quot; else &quot;GBR&quot;)" target="jurisdiction"/>\n'
                 '          <zeebe:input source="=&quot;en&quot;" target="languageCode"/>\n'
                 '          <zeebe:input source="=item.title" target="title"/>\n'
                 '          <zeebe:input source="=item.published" target="decidedAt"/>\n'
                 '          <zeebe:input source="=now" target="fetchedAt"/>\n'
                 '          <zeebe:input source="=1" target="sensitivityOrd"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_L</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '      <bpmn:multiInstanceLoopCharacteristics '
                 'isSequential="false"><bpmn:extensionElements><zeebe:loopCharacteristics '
                 'inputCollection="=items" '
                 'inputElement="item"/></bpmn:extensionElements></bpmn:multiInstanceLoopCharacteristics>\n'
                 '    </bpmn:callActivity>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Loop" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3517,
                 '00-contracts/bpmn/com/etzhayyim/legal-corpus/fetchBailiiDelta.bpmn',
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-bailii-delta-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-world-lii-delta-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_fetch_worldlii_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_fetch_worldlii_delta" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_corpus_fetch_worldlii_delta" name="fetchWorldLiiDelta" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="every '
                 '7d"><bpmn:outgoing>Flow_F</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/P7D</bpmn:timeCycle></bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" '
                 'name="manual"><bpmn:outgoing>Flow_FM</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_FM" sourceRef="Start_Manual" '
                 'targetRef="Task_Fetch"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_F" sourceRef="Start" targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="oai-pmh listrecords">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.http.fetch" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;GET&quot;" target="method"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://www.worldlii.org/cgi-bin/oai.pl?verb=ListRecords&amp;metadataPrefix=oai_dc&amp;from=&quot; '
                 '+ (now - duration(&quot;P7D&quot;))" target="url"/>\n'
                 '          <zeebe:input source="=&quot;oai-pmh&quot;" target="parse"/>\n'
                 '          <zeebe:output source="=records" target="items"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_F</bpmn:incoming><bpmn:outgoing>Flow_L</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_L" sourceRef="Task_Fetch" '
                 'targetRef="Task_Loop"/>\n'
                 '    <bpmn:callActivity id="Task_Loop" name="ingest each record" '
                 'calledElement="legal_corpus_ingest_document">\n'
                 '      <bpmn:extensionElements><zeebe:calledElement '
                 'processId="legal_corpus_ingest_document"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;worldlii&quot;" target="sourceId"/>\n'
                 '          <zeebe:input source="=item.link" target="canonicalUri"/>\n'
                 '          <zeebe:input source="=&quot;opinion&quot;" target="documentType"/>\n'
                 '          <zeebe:input source="=null" target="jurisdiction"/>\n'
                 '          <zeebe:input source="=&quot;en&quot;" target="languageCode"/>\n'
                 '          <zeebe:input source="=item.title" target="title"/>\n'
                 '          <zeebe:input source="=item.published" target="decidedAt"/>\n'
                 '          <zeebe:input source="=now" target="fetchedAt"/>\n'
                 '          <zeebe:input source="=1" target="sensitivityOrd"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_L</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '      <bpmn:multiInstanceLoopCharacteristics '
                 'isSequential="false"><bpmn:extensionElements><zeebe:loopCharacteristics '
                 'inputCollection="=items" '
                 'inputElement="item"/></bpmn:extensionElements></bpmn:multiInstanceLoopCharacteristics>\n'
                 '    </bpmn:callActivity>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Loop" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3228,
                 '00-contracts/bpmn/com/etzhayyim/legal-corpus/fetchWorldLiiDelta.bpmn',
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-world-lii-delta-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-can-lii-delta-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_fetch_canlii_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_fetch_canlii_delta" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_corpus_fetch_canlii_delta" name="fetchCanLiiDelta" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="every '
                 '24h"><bpmn:outgoing>Flow_F</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition><bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT24H</bpmn:timeCycle></bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" '
                 'name="manual"><bpmn:outgoing>Flow_FM</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_FM" sourceRef="Start_Manual" '
                 'targetRef="Task_Key"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_F" sourceRef="Start" targetRef="Task_Key"/>\n'
                 '    <bpmn:serviceTask id="Task_Key" name="load api key">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT secret_ref FROM '
                 'vertex_legal_corpus_source WHERE source_id = \'canlii\' LIMIT 1&quot;" '
                 'target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=rows[1].secret_ref" target="canliiKey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_F</bpmn:incoming><bpmn:incoming>Flow_FM</bpmn:incoming><bpmn:outgoing>Flow_Fetch</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Fetch" sourceRef="Task_Key" '
                 'targetRef="Task_Fetch"/>\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="canlii v1 cases">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.http.fetch" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;GET&quot;" target="method"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://api.canlii.org/v1/caseBrowse/en/csc-scc/?api_key=&quot; + '
                 'canliiKey + &quot;&amp;decisionDateBegin=&quot; + (now - '
                 'duration(&quot;PT24H&quot;))" target="url"/>\n'
                 '          <zeebe:output source="=bodyJson.cases" target="items"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_L</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_L" sourceRef="Task_Fetch" '
                 'targetRef="Task_Loop"/>\n'
                 '    <bpmn:callActivity id="Task_Loop" name="ingest each scc case" '
                 'calledElement="legal_corpus_ingest_document">\n'
                 '      <bpmn:extensionElements><zeebe:calledElement '
                 'processId="legal_corpus_ingest_document"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;canlii&quot;" target="sourceId"/>\n'
                 '          <zeebe:input source="=&quot;https://www.canlii.org/en/&quot; + '
                 'item.databaseId + &quot;/&quot; + item.caseId.en" target="canonicalUri"/>\n'
                 '          <zeebe:input source="=&quot;opinion&quot;" target="documentType"/>\n'
                 '          <zeebe:input source="=&quot;CAN&quot;" target="jurisdiction"/>\n'
                 '          <zeebe:input source="=&quot;Supreme Court of Canada&quot;" '
                 'target="court"/>\n'
                 '          <zeebe:input source="=item.language" target="languageCode"/>\n'
                 '          <zeebe:input source="=item.title" target="title"/>\n'
                 '          <zeebe:input source="=item.citation" target="citation"/>\n'
                 '          <zeebe:input source="=item.decisionDate" target="decidedAt"/>\n'
                 '          <zeebe:input source="=now" target="fetchedAt"/>\n'
                 '          <zeebe:input source="=1" target="sensitivityOrd"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_L</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '      <bpmn:multiInstanceLoopCharacteristics '
                 'isSequential="false"><bpmn:extensionElements><zeebe:loopCharacteristics '
                 'inputCollection="=items" '
                 'inputElement="item"/></bpmn:extensionElements></bpmn:multiInstanceLoopCharacteristics>\n'
                 '    </bpmn:callActivity>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Loop" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4159,
                 '00-contracts/bpmn/com/etzhayyim/legal-corpus/fetchCanLiiDelta.bpmn',
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-can-lii-delta-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-ingestDocument-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'com.etzhayyim.apps.legal-corpus.ingestDocument',
                 'legal_corpus_ingest_document',
                 30000,
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-ingestDocument-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-embedDocument-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'com.etzhayyim.apps.legal-corpus.embedDocument',
                 'legal_corpus_embed_document',
                 60000,
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-embedDocument-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-registerSource-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'com.etzhayyim.apps.legal-corpus.registerSource',
                 'legal_corpus_register_source',
                 15000,
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-registerSource-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchCourtListenerDelta-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'com.etzhayyim.apps.legal-corpus.fetchCourtListenerDelta',
                 'legal_corpus_fetch_courtlistener_delta',
                 600000,
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchCourtListenerDelta-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchEurLexDelta-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'com.etzhayyim.apps.legal-corpus.fetchEurLexDelta',
                 'legal_corpus_fetch_eur_lex_delta',
                 600000,
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchEurLexDelta-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchBailiiDelta-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'com.etzhayyim.apps.legal-corpus.fetchBailiiDelta',
                 'legal_corpus_fetch_bailii_delta',
                 600000,
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchBailiiDelta-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchWorldLiiDelta-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'com.etzhayyim.apps.legal-corpus.fetchWorldLiiDelta',
                 'legal_corpus_fetch_worldlii_delta',
                 600000,
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchWorldLiiDelta-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchCanLiiDelta-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'com.etzhayyim.apps.legal-corpus.fetchCanLiiDelta',
                 'legal_corpus_fetch_canlii_delta',
                 600000,
                 '2026-04-27T23:01:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchCanLiiDelta-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-ingestDocument-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-embedDocument-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-registerSource-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchCourtListenerDelta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchEurLexDelta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchBailiiDelta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchWorldLiiDelta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/legal-corpus-fetchCanLiiDelta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-ingest-document-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-embed-document-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-register-source-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-court-listener-delta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-eur-lex-delta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-bailii-delta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-world-lii-delta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/legal-corpus-fetch-can-lii-delta-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
