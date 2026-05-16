"""Captured from Kysely migration 20260505183000_aircraft_graph_phase3."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260505183000_aircraft_graph_phase3"
down_revision = 'r_20260505140000_seed_aria_market_emotion_influence_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': 'ALTER TABLE vertex_aircraft_state ADD COLUMN IF NOT EXISTS aircraft_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_aircraft_track ADD COLUMN IF NOT EXISTS aircraft_did VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_aircraft ADD COLUMN IF NOT EXISTS registration_country_iso2 VARCHAR',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_aircraft ADD COLUMN IF NOT EXISTS purpose_code VARCHAR',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_aircraft_part (\n'
         '      vertex_id            VARCHAR PRIMARY KEY,\n'
         '      part_kind            VARCHAR,\n'
         '      manufacturer_did     VARCHAR,\n'
         '      manufacturer_lei     VARCHAR,\n'
         '      model_number         VARCHAR,\n'
         '      serial_number        VARCHAR,\n'
         '      certification_authority VARCHAR,\n'
         '      certification_id     VARCHAR,\n'
         '      installed_at         VARCHAR,\n'
         '      removed_at           VARCHAR,\n'
         '      source_url           VARCHAR,\n'
         '      source_license       VARCHAR,\n'
         "      actor_did            VARCHAR DEFAULT 'did:web:maps.gftd.ai:flightradar',\n"
         "      org_did              VARCHAR DEFAULT 'anon',\n"
         '      sensitivity_ord      INTEGER DEFAULT 1,\n'
         "      owner_did            VARCHAR DEFAULT 'did:web:maps.gftd.ai',\n"
         '      created_at           VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_aircraft_part_kind ON vertex_aircraft_part (part_kind)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_aircraft_part_manufacturer_lei ON vertex_aircraft_part '
         '(manufacturer_lei)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_aircraft_has_part (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR,\n'
         '      dst_vid          VARCHAR,\n'
         '      _seq             BIGINT,\n'
         '      created_date     VARCHAR,\n'
         '      sensitivity_ord  INTEGER DEFAULT 1,\n'
         '      owner_did        VARCHAR,\n'
         '      effective_from   VARCHAR,\n'
         '      effective_to     VARCHAR,\n'
         '      role             VARCHAR,\n'
         '      source_url       VARCHAR,\n'
         '      source_license   VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_aircraft_has_part_src ON edge_aircraft_has_part (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_aircraft_has_part_dst ON edge_aircraft_has_part (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_aircraft_part_made_by (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR,\n'
         '      dst_vid          VARCHAR,\n'
         '      _seq             BIGINT,\n'
         '      created_date     VARCHAR,\n'
         '      sensitivity_ord  INTEGER DEFAULT 1,\n'
         '      owner_did        VARCHAR,\n'
         '      effective_from   VARCHAR,\n'
         '      effective_to     VARCHAR,\n'
         '      source_url       VARCHAR,\n'
         '      source_license   VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_aircraft_part_made_by_src ON edge_aircraft_part_made_by '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_aircraft_part_made_by_dst ON edge_aircraft_part_made_by '
         '(dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_flight_purpose (\n'
         '      vertex_id            VARCHAR PRIMARY KEY,\n'
         '      purpose_code         VARCHAR,\n'
         '      label_en             VARCHAR,\n'
         '      label_ja             VARCHAR,\n'
         '      description          VARCHAR,\n'
         '      regulated_under      VARCHAR,\n'
         "      actor_did            VARCHAR DEFAULT 'did:web:maps.gftd.ai:flightradar',\n"
         "      org_did              VARCHAR DEFAULT 'anon',\n"
         '      sensitivity_ord      INTEGER DEFAULT 1,\n'
         "      owner_did            VARCHAR DEFAULT 'did:web:maps.gftd.ai',\n"
         '      created_at           VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_flight_purpose_code ON vertex_flight_purpose '
         '(purpose_code)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_flight_serves_purpose (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR,\n'
         '      dst_vid          VARCHAR,\n'
         '      _seq             BIGINT,\n'
         '      created_date     VARCHAR,\n'
         '      sensitivity_ord  INTEGER DEFAULT 1,\n'
         '      owner_did        VARCHAR,\n'
         '      effective_from   VARCHAR,\n'
         '      effective_to     VARCHAR,\n'
         '      passenger_count  INTEGER,\n'
         '      cargo_kg         DOUBLE PRECISION,\n'
         '      source_url       VARCHAR,\n'
         '      source_license   VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_flight_serves_purpose_src ON edge_flight_serves_purpose '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_flight_serves_purpose_dst ON edge_flight_serves_purpose '
         '(dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_aircraft_state_for_aircraft (\n'
         '      edge_id          VARCHAR PRIMARY KEY,\n'
         '      src_vid          VARCHAR,\n'
         '      dst_vid          VARCHAR,\n'
         '      _seq             BIGINT,\n'
         '      created_date     VARCHAR,\n'
         '      sensitivity_ord  INTEGER DEFAULT 1,\n'
         "      owner_did        VARCHAR DEFAULT 'did:web:maps.gftd.ai',\n"
         '      ts_ms            BIGINT\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_aircraft_state_for_aircraft_src ON '
         'edge_aircraft_state_for_aircraft (src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_aircraft_state_for_aircraft_dst ON '
         'edge_aircraft_state_for_aircraft (dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_purpose (\n'
         '        vertex_id, purpose_code, label_en, label_ja, description, regulated_under, '
         'created_at\n'
         '      )\n'
         "      SELECT $1, $2, $3, $4, $5, 'ICAO Annex 6 + Chicago Convention Art. 3', $6\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_purpose WHERE vertex_id = $7)\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/passenger',
                 'passenger',
                 'Passenger transport',
                 '旅客輸送',
                 'Scheduled or charter passenger flight (ICAO Annex 6 Part I)',
                 '2026-05-05T18:30:00Z',
                 'at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/passenger']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_purpose (\n'
         '        vertex_id, purpose_code, label_en, label_ja, description, regulated_under, '
         'created_at\n'
         '      )\n'
         "      SELECT $1, $2, $3, $4, $5, 'ICAO Annex 6 + Chicago Convention Art. 3', $6\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_purpose WHERE vertex_id = $7)\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/cargo',
                 'cargo',
                 'Cargo transport',
                 '貨物輸送',
                 'Dedicated freight or mail transport',
                 '2026-05-05T18:30:00Z',
                 'at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/cargo']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_purpose (\n'
         '        vertex_id, purpose_code, label_en, label_ja, description, regulated_under, '
         'created_at\n'
         '      )\n'
         "      SELECT $1, $2, $3, $4, $5, 'ICAO Annex 6 + Chicago Convention Art. 3', $6\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_purpose WHERE vertex_id = $7)\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/military',
                 'military',
                 'Military operation',
                 '軍用機',
                 'State aircraft per Chicago Convention Art. 3',
                 '2026-05-05T18:30:00Z',
                 'at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/military']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_purpose (\n'
         '        vertex_id, purpose_code, label_en, label_ja, description, regulated_under, '
         'created_at\n'
         '      )\n'
         "      SELECT $1, $2, $3, $4, $5, 'ICAO Annex 6 + Chicago Convention Art. 3', $6\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_purpose WHERE vertex_id = $7)\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/medevac',
                 'medevac',
                 'Medical evacuation',
                 '救急医療搬送',
                 'Emergency or scheduled HEMS / air ambulance',
                 '2026-05-05T18:30:00Z',
                 'at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/medevac']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_purpose (\n'
         '        vertex_id, purpose_code, label_en, label_ja, description, regulated_under, '
         'created_at\n'
         '      )\n'
         "      SELECT $1, $2, $3, $4, $5, 'ICAO Annex 6 + Chicago Convention Art. 3', $6\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_purpose WHERE vertex_id = $7)\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/training',
                 'training',
                 'Flight training',
                 '訓練',
                 'Type rating / instructional flight',
                 '2026-05-05T18:30:00Z',
                 'at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/training']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_purpose (\n'
         '        vertex_id, purpose_code, label_en, label_ja, description, regulated_under, '
         'created_at\n'
         '      )\n'
         "      SELECT $1, $2, $3, $4, $5, 'ICAO Annex 6 + Chicago Convention Art. 3', $6\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_purpose WHERE vertex_id = $7)\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/test',
                 'test',
                 'Test / ferry',
                 '試験飛行',
                 'Production test, post-maintenance, ferry',
                 '2026-05-05T18:30:00Z',
                 'at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/test']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_purpose (\n'
         '        vertex_id, purpose_code, label_en, label_ja, description, regulated_under, '
         'created_at\n'
         '      )\n'
         "      SELECT $1, $2, $3, $4, $5, 'ICAO Annex 6 + Chicago Convention Art. 3', $6\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_purpose WHERE vertex_id = $7)\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/private',
                 'private',
                 'Private / general aviation',
                 '一般航空',
                 'Non-commercial private operation (Part 91)',
                 '2026-05-05T18:30:00Z',
                 'at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/private']},
 {'sql': '\n'
         '      INSERT INTO vertex_flight_purpose (\n'
         '        vertex_id, purpose_code, label_en, label_ja, description, regulated_under, '
         'created_at\n'
         '      )\n'
         "      SELECT $1, $2, $3, $4, $5, 'ICAO Annex 6 + Chicago Convention Art. 3', $6\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_purpose WHERE vertex_id = $7)\n'
         '    ',
  'parameters': ['at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/government',
                 'government',
                 'Government / state',
                 '政府専用',
                 'Head-of-state, customs, law-enforcement, SAR (non-military)',
                 '2026-05-05T18:30:00Z',
                 'at://did:web:maps.gftd.ai/ai.gftd.apps.maps.flightPurpose/government']}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS edge_aircraft_state_for_aircraft', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_flight_serves_purpose', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_flight_purpose', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_aircraft_part_made_by', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_aircraft_has_part', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_aircraft_part', 'parameters': []},
 {'sql': 'ALTER TABLE vertex_aircraft DROP COLUMN IF EXISTS purpose_code', 'parameters': []},
 {'sql': 'ALTER TABLE vertex_aircraft DROP COLUMN IF EXISTS registration_country_iso2',
  'parameters': []},
 {'sql': 'ALTER TABLE vertex_aircraft_track DROP COLUMN IF EXISTS aircraft_did', 'parameters': []},
 {'sql': 'ALTER TABLE vertex_aircraft_state DROP COLUMN IF EXISTS aircraft_did', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
