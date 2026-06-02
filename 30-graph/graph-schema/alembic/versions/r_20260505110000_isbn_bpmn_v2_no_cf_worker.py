"""Captured from Kysely migration 20260505110000_isbn_bpmn_v2_no_cf_worker."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260505110000_isbn_bpmn_v2_no_cf_worker"
down_revision = 'r_20260505100100_seed_isbn_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/isbn-ingestOpenLibrary-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/isbn-ingestAozora-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/isbn-ingestGutenberg-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/isbn-ingestNdl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/isbn-ingestHathiTrust-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-refresh-daily-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-open-library-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-aozora-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-gutenberg-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-ndl-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-hathitrust-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 2, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-open-library-v2',
                 'did:web:isbn.etzhayyim.com',
                 'isbn_ingest_open_library',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  isbn.etzhayyim.com — Open Library monthly editions dump (autonomous).\n'
                 '\n'
                 '  Timer-start: every month on the 5th @ 00:00 UTC. Open Library\n'
                 '  publishes ol_dump_editions_latest.txt.gz monthly; the 5th gives\n'
                 '  the publishing pipeline buffer. ~10 GiB stream → bulk INSERT\n'
                 '  into vertex_isbn_book + vertex_isbn_publisher.\n'
                 '\n'
                 '  No XRPC entry. No CF Worker. Pure BPMN-as-actor + pyzeebe handler.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_isbn_ingest_open_library"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/isbn"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="isbn_ingest_open_library" name="isbn ingest Open Library '
                 '(monthly)" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="monthly day 5">\n'
                 '      <bpmn:outgoing>Flow_Ingest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0 0 5 * '
                 '?</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="ingest Open Library editions">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="isbn.openLibrary.ingest"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Ingest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Ingest" sourceRef="StartTimer" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:isbn.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;isbn.ingest.openLibrary&quot;" '
                 'target="action"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Ingest" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2409,
                 '00-contracts/bpmn/com/etzhayyim/isbn/ingestOpenLibrary.bpmn',
                 '2026-05-05T11:00:00Z',
                 'did:web:isbn.etzhayyim.com',
                 'did:web:isbn.etzhayyim.com',
                 'sys.bpmn.seed.isbn-no-cf-worker',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-open-library-v2']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 2, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-aozora-v2',
                 'did:web:isbn.etzhayyim.com',
                 'isbn_ingest_aozora',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  isbn.etzhayyim.com — 青空文庫 daily delta (autonomous).\n'
                 '\n'
                 '  Timer-start: every 24h. Aozora catalog re-fetch + new work delta.\n'
                 '  fulltext=true → chapter chunks → B2 + vertex_isbn_book_chapter.\n'
                 '  limit=200 caps per-run cost; full re-walk takes ~3 days at this rate.\n'
                 '\n'
                 '  No XRPC entry. No CF Worker. Pure BPMN-as-actor + pyzeebe handler.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_isbn_ingest_aozora"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/isbn"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="isbn_ingest_aozora" name="isbn ingest 青空文庫 (daily)" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="every 24h">\n'
                 '      <bpmn:outgoing>Flow_Ingest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT24H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="ingest 青空文庫 catalog + fulltext">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="isbn.aozora.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=true" target="fulltext"/>\n'
                 '          <zeebe:input source="=200" target="limit"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Ingest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Ingest" sourceRef="StartTimer" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:isbn.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;isbn.ingest.aozora&quot;" '
                 'target="action"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Ingest" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2508,
                 '00-contracts/bpmn/com/etzhayyim/isbn/ingestAozora.bpmn',
                 '2026-05-05T11:00:00Z',
                 'did:web:isbn.etzhayyim.com',
                 'did:web:isbn.etzhayyim.com',
                 'sys.bpmn.seed.isbn-no-cf-worker',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-aozora-v2']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 2, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-gutenberg-v2',
                 'did:web:isbn.etzhayyim.com',
                 'isbn_ingest_gutenberg',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  isbn.etzhayyim.com — Project Gutenberg daily delta (autonomous).\n'
                 '\n'
                 '  Timer-start: every 24h. GutenDex JSON API pagination + fulltext\n'
                 '  download. limit=200 per run.\n'
                 '\n'
                 '  No XRPC entry. No CF Worker. Pure BPMN-as-actor + pyzeebe handler.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_isbn_ingest_gutenberg"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/isbn"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="isbn_ingest_gutenberg" name="isbn ingest Project Gutenberg '
                 '(daily)" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="every 24h">\n'
                 '      <bpmn:outgoing>Flow_Ingest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT24H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="ingest Gutenberg + fulltext">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="isbn.gutenberg.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=true" target="fulltext"/>\n'
                 '          <zeebe:input source="=200" target="limit"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Ingest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Ingest" sourceRef="StartTimer" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:isbn.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;isbn.ingest.gutenberg&quot;" '
                 'target="action"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Ingest" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2406,
                 '00-contracts/bpmn/com/etzhayyim/isbn/ingestGutenberg.bpmn',
                 '2026-05-05T11:00:00Z',
                 'did:web:isbn.etzhayyim.com',
                 'did:web:isbn.etzhayyim.com',
                 'sys.bpmn.seed.isbn-no-cf-worker',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-gutenberg-v2']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 2, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-ndl-v2',
                 'did:web:isbn.etzhayyim.com',
                 'isbn_ingest_ndl',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  isbn.etzhayyim.com — NDL Search SRU weekly sweep (autonomous).\n'
                 '\n'
                 '  Timer-start: every Monday 00:00 UTC. SRU caps maxRecords=200/req\n'
                 '  so this fires once a week with a broad ISBN wildcard query.\n'
                 '  Per-run cost is bounded; deeper sweeps are operator-driven via\n'
                 '  `kubectl exec`.\n'
                 '\n'
                 '  No XRPC entry. No CF Worker. Pure BPMN-as-actor + pyzeebe handler.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_isbn_ingest_ndl"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/isbn"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="isbn_ingest_ndl" name="isbn ingest NDL SRU (weekly)" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="weekly Mon">\n'
                 '      <bpmn:outgoing>Flow_Ingest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0 0 ? * '
                 'MON</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="ingest NDL SRU page">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="isbn.ndl.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;isbn=*&quot;" target="query"/>\n'
                 '          <zeebe:input source="=200" target="maxRecords"/>\n'
                 '          <zeebe:input source="=1" target="startRecord"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Ingest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Ingest" sourceRef="StartTimer" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:isbn.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;isbn.ingest.ndl&quot;" target="action"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Ingest" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2559,
                 '00-contracts/bpmn/com/etzhayyim/isbn/ingestNdl.bpmn',
                 '2026-05-05T11:00:00Z',
                 'did:web:isbn.etzhayyim.com',
                 'did:web:isbn.etzhayyim.com',
                 'sys.bpmn.seed.isbn-no-cf-worker',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-ndl-v2']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 2, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-hathitrust-v2',
                 'did:web:isbn.etzhayyim.com',
                 'isbn_ingest_hathitrust',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  isbn.etzhayyim.com — HathiTrust monthly hathifile (autonomous).\n'
                 '\n'
                 '  Timer-start: every month on the 8th @ 00:00 UTC. HathiTrust drops\n'
                 '  hathifile_full_*.txt.gz on the 1st-3rd; the 8th gives buffer.\n'
                 '  publicDomainOnly=true filters to access=allow rows (~7M of 18M).\n'
                 '\n'
                 '  hathifileUrl is intentionally unset → handler raises if not\n'
                 '  injected. This BPMN is the schedule contract; the actual URL\n'
                 '  must come from a K8s Secret / env / values.yaml override before\n'
                 '  the timer fires (see deps.toml `[[migrations]] '
                 'isbn-global-library-bulk-ingest-bringup`).\n'
                 '\n'
                 '  No XRPC entry. No CF Worker. Pure BPMN-as-actor + pyzeebe handler.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_isbn_ingest_hathitrust"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/isbn"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="isbn_ingest_hathitrust" name="isbn ingest HathiTrust '
                 '(monthly)" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="monthly day 8">\n'
                 '      <bpmn:outgoing>Flow_Ingest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0 0 8 * '
                 '?</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="ingest HathiTrust hathifile">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="isbn.hathitrust.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=true" target="publicDomainOnly"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Ingest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Ingest" sourceRef="StartTimer" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:isbn.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;isbn.ingest.hathitrust&quot;" '
                 'target="action"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Ingest" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2754,
                 '00-contracts/bpmn/com/etzhayyim/isbn/ingestHathiTrust.bpmn',
                 '2026-05-05T11:00:00Z',
                 'did:web:isbn.etzhayyim.com',
                 'did:web:isbn.etzhayyim.com',
                 'sys.bpmn.seed.isbn-no-cf-worker',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isbn-ingest-hathitrust-v2']}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
