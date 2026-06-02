"""Captured from Kysely migration 20260427160100_seed_flight_airlines_lcc."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427160100_seed_flight_airlines_lcc"
down_revision = 'r_20260427160000_vertex_flight_offer_source_run'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_airline (\n'
         '        vertex_id, iata_code, icao_code, name, country_code, alliance,\n'
         '        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5, $6,\n'
         "             'unknown', 'discovered', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR',
                 'FR',
                 'RYR',
                 'Ryanair',
                 'IE',
                 '',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR']},
 {'sql': '\n'
         '      INSERT INTO vertex_airline (\n'
         '        vertex_id, iata_code, icao_code, name, country_code, alliance,\n'
         '        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5, $6,\n'
         "             'unknown', 'discovered', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2',
                 'U2',
                 'EZY',
                 'easyJet',
                 'GB',
                 '',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2']},
 {'sql': '\n'
         '      INSERT INTO vertex_airline (\n'
         '        vertex_id, iata_code, icao_code, name, country_code, alliance,\n'
         '        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5, $6,\n'
         "             'unknown', 'discovered', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6',
                 'W6',
                 'WZZ',
                 'Wizz Air',
                 'HU',
                 '',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6']},
 {'sql': '\n'
         '      INSERT INTO vertex_airline (\n'
         '        vertex_id, iata_code, icao_code, name, country_code, alliance,\n'
         '        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5, $6,\n'
         "             'unknown', 'discovered', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK',
                 'AK',
                 'AXM',
                 'AirAsia',
                 'MY',
                 '',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK']},
 {'sql': '\n'
         '      INSERT INTO vertex_airline (\n'
         '        vertex_id, iata_code, icao_code, name, country_code, alliance,\n'
         '        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5, $6,\n'
         "             'unknown', 'discovered', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ',
                 'JQ',
                 'JST',
                 'Jetstar Airways',
                 'AU',
                 '',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ']},
 {'sql': '\n'
         '      INSERT INTO vertex_airline (\n'
         '        vertex_id, iata_code, icao_code, name, country_code, alliance,\n'
         '        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5, $6,\n'
         "             'unknown', 'discovered', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J',
                 '5J',
                 'CEB',
                 'Cebu Pacific',
                 'PH',
                 '',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J']},
 {'sql': '\n'
         '      INSERT INTO vertex_airline (\n'
         '        vertex_id, iata_code, icao_code, name, country_code, alliance,\n'
         '        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5, $6,\n'
         "             'unknown', 'discovered', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ',
                 'QZ',
                 'AWQ',
                 'Indonesia AirAsia',
                 'ID',
                 '',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ']},
 {'sql': '\n'
         '      INSERT INTO vertex_airline (\n'
         '        vertex_id, iata_code, icao_code, name, country_code, alliance,\n'
         '        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5, $6,\n'
         "             'unknown', 'discovered', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH',
                 'MH',
                 'MAS',
                 'Malaysia Airlines',
                 'MY',
                 'OneWorld',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH']},
 {'sql': '\n'
         '      INSERT INTO vertex_airline (\n'
         '        vertex_id, iata_code, icao_code, name, country_code, alliance,\n'
         '        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5, $6,\n'
         "             'unknown', 'discovered', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA',
                 'GA',
                 'GIA',
                 'Garuda Indonesia',
                 'ID',
                 'SkyTeam',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA']},
 {'sql': '\n'
         '      INSERT INTO vertex_airline (\n'
         '        vertex_id, iata_code, icao_code, name, country_code, alliance,\n'
         '        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5, $6,\n'
         "             'unknown', 'discovered', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV',
                 'SV',
                 'SVA',
                 'Saudia',
                 'SA',
                 'SkyTeam',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV']},
 {'sql': '\n'
         '      INSERT INTO vertex_airline (\n'
         '        vertex_id, iata_code, icao_code, name, country_code, alliance,\n'
         '        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5, $6,\n'
         "             'unknown', 'discovered', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS',
                 'MS',
                 'MSR',
                 'EgyptAir',
                 'EG',
                 'Star Alliance',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS']},
 {'sql': '\n'
         '      INSERT INTO vertex_airline (\n'
         '        vertex_id, iata_code, icao_code, name, country_code, alliance,\n'
         '        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5, $6,\n'
         "             'unknown', 'discovered', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX',
                 'LX',
                 'SWR',
                 'Swiss International',
                 'CH',
                 'Star Alliance',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR',
                 'amadeus',
                 'FR',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR',
                 'duffel',
                 'FR',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR',
                 'kiwi-tequila',
                 'FR',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR',
                 'travelpayouts-aviasales',
                 'FR',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR',
                 'skyscanner-affiliate',
                 'FR',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2',
                 'amadeus',
                 'U2',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2',
                 'duffel',
                 'U2',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2',
                 'kiwi-tequila',
                 'U2',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2',
                 'travelpayouts-aviasales',
                 'U2',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2',
                 'skyscanner-affiliate',
                 'U2',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6',
                 'amadeus',
                 'W6',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6',
                 'duffel',
                 'W6',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6',
                 'kiwi-tequila',
                 'W6',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6',
                 'travelpayouts-aviasales',
                 'W6',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6',
                 'skyscanner-affiliate',
                 'W6',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK',
                 'amadeus',
                 'AK',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK',
                 'duffel',
                 'AK',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK',
                 'kiwi-tequila',
                 'AK',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK',
                 'travelpayouts-aviasales',
                 'AK',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK',
                 'skyscanner-affiliate',
                 'AK',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ',
                 'amadeus',
                 'JQ',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ',
                 'duffel',
                 'JQ',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ',
                 'kiwi-tequila',
                 'JQ',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ',
                 'travelpayouts-aviasales',
                 'JQ',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ',
                 'skyscanner-affiliate',
                 'JQ',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J',
                 'amadeus',
                 '5J',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J',
                 'duffel',
                 '5J',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J',
                 'kiwi-tequila',
                 '5J',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J',
                 'travelpayouts-aviasales',
                 '5J',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J',
                 'skyscanner-affiliate',
                 '5J',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ',
                 'amadeus',
                 'QZ',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ',
                 'duffel',
                 'QZ',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ',
                 'kiwi-tequila',
                 'QZ',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ',
                 'travelpayouts-aviasales',
                 'QZ',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ',
                 'skyscanner-affiliate',
                 'QZ',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH',
                 'amadeus',
                 'MH',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH',
                 'duffel',
                 'MH',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH',
                 'kiwi-tequila',
                 'MH',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH',
                 'travelpayouts-aviasales',
                 'MH',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH',
                 'skyscanner-affiliate',
                 'MH',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA',
                 'amadeus',
                 'GA',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA',
                 'duffel',
                 'GA',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA',
                 'kiwi-tequila',
                 'GA',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA',
                 'travelpayouts-aviasales',
                 'GA',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA',
                 'skyscanner-affiliate',
                 'GA',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV',
                 'amadeus',
                 'SV',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV',
                 'duffel',
                 'SV',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV',
                 'kiwi-tequila',
                 'SV',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV',
                 'travelpayouts-aviasales',
                 'SV',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV',
                 'skyscanner-affiliate',
                 'SV',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS',
                 'amadeus',
                 'MS',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS',
                 'duffel',
                 'MS',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS',
                 'kiwi-tequila',
                 'MS',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS',
                 'travelpayouts-aviasales',
                 'MS',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS',
                 'skyscanner-affiliate',
                 'MS',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX',
                 'amadeus',
                 'LX',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX',
                 'duffel',
                 'LX',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX',
                 'kiwi-tequila',
                 'LX',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX',
                 'travelpayouts-aviasales',
                 'LX',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX']},
 {'sql': '\n'
         '        INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '        )\n'
         '        SELECT $1, $2, $3,\n'
         "               $4, $5, 'primary',\n"
         "               '', $6, 1, $7, $8, $9\n"
         '        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $10)\n'
         '      ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX',
                 'skyscanner-affiliate',
                 'LX',
                 '2026-04-27T16:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX']}]

DOWN = [{'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/FR']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/U2']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/W6']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JQ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/5J']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/GA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SV']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LX']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
