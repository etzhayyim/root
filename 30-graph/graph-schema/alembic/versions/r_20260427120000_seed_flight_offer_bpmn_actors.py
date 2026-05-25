"""Captured from Kysely migration 20260427120000_seed_flight_offer_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427120000_seed_flight_offer_bpmn_actors"
down_revision = 'r_20260427120000_seed_business_person_bpmn_actor'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         "    SELECT $1, $2, 'flight_offer_search_offers',\n"
         "           1, $3, CAST($4 AS integer), $5, 'active',\n"
         '           $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/flight-offer-search-offers-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_flight_offer_search_offers"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/flight-offer"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="flight_offer_search_offers" name="searchOffers" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Health</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Health" sourceRef="Start" '
                 'targetRef="Task_Health"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Health" name="rw health gate">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="rw.health.probe"/></bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Health</bpmn:incoming><bpmn:outgoing>Flow_Fetch</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Fetch" sourceRef="Task_Health" '
                 'targetRef="Task_Fetch"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch + persist offers">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.offer.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=originIata" target="originIata"/>\n'
                 '          <zeebe:input source="=destinationIata" target="destinationIata"/>\n'
                 '          <zeebe:input source="=outboundDate" target="outboundDate"/>\n'
                 '          <zeebe:input source="=returnDate" target="returnDate"/>\n'
                 '          <zeebe:input source="=if currency != null and currency != &quot;&quot; '
                 'then currency else &quot;USD&quot;" target="currency"/>\n'
                 '          <zeebe:input source="=if provider != null then provider else '
                 '&quot;&quot;" target="provider"/>\n'
                 '          <zeebe:input source="=if maxOffers != null then maxOffers else 20" '
                 'target="maxOffers"/>\n'
                 '          <zeebe:output source="=offersWritten" target="offersWritten"/>\n'
                 '          <zeebe:output source="=offersFetched" target="offersFetched"/>\n'
                 '          <zeebe:output source="=provider" target="resolvedProvider"/>\n'
                 '          <zeebe:output source="=providerObservedAt" '
                 'target="providerObservedAt"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Fetch</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Fetch" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit search">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:flight-offer.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;flight.offer.searchOffers&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={originIata: originIata, destinationIata: '
                 'destinationIata, outboundDate: outboundDate, currency: currency, provider: '
                 'resolvedProvider, offersFetched: offersFetched, offersWritten: offersWritten}" '
                 'target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3357,
                 '00-contracts/bpmn/ai/gftd/flight-offer/searchOffers.bpmn',
                 '2026-04-27T12:00:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/flight-offer-search-offers-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         "    SELECT $1, $2, 'app.etzhayyim.apps.flightOffer.searchOffers',\n"
         "           'flight_offer_search_offers', 1, CAST(15000 AS integer), 'active',\n"
         '           $3, 1, $4, $5, $6\n'
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $7)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/flight-offer-search-offers-v1',
                 'did:web:flight-offer.etzhayyim.com',
                 '2026-04-27T12:00:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/flight-offer-search-offers-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/flight-offer-search-offers-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/flight-offer-search-offers-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
