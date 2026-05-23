"""Captured from Kysely migration 20260428290000_seed_legal_corpus_body_embed_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428290000_seed_legal_corpus_body_embed_bpmn"
down_revision = 'r_20260428285000_seed_open_smartphone_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-fetchAndEmbed-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_fetch_and_embed',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_fetch_and_embed" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="2.0">\n'
                 '  <bpmn:process id="legal_corpus_fetch_and_embed" name="fetchAndEmbed" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" '
                 'name="start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" '
                 'targetRef="Task_FetchBody"/>\n'
                 '    <bpmn:serviceTask id="Task_FetchBody" name="fetch body text">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legal.corpus.fetchBodyText" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=canonicalUri" target="canonicalUri"/>\n'
                 '          <zeebe:input source="=sourceId" target="sourceId"/>\n'
                 '          <zeebe:output source="=bodyText" target="bodyText"/>\n'
                 '          <zeebe:output source="=chars" target="bodyChars"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_W</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_W" sourceRef="Task_FetchBody" '
                 'targetRef="Task_WriteBody"/>\n'
                 '    <bpmn:serviceTask id="Task_WriteBody" name="write body_text to DB">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;UPDATE vertex_legal_corpus_document SET '
                 'body_text = $1 WHERE vertex_id = $2&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[bodyText, vertexId]" target="params"/>\n'
                 '          <zeebe:output source="=updated" target="bodyUpdated"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_W</bpmn:incoming><bpmn:outgoing>Flow_E</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_E" sourceRef="Task_WriteBody" '
                 'targetRef="Task_Embed"/>\n'
                 '    <bpmn:serviceTask id="Task_Embed" name="embed text">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="legal.corpus.embedText" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=bodyText" target="text"/>\n'
                 '          <zeebe:output source="=embedding" target="embedding"/>\n'
                 '          <zeebe:output source="=dim" target="embeddingDim"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_E</bpmn:incoming><bpmn:outgoing>Flow_U</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_U" sourceRef="Task_Embed" '
                 'targetRef="Task_UpdateEmbed"/>\n'
                 '    <bpmn:serviceTask id="Task_UpdateEmbed" name="write embedding to DB">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;UPDATE vertex_legal_corpus_document SET '
                 'embedding_vec = $1::vector(1024), embedding_dim = $2, embedding_model = '
                 '\'BAAI/bge-m3\', embedding_at = now() WHERE vertex_id = $3&quot;" '
                 'target="sql"/>\n'
                 '          <zeebe:input source="=[embedding, embeddingDim, vertexId]" '
                 'target="params"/>\n'
                 '          <zeebe:output source="=updated" target="embedUpdated"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_U</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_UpdateEmbed" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3562,
                 '00-contracts/bpmn/ai/gftd/legal-corpus/fetchAndEmbed.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus-embed',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-fetchAndEmbed-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-backfillBodyText-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_backfill_body_text',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_backfill_body_text" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="2.0">\n'
                 '  <bpmn:process id="legal_corpus_backfill_body_text" name="backfillBodyText" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start_Manual" '
                 'name="manual"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start_Manual" '
                 'targetRef="Task_FindDocs"/>\n'
                 '    <bpmn:serviceTask id="Task_FindDocs" name="find docs without body_text">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id, canonical_uri, source_id '
                 'FROM vertex_legal_corpus_document WHERE body_text IS NULL AND canonical_uri IS '
                 'NOT NULL LIMIT $1&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[batchSize]" target="params"/>\n'
                 '          <zeebe:output source="=rows" target="docs"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_L</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_L" sourceRef="Task_FindDocs" '
                 'targetRef="Task_Loop"/>\n'
                 '    <bpmn:callActivity id="Task_Loop" name="fetch+embed each doc" '
                 'calledElement="legal_corpus_fetch_and_embed">\n'
                 '      <bpmn:extensionElements><zeebe:calledElement '
                 'processId="legal_corpus_fetch_and_embed"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=doc.vertex_id" target="vertexId"/>\n'
                 '          <zeebe:input source="=doc.canonical_uri" target="canonicalUri"/>\n'
                 '          <zeebe:input source="=doc.source_id" target="sourceId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_L</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '      <bpmn:multiInstanceLoopCharacteristics isSequential="true">\n'
                 '        <bpmn:extensionElements><zeebe:loopCharacteristics '
                 'inputCollection="=docs" inputElement="doc"/></bpmn:extensionElements>\n'
                 '      </bpmn:multiInstanceLoopCharacteristics>\n'
                 '    </bpmn:callActivity>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Loop" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2417,
                 '00-contracts/bpmn/ai/gftd/legal-corpus/backfillBodyText.bpmn',
                 '2026-04-28T23:50:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus-embed',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-backfillBodyText-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-fetchAndEmbed-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-backfillBodyText-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
