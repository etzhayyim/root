"""Captured from Kysely migration 20260429040000_seed_live_tweak_track_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429040000_seed_live_tweak_track_bpmn"
down_revision = 'r_20260429030000_vertex_live_track_lighting_cue'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-live-tweak-track-v1',
                 'did:web:live.etzhayyim.com',
                 'live_tweak_track',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  com.etzhayyim.apps.live.tweakTrack — performer edits one track of a setlist.\n'
                 '\n'
                 '  Two-task flow:\n'
                 '    1. generic.db.insert → vertex_live_track (PK rewrite = upsert)\n'
                 '    2. generic.audit.emit → live.tweakTrack\n'
                 '\n'
                 '  The PK is deterministic on (room_slug, position): same PK on re-insert\n'
                 '  causes RisingWave to overwrite, which is the canonical "UPDATE" pattern\n'
                 "  per RW's record-log semantics (no OLTP UPDATE TX guarantees).\n"
                 '\n'
                 '  Caller supplies the full track payload; optional fields (dance, audio,\n'
                 '  cues_json) default to null and clear the column when omitted.\n'
                 '\n'
                 "  RLS shape per ADR-0095. The performer's DID is taken from the dispatch\n"
                 '  context (`callerDid`). org_did is "anon" until a wallet binds.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_live_tweak_track"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/apps/live"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="live_tweak_track" name="live tweakTrack" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="vertex_live_track upsert">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_live_track&quot;" target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id: &quot;at://&quot; + (if callerDid != null then '
                 'string(callerDid) else &quot;did:web:live.etzhayyim.com&quot;) + '
                 '&quot;/com.etzhayyim.apps.live.track/&quot; + string(roomSlug) + &quot;-&quot; + '
                 'string(position),\n'
                 '              room_slug: roomSlug,\n'
                 '              position: position,\n'
                 '              title: title,\n'
                 '              bpm: bpm,\n'
                 '              length_beats: lengthBeats,\n'
                 '              dance: dance,\n'
                 '              audio: audio,\n'
                 '              cues_json: cuesJson,\n'
                 '              name: string(title) + &quot; (track #&quot; + string(position) + '
                 '&quot;)&quot;,\n'
                 '              description: &quot;Track #&quot; + string(position) + &quot; of '
                 'room &quot; + string(roomSlug) + &quot; — &quot; + string(title),\n'
                 '              actor_did: if callerDid != null then callerDid else '
                 '&quot;did:web:live.etzhayyim.com&quot;,\n'
                 '              org_did: if orgDid != null then orgDid else &quot;anon&quot;,\n'
                 '              at_did: callerDid,\n'
                 '              created_at: string(now())\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=true" target="ok"/>\n'
                 '          <zeebe:output source="=&quot;at://&quot; + (if callerDid != null then '
                 'string(callerDid) else &quot;did:web:live.etzhayyim.com&quot;) + '
                 '&quot;/com.etzhayyim.apps.live.track/&quot; + string(roomSlug) + &quot;-&quot; + '
                 'string(position)" target="vertexId"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit live.tweakTrack">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:live.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;live.tweakTrack&quot;" target="action"/>\n'
                 '          <zeebe:input source="={\n'
                 '              roomSlug: roomSlug,\n'
                 '              position: position,\n'
                 '              title: title,\n'
                 '              bpm: bpm,\n'
                 '              dance: dance,\n'
                 '              audio: audio,\n'
                 '              callerDid: callerDid\n'
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
                 4235,
                 '00-contracts/bpmn/com/etzhayyim/apps/live/tweakTrack.bpmn',
                 '2026-04-29T04:00:00Z',
                 'did:web:live.etzhayyim.com',
                 'did:web:live.etzhayyim.com',
                 'sys.bpmn.seed.live.tweakTrack',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-live-tweak-track-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-live-tweakTrack-v1',
                 'did:web:live.etzhayyim.com',
                 'com.etzhayyim.apps.live.tweakTrack',
                 'live_tweak_track',
                 8000,
                 '2026-04-29T04:00:00Z',
                 'did:web:live.etzhayyim.com',
                 'did:web:live.etzhayyim.com',
                 'sys.bpmn.seed.live.tweakTrack',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-live-tweakTrack-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/apps-live-tweakTrack-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/apps-live-tweak-track-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
