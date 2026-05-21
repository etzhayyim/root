"""Captured from Kysely migration 20260429120100_seed_handotai_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429120100_seed_handotai_bpmn_actors"
down_revision = 'r_20260429120000_vertex_handotai_tables'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/handotai-collect-v1',
                 'did:web:handotai.etzhayyim.com',
                 'handotai_collect',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — handotai semiconductor intelligence collection (every 4 '
                 'hours).\n'
                 '\n'
                 '  Pipeline:\n'
                 '\n'
                 '    1. handotai.seed.writers   — idempotent upsert of 6 built-in RSS writer '
                 'sources\n'
                 '                                 into vertex_handotai_source.\n'
                 '    2. handotai.collect.rssAll — fetch all enabled sources, parse RSS/Atom '
                 'items,\n'
                 '                                 write deduplicated articles to '
                 'vertex_handotai_article.\n'
                 "    3. handotai.generate.digest — query today's articles, LLM-summarize into\n"
                 '                                  vertex_handotai_digest.\n'
                 '    4. generic.audit.emit      — OCEL event with aggregate write counts.\n'
                 '\n'
                 '  Cadence: R/PT4H. One BPMN instance every 4 hours.\n'
                 '\n'
                 '  NSID: ai.gftd.apps.handotai.handotaiCollect\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/handotai-collect-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_handotai_collect"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/handotai"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="handotai_collect" name="handotai collect" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.handotai.handotaiCollect", "version": 1, '
                 '"resultTimeoutMs": 600000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 4 hours">\n'
                 '      <bpmn:outgoing>Flow_ToSeedWriters</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT4H">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT4H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / on-demand">\n'
                 '      <bpmn:outgoing>Flow_ToSeedWriters_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSeedWriters"        '
                 'sourceRef="Start_Timer"          targetRef="Task_SeedWriters"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSeedWriters_Manual" '
                 'sourceRef="Start_Manual"         targetRef="Task_SeedWriters"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCollectAll"         '
                 'sourceRef="Task_SeedWriters"     targetRef="Task_CollectAll"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToGenerateDigest"     '
                 'sourceRef="Task_CollectAll"      targetRef="Task_GenerateDigest"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit"              '
                 'sourceRef="Task_GenerateDigest"  targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End"                  '
                 'sourceRef="Task_Audit"           targetRef="End"/>\n'
                 '\n'
                 '    <!-- Step 1: Upsert 6 built-in RSS writer sources into '
                 'vertex_handotai_source. -->\n'
                 '    <bpmn:serviceTask id="Task_SeedWriters" name="seed writer sources">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="handotai.seed.writers"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=upserted" target="seedUpserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Step 2: Fetch all 6 RSS feeds, parse items, write to '
                 'vertex_handotai_article. -->\n'
                 '    <bpmn:serviceTask id="Task_CollectAll" name="collect all RSS feeds">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="handotai.collect.rssAll"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=20" target="maxPerSource"/>\n'
                 '          <zeebe:output source="=written"  target="articlesWritten"/>\n'
                 '          <zeebe:output source="=skipped"  target="articlesSkipped"/>\n'
                 '          <zeebe:output source="=errors"   target="collectErrors"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 "    <!-- Step 3: Query today's articles, LLM-summarize, write to "
                 'vertex_handotai_digest. -->\n'
                 '    <bpmn:serviceTask id="Task_GenerateDigest" name="generate daily digest">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="handotai.generate.digest"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=digest_date"    target="digestDate"/>\n'
                 '          <zeebe:output source="=article_count"  target="digestArticleCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <!-- Step 4: Emit OCEL audit event with aggregate write counts. -->\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit collect audit event">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;ai.gftd.apps.handotai.handotaiCollect&quot;" '
                 'target="event_type"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;did:web:handotai.etzhayyim.com&quot;"              '
                 'target="actor_did"/>\n'
                 '          <zeebe:input source="={ articlesWritten: articlesWritten, '
                 'articlesSkipped: articlesSkipped, digestDate: digestDate, digestArticleCount: '
                 'digestArticleCount }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5003,
                 '00-contracts/bpmn/ai/gftd/handotai/handotaiCollect.bpmn',
                 '2026-04-29T12:01:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/handotai-collect-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/handotai-collect-v1',
                 'did:web:handotai.etzhayyim.com',
                 'ai.gftd.apps.handotai.handotaiCollect',
                 'handotai_collect',
                 600000,
                 '2026-04-29T12:01:00Z',
                 'did:web:handotai.etzhayyim.com',
                 'did:web:handotai.etzhayyim.com',
                 'sys.bpmn.seed.handotai',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/handotai-collect-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/handotai-collect-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/handotai-collect-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
