"""Captured from Kysely migration 20260427150100_seed_flight_airlines_and_sources."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427150100_seed_flight_airlines_and_sources"
down_revision = 'r_20260427150000_vertex_telecom_supplier'
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA',
                 'AA',
                 'AAL',
                 'American Airlines',
                 'US',
                 'OneWorld',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL',
                 'DL',
                 'DAL',
                 'Delta Air Lines',
                 'US',
                 'SkyTeam',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA',
                 'UA',
                 'UAL',
                 'United Airlines',
                 'US',
                 'Star Alliance',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN',
                 'WN',
                 'SWA',
                 'Southwest Airlines',
                 'US',
                 '',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6',
                 'B6',
                 'JBU',
                 'JetBlue Airways',
                 'US',
                 '',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS',
                 'AS',
                 'ASA',
                 'Alaska Airlines',
                 'US',
                 'OneWorld',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC',
                 'AC',
                 'ACA',
                 'Air Canada',
                 'CA',
                 'Star Alliance',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH',
                 'LH',
                 'DLH',
                 'Lufthansa',
                 'DE',
                 'Star Alliance',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF',
                 'AF',
                 'AFR',
                 'Air France',
                 'FR',
                 'SkyTeam',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL',
                 'KL',
                 'KLM',
                 'KLM Royal Dutch Airlines',
                 'NL',
                 'SkyTeam',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA',
                 'BA',
                 'BAW',
                 'British Airways',
                 'GB',
                 'OneWorld',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB',
                 'IB',
                 'IBE',
                 'Iberia',
                 'ES',
                 'OneWorld',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ',
                 'AZ',
                 'ITY',
                 'ITA Airways',
                 'IT',
                 'SkyTeam',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY',
                 'AY',
                 'FIN',
                 'Finnair',
                 'FI',
                 'OneWorld',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS',
                 'VS',
                 'VIR',
                 'Virgin Atlantic',
                 'GB',
                 'SkyTeam',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK',
                 'TK',
                 'THY',
                 'Turkish Airlines',
                 'TR',
                 'Star Alliance',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK',
                 'EK',
                 'UAE',
                 'Emirates',
                 'AE',
                 '',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR',
                 'QR',
                 'QTR',
                 'Qatar Airways',
                 'QA',
                 'OneWorld',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY',
                 'EY',
                 'ETD',
                 'Etihad Airways',
                 'AE',
                 '',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'SQ',
                 'SIA',
                 'Singapore Airlines',
                 'SG',
                 'Star Alliance',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX',
                 'CX',
                 'CPA',
                 'Cathay Pacific',
                 'HK',
                 'OneWorld',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG',
                 'TG',
                 'THA',
                 'Thai Airways International',
                 'TH',
                 'Star Alliance',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'NH',
                 'ANA',
                 'All Nippon Airways',
                 'JP',
                 'Star Alliance',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'JL',
                 'JAL',
                 'Japan Airlines',
                 'JP',
                 'OneWorld',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE',
                 'KE',
                 'KAL',
                 'Korean Air',
                 'KR',
                 'SkyTeam',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ',
                 'OZ',
                 'AAR',
                 'Asiana Airlines',
                 'KR',
                 'Star Alliance',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF',
                 'QF',
                 'QFA',
                 'Qantas',
                 'AU',
                 'OneWorld',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ',
                 'CZ',
                 'CSN',
                 'China Southern',
                 'CN',
                 '',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU',
                 'MU',
                 'CES',
                 'China Eastern',
                 'CN',
                 'SkyTeam',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU']},
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
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA',
                 'CA',
                 'CCA',
                 'Air China',
                 'CN',
                 'Star Alliance',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_offer_source (\n'
         '        vertex_id, source_id, source_type, adapter_key, base_url,\n'
         '        auth_scheme, auth_env_key, cadence_minutes, rate_limit_rpm,\n'
         '        airlines_count, coverage_note, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5,\n'
         '             $6, $7,\n'
         '             CAST($8 AS bigint), CAST($9 AS bigint),\n'
         '             CAST($10 AS bigint), $11, $12, $13,\n'
         '             1, $14, $15, $16\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_offer_source WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'amadeus',
                 'gds',
                 'amadeus',
                 'https://test.api.amadeus.com',
                 'oauth2_client_credentials',
                 'AMADEUS_CLIENT_ID,AMADEUS_CLIENT_SECRET',
                 360,
                 10,
                 440,
                 'Amadeus Self-Service Flight Offers Search v2. Full GDS coverage.',
                 'active',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_offer_source (\n'
         '        vertex_id, source_id, source_type, adapter_key, base_url,\n'
         '        auth_scheme, auth_env_key, cadence_minutes, rate_limit_rpm,\n'
         '        airlines_count, coverage_note, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5,\n'
         '             $6, $7,\n'
         '             CAST($8 AS bigint), CAST($9 AS bigint),\n'
         '             CAST($10 AS bigint), $11, $12, $13,\n'
         '             1, $14, $15, $16\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_offer_source WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'duffel',
                 'gds_ndc',
                 'duffel',
                 'https://api.duffel.com',
                 'bearer',
                 'DUFFEL_API_KEY',
                 360,
                 60,
                 380,
                 'Duffel air offer requests v2. NDC + GDS aggregator.',
                 'active',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_offer_source (\n'
         '        vertex_id, source_id, source_type, adapter_key, base_url,\n'
         '        auth_scheme, auth_env_key, cadence_minutes, rate_limit_rpm,\n'
         '        airlines_count, coverage_note, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5,\n'
         '             $6, $7,\n'
         '             CAST($8 AS bigint), CAST($9 AS bigint),\n'
         '             CAST($10 AS bigint), $11, $12, $13,\n'
         '             1, $14, $15, $16\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_offer_source WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'kiwi-tequila',
                 'metasearch',
                 'kiwi',
                 'https://api.tequila.kiwi.com',
                 'api_key',
                 'KIWI_TEQUILA_API_KEY',
                 360,
                 30,
                 750,
                 'Kiwi.com Tequila Search API. Metasearch incl. virtual interlining.',
                 'stub',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_offer_source (\n'
         '        vertex_id, source_id, source_type, adapter_key, base_url,\n'
         '        auth_scheme, auth_env_key, cadence_minutes, rate_limit_rpm,\n'
         '        airlines_count, coverage_note, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5,\n'
         '             $6, $7,\n'
         '             CAST($8 AS bigint), CAST($9 AS bigint),\n'
         '             CAST($10 AS bigint), $11, $12, $13,\n'
         '             1, $14, $15, $16\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_offer_source WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'travelpayouts-aviasales',
                 'metasearch',
                 'travelpayouts',
                 'https://api.travelpayouts.com',
                 'api_key',
                 'TRAVELPAYOUTS_TOKEN',
                 720,
                 60,
                 700,
                 'Travelpayouts (Aviasales) data API. Cheapest cached prices.',
                 'stub',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_offer_source (\n'
         '        vertex_id, source_id, source_type, adapter_key, base_url,\n'
         '        auth_scheme, auth_env_key, cadence_minutes, rate_limit_rpm,\n'
         '        airlines_count, coverage_note, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5,\n'
         '             $6, $7,\n'
         '             CAST($8 AS bigint), CAST($9 AS bigint),\n'
         '             CAST($10 AS bigint), $11, $12, $13,\n'
         '             1, $14, $15, $16\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_offer_source WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'skyscanner-affiliate',
                 'metasearch',
                 'skyscanner',
                 'https://partners.api.skyscanner.net',
                 'api_key',
                 'SKYSCANNER_API_KEY',
                 720,
                 20,
                 1200,
                 'Skyscanner B2B Affiliate API. Highest carrier breadth; B2B only.',
                 'planned',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_offer_source (\n'
         '        vertex_id, source_id, source_type, adapter_key, base_url,\n'
         '        auth_scheme, auth_env_key, cadence_minutes, rate_limit_rpm,\n'
         '        airlines_count, coverage_note, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5,\n'
         '             $6, $7,\n'
         '             CAST($8 AS bigint), CAST($9 AS bigint),\n'
         '             CAST($10 AS bigint), $11, $12, $13,\n'
         '             1, $14, $15, $16\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_offer_source WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/ana-ndc',
                 'ana-ndc',
                 'direct_ndc',
                 'anaNdc',
                 'https://ndc.ana.co.jp',
                 'oauth2_client_credentials',
                 'ANA_NDC_CLIENT_ID,ANA_NDC_CLIENT_SECRET',
                 240,
                 30,
                 1,
                 'ANA Direct NDC. Marketing carrier NH only.',
                 'planned',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/ana-ndc']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_offer_source (\n'
         '        vertex_id, source_id, source_type, adapter_key, base_url,\n'
         '        auth_scheme, auth_env_key, cadence_minutes, rate_limit_rpm,\n'
         '        airlines_count, coverage_note, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5,\n'
         '             $6, $7,\n'
         '             CAST($8 AS bigint), CAST($9 AS bigint),\n'
         '             CAST($10 AS bigint), $11, $12, $13,\n'
         '             1, $14, $15, $16\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_offer_source WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/jal-ndc',
                 'jal-ndc',
                 'direct_ndc',
                 'jalNdc',
                 'https://ndc.jal.co.jp',
                 'oauth2_client_credentials',
                 'JAL_NDC_CLIENT_ID,JAL_NDC_CLIENT_SECRET',
                 240,
                 30,
                 1,
                 'JAL Direct NDC. Marketing carrier JL only.',
                 'planned',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/jal-ndc']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_offer_source (\n'
         '        vertex_id, source_id, source_type, adapter_key, base_url,\n'
         '        auth_scheme, auth_env_key, cadence_minutes, rate_limit_rpm,\n'
         '        airlines_count, coverage_note, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, $4, $5,\n'
         '             $6, $7,\n'
         '             CAST($8 AS bigint), CAST($9 AS bigint),\n'
         '             CAST($10 AS bigint), $11, $12, $13,\n'
         '             1, $14, $15, $16\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_offer_source WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub',
                 'stub',
                 'stub',
                 'stub',
                 '',
                 'none',
                 '',
                 60,
                 600,
                 3,
                 'Deterministic fixture (NH/JL/SQ). Dev-only fallback.',
                 'active',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA',
                 'amadeus',
                 'AA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL',
                 'amadeus',
                 'DL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA',
                 'amadeus',
                 'UA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN',
                 'amadeus',
                 'WN',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6',
                 'amadeus',
                 'B6',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS',
                 'amadeus',
                 'AS',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC',
                 'amadeus',
                 'AC',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH',
                 'amadeus',
                 'LH',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF',
                 'amadeus',
                 'AF',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL',
                 'amadeus',
                 'KL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA',
                 'amadeus',
                 'BA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB',
                 'amadeus',
                 'IB',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ',
                 'amadeus',
                 'AZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY',
                 'amadeus',
                 'AY',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS',
                 'amadeus',
                 'VS',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK',
                 'amadeus',
                 'TK',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK',
                 'amadeus',
                 'EK',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR',
                 'amadeus',
                 'QR',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY',
                 'amadeus',
                 'EY',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'amadeus',
                 'SQ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX',
                 'amadeus',
                 'CX',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG',
                 'amadeus',
                 'TG',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'amadeus',
                 'NH',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'amadeus',
                 'JL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE',
                 'amadeus',
                 'KE',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ',
                 'amadeus',
                 'OZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF',
                 'amadeus',
                 'QF',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ',
                 'amadeus',
                 'CZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU',
                 'amadeus',
                 'MU',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA',
                 'amadeus',
                 'CA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA',
                 'duffel',
                 'AA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL',
                 'duffel',
                 'DL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA',
                 'duffel',
                 'UA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN',
                 'duffel',
                 'WN',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6',
                 'duffel',
                 'B6',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS',
                 'duffel',
                 'AS',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC',
                 'duffel',
                 'AC',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH',
                 'duffel',
                 'LH',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF',
                 'duffel',
                 'AF',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL',
                 'duffel',
                 'KL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA',
                 'duffel',
                 'BA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB',
                 'duffel',
                 'IB',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ',
                 'duffel',
                 'AZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY',
                 'duffel',
                 'AY',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS',
                 'duffel',
                 'VS',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK',
                 'duffel',
                 'TK',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK',
                 'duffel',
                 'EK',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR',
                 'duffel',
                 'QR',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY',
                 'duffel',
                 'EY',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'duffel',
                 'SQ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX',
                 'duffel',
                 'CX',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG',
                 'duffel',
                 'TG',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'duffel',
                 'NH',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'duffel',
                 'JL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE',
                 'duffel',
                 'KE',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ',
                 'duffel',
                 'OZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF',
                 'duffel',
                 'QF',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ',
                 'duffel',
                 'CZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU',
                 'duffel',
                 'MU',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA',
                 'duffel',
                 'CA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA',
                 'kiwi-tequila',
                 'AA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL',
                 'kiwi-tequila',
                 'DL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA',
                 'kiwi-tequila',
                 'UA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN',
                 'kiwi-tequila',
                 'WN',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6',
                 'kiwi-tequila',
                 'B6',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS',
                 'kiwi-tequila',
                 'AS',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC',
                 'kiwi-tequila',
                 'AC',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH',
                 'kiwi-tequila',
                 'LH',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF',
                 'kiwi-tequila',
                 'AF',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL',
                 'kiwi-tequila',
                 'KL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA',
                 'kiwi-tequila',
                 'BA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB',
                 'kiwi-tequila',
                 'IB',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ',
                 'kiwi-tequila',
                 'AZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY',
                 'kiwi-tequila',
                 'AY',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS',
                 'kiwi-tequila',
                 'VS',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK',
                 'kiwi-tequila',
                 'TK',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK',
                 'kiwi-tequila',
                 'EK',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR',
                 'kiwi-tequila',
                 'QR',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY',
                 'kiwi-tequila',
                 'EY',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'kiwi-tequila',
                 'SQ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX',
                 'kiwi-tequila',
                 'CX',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG',
                 'kiwi-tequila',
                 'TG',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'kiwi-tequila',
                 'NH',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'kiwi-tequila',
                 'JL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE',
                 'kiwi-tequila',
                 'KE',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ',
                 'kiwi-tequila',
                 'OZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF',
                 'kiwi-tequila',
                 'QF',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ',
                 'kiwi-tequila',
                 'CZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU',
                 'kiwi-tequila',
                 'MU',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA',
                 'kiwi-tequila',
                 'CA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA',
                 'travelpayouts-aviasales',
                 'AA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL',
                 'travelpayouts-aviasales',
                 'DL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA',
                 'travelpayouts-aviasales',
                 'UA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN',
                 'travelpayouts-aviasales',
                 'WN',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6',
                 'travelpayouts-aviasales',
                 'B6',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS',
                 'travelpayouts-aviasales',
                 'AS',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC',
                 'travelpayouts-aviasales',
                 'AC',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH',
                 'travelpayouts-aviasales',
                 'LH',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF',
                 'travelpayouts-aviasales',
                 'AF',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL',
                 'travelpayouts-aviasales',
                 'KL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA',
                 'travelpayouts-aviasales',
                 'BA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB',
                 'travelpayouts-aviasales',
                 'IB',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ',
                 'travelpayouts-aviasales',
                 'AZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY',
                 'travelpayouts-aviasales',
                 'AY',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS',
                 'travelpayouts-aviasales',
                 'VS',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK',
                 'travelpayouts-aviasales',
                 'TK',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK',
                 'travelpayouts-aviasales',
                 'EK',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR',
                 'travelpayouts-aviasales',
                 'QR',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY',
                 'travelpayouts-aviasales',
                 'EY',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'travelpayouts-aviasales',
                 'SQ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX',
                 'travelpayouts-aviasales',
                 'CX',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG',
                 'travelpayouts-aviasales',
                 'TG',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'travelpayouts-aviasales',
                 'NH',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'travelpayouts-aviasales',
                 'JL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE',
                 'travelpayouts-aviasales',
                 'KE',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ',
                 'travelpayouts-aviasales',
                 'OZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF',
                 'travelpayouts-aviasales',
                 'QF',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ',
                 'travelpayouts-aviasales',
                 'CZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU',
                 'travelpayouts-aviasales',
                 'MU',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA',
                 'travelpayouts-aviasales',
                 'CA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA',
                 'skyscanner-affiliate',
                 'AA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL',
                 'skyscanner-affiliate',
                 'DL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA',
                 'skyscanner-affiliate',
                 'UA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN',
                 'skyscanner-affiliate',
                 'WN',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6',
                 'skyscanner-affiliate',
                 'B6',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS',
                 'skyscanner-affiliate',
                 'AS',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC',
                 'skyscanner-affiliate',
                 'AC',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH',
                 'skyscanner-affiliate',
                 'LH',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF',
                 'skyscanner-affiliate',
                 'AF',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL',
                 'skyscanner-affiliate',
                 'KL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA',
                 'skyscanner-affiliate',
                 'BA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB',
                 'skyscanner-affiliate',
                 'IB',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ',
                 'skyscanner-affiliate',
                 'AZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY',
                 'skyscanner-affiliate',
                 'AY',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS',
                 'skyscanner-affiliate',
                 'VS',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK',
                 'skyscanner-affiliate',
                 'TK',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK',
                 'skyscanner-affiliate',
                 'EK',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR',
                 'skyscanner-affiliate',
                 'QR',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY',
                 'skyscanner-affiliate',
                 'EY',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'skyscanner-affiliate',
                 'SQ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX',
                 'skyscanner-affiliate',
                 'CX',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG',
                 'skyscanner-affiliate',
                 'TG',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'skyscanner-affiliate',
                 'NH',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'skyscanner-affiliate',
                 'JL',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE',
                 'skyscanner-affiliate',
                 'KE',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ',
                 'skyscanner-affiliate',
                 'OZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF',
                 'skyscanner-affiliate',
                 'QF',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ',
                 'skyscanner-affiliate',
                 'CZ',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU',
                 'skyscanner-affiliate',
                 'MU',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA',
                 'skyscanner-affiliate',
                 'CA',
                 'primary',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/ana-ndc|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/ana-ndc',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'ana-ndc',
                 'NH',
                 'exclusive',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/ana-ndc|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/jal-ndc|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/jal-ndc',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'jal-ndc',
                 'JL',
                 'exclusive',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/jal-ndc|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH',
                 'stub',
                 'NH',
                 'fixture',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL',
                 'stub',
                 'JL',
                 'fixture',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': '\n'
         '      INSERT INTO edge_flight_offer_source_covers_airline (\n'
         '        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,\n'
         '        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3,\n'
         '             $4, $5, $6,\n'
         "             '', $7, 1, $8, $9, $10\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE '
         'edge_id = $11)\n'
         '    ',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ',
                 'stub',
                 'SQ',
                 'fixture',
                 '2026-04-27T15:01:00Z',
                 'did:web:flight-offer.etzhayyim.com',
                 'did:web:flight-offer.etzhayyim.com',
                 'sys.bpmn.seed.flight-offer',
                 'at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']}]

DOWN = [{'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/ana-ndc|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/jal-ndc|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': 'DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub|covers|at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
 {'sql': 'DELETE FROM vertex_flight_offer_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/amadeus']},
 {'sql': 'DELETE FROM vertex_flight_offer_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/duffel']},
 {'sql': 'DELETE FROM vertex_flight_offer_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/kiwi-tequila']},
 {'sql': 'DELETE FROM vertex_flight_offer_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/travelpayouts-aviasales']},
 {'sql': 'DELETE FROM vertex_flight_offer_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/skyscanner-affiliate']},
 {'sql': 'DELETE FROM vertex_flight_offer_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/ana-ndc']},
 {'sql': 'DELETE FROM vertex_flight_offer_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/jal-ndc']},
 {'sql': 'DELETE FROM vertex_flight_offer_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.source/stub']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AA']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/DL']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/UA']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/WN']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/B6']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AS']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AC']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/LH']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AF']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KL']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/BA']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/IB']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AZ']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/AY']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/VS']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TK']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EK']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QR']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/EY']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/SQ']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CX']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/TG']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/NH']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/JL']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/KE']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/OZ']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/QF']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CZ']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/MU']},
 {'sql': 'DELETE FROM vertex_airline WHERE vertex_id = $1',
  'parameters': ['at://did:web:flight-offer.etzhayyim.com/com.etzhayyim.apps.flightOffer.airline/CA']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
