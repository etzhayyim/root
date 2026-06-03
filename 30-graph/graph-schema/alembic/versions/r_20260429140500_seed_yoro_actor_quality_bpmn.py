"""Captured from Kysely migration 20260429140500_seed_yoro_actor_quality_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429140500_seed_yoro_actor_quality_bpmn"
down_revision = 'r_20260429130100_seed_jp_fiscal_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/yoro-actor-quality-enrich-v1',
                 'did:web:yoro.etzhayyim.com',
                 'yoro_actor_quality_enrich',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  YORO actor quality enrichment.\n'
                 '\n'
                 '  Purpose:\n'
                 '    Improve one public actor page at a time so profile, feed, sitemap, SEO\n'
                 '    snapshot, and domain-knowledge surfaces do not expose empty placeholder\n'
                 '    pages.\n'
                 '\n'
                 '  Input variables:\n'
                 '    actorDid       required, e.g. did:etzhayyim:baf...\n'
                 '    handle         optional\n'
                 '    sourceHint     optional, human-readable provenance hint\n'
                 '    dryRun         optional boolean, default false\n'
                 '\n'
                 '  Output variables:\n'
                 '    beforeQuality, afterQuality, missingFields, profileChanged, seedPostCreated\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.yoro.actorQualityEnrich\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_yoro_actor_quality_enrich"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/yoro"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="yoro_actor_quality_enrich" name="YORO actor quality enrich" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.yoro.actorQualityEnrich", "version": 1, '
                 '"resultTimeoutMs": 0 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Actor" name="actor quality request">\n'
                 '      <bpmn:outgoing>Flow_InspectBefore</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:sequenceFlow id="Flow_InspectBefore" sourceRef="Start_Actor" '
                 'targetRef="Task_InspectBefore"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToNeedsEnrich" sourceRef="Task_InspectBefore" '
                 'targetRef="Gateway_NeedsEnrich"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_EnrichProfile" sourceRef="Gateway_NeedsEnrich" '
                 'targetRef="Task_EnrichProfile">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">= '
                 'beforeQuality &lt; 80</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_SkipEnrich" sourceRef="Gateway_NeedsEnrich" '
                 'targetRef="Task_VerifyAfter">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">= '
                 'beforeQuality &gt;= 80</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSeedPost" sourceRef="Task_EnrichProfile" '
                 'targetRef="Gateway_NeedsSeedPost"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_CreateSeedPost" '
                 'sourceRef="Gateway_NeedsSeedPost" targetRef="Task_CreateSeedPost">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">= postsCount = '
                 '0</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_SkipSeedPost" sourceRef="Gateway_NeedsSeedPost" '
                 'targetRef="Task_VerifyAfter">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">= postsCount '
                 '&gt; 0</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_PostToVerify" sourceRef="Task_CreateSeedPost" '
                 'targetRef="Task_VerifyAfter"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_VerifyToAudit" sourceRef="Task_VerifyAfter" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" '
                 'targetRef="End_Done"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_InspectBefore" name="inspect current actor '
                 'quality">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="yoro.actorQuality.inspect"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=actorDid" target="actorDid"/>\n'
                 '          <zeebe:input source="=handle" target="handle"/>\n'
                 '          <zeebe:output source="=qualityScore" target="beforeQuality"/>\n'
                 '          <zeebe:output source="=missingFields" target="missingFields"/>\n'
                 '          <zeebe:output source="=postsCount" target="postsCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gateway_NeedsEnrich" name="quality below '
                 'threshold?"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_EnrichProfile" name="write profile fragments / '
                 'safe profile defaults">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="yoro.actorQuality.enrichProfile" '
                 'retries="3"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=actorDid" target="actorDid"/>\n'
                 '          <zeebe:input source="=handle" target="handle"/>\n'
                 '          <zeebe:input source="=missingFields" target="missingFields"/>\n'
                 '          <zeebe:input source="=sourceHint" target="sourceHint"/>\n'
                 '          <zeebe:input source="=dryRun" target="dryRun"/>\n'
                 '          <zeebe:output source="=profileChanged" target="profileChanged"/>\n'
                 '          <zeebe:output source="=displayName" target="displayName"/>\n'
                 '          <zeebe:output source="=description" target="description"/>\n'
                 '          <zeebe:output source="=seedPostText" target="seedPostText"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gateway_NeedsSeedPost" name="has public post?"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_CreateSeedPost" name="create one provenance seed '
                 'post">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="yoro.actorQuality.ensureSeedPost" '
                 'retries="2"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=actorDid" target="actorDid"/>\n'
                 '          <zeebe:input source="=handle" target="handle"/>\n'
                 '          <zeebe:input source="=displayName" target="displayName"/>\n'
                 '          <zeebe:input source="=description" target="description"/>\n'
                 '          <zeebe:input source="=seedPostText" target="seedPostText"/>\n'
                 '          <zeebe:input source="=sourceHint" target="sourceHint"/>\n'
                 '          <zeebe:input source="=dryRun" target="dryRun"/>\n'
                 '          <zeebe:output source="=seedPostCreated" target="seedPostCreated"/>\n'
                 '          <zeebe:output source="=seedPostUri" target="seedPostUri"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_VerifyAfter" name="verify actor page quality">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="yoro.actorQuality.verify"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=actorDid" target="actorDid"/>\n'
                 '          <zeebe:input source="=handle" target="handle"/>\n'
                 '          <zeebe:input source="=sourceHint" target="sourceHint"/>\n'
                 '          <zeebe:input source="=dryRun" target="dryRun"/>\n'
                 '          <zeebe:output source="=qualityScore" target="afterQuality"/>\n'
                 '          <zeebe:output source="=missingFields" '
                 'target="remainingMissingFields"/>\n'
                 '          <zeebe:output source="=postsCount" target="verifiedPostsCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit actor quality OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.yoro.actorQuality.enrich&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;actorDid&quot;: actorDid, '
                 '&quot;handle&quot;: handle, &quot;sourceHint&quot;: sourceHint, '
                 '&quot;dryRun&quot;: dryRun, &quot;beforeQuality&quot;: beforeQuality, '
                 '&quot;afterQuality&quot;: afterQuality, &quot;profileChanged&quot;: '
                 'profileChanged, &quot;seedPostCreated&quot;: seedPostCreated, '
                 '&quot;seedPostUri&quot;: seedPostUri, &quot;remainingMissingFields&quot;: '
                 'remainingMissingFields, &quot;verifiedPostsCount&quot;: verifiedPostsCount }" '
                 'target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '    </bpmn:serviceTask>\n'
                 '\n'
                 '    <bpmn:endEvent id="End_Done" name="actor quality checked"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 7327,
                 '00-contracts/bpmn/com/etzhayyim/yoro/actorQualityEnrich.bpmn',
                 '2026-04-29T14:05:00Z',
                 'did:web:yoro.etzhayyim.com',
                 'did:web:yoro.etzhayyim.com',
                 'sys.bpmn.seed.yoro',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/yoro-actor-quality-enrich-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST(0 AS integer), 'active',\n"
         '      $5, 1, $6, $7, $8\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/yoro-actor-quality-enrich-v1',
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.actorQualityEnrich',
                 'yoro_actor_quality_enrich',
                 '2026-04-29T14:05:00Z',
                 'did:web:yoro.etzhayyim.com',
                 'did:web:yoro.etzhayyim.com',
                 'sys.bpmn.seed.yoro',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/yoro-actor-quality-enrich-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/yoro-actor-quality-enrich-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/yoro-actor-quality-enrich-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
