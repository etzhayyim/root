"""Captured from Kysely migration 20260508000000_seed_webmk_newsletter_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508000000_seed_webmk_newsletter_bpmn"
down_revision = 'r_20260508000000_kyber_billing'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/webmk-createProposal-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'webmk_create_proposal',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
                 'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
                 'id="Definitions_webmk_create_proposal" '
                 'targetNamespace="https://etzhayyim.com/bpmn/webmk">\n'
                 '  <bpmn:process id="webmk_create_proposal" name="webmk createProposal" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "ai.gftd.apps.webmk.createProposal", '
                 '"version": 1, "resultTimeoutMs": 180000, "adr": '
                 '"2605072000-langgraph-agent-loop-pattern" }</bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>F1</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <!-- Step 1: LangGraph agent loop (research → competitors → strategy → copy '
                 '→ quality gate) -->\n'
                 '    <bpmn:sequenceFlow id="F1" sourceRef="Start" targetRef="RunAgentLoop"/>\n'
                 '    <bpmn:serviceTask id="RunAgentLoop" name="Run LangGraph proposal agent">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="webmk.run_proposal_agent" retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Step 2: Deliver via Resend -->\n'
                 '    <bpmn:sequenceFlow id="F2" sourceRef="RunAgentLoop" '
                 'targetRef="DeliverEmail"/>\n'
                 '    <bpmn:serviceTask id="DeliverEmail" name="Deliver proposal via Resend">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="webmk.deliver_via_resend" retries="3"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F2</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F3</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Step 3: Optionally create ads.etzhayyim.com campaign -->\n'
                 '    <bpmn:sequenceFlow id="F3" sourceRef="DeliverEmail" '
                 'targetRef="CampaignGateway"/>\n'
                 '    <bpmn:exclusiveGateway id="CampaignGateway" name="createAdCampaign?">\n'
                 '      <bpmn:incoming>F3</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F4_yes</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>F4_no</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="F4_yes" sourceRef="CampaignGateway" '
                 'targetRef="CreateAdCampaign">\n'
                 '      <bpmn:conditionExpression>=createAdCampaign = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:serviceTask id="CreateAdCampaign" name="Create ads.etzhayyim.com campaign">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="webmk.create_ad_campaign" retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F4_yes</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F5</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F4_no" sourceRef="CampaignGateway" targetRef="End">\n'
                 '      <bpmn:conditionExpression>=createAdCampaign != '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="F5" sourceRef="CreateAdCampaign" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>F4_no</bpmn:incoming>\n'
                 '      <bpmn:incoming>F5</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3022,
                 '00-contracts/bpmn/ai/gftd/webmk/createProposal.bpmn',
                 '2026-05-08T00:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/webmk-createProposal-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/webmk-deliverProposal-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'webmk_deliver_proposal',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_webmk_deliver_proposal" '
                 'targetNamespace="https://etzhayyim.com/bpmn/webmk">\n'
                 '  <bpmn:process id="webmk_deliver_proposal" name="webmk deliverProposal" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "ai.gftd.apps.webmk.deliverProposal", '
                 '"version": 1, "resultTimeoutMs": 60000 }</bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="F1" sourceRef="Start" targetRef="Task"/>\n'
                 '    <bpmn:serviceTask id="Task" name="re-deliver via Resend">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="webmk.deliver_via_resend" retries="3"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F2" sourceRef="Task" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1117,
                 '00-contracts/bpmn/ai/gftd/webmk/deliverProposal.bpmn',
                 '2026-05-08T00:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/webmk-deliverProposal-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/newsletter-sendCampaign-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'newsletter_send_campaign',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_newsletter_send_campaign" '
                 'targetNamespace="https://etzhayyim.com/bpmn/newsletter">\n'
                 '  <bpmn:process id="newsletter_send_campaign" name="newsletter sendCampaign" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "ai.gftd.apps.newsletter.sendCampaign", '
                 '"version": 1, "resultTimeoutMs": 120000 }</bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="F1" sourceRef="Start" targetRef="Task"/>\n'
                 '    <bpmn:serviceTask id="Task" name="send curated campaign">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="newsletter.send_via_resend" retries="3"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F2" sourceRef="Task" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1133,
                 '00-contracts/bpmn/ai/gftd/newsletter/sendCampaign.bpmn',
                 '2026-05-08T00:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/newsletter-sendCampaign-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id, routing_target)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/webmk-createProposal-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'ai.gftd.apps.webmk.createProposal',
                 'webmk_create_proposal',
                 180000,
                 '2026-05-08T00:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'langgraph',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/webmk-createProposal-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id, routing_target)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/webmk-deliverProposal-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'ai.gftd.apps.webmk.deliverProposal',
                 'webmk_deliver_proposal',
                 60000,
                 '2026-05-08T00:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'zeebe',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/webmk-deliverProposal-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id, routing_target)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/newsletter-sendCampaign-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'ai.gftd.apps.newsletter.sendCampaign',
                 'newsletter_send_campaign',
                 60000,
                 '2026-05-08T00:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'zeebe',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/newsletter-sendCampaign-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/webmk-createProposal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/webmk-deliverProposal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/newsletter-sendCampaign-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/webmk-createProposal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/webmk-deliverProposal-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/newsletter-sendCampaign-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
