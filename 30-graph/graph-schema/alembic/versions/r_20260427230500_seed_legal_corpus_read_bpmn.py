"""Captured from Kysely migration 20260427230500_seed_legal_corpus_read_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427230500_seed_legal_corpus_read_bpmn"
down_revision = 'r_20260427230400_seed_legal_logical_actors_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-search-document-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_search_document',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_search_document" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="2.0">\n'
                 '  <bpmn:process id="legal_corpus_search_document" name="searchDocument" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <!-- Manual trigger (for ad-hoc testing) -->\n'
                 '    <bpmn:startEvent id="Start_Manual" name="Manual">\n'
                 '      <bpmn:outgoing>Flow_M</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_M" sourceRef="Start_Manual" '
                 'targetRef="Task_Search"/>\n'
                 '\n'
                 '    <!-- Single-step: embed query + cosine search in the worker (avoids\n'
                 '         ::vector parameterization issues in RisingWave generic.db.select) -->\n'
                 '    <bpmn:serviceTask id="Task_Search" name="embed + cosine search">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="legal.corpus.searchDocument" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=queryText"     target="queryText"/>\n'
                 '          <zeebe:input source="=jurisdiction"  target="jurisdiction"/>\n'
                 '          <zeebe:input source="=documentType"  target="documentType"/>\n'
                 '          <zeebe:input source="=languageCode"  target="languageCode"/>\n'
                 '          <zeebe:input source="=decidedAfter"  target="decidedAfter"/>\n'
                 '          <zeebe:input source="=decidedBefore" target="decidedBefore"/>\n'
                 '          <zeebe:input source="=if limit = null then 10 else limit" '
                 'target="limit"/>\n'
                 '          <zeebe:output source="=hits"         target="hits"/>\n'
                 '          <zeebe:output source="=hitCount"     target="hitCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_M</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Search" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2030,
                 '00-contracts/bpmn/ai/gftd/legal-corpus/searchDocument.bpmn',
                 '2026-04-27T23:05:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus-read',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-search-document-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-get-document-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_get_document',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_get_document" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_corpus_get_document" name="getDocument" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Select"/>\n'
                 '    <bpmn:serviceTask id="Task_Select" name="select document">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id, source_id, '
                 'canonical_uri, document_type, jurisdiction, court, language_code, title, '
                 'citation, decided_at, published_at, fetched_at, body_text, body_uri, '
                 'topic_tags_csv AS topic_tags, embedding_dim FROM vertex_legal_corpus_document '
                 'WHERE ($1::varchar IS NOT NULL AND vertex_id = $1) OR ($2::varchar IS NOT NULL '
                 'AND canonical_uri = $2) LIMIT 1&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[vertexId, canonicalUri]" target="params"/>\n'
                 '          <zeebe:output source="=rows[1]" target="document"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Select" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1665,
                 '00-contracts/bpmn/ai/gftd/legal-corpus/getDocument.bpmn',
                 '2026-04-27T23:05:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus-read',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-get-document-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-list-jurisdictions-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'legal_corpus_list_jurisdictions',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_legal_corpus_list_jurisdictions" '
                 'targetNamespace="https://etzhayyim.com/bpmn/legal-corpus" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="legal_corpus_list_jurisdictions" name="listJurisdictions" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Select"/>\n'
                 '    <bpmn:serviceTask id="Task_Select" name="select coverage mv">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.select" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT jurisdiction, source_id, '
                 'document_count, last_fetched_at FROM mv_legal_corpus_jurisdiction_coverage WHERE '
                 '($1::varchar IS NULL OR source_id = $1) ORDER BY document_count DESC&quot;" '
                 'target="sql"/>\n'
                 '          <zeebe:input source="=[sourceId]" target="params"/>\n'
                 '          <zeebe:output source="=rows" target="jurisdictions"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Select" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1496,
                 '00-contracts/bpmn/ai/gftd/legal-corpus/listJurisdictions.bpmn',
                 '2026-04-27T23:05:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus-read',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-list-jurisdictions-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/legal-corpus-searchDocument-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'ai.gftd.apps.legal-corpus.searchDocument',
                 'legal_corpus_search_document',
                 30000,
                 '2026-04-27T23:05:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus-read',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/legal-corpus-searchDocument-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/legal-corpus-getDocument-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'ai.gftd.apps.legal-corpus.getDocument',
                 'legal_corpus_get_document',
                 10000,
                 '2026-04-27T23:05:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus-read',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/legal-corpus-getDocument-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/legal-corpus-listJurisdictions-v1',
                 'did:web:legal-corpus.etzhayyim.com',
                 'ai.gftd.apps.legal-corpus.listJurisdictions',
                 'legal_corpus_list_jurisdictions',
                 10000,
                 '2026-04-27T23:05:00Z',
                 'did:web:legal-corpus.etzhayyim.com',
                 'did:web:legal-corpus.etzhayyim.com',
                 'sys.bpmn.seed.legal-corpus-read',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/legal-corpus-listJurisdictions-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/legal-corpus-searchDocument-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/legal-corpus-getDocument-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/legal-corpus-listJurisdictions-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-search-document-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-get-document-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/legal-corpus-list-jurisdictions-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
