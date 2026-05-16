"""Captured from Kysely migration 20260424360000_udf_osm_notes_plus_seed."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424360000_udf_osm_notes_plus_seed"
down_revision = 'r_20260424350000_seed_wikidata_urban_10'
branch_labels = None
depends_on = None

UP = [{'sql': 'DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)', 'parameters': []},
 {'sql': '\n'
         '    CREATE FUNCTION maps_source_dispatch_kind(\n'
         '      source_did varchar,\n'
         '      label      varchar\n'
         '    ) RETURNS varchar\n'
         '    LANGUAGE sql\n'
         '    AS $$\n'
         '      SELECT CASE\n'
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:gleif'       THEN 'gleif'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:wikidata'    THEN "
         "'wikidata'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:wikidata:%'  THEN "
         "'wikidata'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:registry:%'           THEN "
         "'registry_other'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:wikipedia'            THEN "
         "'wikipedia'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:wikipedia:%'          THEN "
         "'wikipedia'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:wikivoyage'           THEN "
         "'wikivoyage'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:wikivoyage:%'         THEN "
         "'wikivoyage'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:commons'              THEN 'commons'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:commons:%'            THEN 'commons'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:inaturalist'          THEN "
         "'inaturalist'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:inaturalist:%'        THEN "
         "'inaturalist'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:gbif'                 THEN 'gbif'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:gbif:%'               THEN 'gbif'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:eonet'                THEN 'eonet'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:eonet:%'              THEN 'eonet'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:opensky'              THEN 'opensky'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:opensky:%'            THEN 'opensky'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:noaa_tides'           THEN "
         "'noaa_tides'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:noaa_tides:%'         THEN "
         "'noaa_tides'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:osm_notes'            THEN "
         "'osm_notes'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:osm_notes:%'          THEN "
         "'osm_notes'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:satellite'            THEN 'stac'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:satellite:%'          THEN 'stac'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:seismic'              THEN 'seismic'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:seismic:%'            THEN 'seismic'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:street_view'          THEN "
         "'mapillary'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:infrastructure'       THEN "
         "'overpass'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:geocode'              THEN "
         "'overpass'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:weather'              THEN "
         "'overpass'\n"
         "        WHEN source_did LIKE 'did:web:maps.gftd.ai:gtfs'                 THEN 'gtfs'\n"
         "        WHEN source_did LIKE 'did:web:site.gftd.ai'                      THEN "
         "'web_crawl'\n"
         "        ELSE 'unsupported'\n"
         '      END\n'
         '    $$\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    INSERT INTO vertex_maps_coverage_target (\n'
         '      vertex_id, source_did, label, world_total, priority_weight,\n'
         '      ttl_hours, org_id, user_id, actor_id, created_at\n'
         '    ) VALUES (\n'
         "      'at://did:web:maps.gftd.ai/ai.gftd.apps.maps.coverageTarget/osm_notes:Spot',\n"
         "      'did:web:maps.gftd.ai:osm_notes', 'Spot', 100000, 0.6, 168.0,\n"
         "      'anon', 'anon', 'did:web:maps.gftd.ai:osm_notes', $1\n"
         '    )\n'
         '  ',
  'parameters': ['2026-05-08T00:19:55.966Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS maps_source_dispatch_kind(varchar, varchar)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
