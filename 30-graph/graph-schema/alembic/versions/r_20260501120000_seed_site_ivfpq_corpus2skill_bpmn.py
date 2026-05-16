"""Captured from Kysely migration 20260501120000_seed_site_ivfpq_corpus2skill_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260501120000_seed_site_ivfpq_corpus2skill_bpmn"
down_revision = 'r_20260501110000_vertex_corpus_skill_node_edge_skill_doc'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, 1, $4,\n'
         "             CAST($5 AS integer), $6, 'active', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/site-ivfPqReindex-v1',
                 'did:web:site.gftd.ai',
                 'site_ivf_pq_reindex',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '                  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '                  id="Definitions_site_ivf_pq_reindex"\n'
                 '                  targetNamespace="https://gftd.ai/bpmn/site"\n'
                 '                  exporter="hand-written"\n'
                 '                  exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="site_ivf_pq_reindex" name="site IVF+PQ Reindex" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "taskType": "site.ivfPq.reindex", "resident": true '
                 '}</bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 7 days">\n'
                 '      <bpmn:outgoing>Flow_Timer_Health</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_P7D">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P7D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual">\n'
                 '      <bpmn:outgoing>Flow_Manual_Health</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Timer_Health"  sourceRef="Start_Timer"  '
                 'targetRef="Task_HealthProbe"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual_Health" sourceRef="Start_Manual" '
                 'targetRef="Task_HealthProbe"/>\n'
                 '\n'
                 '    <!-- RisingWave health gate (ADR-0048 / scaling-contract) -->\n'
                 '    <bpmn:serviceTask id="Task_HealthProbe" name="rw health probe">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rw.health.probe" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=healthy"   target="healthy"/>\n'
                 '          <zeebe:output source="=degraded"  target="degraded"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Timer_Health</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_Manual_Health</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Health_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="GW_Health" name="healthy?">\n'
                 '      <bpmn:incoming>Flow_Health_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Health_OK</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Health_Degraded</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health_Gate"    sourceRef="Task_HealthProbe" '
                 'targetRef="GW_Health"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health_OK"      sourceRef="GW_Health" '
                 'targetRef="Task_EmbedMarkdown">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=healthy = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health_Degraded" sourceRef="GW_Health" '
                 'targetRef="Task_Audit">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=healthy = '
                 'false or degraded = true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <!-- Step 0: embed wet_chunk markdown rows that lack embeddings '
                 '(prerequisite) -->\n'
                 '    <bpmn:serviceTask id="Task_EmbedMarkdown" name="embed WET chunk markdown">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="site.ivfPq.embedMarkdown" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=if domain = null then &quot;site.wet&quot; else '
                 'domain" target="domain"/>\n'
                 '          <zeebe:input  source="=if batch_size = null then 200 else '
                 'batch_size"          target="batch_size"/>\n'
                 '          <zeebe:output source="=total_embedded"  target="embed_total"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Health_OK</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Embed_Centroids</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Embed_Centroids" sourceRef="Task_EmbedMarkdown" '
                 'targetRef="Task_UpdateCentroids"/>\n'
                 '\n'
                 '    <!-- Step 1: re-cluster IVF centroids -->\n'
                 '    <bpmn:serviceTask id="Task_UpdateCentroids" name="update IVF centroids">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="site.ivfPq.updateCentroids" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=if domain = null then &quot;site.wet&quot; else '
                 'domain" target="domain"/>\n'
                 '          <zeebe:input  source="=if n_centroids = null then 256 else '
                 'n_centroids"       target="n_centroids"/>\n'
                 '          <zeebe:output source="=n_centroids"        target="centroid_count"/>\n'
                 '          <zeebe:output source="=n_chunks_assigned"  target="chunks_assigned"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Embed_Centroids</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Centroids_Codebook</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Centroids_Codebook" '
                 'sourceRef="Task_UpdateCentroids" targetRef="Task_TrainCodebook"/>\n'
                 '\n'
                 '    <!-- Step 2: train PQ codebook -->\n'
                 '    <bpmn:serviceTask id="Task_TrainCodebook" name="train PQ codebook">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="site.ivfPq.trainCodebook" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=if domain = null then &quot;site.wet&quot; else '
                 'domain" target="domain"/>\n'
                 '          <zeebe:input  source="=if m_subspaces = null then 96 else '
                 'm_subspaces"        target="m_subspaces"/>\n'
                 '          <zeebe:input  source="=if k_centroids = null then 256 else '
                 'k_centroids"       target="k_centroids"/>\n'
                 '          <zeebe:output source="=version_tag"      target="pq_version_tag"/>\n'
                 '          <zeebe:output source="=n_train_vectors"  target="pq_train_vectors"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Centroids_Codebook</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Codebook_Encode</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Codebook_Encode" sourceRef="Task_TrainCodebook" '
                 'targetRef="Task_EncodeChunks"/>\n'
                 '\n'
                 '    <!-- Step 3: encode all wet_chunks -->\n'
                 '    <bpmn:serviceTask id="Task_EncodeChunks" name="encode WET chunks (PQ)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="site.ivfPq.encodeChunks" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  source="=if domain = null then &quot;site.wet&quot; else '
                 'domain"  target="domain"/>\n'
                 '          <zeebe:input  source="=if batch_size = null then 500 else '
                 'batch_size"            target="batch_size"/>\n'
                 '          <zeebe:output source="=encoded"   target="pq_encoded"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Codebook_Encode</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Encode_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Encode_Audit" sourceRef="Task_EncodeChunks" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <!-- Audit emit -->\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;site.ivfPq.reindex&quot;" '
                 'target="event_type"/>\n'
                 '          <zeebe:input source="=if healthy = false then &quot;degraded&quot; '
                 'else &quot;ok&quot;" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Health_Degraded</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_Encode_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit_End" sourceRef="Task_Audit" '
                 'targetRef="End_Event"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End_Event" name="done">\n'
                 '      <bpmn:incoming>Flow_Audit_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 7405,
                 '00-contracts/bpmn/ai/gftd/site/ivfPqReindex.bpmn',
                 '2026-05-01T10:00:00Z',
                 'did:web:site.gftd.ai',
                 'did:web:site.gftd.ai',
                 'sys.bpmn.seed.site',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/site-ivfPqReindex-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord,\n'
         '         org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1,\n'
         "             CAST($5 AS integer), '',\n"
         "             'active', $6, 1,\n"
         "             $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/site-ivfPqReindex-v1',
                 'did:web:site.gftd.ai',
                 'ai.gftd.apps.site.ivfPqReindex',
                 'site_ivf_pq_reindex',
                 14400000,
                 '2026-05-01T10:00:00Z',
                 'did:web:site.gftd.ai',
                 'did:web:site.gftd.ai',
                 'sys.bpmn.seed.site',
                 'did:web:site.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/site-ivfPqReindex-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, 1, $4,\n'
         "             CAST($5 AS integer), $6, 'active', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/site-corpus2skillDistill-v1',
                 'did:web:site.gftd.ai',
                 'site_corpus2skill_distill',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '                  xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '                  id="Definitions_site_corpus2skill_distill"\n'
                 '                  targetNamespace="https://gftd.ai/bpmn/site"\n'
                 '                  exporter="hand-written"\n'
                 '                  exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="site_corpus2skill_distill" name="site Corpus2Skill Distill" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "taskType": "site.corpus2skill.distill", "resident": '
                 'true }</bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 7 days">\n'
                 '      <bpmn:outgoing>Flow_Timer_Health</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_P7D">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P7D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual">\n'
                 '      <bpmn:outgoing>Flow_Manual_Health</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Timer_Health"  sourceRef="Start_Timer"  '
                 'targetRef="Task_HealthProbe"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual_Health" sourceRef="Start_Manual" '
                 'targetRef="Task_HealthProbe"/>\n'
                 '\n'
                 '    <!-- RisingWave health gate -->\n'
                 '    <bpmn:serviceTask id="Task_HealthProbe" name="rw health probe">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="rw.health.probe" retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=healthy"  target="healthy"/>\n'
                 '          <zeebe:output source="=degraded" target="degraded"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Timer_Health</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_Manual_Health</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Health_Gate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="GW_Health" name="healthy?">\n'
                 '      <bpmn:incoming>Flow_Health_Gate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Health_OK</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_Health_Degraded</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health_Gate"    sourceRef="Task_HealthProbe" '
                 'targetRef="GW_Health"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health_OK"      sourceRef="GW_Health" '
                 'targetRef="Task_ListDomains">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=healthy = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health_Degraded" sourceRef="GW_Health" '
                 'targetRef="Task_Audit">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=healthy = '
                 'false or degraded = true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <!-- List distinct domains with embedded chunks -->\n'
                 '    <bpmn:serviceTask id="Task_ListDomains" name="list domains with '
                 'embeddings">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT DISTINCT domain FROM '
                 'vertex_wet_chunk WHERE embedding IS NOT NULL LIMIT 50&quot;" target="query"/>\n'
                 '          <zeebe:output source="=rows" target="domains"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Health_OK</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_List_MI</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_List_MI" sourceRef="Task_ListDomains" '
                 'targetRef="Task_DistillDomain"/>\n'
                 '\n'
                 '    <!-- Multi-instance distill per domain (sequential to avoid OOM on faiss) '
                 '-->\n'
                 '    <bpmn:serviceTask id="Task_DistillDomain" name="distill domain skill tree">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="site.corpus2skill.distillDomain" '
                 'retries="1"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input  '
                 'source="=domain_item.domain"                                target="domain"/>\n'
                 '          <zeebe:input  source="=if branch_k = null then 8 else '
                 'branch_k"           target="branch_k"/>\n'
                 '          <zeebe:input  source="=if dry_run = null then false else '
                 'dry_run"          target="dry_run"/>\n'
                 '          <zeebe:output source="=nodes_created"  '
                 'target="domain_nodes_created"/>\n'
                 '          <zeebe:output source="=edges_created"  '
                 'target="domain_edges_created"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_List_MI</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_MI_Audit</bpmn:outgoing>\n'
                 '      <bpmn:multiInstanceLoopCharacteristics isSequential="true">\n'
                 '        <bpmn:extensionElements>\n'
                 '          <zeebe:loopCharacteristics inputCollection="=domains" '
                 'inputElement="domain_item"/>\n'
                 '        </bpmn:extensionElements>\n'
                 '      </bpmn:multiInstanceLoopCharacteristics>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_MI_Audit" sourceRef="Task_DistillDomain" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <!-- Audit emit -->\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit" retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;site.corpus2skill.distill&quot;" '
                 'target="event_type"/>\n'
                 '          <zeebe:input source="=if healthy = false then &quot;degraded&quot; '
                 'else &quot;ok&quot;" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Health_Degraded</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_MI_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit_End" sourceRef="Task_Audit" '
                 'targetRef="End_Event"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End_Event" name="done">\n'
                 '      <bpmn:incoming>Flow_Audit_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5748,
                 '00-contracts/bpmn/ai/gftd/site/corpus2skillDistill.bpmn',
                 '2026-05-01T10:00:00Z',
                 'did:web:site.gftd.ai',
                 'did:web:site.gftd.ai',
                 'sys.bpmn.seed.site',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/site-corpus2skillDistill-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord,\n'
         '         org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1,\n'
         "             CAST($5 AS integer), '',\n"
         "             'active', $6, 1,\n"
         "             $7, $8, $9, $10, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/site-corpus2skillDistill-v1',
                 'did:web:site.gftd.ai',
                 'ai.gftd.apps.site.corpus2skillDistill',
                 'site_corpus2skill_distill',
                 28800000,
                 '2026-05-01T10:00:00Z',
                 'did:web:site.gftd.ai',
                 'did:web:site.gftd.ai',
                 'sys.bpmn.seed.site',
                 'did:web:site.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/site-corpus2skillDistill-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/site-ivfPqReindex-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/site-ivfPqReindex-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/site-corpus2skillDistill-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/site-corpus2skillDistill-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
