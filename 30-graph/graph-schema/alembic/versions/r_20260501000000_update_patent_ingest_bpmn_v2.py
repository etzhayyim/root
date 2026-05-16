"""Captured from Kysely migration 20260501000000_update_patent_ingest_bpmn_v2."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260501000000_update_patent_ingest_bpmn_v2"
down_revision = 'r_20260430703000_natural_person_all_latent_materialization'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    UPDATE vertex_bpmn_process_def\n'
         '    SET "xml"          = $1,\n'
         '        xml_byte_size  = CAST($2 AS integer),\n'
         "        status         = 'active'\n"
         '    WHERE bpmn_process_id = $3\n'
         '  ',
  'parameters': ['<?xml version="1.0" encoding="UTF-8"?>\n'
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
                 '    targetNamespace="https://gftd.ai/bpmn/patent"\n'
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
                 '          <zeebe:input source="=&quot;did:web:patent.gftd.ai&quot;" '
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
                 'patent_ingest_uspto_weekly']}]

DOWN = [{'sql': '\n'
         '    UPDATE vertex_bpmn_process_def\n'
         "    SET status = 'inactive'\n"
         '    WHERE bpmn_process_id = $1\n'
         '  ',
  'parameters': ['patent_ingest_uspto_weekly']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
