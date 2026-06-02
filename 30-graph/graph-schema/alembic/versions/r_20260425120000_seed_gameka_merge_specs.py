"""Captured from Kysely migration 20260425120000_seed_gameka_merge_specs."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425120000_seed_gameka_merge_specs"
down_revision = 'r_20260425110000_vertex_gameka_studio_config'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_gameka_spec (\n'
         '        vertex_id, owner_did, rkey, repo,\n'
         '        spec_id, brief, title, slug, genre,\n'
         '        mechanic_json, scene_json,\n'
         '        budget_usd, score, rationale,\n'
         '        iteration, lineage_parent, model_id,\n'
         '        created_at\n'
         '      ) VALUES (\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        $7,\n'
         '        $8,\n'
         '        $9,\n'
         '        $10,\n'
         '        $11,\n'
         '        $12,\n'
         '        $13,\n'
         '        $14,\n'
         '        $15,\n'
         '        $16,\n'
         '        $17,\n'
         '        $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:gameka.etzhayyim.com/com.etzhayyim.apps.gameka.gameSpec/spec-merge-grid-2048',
                 'did:web:gameka.etzhayyim.com',
                 'spec-merge-grid-2048',
                 'did:web:gameka.etzhayyim.com',
                 'spec-merge-grid-2048',
                 'A relaxing quarry-themed 2048 swipe-merge with stone-slab tiles and '
                 'Nintendo-pastel polish.',
                 'Grid Merge — Quarry',
                 'grid-merge-quarry',
                 'puzzle',
                 '{"kind":"grid_2048","description":"4x4 grid puzzle. Swipe to slide all tiles in '
                 'one direction; same-rank tiles touching merge to rank+1. New rank-1 tile spawns '
                 'each turn. Lose when the grid is full and no merges remain. Reach rank 11 to '
                 'win.","coreVerb":"swipe-merge","board":{"kind":"grid","w":4,"h":4},"inputModes":["swipe","arrow-keys"],"progression":{"tiers":11,"scaling":"exponential"},"failState":"deadlock-on-full-grid","target":"reach-rank-11"}',
                 '{"description":"Quarry biome cathedral interior. Tiles are carved stone slabs '
                 'floating mid-air on Splatoon-pastel pedestals. Soft volumetric dust, distant '
                 'rumble of falling rocks. Orbit camera pivots gently while the grid stays '
                 'centered.","biomeHint":"quarry","cameraHint":"orbit-fixed","palette":"splatoon-pastel-neutral","fxBudget":"low","ambient":["dust-motes","distant-rumble"],"audioPalette":{"bgm":"ambient-quarry-low","sfx":["click","success","coin","tick","select","loaded"],"loops":["wind-soft"]},"socialHooks":{"onWin":"share-score","onMilestone":"share-rank"}}',
                 80,
                 0.85,
                 'Seed spec — classic 2048 mechanic on the kami quarry biome. Low fx, single '
                 'board, cheap to render.',
                 0,
                 '',
                 'seed',
                 '2026-04-25T12:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_gameka_spec (\n'
         '        vertex_id, owner_did, rkey, repo,\n'
         '        spec_id, brief, title, slug, genre,\n'
         '        mechanic_json, scene_json,\n'
         '        budget_usd, score, rationale,\n'
         '        iteration, lineage_parent, model_id,\n'
         '        created_at\n'
         '      ) VALUES (\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        $7,\n'
         '        $8,\n'
         '        $9,\n'
         '        $10,\n'
         '        $11,\n'
         '        $12,\n'
         '        $13,\n'
         '        $14,\n'
         '        $15,\n'
         '        $16,\n'
         '        $17,\n'
         '        $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:gameka.etzhayyim.com/com.etzhayyim.apps.gameka.gameSpec/spec-merge-drop-suika',
                 'did:web:gameka.etzhayyim.com',
                 'spec-merge-drop-suika',
                 'did:web:gameka.etzhayyim.com',
                 'spec-merge-drop-suika',
                 'Suika-style physics merge in a tundra glass jar — drop snowballs, fuse them, '
                 'create a glacier.',
                 'Drop Merge — Tundra',
                 'drop-merge-tundra',
                 'puzzle',
                 '{"kind":"drop_suika","description":"Drop snowballs from a fixed top emitter into '
                 'a glass container. Snowballs fall under gravity and bounce. Same-tier snowballs '
                 'in contact merge into the next tier (volume sums, position averages). Lose if '
                 'the stack overflows the top line. Goal: create the largest possible snowball '
                 'without '
                 'overflow.","coreVerb":"drop-and-fuse","physicsHint":"circle2d-aabb-walls","inputModes":["pointer-x","arrow-keys"],"progression":{"tiers":11,"scaling":"1.4x-radius-per-tier"},"failState":"stack-overflow","target":"create-max-tier"}',
                 '{"description":"Tundra biome. Glass jar suspended above a frozen lake; '
                 'snowflakes drift past the camera. The jar is the only foreground element; tundra '
                 'horizon stretches behind it. Static camera, slight parallax from background '
                 'snowfall.","biomeHint":"tundra","cameraHint":"static-front","palette":"splatoon-pastel-cool","fxBudget":"medium","ambient":["snowfall","wind-howl-soft"],"audioPalette":{"bgm":"tundra-wind-soft","sfx":["pop","whoosh","success","loaded","warning","coin"],"loops":["snowfall"]},"socialHooks":{"onWin":"share-score","onMilestone":"share-tier"}}',
                 120,
                 0.85,
                 'Seed spec — Suika-game mechanic, Tundra biome scaffolding. Medium fx for the '
                 'snowfall + jar refraction; physics2d only.',
                 0,
                 '',
                 'seed',
                 '2026-04-25T12:00:00Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_gameka_spec (\n'
         '        vertex_id, owner_did, rkey, repo,\n'
         '        spec_id, brief, title, slug, genre,\n'
         '        mechanic_json, scene_json,\n'
         '        budget_usd, score, rationale,\n'
         '        iteration, lineage_parent, model_id,\n'
         '        created_at\n'
         '      ) VALUES (\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        $7,\n'
         '        $8,\n'
         '        $9,\n'
         '        $10,\n'
         '        $11,\n'
         '        $12,\n'
         '        $13,\n'
         '        $14,\n'
         '        $15,\n'
         '        $16,\n'
         '        $17,\n'
         '        $18\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:gameka.etzhayyim.com/com.etzhayyim.apps.gameka.gameSpec/spec-merge-field-triple',
                 'did:web:gameka.etzhayyim.com',
                 'spec-merge-field-triple',
                 'did:web:gameka.etzhayyim.com',
                 'spec-merge-field-triple',
                 'Triple Town-style place-and-merge on a plains board — grass to castle, '
                 'golden-hour vibes.',
                 'Field Merge — Plains',
                 'field-merge-plains',
                 'puzzle',
                 '{"kind":"field_triple","description":"5x5 plains board. Each turn a previewed '
                 'item is placed on an empty tile chosen by pointer click. When 3+ same-rank items '
                 'touch in any orthogonal cluster, they auto-merge into a single rank+1 item at '
                 'the placement spot. Ranks: grass → bush → tree → hut → house → castle. Lose when '
                 'the board fills and no placement triggers a '
                 'merge.","coreVerb":"place-and-cluster","board":{"kind":"grid","w":5,"h":5},"inputModes":["pointer-click"],"progression":{"tiers":6,"scaling":"narrative-rank"},"failState":"deadlock-on-full-board","target":"build-castle"}',
                 '{"description":"Plains biome with rolling hills. The 5x5 board floats over a '
                 'meadow; clouds pass overhead. Day-night cycle is paused at golden hour for warm '
                 'UI contrast. Orbit camera angles 30 degrees from horizontal, slow '
                 'auto-rotation.","biomeHint":"plains","cameraHint":"orbit-30deg-slow","palette":"splatoon-pastel-warm","fxBudget":"low","ambient":["cloud-shadows","distant-bird"],"audioPalette":{"bgm":"plains-pastoral","sfx":["click","coin","success","loaded","select","navigate"],"loops":["bird-chirps"]},"socialHooks":{"onWin":"share-score","onMilestone":"share-castle"}}',
                 100,
                 0.85,
                 'Seed spec — Triple Town cluster mechanic on the kami plains biome. Low fx, '
                 'golden-hour palette, satisfies kami-pipelines sky+terrain+water defaults.',
                 0,
                 '',
                 'seed',
                 '2026-04-25T12:00:00Z']}]

DOWN = [{'sql': '\n      DELETE FROM vertex_gameka_spec\n      WHERE spec_id = $1\n    ',
  'parameters': ['spec-merge-grid-2048']},
 {'sql': '\n      DELETE FROM vertex_gameka_spec\n      WHERE spec_id = $1\n    ',
  'parameters': ['spec-merge-drop-suika']},
 {'sql': '\n      DELETE FROM vertex_gameka_spec\n      WHERE spec_id = $1\n    ',
  'parameters': ['spec-merge-field-triple']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
