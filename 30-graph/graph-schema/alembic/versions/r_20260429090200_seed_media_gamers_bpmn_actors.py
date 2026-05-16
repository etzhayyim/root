"""Captured from Kysely migration 20260429090200_seed_media_gamers_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429090200_seed_media_gamers_bpmn_actors"
down_revision = 'r_20260429090100_seed_news_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/media-gamers-guideGenerate-v1',
                 'did:web:media-gamers.gftd.ai',
                 'media_gamers_guide_generate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  media-gamers.guideGenerate\n'
                 '\n'
                 '  Zeebe-owned guide generation pipeline for media-gamers.gftd.ai. Python '
                 'workers\n'
                 '  perform target resolution, LLM generation, translation, quality scoring, and\n'
                 '  social-post drafting. Cloudflare app.ts remains the edge/PDS write boundary\n'
                 '  through ai.gftd.apps.media_gamers.guide.commitGuide.\n'
                 '\n'
                 '  Input variables:\n'
                 '    slug, guideType, translate, offset, limit, userId, mood, publish\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_media_gamers_guide_generate"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/media-gamers"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="media_gamers_guide_generate" name="media gamers guide '
                 'generate" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="guide generation requested">\n'
                 '      <bpmn:outgoing>Flow_Resolve</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Resolve" sourceRef="Start" '
                 'targetRef="Task_Resolve"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Resolve" name="resolve guide targets">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="mediaGamers.guide.resolveTargets"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=string(slug)" target="slug"/>\n'
                 '          <zeebe:input source="=string(guideType)" target="guideType"/>\n'
                 '          <zeebe:input source="=offset" target="offset"/>\n'
                 '          <zeebe:input source="=limit" target="limit"/>\n'
                 '          <zeebe:input source="=userId" target="userId"/>\n'
                 '          <zeebe:input source="=mood" target="mood"/>\n'
                 '          <zeebe:output source="=targets" target="targets"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Resolve</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Generate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Generate" sourceRef="Task_Resolve" '
                 'targetRef="Task_Generate"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Generate" name="generate translate and commit '
                 'guides">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="mediaGamers.guide.generate"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=targets" target="targets"/>\n'
                 '          <zeebe:input source="=translate" target="translate"/>\n'
                 '          <zeebe:input source="=publish" target="publish"/>\n'
                 '          <zeebe:output source="=results" target="results"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Generate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Generate" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit guide generation">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:media-gamers.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;media-gamers.guideGenerate&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ slug: string(slug), guideType: '
                 'string(guideType), results: results }" target="payload"/>\n'
                 '          <zeebe:output source="=rkey" target="auditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="guide committed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3673,
                 '00-contracts/bpmn/ai/gftd/media-gamers/guideGenerate.bpmn',
                 '2026-04-29T09:02:00Z',
                 'did:web:media-gamers.gftd.ai',
                 'did:web:media-gamers.gftd.ai',
                 'sys.bpmn.seed.media-gamers',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/media-gamers-guideGenerate-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/media-gamers-guideGenerate-v1',
                 'did:web:media-gamers.gftd.ai',
                 'ai.gftd.apps.media_gamers.guide.guideGenerate',
                 'media_gamers_guide_generate',
                 120000,
                 '2026-04-29T09:02:00Z',
                 'did:web:media-gamers.gftd.ai',
                 'did:web:media-gamers.gftd.ai',
                 'sys.bpmn.seed.media-gamers',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/media-gamers-guideGenerate-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/media-gamers-knowledgeGuideGenerate-v1',
                 'did:web:media-gamers.gftd.ai',
                 'media_gamers_knowledge_guide_generate',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_media_gamers_knowledge_guide_generate"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/media-gamers"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="media_gamers_knowledge_guide_generate" name="media gamers '
                 'knowledge guide generate" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="knowledge guide requested">\n'
                 '      <bpmn:outgoing>Flow_Generate</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Generate" sourceRef="Start" '
                 'targetRef="Task_Generate"/>\n'
                 '    <bpmn:serviceTask id="Task_Generate" name="generate and commit knowledge '
                 'guide">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="mediaGamers.knowledge.generateGuide"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=graph" target="graph"/>\n'
                 '          <zeebe:input source="=postAsGameDid" target="postAsGameDid"/>\n'
                 '          <zeebe:input source="=publish" target="publish"/>\n'
                 '          <zeebe:input source="=sourceQuery" target="sourceQuery"/>\n'
                 '          <zeebe:output source="=result" target="result"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Generate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Generate" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit knowledge guide">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:media-gamers.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;media-gamers.knowledgeGuideGenerate&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ sourceQuery: string(sourceQuery), result: '
                 'result }" target="payload"/>\n'
                 '          <zeebe:output source="=rkey" target="auditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="knowledge guide committed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2459,
                 '00-contracts/bpmn/ai/gftd/media-gamers/knowledgeGuideGenerate.bpmn',
                 '2026-04-29T09:02:00Z',
                 'did:web:media-gamers.gftd.ai',
                 'did:web:media-gamers.gftd.ai',
                 'sys.bpmn.seed.media-gamers',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/media-gamers-knowledgeGuideGenerate-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/media-gamers-knowledgeGuideGenerate-v1',
                 'did:web:media-gamers.gftd.ai',
                 'ai.gftd.apps.media_gamers.knowledge.knowledgeGuideGenerate',
                 'media_gamers_knowledge_guide_generate',
                 120000,
                 '2026-04-29T09:02:00Z',
                 'did:web:media-gamers.gftd.ai',
                 'did:web:media-gamers.gftd.ai',
                 'sys.bpmn.seed.media-gamers',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/media-gamers-knowledgeGuideGenerate-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/media-gamers-evalModels-v1',
                 'did:web:media-gamers.gftd.ai',
                 'media_gamers_eval_models',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_media_gamers_eval_models"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/media-gamers"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="media_gamers_eval_models" name="media gamers eval models" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="model eval requested">\n'
                 '      <bpmn:outgoing>Flow_Eval</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Eval" sourceRef="Start" targetRef="Task_Eval"/>\n'
                 '    <bpmn:serviceTask id="Task_Eval" name="evaluate guide model">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="mediaGamers.eval.models"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=result" target="result"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Eval</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Eval" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit model eval">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:media-gamers.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;media-gamers.evalModels&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ result: result }" target="payload"/>\n'
                 '          <zeebe:output source="=rkey" target="auditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="model eval committed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2052,
                 '00-contracts/bpmn/ai/gftd/media-gamers/evalModels.bpmn',
                 '2026-04-29T09:02:00Z',
                 'did:web:media-gamers.gftd.ai',
                 'did:web:media-gamers.gftd.ai',
                 'sys.bpmn.seed.media-gamers',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/media-gamers-evalModels-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/media-gamers-evalModels-v1',
                 'did:web:media-gamers.gftd.ai',
                 'ai.gftd.apps.media_gamers.evalModelsProcess',
                 'media_gamers_eval_models',
                 120000,
                 '2026-04-29T09:02:00Z',
                 'did:web:media-gamers.gftd.ai',
                 'did:web:media-gamers.gftd.ai',
                 'sys.bpmn.seed.media-gamers',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/media-gamers-evalModels-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/media-gamers-guideGenerate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/media-gamers-guideGenerate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/media-gamers-knowledgeGuideGenerate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/media-gamers-knowledgeGuideGenerate-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/media-gamers-evalModels-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/media-gamers-evalModels-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
