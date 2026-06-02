"""Captured from Kysely migration 20260429090900_seed_shigotoba_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429090900_seed_shigotoba_bpmn_actors"
down_revision = 'r_20260429090800_seed_mangaka_standalone_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shigotoba-ingestJobs-v1',
                 'did:web:shigotoba.etzhayyim.com',
                 'shigotoba_ingest_jobs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Shigotoba public job ingestion.\n'
                 '  Appview dispatches this BPMN only; Python Zeebe worker fetches public APIs,\n'
                 '  normalizes, and writes graph rows.\n'
                 '  in:  source? = all|remotive|arbeitnow|remoteok, limit?\n'
                 '  out: result\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_shigotoba_ingest_jobs"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/shigotoba"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="shigotoba_ingest_jobs" name="shigotoba ingest jobs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="ingest requested">\n'
                 '      <bpmn:outgoing>F1</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="F1" sourceRef="Start" targetRef="Task_Ingest"/>\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="fetch normalize persist">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="shigotoba.jobs.ingest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if source = null then &quot;all&quot; else '
                 'string(source)" target="source"/>\n'
                 '          <zeebe:input source="=if limit = null then 100 else limit" '
                 'target="limit"/>\n'
                 '          <zeebe:output source="=result" target="result"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F2" sourceRef="Task_Ingest" targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:shigotoba.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ingestJobs&quot;" target="action"/>\n'
                 '          <zeebe:input source="=result" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F2</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F3</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F3" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>F3</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2285,
                 '00-contracts/bpmn/com/etzhayyim/shigotoba/ingestJobs.bpmn',
                 '2026-04-29T09:09:00Z',
                 'did:web:shigotoba.etzhayyim.com',
                 'did:web:shigotoba.etzhayyim.com',
                 'sys.bpmn.seed.shigotoba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shigotoba-ingestJobs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shigotoba-ingestJobs-v1',
                 'did:web:shigotoba.etzhayyim.com',
                 'com.etzhayyim.apps.shigotoba.ingestJobs',
                 'shigotoba_ingest_jobs',
                 600000,
                 '2026-04-29T09:09:00Z',
                 'did:web:shigotoba.etzhayyim.com',
                 'did:web:shigotoba.etzhayyim.com',
                 'sys.bpmn.seed.shigotoba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shigotoba-ingestJobs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shigotoba-summarize-v1',
                 'did:web:shigotoba.etzhayyim.com',
                 'shigotoba_summarize',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Shigotoba job-market summary.\n'
                 '  Appview dispatches this BPMN; Python Zeebe generic primitives read the graph\n'
                 '  and call the LLM outside the Worker.\n'
                 '  in:  topic?\n'
                 '  out: summary, topic, model, latencyMs\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_shigotoba_summarize"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/shigotoba"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="shigotoba_summarize" name="shigotoba summarize" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="summary requested">\n'
                 '      <bpmn:outgoing>F1</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="F1" sourceRef="Start" targetRef="Task_SelectJobs"/>\n'
                 '    <bpmn:serviceTask id="Task_SelectJobs" name="read recent jobs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_shigotoba_job_posting&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="=&quot;title, company_name, source&quot;" '
                 'target="columns"/>\n'
                 '          <zeebe:input source="=&quot;actor_id = $1&quot;" target="whereExpr"/>\n'
                 '          <zeebe:input source="=[&quot;a80c21a0&quot;]" target="whereParams"/>\n'
                 '          <zeebe:input source="=&quot;created_at DESC&quot;" target="orderBy"/>\n'
                 '          <zeebe:input source="=20" target="limit"/>\n'
                 '          <zeebe:output source="=rows" target="jobRows"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F2" sourceRef="Task_SelectJobs" '
                 'targetRef="Task_Summarize"/>\n'
                 '    <bpmn:serviceTask id="Task_Summarize" name="summarize market">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.llm.chat"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;classifier&quot;" target="tier"/>\n'
                 '          <zeebe:input source="=&quot;You summarize public job-market data for '
                 'shigotoba.etzhayyim.com. Be concise, factual, and avoid unsupported claims.&quot;" '
                 'target="system"/>\n'
                 '          <zeebe:input source="=&quot;Topic: &quot; + (if topic = null then '
                 '&quot;job market&quot; else string(topic)) + &quot;\\nRecent jobs JSON: &quot; + '
                 'string(jobRows)" target="user"/>\n'
                 '          <zeebe:input source="=500" target="maxTokens"/>\n'
                 '          <zeebe:input source="=0.2" target="temperature"/>\n'
                 '          <zeebe:output source="=content" target="summary"/>\n'
                 '          <zeebe:output source="=model" target="model"/>\n'
                 '          <zeebe:output source="=latencyMs" target="latencyMs"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F2</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F3</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F3" sourceRef="Task_Summarize" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:shigotoba.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;summarize&quot;" target="action"/>\n'
                 '          <zeebe:input source="={topic: (if topic = null then &quot;job '
                 'market&quot; else string(topic)), model: string(model), latencyMs: latencyMs}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F3</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F4</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F4" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>F4</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3820,
                 '00-contracts/bpmn/com/etzhayyim/shigotoba/summarize.bpmn',
                 '2026-04-29T09:09:00Z',
                 'did:web:shigotoba.etzhayyim.com',
                 'did:web:shigotoba.etzhayyim.com',
                 'sys.bpmn.seed.shigotoba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shigotoba-summarize-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shigotoba-summarize-v1',
                 'did:web:shigotoba.etzhayyim.com',
                 'com.etzhayyim.apps.shigotoba.summarize',
                 'shigotoba_summarize',
                 180000,
                 '2026-04-29T09:09:00Z',
                 'did:web:shigotoba.etzhayyim.com',
                 'did:web:shigotoba.etzhayyim.com',
                 'sys.bpmn.seed.shigotoba',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shigotoba-summarize-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shigotoba-ingestJobs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shigotoba-ingestJobs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/shigotoba-summarize-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/shigotoba-summarize-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
