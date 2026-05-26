"""Captured from Kysely migration 20260429144100_seed_llm_knowledge_bpmn_actor."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429144100_seed_llm_knowledge_bpmn_actor"
down_revision = 'r_20260429144000_llm_domain_knowledge_rag'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '      actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1, $4,\n'
         "      CAST($5 AS integer), $6, 'active', $7,\n"
         "      1, $8, $9, $10, $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/llm-answer-with-knowledge-v1',
                 'did:web:llm.etzhayyim.com',
                 'llm_answer_with_knowledge',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  llm.answerWithKnowledge\n'
                 '\n'
                 '  Proper RAG path for llm.etzhayyim.com:\n'
                 '    1. Retrieve domain knowledge from RisingWave vertex/edge/MV tables.\n'
                 '    2. Run a Python LangGraph answer graph over retrieved evidence.\n'
                 '    3. Emit audit.\n'
                 '\n'
                 '  The CF Worker remains a thin OpenAI/XRPC facade. It must not embed\n'
                 '  application facts or game-specific branches.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_llm_answer_with_knowledge"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/llm"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="llm_answer_with_knowledge" name="llm answer with knowledge" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "app.etzhayyim.apps.llm.answerWithKnowledge", "version": 1, '
                 '"resultTimeoutMs": 90000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="question submitted">\n'
                 '      <bpmn:outgoing>Flow_Retrieve</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Retrieve" sourceRef="Start" '
                 'targetRef="Task_Retrieve"/>\n'
                 '    <bpmn:serviceTask id="Task_Retrieve" name="retrieve RisingWave domain '
                 'knowledge">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="llm.knowledge.retrieve"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=string(question)" target="question"/>\n'
                 '          <zeebe:input source="=if domain = null then &quot;&quot; else '
                 'string(domain)" target="domain"/>\n'
                 '          <zeebe:input source="=if game_slug = null then &quot;&quot; else '
                 'string(game_slug)" target="gameSlug"/>\n'
                 '          <zeebe:input source="=if lang = null then &quot;ja&quot; else '
                 'string(lang)" target="lang"/>\n'
                 '          <zeebe:input source="=if topK = null then 8 else topK" '
                 'target="topK"/>\n'
                 '          <zeebe:output source="=contexts" target="contexts"/>\n'
                 '          <zeebe:output source="=citations" target="citations"/>\n'
                 '          <zeebe:output source="=usedKnowledge" target="usedKnowledge"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Retrieve</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Answer</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_Answer" sourceRef="Task_Retrieve" '
                 'targetRef="Task_Answer"/>\n'
                 '    <bpmn:serviceTask id="Task_Answer" name="LangGraph answer from evidence">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="llm.knowledge.langgraphAnswer"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=string(question)" target="question"/>\n'
                 '          <zeebe:input source="=contexts" target="contexts"/>\n'
                 '          <zeebe:input source="=citations" target="citations"/>\n'
                 '          <zeebe:input source="=if tier = null then &quot;fast&quot; else '
                 'string(tier)" target="tier"/>\n'
                 '          <zeebe:input source="=if model = null then &quot;&quot; else '
                 'string(model)" target="model"/>\n'
                 '          <zeebe:input source="=if lang = null then &quot;ja&quot; else '
                 'string(lang)" target="lang"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=answer" target="answer"/>\n'
                 '          <zeebe:output source="=confidence" target="confidence"/>\n'
                 '          <zeebe:output source="=model" target="model"/>\n'
                 '          <zeebe:output source="=latencyMs" target="latencyMs"/>\n'
                 '          <zeebe:output source="=error" target="error"/>\n'
                 '          <zeebe:output source="=errorKind" target="errorKind"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Answer</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Answer" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="answer ready">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3837,
                 '00-contracts/bpmn/ai/gftd/llm/answerWithKnowledge.bpmn',
                 '2026-04-29T14:41:00+09:00',
                 'did:web:llm.etzhayyim.com',
                 'did:web:llm.etzhayyim.com',
                 'sys.bpmn.seed.llm-knowledge',
                 'did:web:llm.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/llm-answer-with-knowledge-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '      org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST(90000 AS integer), 'active', $5, 1,\n"
         "      $6, $7, $8, $9, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/llm-answer-with-knowledge-v1',
                 'did:web:llm.etzhayyim.com',
                 'app.etzhayyim.apps.llm.answerWithKnowledge',
                 'llm_answer_with_knowledge',
                 '2026-04-29T14:41:00+09:00',
                 'did:web:llm.etzhayyim.com',
                 'did:web:llm.etzhayyim.com',
                 'sys.bpmn.seed.llm-knowledge',
                 'did:web:llm.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/llm-answer-with-knowledge-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/llm-answer-with-knowledge-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/llm-answer-with-knowledge-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
