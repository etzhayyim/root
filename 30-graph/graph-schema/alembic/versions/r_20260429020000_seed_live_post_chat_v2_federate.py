"""Captured from Kysely migration 20260429020000_seed_live_post_chat_v2_federate."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429020000_seed_live_post_chat_v2_federate"
down_revision = 'r_20260429010000_seed_apps_live_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         "      $1, $2, 'live_post_chat', 2,\n"
         "      $3, CAST($4 AS integer), $5, 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/apps-live-post-chat-v2',
                 'did:web:live.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  ai.gftd.apps.live.postChat — append an actor utterance to a live room.\n'
                 '\n'
                 '  Three-task flow:\n'
                 '    1. generic.db.insert  → vertex_live_chat (Tier 2 Domain write)\n'
                 '    2. generic.pds.dispatch → app.bsky.feed.post as actorDid (Tier 1\n'
                 '       Social write — federation via AT Protocol firehose)\n'
                 '    3. generic.audit.emit → live.postChat (audit trail)\n'
                 '\n'
                 '  RLS shape per ADR-0095. The federation step is best-effort: a 4xx\n'
                 '  from atproto.etzhayyim.com (e.g. unmintable Service Auth for the actor)\n'
                 "  doesn't roll back the local chat row — viewers still see the bubble\n"
                 '  via the WebSocket fan-out from the DO.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_live_post_chat"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/apps/live"\n'
                 '    exporter="hand-written" exporterVersion="1.1">\n'
                 '  <bpmn:process id="live_post_chat" name="live postChat" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '\n'
                 '    <!-- 1. Tier 2 Domain write — vertex_live_chat. -->\n'
                 '    <bpmn:serviceTask id="Task_Save" name="vertex_live_chat insert">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_live_chat&quot;" target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: &quot;at://&quot; + string(actorDid) + '
                 '&quot;/ai.gftd.apps.live.chat/&quot; + string(now()) + &quot;-&quot; + '
                 'string(actorDid),\n'
                 '              room_slug: roomSlug,\n'
                 '              actor_handle: handle,\n'
                 '              text: text,\n'
                 '              kind: kind,\n'
                 '              tint_r: if tint != null then tint[1] else null,\n'
                 '              tint_g: if tint != null then tint[2] else null,\n'
                 '              tint_b: if tint != null then tint[3] else null,\n'
                 '              posted_at: now(),\n'
                 '              name: string(handle) + &quot;: &quot; + string(text),\n'
                 '              description: text,\n'
                 '              actor_did: actorDid,\n'
                 '              org_did: if orgDid != null then orgDid else &quot;anon&quot;,\n'
                 '              at_did: actorDid,\n'
                 '              created_at: string(now())\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=true" target="accepted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_F</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_F" sourceRef="Task_Save" '
                 'targetRef="Task_Federate"/>\n'
                 '\n'
                 '    <!-- 2. Tier 1 Social write — app.bsky.feed.post as actorDid.\n'
                 '         The post text is prefixed with the room handle so the\n'
                 '         federation feed makes context-free sense. Best-effort:\n'
                 '         retries=0 keeps the chat fan-out fast and avoids reposting\n'
                 '         duplicates if the worker re-activates after timeout. -->\n'
                 '    <bpmn:serviceTask id="Task_Federate" name="app.bsky.feed.post (as actor)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.pds.dispatch" retries="0"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;app.bsky.feed.post&quot;" target="type"/>\n'
                 '          <zeebe:input source="=actorDid" target="callerDid"/>\n'
                 '          <zeebe:input source="={\n'
                 '              repo: actorDid,\n'
                 '              record: {\n'
                 '                  &quot;$type&quot;: &quot;app.bsky.feed.post&quot;,\n'
                 '                  text: &quot;[live:&quot; + string(roomSlug) + &quot;] &quot; + '
                 'string(text),\n'
                 '                  createdAt: string(now()),\n'
                 '                  langs: [&quot;ja&quot;],\n'
                 '                  labels: {\n'
                 '                      &quot;$type&quot;: '
                 '&quot;com.atproto.label.defs#selfLabels&quot;,\n'
                 '                      values: [{ val: &quot;live-room-chat&quot; }]\n'
                 '                  }\n'
                 '              }\n'
                 '          }" target="payload"/>\n'
                 '          <zeebe:output source="=body.uri" target="federatedUri"/>\n'
                 '          <zeebe:output source="=status" target="federatedStatus"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_F</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Federate" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <!-- 3. Audit. Captures the federation status for observability. -->\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit live.postChat">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:live.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;live.postChat&quot;" target="action"/>\n'
                 '          <zeebe:input source="={\n'
                 '              roomSlug: roomSlug,\n'
                 '              actorDid: actorDid,\n'
                 '              kind: kind,\n'
                 '              federatedUri: federatedUri,\n'
                 '              federatedStatus: federatedStatus\n'
                 '          }" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5459,
                 '00-contracts/bpmn/ai/gftd/apps/live/postChat.bpmn',
                 '2026-04-29T02:00:00Z',
                 'did:web:live.etzhayyim.com',
                 'did:web:live.etzhayyim.com',
                 'sys.bpmn.seed.live.v2',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/apps-live-post-chat-v2']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_process_def\n'
         "    SET status = 'superseded'\n"
         "    WHERE bpmn_process_id = 'live_post_chat'\n"
         '      AND version = 1\n'
         "      AND status = 'active'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET bpmn_version = 2,\n'
         '        result_timeout_ms = CAST(15000 AS integer)\n'
         '    WHERE vertex_id = $1\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/apps-live-postChat-v1']}]

DOWN = [{'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET bpmn_version = 1,\n'
         '        result_timeout_ms = CAST(5000 AS integer)\n'
         '    WHERE vertex_id = $1\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/apps-live-postChat-v1']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_process_def\n'
         "    SET status = 'active'\n"
         "    WHERE bpmn_process_id = 'live_post_chat'\n"
         '      AND version = 1\n'
         '  ',
  'parameters': []},
 {'sql': '\n    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/apps-live-post-chat-v2']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
