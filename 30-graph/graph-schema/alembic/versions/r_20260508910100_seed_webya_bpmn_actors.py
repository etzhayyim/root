"""Captured from Kysely migration 20260508910100_seed_webya_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508910100_seed_webya_bpmn_actors"
down_revision = 'r_20260508910000_vertex_webya_schema'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, bpmn_process_id, version, xml,\n'
         '         owner_did, status, deployed_at, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, 1, $3,\n'
         "        $4, 'active', NULL, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/webya-create-site-v1',
                 'webya_create_site',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  webya.gftd.ai — createSite workflow (XRPC ai.gftd.apps.webya.createSite).\n'
                 '\n'
                 "  routing_target = 'langgraph'\n"
                 "  assistant_id   = 'webya_create_site'\n"
                 '\n'
                 '  The bpmn-dispatcher intercepts this XRPC call and routes directly to\n'
                 '  LangGraph Server (POST /runs) without deploying to Zeebe.\n'
                 '  This BPMN is documentation only — it describes the LangGraph graph topology.\n'
                 '\n'
                 '  LangGraph graph: webya_site_generation\n'
                 '    intake_analyzer → structure_planner → legal_disclosure_guard\n'
                 '    → content_generator (loop × N pages)\n'
                 '    → quality_reviewer → (revision loop ≤ 2)\n'
                 '    → seo_optimizer → html_renderer → publisher\n'
                 '\n'
                 '  Result: { ok, siteId, jobId, subdomain, status }\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_webya_create_site"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/webya"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="webya_create_site" name="webya create site" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.webya.createSite", "version": 1, '
                 '"resultTimeoutMs": 300000, "routing_target": "langgraph" }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="createSite XRPC">\n'
                 '      <bpmn:outgoing>Flow_ToGenerate</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Generate" name="LangGraph: '
                 'webya_site_generation">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="webya.site.generate"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=clientName"         target="clientName"/>\n'
                 '          <zeebe:input source="=professionKind"     target="professionKind"/>\n'
                 '          <zeebe:input source="=representativeName" '
                 'target="representativeName"/>\n'
                 '          <zeebe:input source="=address"            target="address"/>\n'
                 '          <zeebe:input source="=phone"              target="phone"/>\n'
                 '          <zeebe:input source="=email"              target="email"/>\n'
                 '          <zeebe:input source="=specialties"        target="specialties"/>\n'
                 '          <zeebe:input source="=tone"               target="tone"/>\n'
                 '          <zeebe:input source="=registrationNumber" '
                 'target="registrationNumber"/>\n'
                 '          <zeebe:input source="=associationName"    target="associationName"/>\n'
                 '          <zeebe:input source="=customDomain"       target="customDomain"/>\n'
                 '          <zeebe:output source="=ok"       target="ok"/>\n'
                 '          <zeebe:output source="=siteId"   target="siteId"/>\n'
                 '          <zeebe:output source="=jobId"    target="jobId"/>\n'
                 '          <zeebe:output source="=subdomain" target="subdomain"/>\n'
                 '          <zeebe:output source="=status"   target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToGenerate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToGenerate" sourceRef="Start"         '
                 'targetRef="Task_Generate"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit.emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;webya.createSite&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=siteId"                       '
                 'target="subject"/>\n'
                 '          <zeebe:input source="=status"                       '
                 'target="outcome"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Generate" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 'did:web:webya.gftd.ai',
                 '2026-05-08T09:10:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, bpmn_process_id, version, xml,\n'
         '         owner_did, status, deployed_at, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, 1, $3,\n'
         "        $4, 'active', NULL, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/webya-revise-site-v1',
                 'webya_revise_site',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  webya.gftd.ai — reviseSite workflow (XRPC ai.gftd.apps.webya.reviseSite).\n'
                 '\n'
                 "  routing_target = 'langgraph'\n"
                 "  assistant_id   = 'webya_revise_site'\n"
                 '\n'
                 '  LangGraph graph: webya_site_revision\n'
                 '    revision_analyzer → content_regenerator (affected pages only)\n'
                 '    → quality_reviewer → html_renderer → republisher\n'
                 '\n'
                 '  Result: { ok, jobId, revisionCount, status }\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_webya_revise_site"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/webya"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="webya_revise_site" name="webya revise site" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.webya.reviseSite", "version": 1, '
                 '"resultTimeoutMs": 180000, "routing_target": "langgraph" }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="reviseSite XRPC">\n'
                 '      <bpmn:outgoing>Flow_ToRevise</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Revise" name="LangGraph: webya_site_revision">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="webya.site.revise"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=siteId"      target="siteId"/>\n'
                 '          <zeebe:input source="=instruction" target="instruction"/>\n'
                 '          <zeebe:input source="=targetPages" target="targetPages"/>\n'
                 '          <zeebe:output source="=ok"            target="ok"/>\n'
                 '          <zeebe:output source="=jobId"         target="jobId"/>\n'
                 '          <zeebe:output source="=revisionCount" target="revisionCount"/>\n'
                 '          <zeebe:output source="=status"        target="status"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToRevise</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToRevise" sourceRef="Start" '
                 'targetRef="Task_Revise"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit.emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;webya.reviseSite&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=siteId"                       '
                 'target="subject"/>\n'
                 '          <zeebe:input source="=status"                       '
                 'target="outcome"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Revise" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 'did:web:webya.gftd.ai',
                 '2026-05-08T09:10:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, bpmn_process_id, version, xml,\n'
         '         owner_did, status, deployed_at, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, 1, $3,\n'
         "        $4, 'active', NULL, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/webya-domain-ssl-monitor-v1',
                 'webya_domain_ssl_monitor',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  webya.gftd.ai — domainSslMonitor (autonomous timer R/PT30M).\n'
                 '\n'
                 "  Polls all vertex_webya_domain WHERE ssl_status != 'active'.\n"
                 '  Calls CF API GET /zones/{zone}/custom_hostnames/{id} for each pending domain.\n'
                 '  Updates ssl_status + ownership_verified on active/error response.\n'
                 '\n'
                 '  No XRPC binding — timer-start only (Zeebe deploys via F5 watcher).\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_webya_domain_ssl_monitor"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/webya"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="webya_domain_ssl_monitor" name="webya domain ssl monitor" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="R/PT30M">\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT30M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '      <bpmn:outgoing>Flow_ToCheck</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_CheckPending" name="check all pending SSL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="webya.domain.checkAllPending"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=pendingCount"  target="pendingCount"/>\n'
                 '          <zeebe:output source="=activatedCount" target="activatedCount"/>\n'
                 '          <zeebe:output source="=errorCount"    target="errorCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToCheck</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCheck" sourceRef="Start" '
                 'targetRef="Task_CheckPending"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit.emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;webya.domainSslMonitor&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;ssl-monitor-tick&quot;"       '
                 'target="subject"/>\n'
                 '          <zeebe:input source="=pendingCount"                       '
                 'target="pendingCount"/>\n'
                 '          <zeebe:input source="=activatedCount"                     '
                 'target="activatedCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_CheckPending" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 'did:web:webya.gftd.ai',
                 '2026-05-08T09:10:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def\n'
         '        (vertex_id, bpmn_process_id, version, xml,\n'
         '         owner_did, status, deployed_at, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, 1, $3,\n'
         "        $4, 'active', NULL, $5\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/webya-seo-audit-v1',
                 'webya_seo_audit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  webya.gftd.ai — seoAudit (autonomous cron 0 0 0 ? * MON — 毎週月曜 00:00 UTC).\n'
                 '\n'
                 '  Audits all published sites for SEO health (meta description length,\n'
                 '  JSON-LD completeness, title uniqueness). LLM generates improvement\n'
                 '  suggestions; updated slots are written back to vertex_webya_page.\n'
                 '\n'
                 '  No XRPC binding — cron timer-start only.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_webya_seo_audit"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/webya"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="webya_seo_audit" name="webya seo audit" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="cron 0 0 0 ? * MON">\n'
                 '      <bpmn:timerEventDefinition>\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">0 0 0 ? * '
                 'MON</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_AuditAll" name="seo.auditAllSites">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="webya.seo.auditAllSites"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=sitesAudited"   target="sitesAudited"/>\n'
                 '          <zeebe:output source="=pagesUpdated"   target="pagesUpdated"/>\n'
                 '          <zeebe:output source="=issuesFound"    target="issuesFound"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEmit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Start" '
                 'targetRef="Task_AuditAll"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Emit" name="audit.emit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;webya.seoAudit&quot;" target="actor"/>\n'
                 '          <zeebe:input source="=&quot;weekly-seo-audit&quot;" '
                 'target="subject"/>\n'
                 '          <zeebe:input source="=sitesAudited"               '
                 'target="sitesAudited"/>\n'
                 '          <zeebe:input source="=pagesUpdated"               '
                 'target="pagesUpdated"/>\n'
                 '          <zeebe:input source="=issuesFound"                '
                 'target="issuesFound"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToEmit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEmit" sourceRef="Task_AuditAll" '
                 'targetRef="Task_Emit"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Emit" targetRef="End"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 'did:web:webya.gftd.ai',
                 '2026-05-08T09:10:00Z']},
 {'sql': 'FLUSH', 'parameters': []},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, nsid, bpmn_process_id, owner_did,\n'
         '         result_timeout_ms, routing_target, status, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3, $4,\n'
         "        $5, $6, 'active', $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/webya-createSite-v1',
                 'ai.gftd.apps.webya.createSite',
                 'webya_create_site',
                 'did:web:webya.gftd.ai',
                 300000,
                 'langgraph',
                 '2026-05-08T09:10:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, nsid, bpmn_process_id, owner_did,\n'
         '         result_timeout_ms, routing_target, status, created_at)\n'
         '      VALUES (\n'
         '        $1, $2, $3, $4,\n'
         "        $5, $6, 'active', $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/webya-reviseSite-v1',
                 'ai.gftd.apps.webya.reviseSite',
                 'webya_revise_site',
                 'did:web:webya.gftd.ai',
                 180000,
                 'langgraph',
                 '2026-05-08T09:10:00Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/webya-createSite-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/webya-reviseSite-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/webya-create-site-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/webya-revise-site-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/webya-domain-ssl-monitor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/webya-seo-audit-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
