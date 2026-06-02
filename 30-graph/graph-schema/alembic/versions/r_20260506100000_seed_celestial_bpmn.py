"""Captured from Kysely migration 20260506100000_seed_celestial_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506100000_seed_celestial_bpmn"
down_revision = 'r_20260506093000_vertex_ads_analysis'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT $1, $2, $3, 1, $4,\n'
         "           CAST($5 AS integer), $6, 'active', $7,\n"
         '           1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-ingestCelestialCatalogs-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_ingest_celestial_catalogs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — celestial catalog ingest (HYG + OpenNGC).\n'
                 '\n'
                 "  Pipeline (R/P30D — celestial positions don't change quickly):\n"
                 '    1. celestial.hyg.refresh — naked-eye stars (mag ≤ 6.5)\n'
                 '    2. celestial.ngc.refresh — galaxies / nebulae / clusters\n'
                 '\n'
                 '  com.etzhayyim.apps.maps.ingestCelestialCatalogs.\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_maps_ingest_celestial"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/maps"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="maps_ingest_celestial_catalogs" name="maps ingest celestial '
                 'catalogs" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.maps.ingestCelestialCatalogs", "version": 1, '
                 '"resultTimeoutMs": 1800000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 30 days">\n'
                 '      <bpmn:outgoing>Flow_ToHyg</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_P30D">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P30D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual">\n'
                 '      <bpmn:outgoing>Flow_ToHyg_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToHyg" sourceRef="Start_Timer" '
                 'targetRef="Task_Hyg"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToHyg_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_Hyg"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Hyg" name="HYG naked-eye stars">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="celestial.hyg.refresh"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=6.5" target="mag_max"/>\n'
                 '          <zeebe:input source="=12000" target="max_rows"/>\n'
                 '          <zeebe:output source="=runId" target="hygRunId"/>\n'
                 '          <zeebe:output source="=ingested" target="hygIngested"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToHyg</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_ToHyg_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToNgc</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToNgc" sourceRef="Task_Hyg" '
                 'targetRef="Task_Ngc"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Ngc" name="OpenNGC deep-sky">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="celestial.ngc.refresh"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=5000" target="max_rows"/>\n'
                 '          <zeebe:output source="=ingested" target="ngcIngested"/>\n'
                 '          <zeebe:output source="=messierCount" target="messierCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToNgc</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Ngc" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit celestial-ingest OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.maps.ingestCelestialCatalogs&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;hygIngested&quot;: hygIngested, '
                 '&quot;ngcIngested&quot;: ngcIngested, &quot;messierCount&quot;: messierCount }" '
                 'target="attributes"/>\n'
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
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3833,
                 '00-contracts/bpmn/com/etzhayyim/maps/ingestCelestialCatalogs.bpmn',
                 '2026-05-06T10:00:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-celestial',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-ingestCelestialCatalogs-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '       write_table_allowlist, status, created_at, sensitivity_ord,\n'
         '       org_id, user_id, actor_id, actor_did, org_did)\n'
         '    SELECT $1, $2, $3, $4, 1,\n'
         '           CAST($5 AS integer), $6,\n'
         "           'active', $7, 1,\n"
         "           $8, $9, $10, $11, 'anon'\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/maps-ingestCelestialCatalogs-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.ingestCelestialCatalogs',
                 'maps_ingest_celestial_catalogs',
                 1800000,
                 'vertex_celestial_catalog,vertex_celestial_object',
                 '2026-05-06T10:00:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-celestial',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/maps-ingestCelestialCatalogs-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.lexiconBinding/maps-ingestCelestialCatalogs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-ingestCelestialCatalogs-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
