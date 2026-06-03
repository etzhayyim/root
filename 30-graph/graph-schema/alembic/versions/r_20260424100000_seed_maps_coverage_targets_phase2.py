"""Captured from Kysely migration 20260424100000_seed_maps_coverage_targets_phase2."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424100000_seed_maps_coverage_targets_phase2"
down_revision = 'r_20260424090000_mv_maps_collected_per_source_label'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/street_view:StreetChunk',
                 'did:web:maps.etzhayyim.com:street_view',
                 'StreetChunk',
                 50000000,
                 0.6,
                 720,
                 'did:web:maps.etzhayyim.com:street_view',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/satellite:SatelliteScene',
                 'did:web:maps.etzhayyim.com:satellite',
                 'SatelliteScene',
                 10000000,
                 0.6,
                 720,
                 'did:web:maps.etzhayyim.com:satellite',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/satellite:TerrainPatch',
                 'did:web:maps.etzhayyim.com:satellite',
                 'TerrainPatch',
                 14000000,
                 0.6,
                 720,
                 'did:web:maps.etzhayyim.com:satellite',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-uk-ch:LegalEntity',
                 'did:web:maps.etzhayyim.com:registry:uk-ch',
                 'LegalEntity',
                 5500000,
                 1,
                 168,
                 'did:web:maps.etzhayyim.com:registry:uk-ch',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-us-edgar:LegalEntity',
                 'did:web:maps.etzhayyim.com:registry:us-edgar',
                 'LegalEntity',
                 700000,
                 1,
                 168,
                 'did:web:maps.etzhayyim.com:registry:us-edgar',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-eu-br:LegalEntity',
                 'did:web:maps.etzhayyim.com:registry:eu-br',
                 'LegalEntity',
                 15000000,
                 1,
                 720,
                 'did:web:maps.etzhayyim.com:registry:eu-br',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/registry-jp-moj:LandRegistry',
                 'did:web:maps.etzhayyim.com:registry:jp-moj',
                 'LandRegistry',
                 200000000,
                 1,
                 720,
                 'did:web:maps.etzhayyim.com:registry:jp-moj',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:Port',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Port',
                 5000,
                 1,
                 168,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:Road',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Road',
                 20000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:Railway',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'Railway',
                 5000,
                 0.6,
                 168,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/infrastructure:EvCharger',
                 'did:web:maps.etzhayyim.com:infrastructure',
                 'EvCharger',
                 100000,
                 0.3,
                 168,
                 'did:web:maps.etzhayyim.com:infrastructure',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/seismic:SpatialEvent',
                 'did:web:maps.etzhayyim.com:seismic',
                 'SpatialEvent',
                 100000,
                 0.3,
                 1,
                 'did:web:maps.etzhayyim.com:seismic',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         '        $1, $2, $3, $4, $5,\n'
         "        $6, 'anon', 'anon', $7, $8\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/did-web-site-etzhayyim-ai:WebCrawlGeoEntity',
                 'did:web:site.etzhayyim.com',
                 'WebCrawlGeoEntity',
                 1000000,
                 0.3,
                 168,
                 'did:web:site.etzhayyim.com',
                 '2026-05-08T00:12:41.282Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
