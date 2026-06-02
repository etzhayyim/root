"""Captured from Kysely migration 20260508970000_activate_ki_saikin_webmk_newsletter_bpmns."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508970000_activate_ki_saikin_webmk_newsletter_bpmns"
down_revision = 'r_20260508960000_retire_yoro_platform_pulse_zeebe_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'active'\n"
         '      WHERE bpmn_process_id = $1\n'
         "        AND status = 'inactive'\n"
         '    ',
  'parameters': ['ki_vascular_synthesis_cycle']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'active'\n"
         '      WHERE bpmn_process_id = $1\n'
         "        AND status = 'inactive'\n"
         '    ',
  'parameters': ['saikin_horizontal_transfer_cycle']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'active'\n"
         '      WHERE bpmn_process_id = $1\n'
         "        AND status = 'inactive'\n"
         '    ',
  'parameters': ['webmk_create_proposal']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         "      $1, $2, 'newsletter_weekly_send', 1,\n"
         '      $3, CAST($4 AS integer),\n'
         "      $5, 'active', $6,\n"
         "      1, $7, $8, 'sys.bpmn.seed.newsletter'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/newsletter-weeklySend-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_newsletter_weekly_send" '
                 'targetNamespace="https://etzhayyim.com/bpmn/newsletter">\n'
                 '  <bpmn:process id="newsletter_weekly_send" name="newsletter weeklySend" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>{ "nsid": "com.etzhayyim.apps.newsletter.weeklySend", '
                 '"version": 1, "schedule": "0 0 * * 2", "tz": "Asia/Tokyo", "adr": '
                 '"2605072000-langgraph-agent-loop-pattern" }</bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent>\n'
                 '\n'
                 '    <!-- Step 1: LangGraph curation loop -->\n'
                 '    <bpmn:sequenceFlow id="F1" sourceRef="Start" targetRef="RunCurationAgent"/>\n'
                 '    <bpmn:serviceTask id="RunCurationAgent" name="Run LangGraph curation '
                 'agent">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="newsletter.run_curation_agent" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Step 2: Resend batch send -->\n'
                 '    <bpmn:sequenceFlow id="F2" sourceRef="RunCurationAgent" '
                 'targetRef="SendViaResend"/>\n'
                 '    <bpmn:serviceTask id="SendViaResend" name="Batch send via Resend">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="newsletter.send_via_resend" retries="3"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F2</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F3</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Step 3: Optionally create ads.etzhayyim.com sponsor slot -->\n'
                 '    <bpmn:sequenceFlow id="F3" sourceRef="SendViaResend" '
                 'targetRef="AdGateway"/>\n'
                 '    <bpmn:exclusiveGateway id="AdGateway" name="includeAdSlot?">\n'
                 '      <bpmn:incoming>F3</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F4_yes</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>F4_no</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="F4_yes" sourceRef="AdGateway" '
                 'targetRef="CreateSponsorSlot">\n'
                 '      <bpmn:conditionExpression>=includeAdSlot = '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:serviceTask id="CreateSponsorSlot" name="Create ads.etzhayyim.com sponsor '
                 'slot">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="newsletter.create_sponsor_slot" '
                 'retries="2"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>F4_yes</bpmn:incoming>\n'
                 '      <bpmn:outgoing>F5</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="F4_no" sourceRef="AdGateway" targetRef="End">\n'
                 '      <bpmn:conditionExpression>=includeAdSlot != '
                 'true</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="F5" sourceRef="CreateSponsorSlot" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>F4_no</bpmn:incoming>\n'
                 '      <bpmn:incoming>F5</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2867,
                 '00-contracts/bpmn/com/etzhayyim/newsletter/weeklySend.bpmn',
                 '2026-05-08T09:45:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/newsletter-weeklySend-v1']}]

DOWN = [{'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'inactive'\n"
         '      WHERE bpmn_process_id = $1\n'
         '    ',
  'parameters': ['ki_vascular_synthesis_cycle']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'inactive'\n"
         '      WHERE bpmn_process_id = $1\n'
         '    ',
  'parameters': ['saikin_horizontal_transfer_cycle']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'inactive'\n"
         '      WHERE bpmn_process_id = $1\n'
         '    ',
  'parameters': ['webmk_create_proposal']},
 {'sql': '\n'
         '    DELETE FROM vertex_bpmn_process_def\n'
         '    WHERE vertex_id = '
         "'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/newsletter-weeklySend-v1'\n"
         '  ',
  'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
