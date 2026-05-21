"""Captured from Kysely migration 20260427160200_seed_flight_offer_source_health_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427160200_seed_flight_offer_source_health_bpmn"
down_revision = 'r_20260427160100_seed_flight_airlines_lcc'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         "    SELECT $1, $2, 'flight_offer_source_health',\n"
         "           1, $3, CAST($4 AS integer), $5, 'active',\n"
         '           $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-source-health-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_flight_offer_source_health"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/flight-offer"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="flight_offer_source_health" name="sourceHealth" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Get</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Get" sourceRef="Start" targetRef="Task_Get"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Get" name="select source health from MV">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.offer.sourceHealth"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=if limit != null then limit else 50" '
                 'target="limit"/>\n'
                 '          <zeebe:output source="=items" target="items"/>\n'
                 '          <zeebe:output source="=count" target="count"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Get</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Get" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1409,
                 '00-contracts/bpmn/ai/gftd/flight-offer/sourceHealth.bpmn',
                 '2026-04-27T16:02:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-source-health-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         "    SELECT $1, $2, 'ai.gftd.apps.flightOffer.sourceHealth',\n"
         "           'flight_offer_source_health', 1, CAST(10000 AS integer), 'active',\n"
         '           $3, 1, $4, $5, $6\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $7)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-source-health-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 '2026-04-27T16:02:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-source-health-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/flight-offer-source-health-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-source-health-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
