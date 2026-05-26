"""Captured from Kysely migration 20260425102500_seed_patent_bulk_ingest_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425102500_seed_patent_bulk_ingest_bpmn_actors"
down_revision = 'r_20260425102400_vertex_patent_blob'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/patent-ingest-uspto-weekly-v1',
                 'did:web:patent.etzhayyim.com',
                 'patent_ingest_uspto_weekly',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  ADR 2604251024 — patent bulk ingest (USPTO PatentsView weekly TSV).\n'
                 '\n'
                 '  Timer-start (Sun 00:00 UTC). Pulls the PatentsView manifest + granted\n'
                 '  patent TSV + citation TSV and bulk-inserts into vertex_open_patent_patent\n'
                 '  and edge_open_patent_citation_pair. metadata only — PDF / webp are\n'
                 "  handled by patent-blob-convert.bpmn when a blob row with status='pending'\n"
                 '  is produced here for granted filings with filing_date >= 2010-01-01.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_patent_ingest_uspto_weekly"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/patent"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="patent_ingest_uspto_weekly" name="patent ingest USPTO '
                 'weekly" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="weekly">\n'
                 '      <bpmn:outgoing>Flow_Patent</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0 0 ? * '
                 'SUN</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_IngestPatent" name="ingest g_patent.tsv">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="patent.usptoPatentsview.ingestPatent"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://s3.amazonaws.com/data.patentsview.org/download/g_patent.tsv.zip&quot;" '
                 'target="tsvUrl"/>\n'
                 '          <zeebe:input source="=2000" target="batchSize"/>\n'
                 '          <zeebe:input source="=&quot;vertex_open_patent_patent&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="=&quot;2010-01-01&quot;" '
                 'target="blobThresholdDate"/>\n'
                 '          <zeebe:input source="=&quot;vertex_patent_blob&quot;" '
                 'target="blobTable"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Patent</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Citation</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Patent" sourceRef="StartTimer" '
                 'targetRef="Task_IngestPatent"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Citation" sourceRef="Task_IngestPatent" '
                 'targetRef="Task_IngestCitation"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_IngestCitation" name="ingest '
                 'g_us_patent_citation.tsv">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="patent.usptoPatentsview.ingestCitation"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://s3.amazonaws.com/data.patentsview.org/download/g_us_patent_citation.tsv.zip&quot;" '
                 'target="tsvUrl"/>\n'
                 '          <zeebe:input source="=2000" target="batchSize"/>\n'
                 '          <zeebe:input source="=&quot;vertex_open_patent_citation&quot;" '
                 'target="vertexTable"/>\n'
                 '          <zeebe:input source="=&quot;edge_open_patent_citation_pair&quot;" '
                 'target="edgeTable"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Citation</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_IngestCitation" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:patent.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;patent.ingest.uspto.weekly&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={\n'
                 '              patentRows:   ingest.result.rows,\n'
                 '              citationRows: citation.result.rows,\n'
                 '              blobQueued:   ingest.result.blobQueued\n'
                 '          }" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4122,
                 '00-contracts/bpmn/ai/gftd/patent/ingestUsptoWeekly.bpmn',
                 '2026-04-25T10:24:00Z',
                 'did:web:patent.etzhayyim.com',
                 'did:web:patent.etzhayyim.com',
                 'sys.bpmn.seed.patent-bulk-ingest',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/patent-ingest-uspto-weekly-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/patent-ingest-epo-citation-fill-v1',
                 'did:web:patent.etzhayyim.com',
                 'patent_ingest_epo_citation_fill',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  ADR 2604251024 — EPO OPS REST citation / family fill.\n'
                 '\n'
                 '  Timer-start every 6h. For the next 1000 US patents whose citations have\n'
                 '  not yet been enriched with EPO cross-jurisdiction links, fetch OPS\n'
                 '  biblio + citation list and insert additional edges into\n'
                 '  edge_open_patent_citation_pair and edge_family_member.\n'
                 '\n'
                 '  OPS free tier = 4 GB/week — batch size tuned so a single 6h sweep\n'
                 '  stays under ~600 MB.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_patent_ingest_epo_citation_fill"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/patent"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="patent_ingest_epo_citation_fill" name="patent EPO OPS '
                 'citation fill" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="every 6h">\n'
                 '      <bpmn:outgoing>Flow_Pending</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0 0/6 * * '
                 '?</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Pending" sourceRef="StartTimer" '
                 'targetRef="Task_Pending"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Pending" name="list patents missing EPO '
                 'citations">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_patent_patent&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="=&quot;vertex_id, patent_number, '
                 'jurisdiction&quot;" target="columns"/>\n'
                 '          <zeebe:input source="={jurisdiction: &quot;US&quot;, status: '
                 '&quot;granted&quot;}" target="where"/>\n'
                 '          <zeebe:input source="=1000" target="limit"/>\n'
                 '          <zeebe:input source="=&quot;pending&quot;" target="resultKey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Pending</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Fill</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Fill" sourceRef="Task_Pending" '
                 'targetRef="Task_Fill"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Fill" name="fetch OPS + fan out citations">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="patent.epoOps.fillCitations"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=pending" target="rows"/>\n'
                 '          <zeebe:input source="=100" target="rateLimitPerMin"/>\n'
                 '          <zeebe:input source="=&quot;edge_open_patent_citation_pair&quot;" '
                 'target="citationEdgeTable"/>\n'
                 '          <zeebe:input source="=&quot;edge_family_member&quot;" '
                 'target="familyEdgeTable"/>\n'
                 '          <zeebe:input source="=&quot;fill.result&quot;" target="resultKey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Fill</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Fill" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:patent.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;patent.ingest.epo.citationFill&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={\n'
                 '              examined:       count(pending),\n'
                 '              citationEdges:  fill.result.citationEdges,\n'
                 '              familyEdges:    fill.result.familyEdges,\n'
                 '              quotaUsedBytes: fill.result.quotaUsedBytes\n'
                 '          }" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4079,
                 '00-contracts/bpmn/ai/gftd/patent/ingestEpoCitationFill.bpmn',
                 '2026-04-25T10:24:00Z',
                 'did:web:patent.etzhayyim.com',
                 'did:web:patent.etzhayyim.com',
                 'sys.bpmn.seed.patent-bulk-ingest',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/patent-ingest-epo-citation-fill-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/patent-blob-convert-v1',
                 'did:web:patent.etzhayyim.com',
                 'patent_blob_convert',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  ADR 2604251024 — patent PDF → webp + OCR text → B2 with CID persistence.\n'
                 '\n'
                 '  Timer-start every 5 minutes. For the next 100 vertex_patent_blob rows\n'
                 "  in status='pending' ordered by _seq, the patent-blob-converter pod\n"
                 '  (Vultr LAX) performs:\n'
                 '    1. HEAD + GET pdf_source_url\n'
                 '    2. sha256(pdf) → B2 PUT patent-blobs/pdf/{sha256} (dedup)\n'
                 '    3. poppler pdftocairo -png → cwebp -q 80 → CIDv1 → B2 PUT webp/{cid}\n'
                 '    4. pdftotext → CIDv1 → B2 PUT text/{cid}\n'
                 '    5. UPDATE vertex_patent_blob SET pdf_sha256, webp_cid, ocr_text_cid,\n'
                 "       status='ocr_done'\n"
                 '\n'
                 '  All of (1)..(5) happen inside the patent.blob.convert primitive\n'
                 "  (implemented by the pod's pyzeebe worker). The BPMN process exists so\n"
                 '  the operation is observable in Zeebe / Operate and consumes the same\n'
                 '  audit surface as the rest of ADR-0056 BPMN-as-actor work.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_patent_blob_convert"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/patent"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="patent_blob_convert" name="patent PDF→webp B2 persistence" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="every 5 min">\n'
                 '      <bpmn:outgoing>Flow_Pending</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0/5 * * * '
                 '?</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Pending" sourceRef="StartTimer" '
                 'targetRef="Task_Pending"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Pending" name="pending blob rows">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_patent_blob&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="=&quot;vertex_id, patent_number, jurisdiction, '
                 'pdf_source_url&quot;" target="columns"/>\n'
                 '          <zeebe:input source="={status: &quot;pending&quot;}" target="where"/>\n'
                 '          <zeebe:input source="=&quot;_seq ASC&quot;" target="orderBy"/>\n'
                 '          <zeebe:input source="=100" target="limit"/>\n'
                 '          <zeebe:input source="=&quot;pending&quot;" target="resultKey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Pending</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Convert</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Convert" sourceRef="Task_Pending" '
                 'targetRef="Task_Convert"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Convert" name="convert PDF → webp + OCR (pod)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="patent.blob.convert" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=pending" target="rows"/>\n'
                 '          <zeebe:input source="=&quot;patent-blobs&quot;" target="b2Bucket"/>\n'
                 '          <zeebe:input source="=&quot;s3.us-west-004.backblazeb2.com&quot;" '
                 'target="b2Endpoint"/>\n'
                 '          <zeebe:input source="=&quot;pdf/&quot;" target="b2PdfPrefix"/>\n'
                 '          <zeebe:input source="=&quot;webp/&quot;" target="b2WebpPrefix"/>\n'
                 '          <zeebe:input source="=&quot;text/&quot;" target="b2TextPrefix"/>\n'
                 '          <zeebe:input source="=80" target="webpQuality"/>\n'
                 '          <zeebe:input source="=&quot;convert.result&quot;" '
                 'target="resultKey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Convert</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Convert" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:patent.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;patent.blob.convert&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={\n'
                 '              attempted: count(pending),\n'
                 '              converted: convert.result.converted,\n'
                 '              dedupHit:  convert.result.dedupHit,\n'
                 '              failed:    convert.result.failed,\n'
                 '              bytesPdf:  convert.result.bytesPdf,\n'
                 '              bytesWebp: convert.result.bytesWebp\n'
                 '          }" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4815,
                 '00-contracts/bpmn/ai/gftd/patent/patentBlobConvert.bpmn',
                 '2026-04-25T10:24:00Z',
                 'did:web:patent.etzhayyim.com',
                 'did:web:patent.etzhayyim.com',
                 'sys.bpmn.seed.patent-bulk-ingest',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/patent-blob-convert-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/patent-ingestUsptoWeekly-v1',
                 'did:web:patent.etzhayyim.com',
                 'app.etzhayyim.apps.patent.ingestUsptoWeekly',
                 'patent_ingest_uspto_weekly',
                 600000,
                 '2026-04-25T10:24:00Z',
                 'did:web:patent.etzhayyim.com',
                 'did:web:patent.etzhayyim.com',
                 'sys.bpmn.seed.patent-bulk-ingest',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/patent-ingestUsptoWeekly-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/patent-ingestEpoCitationFill-v1',
                 'did:web:patent.etzhayyim.com',
                 'app.etzhayyim.apps.patent.ingestEpoCitationFill',
                 'patent_ingest_epo_citation_fill',
                 300000,
                 '2026-04-25T10:24:00Z',
                 'did:web:patent.etzhayyim.com',
                 'did:web:patent.etzhayyim.com',
                 'sys.bpmn.seed.patent-bulk-ingest',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/patent-ingestEpoCitationFill-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/patent-blobConvert-v1',
                 'did:web:patent.etzhayyim.com',
                 'app.etzhayyim.apps.patent.blobConvert',
                 'patent_blob_convert',
                 300000,
                 '2026-04-25T10:24:00Z',
                 'did:web:patent.etzhayyim.com',
                 'did:web:patent.etzhayyim.com',
                 'sys.bpmn.seed.patent-bulk-ingest',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/patent-blobConvert-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/patent-ingestUsptoWeekly-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/patent-ingestEpoCitationFill-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/patent-blobConvert-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/patent-ingest-uspto-weekly-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/patent-ingest-epo-citation-fill-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/patent-blob-convert-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
