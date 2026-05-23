"""Captured from Kysely migration 20260429090800_seed_mangaka_standalone_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429090800_seed_mangaka_standalone_bpmn_actors"
down_revision = 'r_20260429090700_seed_comfyui_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-generateImageStandalone-v1',
                 'did:web:mangaka.etzhayyim.com',
                 'mangaka_generate_image_standalone',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Standalone mangaka image generation.\n'
                 '  Appview stays thin and dispatches this BPMN; Python Zeebe primitives handle\n'
                 '  ComfyUI invocation, blob upload, and audit.\n'
                 '  in:  prompt, style?\n'
                 '  out: blobCid, meta, latencyMs\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_mangaka_generate_image_standalone"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/mangaka"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="mangaka_generate_image_standalone" name="mangaka standalone '
                 'image generation" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="image requested">\n'
                 '      <bpmn:outgoing>F1</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="F1" sourceRef="Start" targetRef="Task_Render"/>\n'
                 '    <bpmn:serviceTask id="Task_Render" name="render manga panel">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.comfyui.call"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;/v1/images/generations&quot;" '
                 'target="route"/>\n'
                 '          <zeebe:input source="={\n'
                 '              prompt: (if prompt = null then &quot;manga panel '
                 'illustration&quot; else string(prompt)) + &quot;, &quot; + (if style = null then '
                 '&quot;manga&quot; else string(style)) + &quot; manga panel, black and white ink, '
                 'high contrast, clean line art, screentone shading, professional manga art, no '
                 'text, no watermark&quot;,\n'
                 '              negative_prompt: &quot;color, photograph, text, watermark, '
                 'signature, blurry, low quality, jpeg artifacts, extra limbs&quot;,\n'
                 '              size: &quot;832x1216&quot;,\n'
                 '              steps: 24,\n'
                 '              cfg_scale: 6.0,\n'
                 '              n: 1\n'
                 '          }" target="body"/>\n'
                 '          <zeebe:input source="=&quot;binary&quot;" target="outputFormat"/>\n'
                 '          <zeebe:input source="=180" target="timeoutSec"/>\n'
                 '          <zeebe:output source="=blobCid" target="blobCid"/>\n'
                 '          <zeebe:output source="=meta" target="meta"/>\n'
                 '          <zeebe:output source="=latencyMs" target="latencyMs"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F2" sourceRef="Task_Render" targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:mangaka.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;generateImage&quot;" target="action"/>\n'
                 '          <zeebe:input source="={prompt: string(prompt), style: (if style = null '
                 'then &quot;manga&quot; else string(style)), blobCid: string(blobCid), latencyMs: '
                 'latencyMs}" target="payload"/>\n'
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
                 3241,
                 '00-contracts/bpmn/ai/gftd/mangaka/generateImageStandalone.bpmn',
                 '2026-04-29T09:08:00Z',
                 'did:web:mangaka.etzhayyim.com',
                 'did:web:mangaka.etzhayyim.com',
                 'sys.bpmn.seed.mangaka.standalone',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-generateImageStandalone-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-generateImageStandalone-v1',
                 'did:web:mangaka.etzhayyim.com',
                 'ai.gftd.apps.mangaka.generateImage',
                 'mangaka_generate_image_standalone',
                 600000,
                 '2026-04-29T09:08:00Z',
                 'did:web:mangaka.etzhayyim.com',
                 'did:web:mangaka.etzhayyim.com',
                 'sys.bpmn.seed.mangaka.standalone',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-generateImageStandalone-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-realtimeDraw-v1',
                 'did:web:mangaka.etzhayyim.com',
                 'mangaka_realtime_draw',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Standalone sketch-to-image. Heavy base64/image handling is delegated to\n'
                 '  the Zeebe Python ComfyUI primitive instead of the appview Worker.\n'
                 '  in:  sketchBase64, prompt?, strength?, steps?\n'
                 '  out: blobCid, meta, latencyMs\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_mangaka_realtime_draw"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/mangaka"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="mangaka_realtime_draw" name="mangaka realtime sketch to '
                 'image" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="sketch requested">\n'
                 '      <bpmn:outgoing>F1</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="F1" sourceRef="Start" targetRef="Task_Render"/>\n'
                 '    <bpmn:serviceTask id="Task_Render" name="render sketch img2img">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.comfyui.call"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;/v1/images/edits&quot;" target="route"/>\n'
                 '          <zeebe:input source="={\n'
                 '              image: string(sketchBase64),\n'
                 '              prompt: if prompt = null then &quot;1girl, masterpiece, best '
                 'quality, anime, manga style&quot; else string(prompt),\n'
                 '              negative_prompt: &quot;lowres, bad anatomy, bad hands, text, '
                 'watermark, blurry, jpeg artifacts, extra limbs&quot;,\n'
                 '              strength: if strength = null then 0.7 else strength,\n'
                 '              steps: if steps = null then 20 else steps\n'
                 '          }" target="body"/>\n'
                 '          <zeebe:input source="=&quot;binary&quot;" target="outputFormat"/>\n'
                 '          <zeebe:input source="=180" target="timeoutSec"/>\n'
                 '          <zeebe:output source="=blobCid" target="blobCid"/>\n'
                 '          <zeebe:output source="=meta" target="meta"/>\n'
                 '          <zeebe:output source="=latencyMs" target="latencyMs"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F2" sourceRef="Task_Render" targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:mangaka.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;realtimeDraw&quot;" target="action"/>\n'
                 '          <zeebe:input source="={blobCid: string(blobCid), latencyMs: latencyMs, '
                 'strength: (if strength = null then 0.7 else strength), steps: (if steps = null '
                 'then 20 else steps)}" target="payload"/>\n'
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
                 3064,
                 '00-contracts/bpmn/ai/gftd/mangaka/realtimeDraw.bpmn',
                 '2026-04-29T09:08:00Z',
                 'did:web:mangaka.etzhayyim.com',
                 'did:web:mangaka.etzhayyim.com',
                 'sys.bpmn.seed.mangaka.standalone',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-realtimeDraw-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-realtimeDraw-v1',
                 'did:web:mangaka.etzhayyim.com',
                 'ai.gftd.apps.mangaka.realtimeDraw',
                 'mangaka_realtime_draw',
                 600000,
                 '2026-04-29T09:08:00Z',
                 'did:web:mangaka.etzhayyim.com',
                 'did:web:mangaka.etzhayyim.com',
                 'sys.bpmn.seed.mangaka.standalone',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-realtimeDraw-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-storyboardStandalone-v1',
                 'did:web:mangaka.etzhayyim.com',
                 'mangaka_storyboard_standalone',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Standalone storyboard director. Appview dispatches only; Python Zeebe LLM\n'
                 '  primitive handles JSON generation and parsing.\n'
                 '  in:  story\n'
                 '  out: storyboardData\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_mangaka_storyboard_standalone"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/mangaka"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="mangaka_storyboard_standalone" name="mangaka standalone '
                 'storyboard" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="storyboard requested">\n'
                 '      <bpmn:outgoing>F1</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="F1" sourceRef="Start" targetRef="Task_Storyboard"/>\n'
                 '    <bpmn:serviceTask id="Task_Storyboard" name="draft panel prompts">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.llm.json"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;classifier&quot;" target="tier"/>\n'
                 '          <zeebe:input source="=&quot;You are a professional manga storyboard '
                 'director. Break the story into 4-6 manga panels. Output ONE JSON object '
                 '{panels:[{prompt:string}]} only. Each prompt must describe pose, camera angle, '
                 'expression, background, and action. No prose outside JSON.&quot;" '
                 'target="system"/>\n'
                 '          <zeebe:input source="=string(story)" target="user"/>\n'
                 '          <zeebe:input source="=1000" target="maxTokens"/>\n'
                 '          <zeebe:input source="=0.4" target="temperature"/>\n'
                 '          <zeebe:output source="=data" target="storyboardData"/>\n'
                 '          <zeebe:output source="=model" target="model"/>\n'
                 '          <zeebe:output source="=latencyMs" target="latencyMs"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F2" sourceRef="Task_Storyboard" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:mangaka.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;storyboard&quot;" target="action"/>\n'
                 '          <zeebe:input source="={model: string(model), latencyMs: latencyMs}" '
                 'target="payload"/>\n'
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
                 2790,
                 '00-contracts/bpmn/ai/gftd/mangaka/storyboardStandalone.bpmn',
                 '2026-04-29T09:08:00Z',
                 'did:web:mangaka.etzhayyim.com',
                 'did:web:mangaka.etzhayyim.com',
                 'sys.bpmn.seed.mangaka.standalone',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-storyboardStandalone-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-storyboardStandalone-v1',
                 'did:web:mangaka.etzhayyim.com',
                 'ai.gftd.apps.mangaka.storyboard',
                 'mangaka_storyboard_standalone',
                 180000,
                 '2026-04-29T09:08:00Z',
                 'did:web:mangaka.etzhayyim.com',
                 'did:web:mangaka.etzhayyim.com',
                 'sys.bpmn.seed.mangaka.standalone',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-storyboardStandalone-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-autoLayoutStandalone-v1',
                 'did:web:mangaka.etzhayyim.com',
                 'mangaka_auto_layout_standalone',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Standalone manga page auto-layout.\n'
                 '  Appview dispatches only; Python Zeebe generic LLM JSON primitive builds the\n'
                 '  suggested panel geometry.\n'
                 '  in:  pageId, panelCount?, style?\n'
                 '  out: layoutData, model, latencyMs\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_mangaka_auto_layout_standalone"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/mangaka"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="mangaka_auto_layout_standalone" name="mangaka standalone '
                 'auto layout" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="layout requested">\n'
                 '      <bpmn:outgoing>F1</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="F1" sourceRef="Start" targetRef="Task_Layout"/>\n'
                 '    <bpmn:serviceTask id="Task_Layout" name="generate panel layout">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.llm.json"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;classifier&quot;" target="tier"/>\n'
                 '          <zeebe:input source="=&quot;Generate manga page panel layout JSON '
                 'only. Page size is 2480x3508. Output ONE JSON object '
                 '{panels:[{x:number,y:number,w:number,h:number,order:number}]}. Vary panel sizes '
                 'for dynamic koma-wari while keeping panels within page bounds.&quot;" '
                 'target="system"/>\n'
                 '          <zeebe:input source="=&quot;pageId: &quot; + string(pageId) + '
                 '&quot;\\npanelCount: &quot; + string(if panelCount = null then 5 else '
                 'panelCount) + &quot;\\nstyle: &quot; + (if style = null then '
                 '&quot;standard&quot; else string(style))" target="user"/>\n'
                 '          <zeebe:input source="=700" target="maxTokens"/>\n'
                 '          <zeebe:input source="=0.2" target="temperature"/>\n'
                 '          <zeebe:output source="=data" target="layoutData"/>\n'
                 '          <zeebe:output source="=model" target="model"/>\n'
                 '          <zeebe:output source="=latencyMs" target="latencyMs"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F2" sourceRef="Task_Layout" targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:mangaka.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;autoLayout&quot;" target="action"/>\n'
                 '          <zeebe:input source="={pageId: string(pageId), panelCount: (if '
                 'panelCount = null then 5 else panelCount), style: (if style = null then '
                 '&quot;standard&quot; else string(style)), model: string(model), latencyMs: '
                 'latencyMs}" target="payload"/>\n'
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
                 3162,
                 '00-contracts/bpmn/ai/gftd/mangaka/autoLayoutStandalone.bpmn',
                 '2026-04-29T09:08:00Z',
                 'did:web:mangaka.etzhayyim.com',
                 'did:web:mangaka.etzhayyim.com',
                 'sys.bpmn.seed.mangaka.standalone',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-autoLayoutStandalone-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-autoLayoutStandalone-v1',
                 'did:web:mangaka.etzhayyim.com',
                 'ai.gftd.apps.mangaka.autoLayout',
                 'mangaka_auto_layout_standalone',
                 180000,
                 '2026-04-29T09:08:00Z',
                 'did:web:mangaka.etzhayyim.com',
                 'did:web:mangaka.etzhayyim.com',
                 'sys.bpmn.seed.mangaka.standalone',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-autoLayoutStandalone-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-projectChatStandalone-v1',
                 'did:web:mangaka.etzhayyim.com',
                 'mangaka_project_chat_standalone',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Standalone project chat. Appview dispatches only; Python Zeebe generic LLM\n'
                 '  primitive handles generation outside the Worker.\n'
                 '  in:  projectId?, message\n'
                 '  out: reply, model, latencyMs\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_mangaka_project_chat_standalone"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/mangaka"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="mangaka_project_chat_standalone" name="mangaka standalone '
                 'project chat" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="chat requested">\n'
                 '      <bpmn:outgoing>F1</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="F1" sourceRef="Start" targetRef="Task_Chat"/>\n'
                 '    <bpmn:serviceTask id="Task_Chat" name="chat">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.llm.chat"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;classifier&quot;" target="tier"/>\n'
                 '          <zeebe:input source="=&quot;You are Mangaka AI, a manga creation '
                 'assistant. Help with story, character design, panel layout, and art direction. '
                 'Reply in the user\'s language. Be concrete and concise.&quot;" '
                 'target="system"/>\n'
                 '          <zeebe:input source="=if projectId = null then string(message) else '
                 '(&quot;Project ID: &quot; + string(projectId) + &quot;\\nUser: &quot; + '
                 'string(message))" target="user"/>\n'
                 '          <zeebe:input source="=700" target="maxTokens"/>\n'
                 '          <zeebe:input source="=0.4" target="temperature"/>\n'
                 '          <zeebe:output source="=content" target="reply"/>\n'
                 '          <zeebe:output source="=model" target="model"/>\n'
                 '          <zeebe:output source="=latencyMs" target="latencyMs"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F2" sourceRef="Task_Chat" targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:mangaka.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;projectChat&quot;" target="action"/>\n'
                 '          <zeebe:input source="={projectId: (if projectId = null then '
                 '&quot;&quot; else string(projectId)), model: string(model), latencyMs: '
                 'latencyMs}" target="payload"/>\n'
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
                 2893,
                 '00-contracts/bpmn/ai/gftd/mangaka/projectChatStandalone.bpmn',
                 '2026-04-29T09:08:00Z',
                 'did:web:mangaka.etzhayyim.com',
                 'did:web:mangaka.etzhayyim.com',
                 'sys.bpmn.seed.mangaka.standalone',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-projectChatStandalone-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-projectChatStandalone-v1',
                 'did:web:mangaka.etzhayyim.com',
                 'ai.gftd.apps.mangaka.projectChat',
                 'mangaka_project_chat_standalone',
                 180000,
                 '2026-04-29T09:08:00Z',
                 'did:web:mangaka.etzhayyim.com',
                 'did:web:mangaka.etzhayyim.com',
                 'sys.bpmn.seed.mangaka.standalone',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-projectChatStandalone-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-generateImageStandalone-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-generateImageStandalone-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-realtimeDraw-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-realtimeDraw-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-storyboardStandalone-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-storyboardStandalone-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-autoLayoutStandalone-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-autoLayoutStandalone-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/mangaka-projectChatStandalone-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/mangaka-projectChatStandalone-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
