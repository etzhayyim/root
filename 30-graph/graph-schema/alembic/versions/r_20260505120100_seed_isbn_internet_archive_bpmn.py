"""Captured from Kysely migration 20260505120100_seed_isbn_internet_archive_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260505120100_seed_isbn_internet_archive_bpmn"
down_revision = 'r_20260505120000_vertex_isbn_book_image'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/isbn-ingest-internet-archive-v1',
                 'did:web:isbn.etzhayyim.com',
                 'isbn_ingest_internet_archive',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  isbn.etzhayyim.com — Internet Archive (archive.org) daily.\n'
                 '\n'
                 '  Timer-start: every 24h. Pulls 50 PD texts items per run with:\n'
                 '    - cover image  (services/img)\n'
                 '    - body text    (DjVu OCR)\n'
                 '    - per-page IIIF images capped at 10/book (fetchPageImages defaults\n'
                 '      to false for routine runs to keep the egress + B2 cost bounded;\n'
                 '      operator can run a manual fan-out for specific identifiers via\n'
                 '      kubectl exec).\n'
                 '\n'
                 '  No XRPC entry. No CF Worker. Pure BPMN-as-actor + pyzeebe handler.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_isbn_ingest_internet_archive"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/isbn"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="isbn_ingest_internet_archive" name="isbn ingest Internet '
                 'Archive (daily)" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="StartTimer" name="every 24h">\n'
                 '      <bpmn:outgoing>Flow_Ingest</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT24H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="ingest archive.org PD texts">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="isbn.internetArchive.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;mediatype:texts AND collection:opensource '
                 'AND format:DjVuTXT&quot;" target="query"/>\n'
                 '          <zeebe:input source="=50" target="rows"/>\n'
                 '          <zeebe:input source="=true" target="fulltext"/>\n'
                 '          <zeebe:input source="=true" target="fetchCovers"/>\n'
                 '          <zeebe:input source="=false" target="fetchPageImages"/>\n'
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
                 '          <zeebe:input source="=&quot;isbn.ingest.internetArchive&quot;" '
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
                 2935,
                 '00-contracts/bpmn/ai/gftd/isbn/ingestInternetArchive.bpmn',
                 '2026-05-05T12:01:00Z',
                 'did:web:isbn.etzhayyim.com',
                 'did:web:isbn.etzhayyim.com',
                 'sys.bpmn.seed.isbn-internet-archive',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/isbn-ingest-internet-archive-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/isbn-ingest-internet-archive-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
