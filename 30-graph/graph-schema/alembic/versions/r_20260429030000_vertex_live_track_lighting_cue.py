"""Captured from Kysely migration 20260429030000_vertex_live_track_lighting_cue."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429030000_vertex_live_track_lighting_cue"
down_revision = 'r_20260429020000_seed_live_post_chat_v2_federate'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_live_track (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      _seq BIGINT,\n'
         '      room_slug VARCHAR NOT NULL,\n'
         '      position BIGINT NOT NULL,\n'
         '      title VARCHAR NOT NULL,\n'
         '      bpm DOUBLE PRECISION NOT NULL,\n'
         '      length_beats BIGINT NOT NULL,\n'
         '      dance VARCHAR,\n'
         '      audio VARCHAR,\n'
         '      cues_json TEXT,\n'
         '      name VARCHAR,\n'
         '      description VARCHAR,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      at_did VARCHAR,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_live_lighting_cue (\n'
         '      vertex_id VARCHAR PRIMARY KEY,\n'
         '      _seq BIGINT,\n'
         '      room_slug VARCHAR NOT NULL,\n'
         '      fixture VARCHAR NOT NULL,\n'
         '      color_r DOUBLE PRECISION NOT NULL,\n'
         '      color_g DOUBLE PRECISION NOT NULL,\n'
         '      color_b DOUBLE PRECISION NOT NULL,\n'
         '      intensity DOUBLE PRECISION NOT NULL,\n'
         '      envelope VARCHAR NOT NULL,\n'
         '      envelope_param DOUBLE PRECISION,\n'
         '      bars BIGINT NOT NULL,\n'
         '      start_bar BIGINT NOT NULL,\n'
         '      name VARCHAR,\n'
         '      description VARCHAR,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      at_did VARCHAR,\n'
         '      created_at VARCHAR NOT NULL\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_live_room_track (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      _seq BIGINT,\n'
         '      src_vid VARCHAR NOT NULL,\n'
         '      dst_vid VARCHAR NOT NULL,\n'
         '      position BIGINT NOT NULL,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      at_did VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_live_room_lighting_cue (\n'
         '      edge_id VARCHAR PRIMARY KEY,\n'
         '      _seq BIGINT,\n'
         '      src_vid VARCHAR NOT NULL,\n'
         '      dst_vid VARCHAR NOT NULL,\n'
         '      start_bar BIGINT NOT NULL,\n'
         '      created_at VARCHAR NOT NULL,\n'
         '      actor_did VARCHAR NOT NULL,\n'
         '      org_did VARCHAR NOT NULL,\n'
         '      at_did VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '      INSERT INTO vertex_live_track (\n'
         '        vertex_id, room_slug, position, title, bpm, length_beats,\n'
         '        dance, audio, cues_json, name, description,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, 'demo', $2, $3, $4, $5,\n"
         '        $6, $7, $8,\n'
         '        $9,\n'
         '        $10,\n'
         "        'did:web:live.gftd.ai', 'anon', 'did:web:live.gftd.ai',\n"
         "        '2026-04-29T03:00:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:live.gftd.ai/ai.gftd.apps.live.track/demo-1',
                 1,
                 'Opener (Wota Call)',
                 128,
                 128,
                 'wota',
                 'opener',
                 '[{"atBeat":32,"kind":"drop","tag":"first-drop"},{"atBeat":96,"kind":"drop","tag":"second-drop"}]',
                 'Opener (Wota Call) (track #1)',
                 'Live track 1 of room demo — wota']},
 {'sql': '\n'
         '      INSERT INTO edge_live_room_track (\n'
         '        edge_id, src_vid, dst_vid, position, created_at,\n'
         '        actor_did, org_did, at_did\n'
         '      )\n'
         '      VALUES (\n'
         '        $1,\n'
         "        'at://did:web:live.gftd.ai/ai.gftd.apps.live.room/demo',\n"
         '        $2,\n'
         '        $3,\n'
         "        '2026-04-29T03:00:00Z',\n"
         "        'did:web:live.gftd.ai', 'anon', 'did:web:live.gftd.ai'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:live.gftd.ai/ai.gftd.apps.live.roomTrack/demo-1',
                 'at://did:web:live.gftd.ai/ai.gftd.apps.live.track/demo-1',
                 1]},
 {'sql': '\n'
         '      INSERT INTO vertex_live_track (\n'
         '        vertex_id, room_slug, position, title, bpm, length_beats,\n'
         '        dance, audio, cues_json, name, description,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, 'demo', $2, $3, $4, $5,\n"
         '        $6, $7, $8,\n'
         '        $9,\n'
         '        $10,\n'
         "        'did:web:live.gftd.ai', 'anon', 'did:web:live.gftd.ai',\n"
         "        '2026-04-29T03:00:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:live.gftd.ai/ai.gftd.apps.live.track/demo-2',
                 2,
                 'Ballad Breakdown',
                 92,
                 96,
                 'hold',
                 'ballad',
                 '[{"atBeat":16,"kind":"breakdown","tag":"sway"}]',
                 'Ballad Breakdown (track #2)',
                 'Live track 2 of room demo — hold']},
 {'sql': '\n'
         '      INSERT INTO edge_live_room_track (\n'
         '        edge_id, src_vid, dst_vid, position, created_at,\n'
         '        actor_did, org_did, at_did\n'
         '      )\n'
         '      VALUES (\n'
         '        $1,\n'
         "        'at://did:web:live.gftd.ai/ai.gftd.apps.live.room/demo',\n"
         '        $2,\n'
         '        $3,\n'
         "        '2026-04-29T03:00:00Z',\n"
         "        'did:web:live.gftd.ai', 'anon', 'did:web:live.gftd.ai'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:live.gftd.ai/ai.gftd.apps.live.roomTrack/demo-2',
                 'at://did:web:live.gftd.ai/ai.gftd.apps.live.track/demo-2',
                 2]},
 {'sql': '\n'
         '      INSERT INTO vertex_live_track (\n'
         '        vertex_id, room_slug, position, title, bpm, length_beats,\n'
         '        dance, audio, cues_json, name, description,\n'
         '        actor_did, org_did, at_did, created_at\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, 'demo', $2, $3, $4, $5,\n"
         '        $6, $7, $8,\n'
         '        $9,\n'
         '        $10,\n'
         "        'did:web:live.gftd.ai', 'anon', 'did:web:live.gftd.ai',\n"
         "        '2026-04-29T03:00:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:live.gftd.ai/ai.gftd.apps.live.track/demo-3',
                 3,
                 'K-Pop Encore',
                 140,
                 128,
                 'kpop-point',
                 'encore',
                 '[{"atBeat":16,"kind":"callout","tag":"hello-tokyo"},{"atBeat":64,"kind":"drop","tag":"encore-drop"}]',
                 'K-Pop Encore (track #3)',
                 'Live track 3 of room demo — kpop-point']},
 {'sql': '\n'
         '      INSERT INTO edge_live_room_track (\n'
         '        edge_id, src_vid, dst_vid, position, created_at,\n'
         '        actor_did, org_did, at_did\n'
         '      )\n'
         '      VALUES (\n'
         '        $1,\n'
         "        'at://did:web:live.gftd.ai/ai.gftd.apps.live.room/demo',\n"
         '        $2,\n'
         '        $3,\n'
         "        '2026-04-29T03:00:00Z',\n"
         "        'did:web:live.gftd.ai', 'anon', 'did:web:live.gftd.ai'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:live.gftd.ai/ai.gftd.apps.live.roomTrack/demo-3',
                 'at://did:web:live.gftd.ai/ai.gftd.apps.live.track/demo-3',
                 3]},
 {'sql': '\n'
         '      INSERT INTO vertex_live_lighting_cue (\n'
         '        vertex_id, room_slug, fixture, color_r, color_g, color_b,\n'
         '        intensity, envelope, envelope_param, bars, start_bar,\n'
         '        name, description, actor_did, org_did, at_did, created_at\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, 'demo', $2, $3, $4, $5,\n"
         '        $6, $7, $8, $9, $10,\n'
         '        $11,\n'
         '        $12,\n'
         "        'did:web:live.gftd.ai', 'anon', 'did:web:live.gftd.ai',\n"
         "        '2026-04-29T03:00:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:live.gftd.ai/ai.gftd.apps.live.lightingCue/demo-1',
                 'frontPar',
                 1,
                 0.55,
                 0.35,
                 0.85,
                 'breathe',
                 None,
                 16,
                 0,
                 'frontPar breathe #1',
                 'Lighting cue #1 for room demo — frontPar breathe']},
 {'sql': '\n'
         '      INSERT INTO edge_live_room_lighting_cue (\n'
         '        edge_id, src_vid, dst_vid, start_bar, created_at,\n'
         '        actor_did, org_did, at_did\n'
         '      )\n'
         '      VALUES (\n'
         '        $1,\n'
         "        'at://did:web:live.gftd.ai/ai.gftd.apps.live.room/demo',\n"
         '        $2,\n'
         '        $3,\n'
         "        '2026-04-29T03:00:00Z',\n"
         "        'did:web:live.gftd.ai', 'anon', 'did:web:live.gftd.ai'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:live.gftd.ai/ai.gftd.apps.live.roomLightingCue/demo-1',
                 'at://did:web:live.gftd.ai/ai.gftd.apps.live.lightingCue/demo-1',
                 0]},
 {'sql': '\n'
         '      INSERT INTO vertex_live_lighting_cue (\n'
         '        vertex_id, room_slug, fixture, color_r, color_g, color_b,\n'
         '        intensity, envelope, envelope_param, bars, start_bar,\n'
         '        name, description, actor_did, org_did, at_did, created_at\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, 'demo', $2, $3, $4, $5,\n"
         '        $6, $7, $8, $9, $10,\n'
         '        $11,\n'
         '        $12,\n'
         "        'did:web:live.gftd.ai', 'anon', 'did:web:live.gftd.ai',\n"
         "        '2026-04-29T03:00:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:live.gftd.ai/ai.gftd.apps.live.lightingCue/demo-2',
                 'laser',
                 0.2,
                 0.7,
                 1,
                 0.9,
                 'hold',
                 None,
                 24,
                 0,
                 'laser hold #2',
                 'Lighting cue #2 for room demo — laser hold']},
 {'sql': '\n'
         '      INSERT INTO edge_live_room_lighting_cue (\n'
         '        edge_id, src_vid, dst_vid, start_bar, created_at,\n'
         '        actor_did, org_did, at_did\n'
         '      )\n'
         '      VALUES (\n'
         '        $1,\n'
         "        'at://did:web:live.gftd.ai/ai.gftd.apps.live.room/demo',\n"
         '        $2,\n'
         '        $3,\n'
         "        '2026-04-29T03:00:00Z',\n"
         "        'did:web:live.gftd.ai', 'anon', 'did:web:live.gftd.ai'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:live.gftd.ai/ai.gftd.apps.live.roomLightingCue/demo-2',
                 'at://did:web:live.gftd.ai/ai.gftd.apps.live.lightingCue/demo-2',
                 0]},
 {'sql': '\n'
         '      INSERT INTO vertex_live_lighting_cue (\n'
         '        vertex_id, room_slug, fixture, color_r, color_g, color_b,\n'
         '        intensity, envelope, envelope_param, bars, start_bar,\n'
         '        name, description, actor_did, org_did, at_did, created_at\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, 'demo', $2, $3, $4, $5,\n"
         '        $6, $7, $8, $9, $10,\n'
         '        $11,\n'
         '        $12,\n'
         "        'did:web:live.gftd.ai', 'anon', 'did:web:live.gftd.ai',\n"
         "        '2026-04-29T03:00:00Z'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:live.gftd.ai/ai.gftd.apps.live.lightingCue/demo-3',
                 'strobe',
                 1,
                 1,
                 1,
                 1,
                 'strobe',
                 0.25,
                 4,
                 2,
                 'strobe strobe #3',
                 'Lighting cue #3 for room demo — strobe strobe']},
 {'sql': '\n'
         '      INSERT INTO edge_live_room_lighting_cue (\n'
         '        edge_id, src_vid, dst_vid, start_bar, created_at,\n'
         '        actor_did, org_did, at_did\n'
         '      )\n'
         '      VALUES (\n'
         '        $1,\n'
         "        'at://did:web:live.gftd.ai/ai.gftd.apps.live.room/demo',\n"
         '        $2,\n'
         '        $3,\n'
         "        '2026-04-29T03:00:00Z',\n"
         "        'did:web:live.gftd.ai', 'anon', 'did:web:live.gftd.ai'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:live.gftd.ai/ai.gftd.apps.live.roomLightingCue/demo-3',
                 'at://did:web:live.gftd.ai/ai.gftd.apps.live.lightingCue/demo-3',
                 2]}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS edge_live_room_lighting_cue', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_live_room_track', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_live_lighting_cue', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_live_track', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
