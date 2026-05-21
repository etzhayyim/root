"""Captured from Kysely migration 20260429090700_seed_comfyui_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429090700_seed_comfyui_bpmn_actors"
down_revision = 'r_20260429090600_seed_livecam_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/comfyui-generateImage-v1',
                 'did:web:comfyui.etzhayyim.com',
                 'comfyui_openai_image_generation',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_comfyui_openai_image_generation"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/comfyui"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="comfyui_openai_image_generation" name="comfyui OpenAI image '
                 'generation" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="image generation requested">\n'
                 '      <bpmn:outgoing>Flow_Generate</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Generate" sourceRef="Start" '
                 'targetRef="Task_Generate"/>\n'
                 '    <bpmn:serviceTask id="Task_Generate" name="generate image via ComfyUI">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="comfyui.openai.generateImage"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=request" target="request"/>\n'
                 '          <zeebe:output source="=result" target="result"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Generate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Generate" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit ComfyUI generation">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:comfyui.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;comfyui.generateImage&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ result: result }" target="payload"/>\n'
                 '          <zeebe:output source="=rkey" target="auditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="image generation completed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2176,
                 '00-contracts/bpmn/ai/gftd/comfyui/generateImage.bpmn',
                 '2026-04-29T09:07:00Z',
                 'did:web:comfyui.etzhayyim.com',
                 'did:web:comfyui.etzhayyim.com',
                 'sys.bpmn.seed.comfyui',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/comfyui-generateImage-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/comfyui-generateImage-v1',
                 'did:web:comfyui.etzhayyim.com',
                 'ai.gftd.apps.comfyui.generateImage',
                 'comfyui_openai_image_generation',
                 600000,
                 '2026-04-29T09:07:00Z',
                 'did:web:comfyui.etzhayyim.com',
                 'did:web:comfyui.etzhayyim.com',
                 'sys.bpmn.seed.comfyui',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/comfyui-generateImage-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/comfyui-editImage-v1',
                 'did:web:comfyui.etzhayyim.com',
                 'comfyui_openai_image_edit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_comfyui_openai_image_edit"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/comfyui"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="comfyui_openai_image_edit" name="comfyui OpenAI image edit" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="image edit requested">\n'
                 '      <bpmn:outgoing>Flow_Edit</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Edit" sourceRef="Start" targetRef="Task_Edit"/>\n'
                 '    <bpmn:serviceTask id="Task_Edit" name="edit image via ComfyUI">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="comfyui.openai.editImage"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=request" target="request"/>\n'
                 '          <zeebe:output source="=result" target="result"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Edit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Edit" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit ComfyUI edit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:comfyui.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;comfyui.editImage&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ result: result }" target="payload"/>\n'
                 '          <zeebe:output source="=rkey" target="auditRkey"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Audit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="image edit completed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2104,
                 '00-contracts/bpmn/ai/gftd/comfyui/editImage.bpmn',
                 '2026-04-29T09:07:00Z',
                 'did:web:comfyui.etzhayyim.com',
                 'did:web:comfyui.etzhayyim.com',
                 'sys.bpmn.seed.comfyui',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/comfyui-editImage-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/comfyui-editImage-v1',
                 'did:web:comfyui.etzhayyim.com',
                 'ai.gftd.apps.comfyui.editImage',
                 'comfyui_openai_image_edit',
                 600000,
                 '2026-04-29T09:07:00Z',
                 'did:web:comfyui.etzhayyim.com',
                 'did:web:comfyui.etzhayyim.com',
                 'sys.bpmn.seed.comfyui',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/comfyui-editImage-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/comfyui-generateImage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/comfyui-generateImage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/comfyui-editImage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/comfyui-editImage-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
