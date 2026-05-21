"""Captured from Kysely migration 20260425211000_seed_real_estate_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425211000_seed_real_estate_bpmn_actors"
down_revision = 'r_20260425210000_global_real_estate_schema'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, '
         'version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, '
         'user_id, actor_id)\n'
         "      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/real-estate-register-property-v1',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'real_estate_register_property',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_real_estate_register_property" '
                 'targetNamespace="https://etzhayyim.com/bpmn/real-estate" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="real_estate_register_property" name="registerProperty" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Save</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save property">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_real_estate_property&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, property_id: propertyId, canonical_property_key: '
                 'canonicalPropertyKey, property_type: propertyType, country_iso2: countryIso2, '
                 'country_iso3: countryIso3, admin1: admin1, admin2: admin2, city: city, '
                 'postal_code: postalCode, address_text: addressText, latitude: latitude, '
                 'longitude: longitude, geohash: geohash, land_area_sqm: landAreaSqm, '
                 'floor_area_sqm: floorAreaSqm, building_area_sqm: buildingAreaSqm, rooms: rooms, '
                 'bedrooms: bedrooms, bathrooms: bathrooms, year_built: yearBuilt, '
                 'land_rights_type: landRightsType, registry_number: registryNumber, cadastral_id: '
                 'cadastralId, source_id: sourceId, source_url: sourceUrl, data_hash: dataHash, '
                 'observed_at: observedAt, status: &quot;active&quot;, created_at: string(now()), '
                 'owner_did: callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, '
                 'actor_id: &quot;sys.bpmn.real-estate&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" '
                 'name="audit"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:real-estate.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;realEstate.registerProperty&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, propertyId: propertyId, canonicalPropertyKey: '
                 'canonicalPropertyKey}" '
                 'target="payload"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2812,
                 '00-contracts/bpmn/ai/gftd/real-estate/registerProperty.bpmn',
                 '2026-04-25T21:10:00Z',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'sys.bpmn.seed.real-estate',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/real-estate-register-property-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, write_table_allowlist, status, '
         'created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/real-estate-register-property-v1',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'ai.gftd.apps.realEstate.registerProperty',
                 'real_estate_register_property',
                 20000,
                 'vertex_real_estate_property',
                 '2026-04-25T21:10:00Z',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'sys.bpmn.seed.real-estate',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/real-estate-register-property-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, '
         'version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, '
         'user_id, actor_id)\n'
         "      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/real-estate-publish-listing-v1',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'real_estate_publish_listing',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_real_estate_publish_listing" '
                 'targetNamespace="https://etzhayyim.com/bpmn/real-estate" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="real_estate_publish_listing" name="publishListing" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Save</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save listing">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_real_estate_listing&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, listing_id: listingId, property_vid: propertyVid, '
                 'canonical_property_key: canonicalPropertyKey, listing_kind: listingKind, '
                 'offer_status: offerStatus, country_iso2: countryIso2, city: city, postal_code: '
                 'postalCode, geohash: geohash, currency: currency, price: price, rent_period: '
                 'rentPeriod, deposit_amount: depositAmount, fees_amount: feesAmount, '
                 'price_per_sqm: pricePerSqm, listed_at: listedAt, first_seen_at: firstSeenAt, '
                 'last_seen_at: lastSeenAt, source_id: sourceId, source_url: sourceUrl, title: '
                 'title, summary: summary, media_count: mediaCount, agent_party_vid: '
                 'agentPartyVid, seller_party_vid: sellerPartyVid, landlord_party_vid: '
                 'landlordPartyVid, data_hash: dataHash, status: &quot;active&quot;, created_at: '
                 'string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: callerDid, '
                 'user_id: callerDid, actor_id: &quot;sys.bpmn.real-estate&quot;}" '
                 'target="values"/><zeebe:input source="=&quot;ignore&quot;" '
                 'target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" '
                 'name="audit"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:real-estate.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;realEstate.publishListing&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, listingId: listingId, listingKind: listingKind}" '
                 'target="payload"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2791,
                 '00-contracts/bpmn/ai/gftd/real-estate/publishListing.bpmn',
                 '2026-04-25T21:10:00Z',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'sys.bpmn.seed.real-estate',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/real-estate-publish-listing-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, write_table_allowlist, status, '
         'created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/real-estate-publish-listing-v1',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'ai.gftd.apps.realEstate.publishListing',
                 'real_estate_publish_listing',
                 20000,
                 'vertex_real_estate_listing',
                 '2026-04-25T21:10:00Z',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'sys.bpmn.seed.real-estate',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/real-estate-publish-listing-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, '
         'version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, '
         'user_id, actor_id)\n'
         "      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/real-estate-record-transaction-v1',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'real_estate_record_transaction',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_real_estate_record_transaction" '
                 'targetNamespace="https://etzhayyim.com/bpmn/real-estate" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="real_estate_record_transaction" name="recordTransaction" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Save</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save transaction">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_real_estate_transaction&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, transaction_id: '
                 'transactionId, property_vid: propertyVid, listing_vid: listingVid, '
                 'transaction_kind: transactionKind, country_iso2: countryIso2, currency: '
                 'currency, amount: amount, rent_period: rentPeriod, contract_start_date: '
                 'contractStartDate, contract_end_date: contractEndDate, signed_at: signedAt, '
                 'registered_at: registeredAt, source_id: sourceId, source_url: sourceUrl, '
                 'buyer_party_vid: buyerPartyVid, seller_party_vid: sellerPartyVid, '
                 'tenant_party_vid: tenantPartyVid, landlord_party_vid: landlordPartyVid, '
                 'broker_party_vid: brokerPartyVid, confidence: confidence, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.real-estate&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" '
                 'name="audit"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:real-estate.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;realEstate.recordTransaction&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, transactionId: transactionId, transactionKind: '
                 'transactionKind}" '
                 'target="payload"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2723,
                 '00-contracts/bpmn/ai/gftd/real-estate/recordTransaction.bpmn',
                 '2026-04-25T21:10:00Z',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'sys.bpmn.seed.real-estate',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/real-estate-record-transaction-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, write_table_allowlist, status, '
         'created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/real-estate-record-transaction-v1',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'ai.gftd.apps.realEstate.recordTransaction',
                 'real_estate_record_transaction',
                 20000,
                 'vertex_real_estate_transaction',
                 '2026-04-25T21:10:00Z',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'sys.bpmn.seed.real-estate',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/real-estate-record-transaction-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, '
         'version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, '
         'user_id, actor_id)\n'
         "      SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/real-estate-register-source-v1',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'real_estate_register_source',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_real_estate_register_source" '
                 'targetNamespace="https://etzhayyim.com/bpmn/real-estate" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="real_estate_register_source" name="registerSource" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_Save</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Save" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save source">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_real_estate_source&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, source_id: sourceId, source_kind: sourceKind, '
                 'country_iso2: countryIso2, country_iso3: countryIso3, jurisdiction: '
                 'jurisdiction, base_url: baseUrl, license: license, refresh_cadence: '
                 'refreshCadence, terms_url: termsUrl, status: &quot;active&quot;, created_at: '
                 'string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: callerDid, '
                 'user_id: callerDid, actor_id: &quot;sys.bpmn.real-estate&quot;}" '
                 'target="values"/><zeebe:input source="=&quot;ignore&quot;" '
                 'target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_Save</bpmn:incoming><bpmn:outgoing>Flow_Audit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_Audit" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" '
                 'name="audit"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="generic.audit.emit"/><zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:real-estate.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;realEstate.registerSource&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId, sourceId: sourceId}" '
                 'target="payload"/></zeebe:ioMapping></bpmn:extensionElements><bpmn:incoming>Flow_Audit</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing></bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2304,
                 '00-contracts/bpmn/ai/gftd/real-estate/registerSource.bpmn',
                 '2026-04-25T21:10:00Z',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'sys.bpmn.seed.real-estate',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/real-estate-register-source-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, write_table_allowlist, status, '
         'created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = '
         '$11)\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/real-estate-register-source-v1',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'ai.gftd.apps.realEstate.registerSource',
                 'real_estate_register_source',
                 15000,
                 'vertex_real_estate_source',
                 '2026-04-25T21:10:00Z',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'did:web:real-estate.etzhayyim.com:ops',
                 'sys.bpmn.seed.real-estate',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/real-estate-register-source-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/real-estate-register-property-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/real-estate-register-property-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/real-estate-publish-listing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/real-estate-publish-listing-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/real-estate-record-transaction-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/real-estate-record-transaction-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/real-estate-register-source-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/real-estate-register-source-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
