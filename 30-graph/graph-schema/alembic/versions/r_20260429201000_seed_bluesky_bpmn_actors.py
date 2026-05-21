"""Captured from Kysely migration 20260429201000_seed_bluesky_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429201000_seed_bluesky_bpmn_actors"
down_revision = 'r_20260429200000_seed_open_adnetwork_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1, $4, CAST($5 AS integer),\n'
         "        $6, 'active', $7, 1, $8, $9, $10,\n"
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/bluesky-ingest-actor-v1',
                 'did:web:bluesky.etzhayyim.com',
                 'bluesky_ingest_actor',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Bluesky ingestActor — manual one-shot ingest via Zeebe/Python.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.bluesky.ingestActor\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/bluesky-ingest-actor-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_bluesky_ingest_actor"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/bluesky"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="bluesky_ingest_actor" name="bluesky ingest actor" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.bluesky.ingestActor", "version": 1, '
                 '"resultTimeoutMs": 120000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="manual">\n'
                 '      <bpmn:outgoing>Flow_ToIngest</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToIngest" sourceRef="Start" '
                 'targetRef="Task_Ingest"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ingest" name="ingest public actor">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="bluesky.ingest.actor"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=actor" target="actor"/>\n'
                 '          <zeebe:input source="=if appview = null then '
                 '&quot;https://public.api.bsky.app&quot; else appview" target="appview"/>\n'
                 '          <zeebe:input source="=if nanoid = null then &quot;bsky1ngs&quot; else '
                 'nanoid" target="nanoid"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=actor" target="actorDid"/>\n'
                 '          <zeebe:output source="=handle" target="handle"/>\n'
                 '          <zeebe:output source="=ingested" target="ingested"/>\n'
                 '          <zeebe:output source="=tombstoned" target="tombstoned"/>\n'
                 '          <zeebe:output source="=skippedOptOut" target="skippedOptOut"/>\n'
                 '          <zeebe:output source="=skippedForbidden" target="skippedForbidden"/>\n'
                 '          <zeebe:output source="=error" target="error"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToIngest</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Ingest" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2370,
                 '00-contracts/bpmn/ai/gftd/bluesky/ingestActor.bpmn',
                 '2026-04-29T20:10:00+09:00',
                 'did:web:bluesky.etzhayyim.com',
                 'did:web:bluesky.etzhayyim.com',
                 'sys.bpmn.seed.bluesky',
                 'did:web:bluesky.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/bluesky-ingest-actor-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/bluesky-ingest-actor-v1',
                 'did:web:bluesky.etzhayyim.com',
                 'ai.gftd.apps.bluesky.ingestActor',
                 'bluesky_ingest_actor',
                 120000,
                 'vertex_bluesky_profile,vertex_bluesky_post,vertex_bluesky_opt_out,vertex_bluesky_tombstone',
                 '2026-04-29T20:10:00+09:00',
                 'did:web:bluesky.etzhayyim.com',
                 'did:web:bluesky.etzhayyim.com',
                 'sys.bpmn.seed.bluesky',
                 'did:web:bluesky.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/bluesky-ingest-actor-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['vertex_bluesky_profile,vertex_bluesky_post,vertex_bluesky_opt_out,vertex_bluesky_tombstone',
                 'bluesky_ingest_actor',
                 'ai.gftd.apps.bluesky.ingestActor',
                 'vertex_bluesky_profile,vertex_bluesky_post,vertex_bluesky_opt_out,vertex_bluesky_tombstone']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1, $4, CAST($5 AS integer),\n'
         "        $6, 'active', $7, 1, $8, $9, $10,\n"
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/bluesky-refresh-stalest-v1',
                 'did:web:bluesky.etzhayyim.com',
                 'bluesky_refresh_stalest',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Bluesky refreshStalest — BPMN timer replacement for CF Worker cron.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.bluesky.refreshStalest\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/bluesky-refresh-stalest-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_bluesky_refresh_stalest"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/bluesky"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="bluesky_refresh_stalest" name="bluesky refresh stalest '
                 'actors (R/PT30M)" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.bluesky.refreshStalest", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="every 30 minutes">\n'
                 '      <bpmn:outgoing>Flow_ToRefresh</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_30m">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToRefresh" sourceRef="Start" '
                 'targetRef="Task_Refresh"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Refresh" name="refresh stalest tracked actors">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="bluesky.ingest.refreshStalest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if batchSize = null then 10 else batchSize" '
                 'target="batchSize"/>\n'
                 '          <zeebe:input source="=if appview = null then '
                 '&quot;https://public.api.bsky.app&quot; else appview" target="appview"/>\n'
                 '          <zeebe:input source="=if nanoid = null then &quot;bsky1ngs&quot; else '
                 'nanoid" target="nanoid"/>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=actorsRead" target="actorsRead"/>\n'
                 '          <zeebe:output source="=ingested" target="ingested"/>\n'
                 '          <zeebe:output source="=tombstoned" target="tombstoned"/>\n'
                 '          <zeebe:output source="=errorCount" target="errorCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToRefresh</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Refresh" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit bluesky.refresh audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.bluesky.refreshStalest&quot;" '
                 'target="activity"/>\n'
                 '          <zeebe:input source="=&quot;bluesky.etzhayyim.com&quot;" '
                 'target="actorDid"/>\n'
                 '          <zeebe:input source="=actorsRead" target="actorsRead"/>\n'
                 '          <zeebe:input source="=ingested" target="ingested"/>\n'
                 '          <zeebe:input source="=tombstoned" target="tombstoned"/>\n'
                 '          <zeebe:input source="=errorCount" target="errorCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3421,
                 '00-contracts/bpmn/ai/gftd/bluesky/refreshStalest.bpmn',
                 '2026-04-29T20:10:00+09:00',
                 'did:web:bluesky.etzhayyim.com',
                 'did:web:bluesky.etzhayyim.com',
                 'sys.bpmn.seed.bluesky',
                 'did:web:bluesky.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/bluesky-refresh-stalest-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        1, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/bluesky-refresh-stalest-v1',
                 'did:web:bluesky.etzhayyim.com',
                 'ai.gftd.apps.bluesky.refreshStalest',
                 'bluesky_refresh_stalest',
                 300000,
                 'vertex_bluesky_profile,vertex_bluesky_post,vertex_bluesky_opt_out,vertex_bluesky_tombstone',
                 '2026-04-29T20:10:00+09:00',
                 'did:web:bluesky.etzhayyim.com',
                 'did:web:bluesky.etzhayyim.com',
                 'sys.bpmn.seed.bluesky',
                 'did:web:bluesky.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/bluesky-refresh-stalest-v1']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '        AND nsid = $3\n'
         '        AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '    ',
  'parameters': ['vertex_bluesky_profile,vertex_bluesky_post,vertex_bluesky_opt_out,vertex_bluesky_tombstone',
                 'bluesky_refresh_stalest',
                 'ai.gftd.apps.bluesky.refreshStalest',
                 'vertex_bluesky_profile,vertex_bluesky_post,vertex_bluesky_opt_out,vertex_bluesky_tombstone']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/bluesky-ingest-actor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/bluesky-ingest-actor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/bluesky-refresh-stalest-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/bluesky-refresh-stalest-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
