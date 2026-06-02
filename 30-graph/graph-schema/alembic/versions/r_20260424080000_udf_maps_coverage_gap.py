"""Captured from Kysely migration 20260424080000_udf_maps_coverage_gap."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424080000_udf_maps_coverage_gap"
down_revision = 'r_20260424030000_vertex_human_task_bpmn_columns'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_maps_coverage_target (\n'
         '      vertex_id        varchar NOT NULL PRIMARY KEY,\n'
         '      source_did       varchar NOT NULL,\n'
         '      label            varchar NOT NULL,\n'
         '      world_total      bigint  NOT NULL,\n'
         '      collected_count  bigint  NOT NULL DEFAULT 0,\n'
         '      priority_weight  real    NOT NULL DEFAULT 0.5,\n'
         '      last_fetched_at  timestamp,\n'
         '      ttl_hours        real    NOT NULL DEFAULT 168.0,\n'
         "      org_id           varchar NOT NULL DEFAULT 'anon',\n"
         "      user_id          varchar NOT NULL DEFAULT 'anon',\n"
         "      actor_id         varchar NOT NULL DEFAULT '',\n"
         '      created_at       varchar NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS maps_coverage_gap_score(bigint, bigint, real, real)',
  'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS maps_coverage_gap_score(bigint, bigint, real, double precision)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE FUNCTION maps_coverage_gap_score(\n'
         '      collected         bigint,\n'
         '      world_total       bigint,\n'
         '      priority_weight   real,\n'
         '      hours_since_fetch double precision\n'
         '    ) RETURNS double precision\n'
         '    LANGUAGE sql\n'
         '    AS $$\n'
         '      SELECT\n'
         '        COALESCE(priority_weight, 0.5)::double precision\n'
         '        * (1.0 - LEAST(1.0,\n'
         '            COALESCE(collected, 0)::double precision\n'
         '              / GREATEST(COALESCE(world_total, 1), 1)::double precision))\n'
         '        * LEAST(10.0, 1.0 + COALESCE(hours_since_fetch, 24.0)::double precision / 24.0)\n'
         '    $$\n'
         '  ',
  'parameters': []},
 {'sql': 'DROP VIEW IF EXISTS view_maps_coverage_gap_ranked', 'parameters': []},
 {'sql': '\n'
         '    CREATE VIEW view_maps_coverage_gap_ranked AS\n'
         '    SELECT\n'
         '      vertex_id,\n'
         '      source_did,\n'
         '      label,\n'
         '      collected_count,\n'
         '      world_total,\n'
         '      priority_weight,\n'
         '      last_fetched_at,\n'
         '      ttl_hours,\n'
         '      CASE\n'
         '        WHEN last_fetched_at IS NULL THEN ttl_hours\n'
         '        ELSE EXTRACT(EPOCH FROM (NOW() - last_fetched_at))::real / 3600.0\n'
         '      END AS hours_since_fetch,\n'
         '      maps_coverage_gap_score(\n'
         '        collected_count,\n'
         '        world_total,\n'
         '        priority_weight,\n'
         '        CASE\n'
         '          WHEN last_fetched_at IS NULL THEN ttl_hours\n'
         '          ELSE EXTRACT(EPOCH FROM (NOW() - last_fetched_at))::real / 3600.0\n'
         '        END\n'
         '      ) AS gap_score\n'
         '    FROM vertex_maps_coverage_target\n'
         '    ORDER BY gap_score DESC\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-gleif:LegalEntity',
                 'did:web:maps.etzhayyim.com:registry:gleif',
                 'LegalEntity',
                 2500000,
                 1,
                 'did:web:maps.etzhayyim.com:registry:gleif',
                 '2026-05-08T00:12:34.400Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-jp-nta:LegalEntity',
                 'did:web:maps.etzhayyim.com:registry:jp-nta',
                 'LegalEntity',
                 6000000,
                 1,
                 'did:web:maps.etzhayyim.com:registry:jp-nta',
                 '2026-05-08T00:12:34.400Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-wikidata:LegalEntity',
                 'did:web:maps.etzhayyim.com:registry:wikidata',
                 'LegalEntity',
                 500000,
                 1,
                 'did:web:maps.etzhayyim.com:registry:wikidata',
                 '2026-05-08T00:12:34.400Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-openaddresses:Place',
                 'did:web:maps.etzhayyim.com:registry:openaddresses',
                 'Place',
                 1000000000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:openaddresses',
                 '2026-05-08T00:12:34.400Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-opencorporates:LegalEntity',
                 'did:web:maps.etzhayyim.com:registry:opencorporates',
                 'LegalEntity',
                 200000000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:opencorporates',
                 '2026-05-08T00:12:34.400Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-osm:Place',
                 'did:web:maps.etzhayyim.com:registry:osm',
                 'Place',
                 50000000,
                 0.3,
                 'did:web:maps.etzhayyim.com:registry:osm',
                 '2026-05-08T00:12:34.400Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:Building',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Building',
                 10000000,
                 0.6,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:12:34.400Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:Airport',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Airport',
                 3000,
                 1,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:12:34.400Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:Station',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Station',
                 10000,
                 0.6,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:12:34.400Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:AdminArea',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'AdminArea',
                 7800,
                 1,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:12:34.400Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/satellite:SatelliteScene',
                 'did:web:maps.etzhayyim.com:satellite',
                 'SatelliteScene',
                 500000,
                 0.3,
                 'did:web:maps.etzhayyim.com:satellite',
                 '2026-05-08T00:12:34.400Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        168.0, 'anon', 'anon', $6, $7\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/gtfs:BusRoute',
                 'did:web:maps.etzhayyim.com:gtfs',
                 'BusRoute',
                 50000,
                 0.6,
                 'did:web:maps.etzhayyim.com:gtfs',
                 '2026-05-08T00:12:34.400Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': 'DROP VIEW IF EXISTS view_maps_coverage_gap_ranked', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS maps_coverage_gap_score(bigint, bigint, real, double precision)',
  'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_maps_coverage_target', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
