"""Captured from Kysely migration 20260429010000_seed_apps_live_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429010000_seed_apps_live_bpmn_actors"
down_revision = 'r_20260429000000_vertex_live_room_chat'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/apps-live-post-chat-v1',
                 'did:web:live.etzhayyim.com',
                 'live_post_chat',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  app.etzhayyim.apps.live.postChat — append an actor utterance to a live room.\n'
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
                 '&quot;/app.etzhayyim.apps.live.chat/&quot; + string(now()) + &quot;-&quot; + '
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
                 '2026-04-29T01:00:00Z',
                 'did:web:live.etzhayyim.com',
                 'did:web:live.etzhayyim.com',
                 'sys.bpmn.seed.live',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/apps-live-post-chat-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/apps-live-schedule-set-v1',
                 'did:web:live.etzhayyim.com',
                 'live_schedule_set',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  app.etzhayyim.apps.live.scheduleSet — performer authors / replaces a room.\n'
                 '\n'
                 '  Single-task flow. Upserts (insert with `on conflict ignore` semantics\n'
                 '  via PK rewrite) into `vertex_live_room`. RisingWave overwrites on\n'
                 '  duplicate PK so this is effectively a put.\n'
                 '\n'
                 '  RLS shape per ADR-0095.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_live_schedule_set"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/apps/live"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="live_schedule_set" name="live scheduleSet" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="vertex_live_room upsert">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_live_room&quot;" target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: &quot;at://&quot; + string(performerDid) + '
                 '&quot;/app.etzhayyim.apps.live.room/&quot; + string(roomSlug),\n'
                 '              slug: roomSlug,\n'
                 '              bpm: bpm,\n'
                 '              start_at: startAt,\n'
                 '              stage_preset: stagePreset,\n'
                 '              performer_handle: performerHandle,\n'
                 '              setlist_json: setlistJson,\n'
                 '              lighting_json: lightingJson,\n'
                 '              crowd_seed: crowdSeed,\n'
                 '              fans_target: fansTarget,\n'
                 '              name: string(roomSlug) + &quot; — &quot; + string(stagePreset),\n'
                 '              description: &quot;Live virtual concert room scheduled by &quot; + '
                 'string(performerHandle),\n'
                 '              actor_did: performerDid,\n'
                 '              org_did: if orgDid != null then orgDid else &quot;anon&quot;,\n'
                 '              at_did: performerDid,\n'
                 '              created_at: string(now())\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=&quot;scheduled&quot;" target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit live.scheduleSet">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:live.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;live.scheduleSet&quot;" target="action"/>\n'
                 '          <zeebe:input source="={ roomSlug: roomSlug, bpm: bpm, stagePreset: '
                 'stagePreset }" target="payload"/>\n'
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
                 3303,
                 '00-contracts/bpmn/ai/gftd/apps/live/scheduleSet.bpmn',
                 '2026-04-29T01:00:00Z',
                 'did:web:live.etzhayyim.com',
                 'did:web:live.etzhayyim.com',
                 'sys.bpmn.seed.live',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/apps-live-schedule-set-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/apps-live-send-cheer-v1',
                 'did:web:live.etzhayyim.com',
                 'live_send_cheer',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  app.etzhayyim.apps.live.sendCheer — viewer cheer event.\n'
                 '\n'
                 '  Single-task flow. Cheers are append-only into vertex_live_chat with\n'
                 '  kind = "cheer-{originalKind}" so the existing chat fan-out picks\n'
                 '  them up alongside actor utterances. The text becomes the cheer kind\n'
                 '  badge ("CLAP!" / "YELL!" / etc) so screen readers / archival\n'
                 '  consumers see something readable.\n'
                 '\n'
                 '  RLS shape per ADR-0095. Anonymous viewers ride on actor_did = "anon".\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_live_send_cheer"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/apps/live"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="live_send_cheer" name="live sendCheer" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="vertex_live_chat insert (cheer)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_live_chat&quot;" target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: &quot;at://&quot; + (if callerDid != null then '
                 'string(callerDid) else &quot;anon&quot;) + &quot;/app.etzhayyim.apps.live.cheer/&quot; '
                 '+ string(now()),\n'
                 '              room_slug: roomSlug,\n'
                 '              actor_handle: if callerDid != null then string(callerDid) else '
                 '&quot;anon&quot;,\n'
                 '              text: upper case(string(kind)) + &quot;!&quot;,\n'
                 '              kind: &quot;cheer-&quot; + string(kind),\n'
                 '              tint_r: null,\n'
                 '              tint_g: null,\n'
                 '              tint_b: null,\n'
                 '              posted_at: now(),\n'
                 '              name: &quot;cheer:&quot; + string(kind),\n'
                 '              description: &quot;weight=&quot; + string(if weight != null then '
                 'weight else 1.0),\n'
                 '              actor_did: if callerDid != null then callerDid else '
                 '&quot;did:web:live.etzhayyim.com:viewer:anon&quot;,\n'
                 '              org_did: if orgDid != null then orgDid else &quot;anon&quot;,\n'
                 '              at_did: callerDid,\n'
                 '              created_at: string(now())\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=true" target="accepted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Save" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2839,
                 '00-contracts/bpmn/ai/gftd/apps/live/sendCheer.bpmn',
                 '2026-04-29T01:00:00Z',
                 'did:web:live.etzhayyim.com',
                 'did:web:live.etzhayyim.com',
                 'sys.bpmn.seed.live',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/apps-live-send-cheer-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/apps-live-postChat-v1',
                 'did:web:live.etzhayyim.com',
                 'app.etzhayyim.apps.live.postChat',
                 'live_post_chat',
                 5000,
                 '2026-04-29T01:00:00Z',
                 'did:web:live.etzhayyim.com',
                 'did:web:live.etzhayyim.com',
                 'sys.bpmn.seed.live',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/apps-live-postChat-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/apps-live-scheduleSet-v1',
                 'did:web:live.etzhayyim.com',
                 'app.etzhayyim.apps.live.scheduleSet',
                 'live_schedule_set',
                 10000,
                 '2026-04-29T01:00:00Z',
                 'did:web:live.etzhayyim.com',
                 'did:web:live.etzhayyim.com',
                 'sys.bpmn.seed.live',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/apps-live-scheduleSet-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/apps-live-sendCheer-v1',
                 'did:web:live.etzhayyim.com',
                 'app.etzhayyim.apps.live.sendCheer',
                 'live_send_cheer',
                 5000,
                 '2026-04-29T01:00:00Z',
                 'did:web:live.etzhayyim.com',
                 'did:web:live.etzhayyim.com',
                 'sys.bpmn.seed.live',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/apps-live-sendCheer-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/apps-live-postChat-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/apps-live-scheduleSet-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/apps-live-sendCheer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/apps-live-post-chat-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/apps-live-schedule-set-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/apps-live-send-cheer-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
