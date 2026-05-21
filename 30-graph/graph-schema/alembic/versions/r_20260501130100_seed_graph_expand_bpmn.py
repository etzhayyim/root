"""Captured from Kysely migration 20260501130100_seed_graph_expand_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260501130100_seed_graph_expand_bpmn"
down_revision = 'r_20260501130000_vertex_graph_expand_proposal'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/graph-expand-tick-v1',
                 'did:web:graph.etzhayyim.com',
                 'graph_expand_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Graph expansion tick — ADR 2605011200.\n'
                 '\n'
                 '  Every 30 minutes (and on-demand via XRPC), pick ONE stale vertex_actor row,\n'
                 '  ask the classifier-tier LLM to propose ONE related vertex/edge, and write\n'
                 "  the proposal into vertex_graph_expand_proposal (status='proposed').\n"
                 '\n'
                 '  Never writes edge_* directly — promotion is a separate downstream step.\n'
                 '\n'
                 '  NSID:      ai.gftd.apps.graph.expandTick\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/graph-expandTick-v1\n'
                 '  binding allowlist: vertex_graph_expand_proposal\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_graph_expand_tick"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/graph"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="graph_expand_tick" name="graph expand tick" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.graph.expandTick", "version": 1, '
                 '"resultTimeoutMs": 60000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 30 minutes">\n'
                 '      <bpmn:outgoing>Flow_Timer</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT30M">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '                        '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT30M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / on-demand">\n'
                 '      <bpmn:outgoing>Flow_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Timer"  sourceRef="Start_Timer"  '
                 'targetRef="Task_Pick"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_Pick"/>\n'
                 '\n'
                 '    <!--\n'
                 "      Task 1 — pick ONE stale vertex_actor row that we haven't proposed for in\n"
                 '      the last 7 days under the same llm_model. Conservative: LIMIT 1.\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Pick" name="pick stale vertex_actor seed">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT vertex_id, COALESCE(display_name, '
                 "name, handle, '') AS label, COALESCE(category, classification, '') AS summary "
                 'FROM vertex_actor WHERE display_name IS NOT NULL ORDER BY _seq DESC LIMIT '
                 '1&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[]" target="params"/>\n'
                 '          <zeebe:output source="=rows" target="seedRows"/>\n'
                 '          <zeebe:output source="=rowCount" target="seedCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Timer</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Pick_Infer</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Pick_Infer" sourceRef="Task_Pick" '
                 'targetRef="Task_Infer"/>\n'
                 '\n'
                 '    <!--\n'
                 '      Task 2 — ask the classifier-tier LLM for ONE proposal in strict JSON.\n'
                 '      Empty seed (seedCount = 0) still calls LLM with empty user prompt —\n'
                 '      generic.llm.json returns {ok:false, error:...} which we still record\n'
                 '      in audit so we can spot saturation. Optional optimisation: gateway\n'
                 '      with seedCount > 0 (defer).\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Infer" name="LLM propose one related '
                 'vertex/edge">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.llm.json"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;classifier&quot;" target="tier"/>\n'
                 '          <zeebe:input source="=&quot;You expand a knowledge graph. Output ONE '
                 'JSON object only, no preamble. Schema: '
                 '{dstLabel:string,edgeKind:string,confidence:number,rationale:string}. edgeKind '
                 'must be a short snake_case verb. confidence in [0,1]. rationale ≤ 240 '
                 'chars.&quot;" target="system"/>\n'
                 '          <zeebe:input source="=&quot;Source vertex: &quot; + (if seedCount &gt; '
                 '0 then seedRows[1].label else &quot;(none)&quot;) + &quot;. Summary: &quot; + '
                 '(if seedCount &gt; 0 then seedRows[1].summary else &quot;(none)&quot;) + &quot;. '
                 'Propose ONE most-likely related vertex (concept, organization, technology, '
                 'person, etc.) and the edge linking them.&quot;" target="user"/>\n'
                 '          <zeebe:input source="=400" target="maxTokens"/>\n'
                 '          <zeebe:input source="=0.1" target="temperature"/>\n'
                 '          <zeebe:output source="=ok"    target="llmOk"/>\n'
                 '          <zeebe:output source="=data"  target="llmData"/>\n'
                 '          <zeebe:output source="=model" target="llmModel"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Pick_Infer</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Infer_Write</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Infer_Write" sourceRef="Task_Infer" '
                 'targetRef="Task_Write"/>\n'
                 '\n'
                 '    <!--\n'
                 '      Task 3 — INSERT proposal row. Raw SQL path (allowed table guarded by\n'
                 '      vertex_bpmn_lexicon_binding.write_table_allowlist = '
                 "'vertex_graph_expand_proposal').\n"
                 "      vertex_id = content-hashed: source_vid + '|' + edgeKind + '|' + dstLabel + "
                 "'|' + llmModel.\n"
                 '      We let RisingWave PK implicit-upsert dedupe (CLAUDE.md §record-log '
                 'semantics).\n'
                 '    -->\n'
                 '    <bpmn:serviceTask id="Task_Write" name="insert proposal (status=proposed)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;INSERT INTO vertex_graph_expand_proposal '
                 '(vertex_id, source_vid, proposed_dst_label, edge_kind, confidence, rationale, '
                 'llm_model, status, created_at, owner_did, sensitivity_ord, org_id, user_id, '
                 "actor_id, actor_did, org_did) VALUES ($1, $2, $3, $4, $5, $6, $7, 'proposed', "
                 "$8, 'did:web:graph.etzhayyim.com', 1, 'did:web:graph.etzhayyim.com', "
                 "'did:web:graph.etzhayyim.com', 'sys.bpmn.graph.expand', 'did:web:graph.etzhayyim.com', "
                 '\'anon\')&quot;" target="sql"/>\n'
                 '          <zeebe:input source="=[ '
                 '&quot;at://did:web:graph.etzhayyim.com/ai.gftd.apps.graph.expandProposal/&quot; + (if '
                 'seedCount &gt; 0 then seedRows[1].vertex_id else &quot;empty&quot;) + '
                 '&quot;|&quot; + (if llmOk then llmData.edgeKind else &quot;none&quot;) + '
                 '&quot;|&quot; + (if llmOk then llmData.dstLabel else &quot;none&quot;), if '
                 'seedCount &gt; 0 then seedRows[1].vertex_id else &quot;&quot;, if llmOk then '
                 'llmData.dstLabel else &quot;&quot;, if llmOk then llmData.edgeKind else '
                 '&quot;none&quot;, if llmOk then llmData.confidence else 0.0, if llmOk then '
                 'llmData.rationale else &quot;llm_failed&quot;, llmModel, string(now()) ]" '
                 'target="params"/>\n'
                 '          <zeebe:output source="=inserted" target="proposalInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Infer_Write</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Write_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Write_Audit" sourceRef="Task_Write" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit graph.expand.proposal OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.graph.expand.proposal&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;seedCount&quot;: seedCount, '
                 '&quot;llmOk&quot;: llmOk, &quot;edgeKind&quot;: if llmOk then llmData.edgeKind '
                 'else &quot;none&quot;, &quot;confidence&quot;: if llmOk then llmData.confidence '
                 'else 0.0, &quot;inserted&quot;: proposalInserted }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Write_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit_End" sourceRef="Task_Audit" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_Audit_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 7830,
                 '00-contracts/bpmn/ai/gftd/graph/expandTick.bpmn',
                 '2026-05-01T13:00:00Z',
                 'did:web:graph.etzhayyim.com',
                 'did:web:graph.etzhayyim.com',
                 'sys.bpmn.seed.graph',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/graph-expand-tick-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord,\n'
         '         org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1,\n'
         '             CAST($5 AS integer), $6,\n'
         "             'active', $7, 1,\n"
         "             $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/graph-expandTick-v1',
                 'did:web:graph.etzhayyim.com',
                 'ai.gftd.apps.graph.expandTick',
                 'graph_expand_tick',
                 60000,
                 'vertex_graph_expand_proposal',
                 '2026-05-01T13:00:00Z',
                 'did:web:graph.etzhayyim.com',
                 'did:web:graph.etzhayyim.com',
                 'sys.bpmn.seed.graph',
                 'did:web:graph.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/graph-expandTick-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/graph-expandTick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/graph-expand-tick-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
