"""Captured from Kysely migration 20260508000100_seed_chat_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508000100_seed_chat_bpmn_actors"
down_revision = 'r_20260508000000_vertex_training_lineage'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/chat-memory-reindex-v1',
                 'did:web:etzhayyim.com',
                 'chat_memory_reindex',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  etzhayyim.com chat — memory reindex (timer-start, autonomous, R/PT24H).\n'
                 '\n'
                 '  Walks vertex_chat_message.embedding IS NULL rows (last 24h),\n'
                 '  embeds via Murakumo-served sentence-transformers actor, writes\n'
                 '  embedding + ivf_cluster_id back. Promotes "important" messages\n'
                 '  to vertex_chat_memory (long-term) based on importance_score.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_chat_memory_reindex"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/chat"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="chat_memory_reindex" name="chat memory reindex" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "version": 1, "schedule": "R/PT24H" }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="daily 03:00 UTC">\n'
                 '      <bpmn:outgoing>Flow_ToReindex</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_Daily">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0 3 * * '
                 '?</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Reindex" name="embed unindexed messages">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="chat.memory.reindex"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=embedded" target="embedded"/>\n'
                 '          <zeebe:output source="=promotedToLongTerm" '
                 'target="promotedToLongTerm"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToReindex</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToReindex" sourceRef="Start" '
                 'targetRef="Task_Reindex"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:etzhayyim.com&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;app.etzhayyim.apps.chat.memoryReindex&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;embedded&quot;: embedded, '
                 '&quot;promotedToLongTerm&quot;: promotedToLongTerm }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Reindex" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2854,
                 '00-contracts/bpmn/ai/gftd/chat/memoryReindex.bpmn',
                 '2026-05-08T00:00:00Z',
                 'did:web:etzhayyim.com',
                 'did:web:etzhayyim.com',
                 'sys.bpmn.seed.chat',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/chat-memory-reindex-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/chat-artifact-gc-v1',
                 'did:web:etzhayyim.com',
                 'chat_artifact_gc',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  etzhayyim.com chat — artifact GC (timer-start, autonomous, R/PT24H).\n'
                 '\n'
                 '  Removes B2 objects + soft-deletes vertex_chat_artifact rows whose\n'
                 "  expires_at < now() OR (status='gc-pending' AND ts_ms older than 30 d).\n"
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_chat_artifact_gc"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/chat"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="chat_artifact_gc" name="chat artifact GC" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "version": 1, "schedule": "R/PT24H" }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="daily 04:00 UTC">\n'
                 '      <bpmn:outgoing>Flow_ToGc</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_Daily">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0 4 * * '
                 '?</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Gc" name="delete expired B2 artifacts">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="chat.artifact.gc"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=deleted" target="deleted"/>\n'
                 '          <zeebe:output source="=bytesFreed" target="bytesFreed"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToGc</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToGc" sourceRef="Start" targetRef="Task_Gc"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:etzhayyim.com&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;app.etzhayyim.apps.chat.artifactGc&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;deleted&quot;: deleted, '
                 '&quot;bytesFreed&quot;: bytesFreed }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Gc" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2658,
                 '00-contracts/bpmn/ai/gftd/chat/artifactGc.bpmn',
                 '2026-05-08T00:00:00Z',
                 'did:web:etzhayyim.com',
                 'did:web:etzhayyim.com',
                 'sys.bpmn.seed.chat',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/chat-artifact-gc-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/chat-conversation-archive-v1',
                 'did:web:etzhayyim.com',
                 'chat_conversation_archive',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  etzhayyim.com chat — conversation archive (timer-start, autonomous, R/P7D).\n'
                 '\n'
                 "  Conversations idle > 90 d → status='archived', dump rolled into\n"
                 '  Iceberg parquet (read-only cold tier). Active hot store stays\n'
                 '  small for fast IVF / RAG.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_chat_conversation_archive"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/chat"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="chat_conversation_archive" name="chat conversation archive" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "version": 1, "schedule": "weekly Sunday 02:00 UTC" }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="weekly Sunday 02:00 UTC">\n'
                 '      <bpmn:outgoing>Flow_ToArchive</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_Weekly">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0 2 ? * '
                 'SUN</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Archive" name="archive idle conversations">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="chat.conversation.archive"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=archivedConversations" '
                 'target="archivedConversations"/>\n'
                 '          <zeebe:output source="=archivedMessages" target="archivedMessages"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToArchive</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToArchive" sourceRef="Start" '
                 'targetRef="Task_Archive"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:etzhayyim.com&quot;" target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;app.etzhayyim.apps.chat.conversationArchive&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;archivedConversations&quot;: '
                 'archivedConversations, &quot;archivedMessages&quot;: archivedMessages }" '
                 'target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Archive" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2865,
                 '00-contracts/bpmn/ai/gftd/chat/conversationArchive.bpmn',
                 '2026-05-08T00:00:00Z',
                 'did:web:etzhayyim.com',
                 'did:web:etzhayyim.com',
                 'sys.bpmn.seed.chat',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/chat-conversation-archive-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/chat-schedule-report-v1',
                 'did:web:etzhayyim.com',
                 'chat_schedule_report',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  etzhayyim.com chat — scheduleReport (XRPC app.etzhayyim.apps.chat.scheduleReport).\n'
                 '\n'
                 '  Side-effect tool example: LangGraph agent calls this when the user asks\n'
                 '  for a deferred report. The BPMN runs Murakumo deep research, persists\n'
                 '  result as vertex_chat_artifact, and posts a follow-up assistant message\n'
                 '  back into the original conv via generic.pds.dispatch.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_chat_schedule_report"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/chat"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="chat_schedule_report" name="chat schedule report" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.chat.scheduleReport", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="scheduleReport">\n'
                 '      <bpmn:outgoing>Flow_ToCompose</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Compose" name="compose report (LLM, deep '
                 'research)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="chat.report.compose"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=convId" target="convId"/>\n'
                 '          <zeebe:input source="=msgId" target="msgId"/>\n'
                 '          <zeebe:input source="=title" target="title"/>\n'
                 '          <zeebe:input source="=prompt" target="prompt"/>\n'
                 '          <zeebe:input source="=deliverAt" target="deliverAt"/>\n'
                 '          <zeebe:input source="=deliverChannel" target="deliverChannel"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=runId" target="runId"/>\n'
                 '          <zeebe:output source="=artifactId" target="artifactId"/>\n'
                 '          <zeebe:output source="=scheduledAt" target="scheduledAt"/>\n'
                 '          <zeebe:output source="=deliveryChannel" target="deliveryChannel"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToCompose</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCompose" sourceRef="Start" '
                 'targetRef="Task_Compose"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:etzhayyim.com&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;app.etzhayyim.apps.chat.scheduleReport&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;convId&quot;: convId, &quot;runId&quot;: '
                 'runId, &quot;artifactId&quot;: artifactId, &quot;deliverChannel&quot;: '
                 'deliveryChannel }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Compose" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3308,
                 '00-contracts/bpmn/ai/gftd/chat/scheduleReport.bpmn',
                 '2026-05-08T00:00:00Z',
                 'did:web:etzhayyim.com',
                 'did:web:etzhayyim.com',
                 'sys.bpmn.seed.chat',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/chat-schedule-report-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/chat-scheduleReport-v1',
                 'did:web:etzhayyim.com',
                 'app.etzhayyim.apps.chat.scheduleReport',
                 'chat_schedule_report',
                 30000,
                 '2026-05-08T00:00:00Z',
                 'did:web:etzhayyim.com',
                 'did:web:etzhayyim.com',
                 'sys.bpmn.seed.chat',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/chat-scheduleReport-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/chat-scheduleReport-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/chat-memory-reindex-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/chat-artifact-gc-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/chat-conversation-archive-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/chat-schedule-report-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
