"""Captured from Kysely migration 20260427210000_vertex_app_icon_yoro_apps_backfill."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427210000_vertex_app_icon_yoro_apps_backfill"
down_revision = 'r_20260427210000_seed_maps_sentinel_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': 'ALTER TABLE "vertex_app" ADD COLUMN IF NOT EXISTS "icon" VARCHAR', 'parameters': []},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/gftd',
                 'gftd',
                 'GFTD',
                 'GFTD portal',
                 '🌐',
                 'Orgs',
                 'https://gftd.ai',
                 'did:web:gftd.ai',
                 'active',
                 'organization',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/kiyome',
                 'kiyome',
                 'Kiyome',
                 'SMS phishing analysis & threat intelligence',
                 '🔍',
                 'Services',
                 'https://smishing.gftd.ai',
                 'did:web:smishing.gftd.ai:actor:kiyome',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/harai',
                 'harai',
                 'Harai',
                 'Smishing enforcement & takedown coordinator',
                 '🚫',
                 'Services',
                 'https://smishing.gftd.ai',
                 'did:web:smishing.gftd.ai:actor:harai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/news',
                 'news',
                 'News',
                 'AI-driven news portal',
                 '📰',
                 'Services',
                 'https://news.gftd.ai',
                 'did:web:news.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/search',
                 'search',
                 'Search',
                 'Unified search and discovery',
                 '🔎',
                 'Services',
                 'https://search.gftd.ai',
                 'did:web:search.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/6ir',
                 '6ir',
                 '6IR',
                 '6IR analytics',
                 '🧠',
                 'Services',
                 'https://6ir.gftd.ai',
                 'did:web:6ir.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/maps',
                 'maps',
                 'Maps',
                 'Spatial maps and geolocation',
                 '🗺️',
                 'Services',
                 'https://maps.gftd.ai',
                 'did:web:maps.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/kareyanagi',
                 'kareyanagi',
                 'Kareyanagi',
                 'Mold eradication platform with IoT sensors and maps integration',
                 '🦠',
                 'Services',
                 'https://kareyanagi.gftd.ai',
                 'did:web:kareyanagi.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/drive',
                 'drive',
                 'Drive',
                 'Cloud storage',
                 '📁',
                 'Services',
                 'https://drive.gftd.ai',
                 'did:web:drive.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/organizer',
                 'organizer',
                 'Organizer',
                 'Upload anything — AI auto-classifies, tags, and organizes',
                 '🗂️',
                 'Services',
                 'https://organizer.gftd.ai',
                 'did:web:organizer.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/sheets',
                 'sheets',
                 'Sheets',
                 'Spreadsheets',
                 '📊',
                 'Services',
                 'https://sheets.gftd.ai',
                 'did:web:sheets.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/docs',
                 'docs',
                 'Docs',
                 'Documentation',
                 '📝',
                 'Services',
                 'https://docs.gftd.ai',
                 'did:web:docs.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/mailer',
                 'mailer',
                 'Mailer',
                 'Email client',
                 '📧',
                 'Services',
                 'https://mailer.gftd.ai',
                 'did:web:mailer.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/gmail',
                 'gmail',
                 'Gmail',
                 'Gmail sync + AI triage + contact DID messenger bridge',
                 '✉️',
                 'Services',
                 'https://gmail.gftd.ai',
                 'did:web:gmail.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/outlook',
                 'outlook',
                 'Outlook',
                 'Outlook sync + calendar + contact DID bridge',
                 '📬',
                 'Services',
                 'https://outlook.gftd.ai',
                 'did:web:outlook.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/oshikatsu',
                 'oshikatsu',
                 'Oshikatsu',
                 'Career support',
                 '🍚',
                 'Services',
                 'https://oshikatsu.gftd.ai',
                 'did:web:oshikatsu.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/oshinobi',
                 'oshinobi',
                 'Oshinobi',
                 'Creator subscription platform (tiers, tips, posts)',
                 '🥷',
                 'Services',
                 'https://oshinobi.gftd.ai',
                 'did:web:oshinobi.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/calendar',
                 'calendar',
                 'Calendar',
                 'Calendar',
                 '📅',
                 'Services',
                 'https://calendar.gftd.ai',
                 'did:web:calendar.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/forms',
                 'forms',
                 'Forms',
                 'Forms builder',
                 '📋',
                 'Services',
                 'https://forms.gftd.ai',
                 'did:web:forms.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/threads',
                 'threads',
                 'Matrix',
                 'Matrix messaging',
                 '💬',
                 'Services',
                 'https://gftd.ai',
                 'did:web:gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/hub',
                 'hub',
                 'Hub',
                 'Git-compatible project hub',
                 '🏠',
                 'Services',
                 'https://hub.gftd.ai',
                 'did:web:hub.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/translate',
                 'translate',
                 'Translate',
                 'Translation service',
                 '🌍',
                 'Services',
                 'https://translate.gftd.ai',
                 'did:web:translate.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/images',
                 'images',
                 'Images',
                 'Image processing',
                 '🖼️',
                 'Services',
                 'https://images.gftd.ai',
                 'did:web:images.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/videos',
                 'videos',
                 'Videos',
                 'Video platform',
                 '🎬',
                 'Services',
                 'https://douga.gftd.ai',
                 'did:web:douga.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/videos-legacy',
                 'videos-legacy',
                 'Videos2',
                 'Video platform',
                 '🎥',
                 'Services',
                 'https://videos.gftd.ai',
                 'did:web:videos.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/music',
                 'music',
                 'Music',
                 'Music streaming',
                 '🎵',
                 'Services',
                 'https://music.gftd.ai',
                 'did:web:music.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/manga',
                 'manga',
                 'Manga',
                 'Manga reader',
                 '📚',
                 'Services',
                 'https://manga.gftd.ai',
                 'did:web:manga.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/anime',
                 'anime',
                 'Anime',
                 'Anime platform',
                 '🎞️',
                 'Services',
                 'https://anime.gftd.ai',
                 'did:web:anime.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/games',
                 'games',
                 'Games',
                 'Games',
                 '🎮',
                 'Services',
                 'https://games.gftd.ai',
                 'did:web:games.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/narou',
                 'narou',
                 'Narou',
                 'Novel platform',
                 '📖',
                 'Services',
                 'https://narou.gftd.ai',
                 'did:web:narou.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/cards',
                 'cards',
                 'Cards',
                 'Stripe Issuing cards',
                 '💳',
                 'Services',
                 'https://cards.gftd.ai',
                 'did:web:cards.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/tenki',
                 'tenki',
                 'Tenki',
                 'Weather',
                 '🌤️',
                 'Services',
                 'https://tenki.gftd.ai',
                 'did:web:tenki.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/yadoya',
                 'yadoya',
                 'Yadoya',
                 'Lodging and stays',
                 '🏨',
                 'Services',
                 'https://yadoya.gftd.ai',
                 'did:web:yadoya.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/fleamarket',
                 'fleamarket',
                 'FleaMarket',
                 'Marketplace',
                 '🛍️',
                 'Services',
                 'https://fleamarket.gftd.ai',
                 'did:web:fleamarket.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/okaimono',
                 'okaimono',
                 'Shopping',
                 'Shopping',
                 '🛒',
                 'Services',
                 'https://okaimono.gftd.ai',
                 'did:web:okaimono.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/briefing',
                 'briefing',
                 'Briefing',
                 'Content briefing',
                 '📑',
                 'Services',
                 'https://briefing.gftd.ai',
                 'did:web:briefing.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/tsukuru',
                 'tsukuru',
                 'Tsukuru',
                 'Factory-direct ordering platform',
                 '🏭',
                 'Services',
                 'https://tsukuru.gftd.ai',
                 'did:web:tsukuru.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/cowork',
                 'cowork',
                 'Cowork',
                 'Co-working',
                 '👥',
                 'Services',
                 'https://cowork.gftd.ai',
                 'did:web:cowork.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/shigotoba',
                 'shigotoba',
                 'Shigotoba',
                 'Job board',
                 '💼',
                 'Services',
                 'https://shigotoba.gftd.ai',
                 'did:web:shigotoba.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/scheduler',
                 'scheduler',
                 'Scheduler',
                 'Scheduler and automation',
                 '⏰',
                 'Services',
                 'https://scheduler.gftd.ai',
                 'did:web:scheduler.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/web4',
                 'web4',
                 'Web4',
                 'Web4 / GCC token',
                 '🔗',
                 'Services',
                 'https://web4.gftd.ai',
                 'did:web:web4.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/society6',
                 'society6',
                 'Society6',
                 'COFOG access and Society6 policy portal',
                 '🏛️',
                 'Services',
                 'https://society6.gftd.ai',
                 'did:web:society6.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/lawfirm',
                 'lawfirm',
                 'Law Firm',
                 'Law firm client portal',
                 '⚖️',
                 'Services',
                 'https://lawfirm.gftd.ai',
                 'did:web:lawfirm.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/lawyer',
                 'lawyer',
                 'Lawyer',
                 'Lawyer workspace',
                 '👨\u200d⚖️',
                 'Services',
                 'https://lawyer.gftd.ai',
                 'did:web:lawyer.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/ekyc',
                 'ekyc',
                 'eKYC',
                 'Identity verification',
                 '🪪',
                 'Services',
                 'https://ekyc.gftd.ai',
                 'did:web:ekyc.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/shomeisyashin',
                 'shomeisyashin',
                 'ID Photo',
                 'AI証明写真メーカー',
                 '📸',
                 'Services',
                 'https://shomeisyashin.gftd.ai',
                 'did:web:shomeisyashin.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/global',
                 'global',
                 'Global',
                 'Global services',
                 '🌏',
                 'Services',
                 'https://global.gftd.ai',
                 'did:web:global.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/worlds',
                 'worlds',
                 'Worlds',
                 'Virtual worlds',
                 '🌌',
                 'Services',
                 'https://worlds.gftd.ai',
                 'did:web:worlds.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/pachinko',
                 'pachinko',
                 'Pachinko',
                 'Pachinko simulation',
                 '🎰',
                 'Services',
                 'https://pachinko.gftd.ai',
                 'did:web:pachinko.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/casino',
                 'casino',
                 'Casino',
                 'World casino directory',
                 '🎲',
                 'Services',
                 'https://casino.gftd.ai',
                 'did:web:casino.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/oshiete',
                 'oshiete',
                 'Oshiete',
                 'Q&A platform',
                 '❓',
                 'Services',
                 'https://oshiete.gftd.ai',
                 'did:web:oshiete.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/webpage',
                 'webpage',
                 'Webpage',
                 'Web page crawl and text extraction',
                 '🌐',
                 'Services',
                 'https://webpage.gftd.ai',
                 'did:web:webpage.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/marketer',
                 'marketer',
                 'Marketer',
                 'Marketing tools',
                 '📣',
                 'Services',
                 'https://marketer.gftd.ai',
                 'did:web:marketer.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/omikuji',
                 'omikuji',
                 'Omikuji',
                 'Fortune telling',
                 '🎋',
                 'Services',
                 'https://omikuji.gftd.ai',
                 'did:web:omikuji.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/aima',
                 'aima',
                 'AIMA',
                 'AI models',
                 '🤖',
                 'Services',
                 'https://aima.gftd.ai',
                 'did:web:aima.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/robot',
                 'robot',
                 'Robot',
                 'Robot automation',
                 '🦾',
                 'Services',
                 'https://robot.gftd.ai',
                 'did:web:robot.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/wire',
                 'wire',
                 'Wire',
                 'Messaging',
                 '📡',
                 'Services',
                 'https://wire.gftd.ai',
                 'did:web:wire.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/lawfirm-admin',
                 'lawfirm-admin',
                 'LF Admin',
                 'Law firm admin',
                 '🏛️',
                 'Services',
                 'https://lawfirm-admin.gftd.ai',
                 'did:web:lawfirm-admin.gftd.ai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/performers',
                 'performers',
                 'Performers',
                 'Platform dashboard',
                 '🚀',
                 'Systems',
                 'https://gftd.ai',
                 'did:web:gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/analytics',
                 'analytics',
                 'Analytics',
                 'Analytics dashboard',
                 '📈',
                 'Systems',
                 'https://analytics.gftd.ai',
                 'did:web:analytics.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/ops',
                 'ops',
                 'Ops',
                 'Project operations',
                 '⚙️',
                 'Systems',
                 'https://ops.gftd.ai',
                 'did:web:ops.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/sre',
                 'sre',
                 'SRE',
                 'Site reliability',
                 '🔧',
                 'Systems',
                 'https://sre.gftd.ai',
                 'did:web:sre.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/os',
                 'os',
                 'OS',
                 'Operating system UI',
                 '🖥️',
                 'Systems',
                 'https://os.gftd.ai',
                 'did:web:os.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/po',
                 'po',
                 'PO',
                 'Projection operator',
                 '📐',
                 'Systems',
                 'https://po.gftd.ai',
                 'did:web:po.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/gov',
                 'gov',
                 'Gov',
                 'Governance',
                 '🏢',
                 'Systems',
                 'https://gov.gftd.ai',
                 'did:web:gov.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/resources',
                 'resources',
                 'Resources',
                 'JSON-LD/RDF resources',
                 '🗄️',
                 'Systems',
                 'https://resources.gftd.ai',
                 'did:web:resources.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/completer',
                 'completer',
                 'Completer',
                 'Code completion',
                 '✏️',
                 'Systems',
                 'https://completer.gftd.ai',
                 'did:web:completer.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/har',
                 'har',
                 'HAR',
                 'HAR viewer',
                 '🗂️',
                 'Systems',
                 'https://har.gftd.ai',
                 'did:web:har.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/provider-pod',
                 'provider-pod',
                 'Provider',
                 'Provider pod marketplace',
                 '📦',
                 'Systems',
                 'https://provider-pod.gftd.ai',
                 'did:web:provider-pod.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/ge',
                 'ge',
                 'GE',
                 'General education',
                 '🎓',
                 'Systems',
                 'https://ge.gftd.ai',
                 'did:web:ge.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/lo',
                 'lo',
                 'LO',
                 'Learning objects',
                 '🧩',
                 'Systems',
                 'https://lo.gftd.ai',
                 'did:web:lo.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/tia',
                 'tia',
                 'TIA',
                 'TIA assistant',
                 '🎙️',
                 'Systems',
                 'https://tia.gftd.ai',
                 'did:web:tia.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/wvme',
                 'wvme',
                 'WVME',
                 'WVME platform',
                 '🎛️',
                 'Systems',
                 'https://wvme.gftd.ai',
                 'did:web:wvme.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']},
 {'sql': '\n'
         '        INSERT INTO "vertex_app" (\n'
         '          "vertex_id", "handle", "display_name", "description", "icon",\n'
         '          "classification", "embed_url", "app_did", "status", "performer_type",\n'
         '          "sensitivity", "sensitivity_ord", "owner_did", "collection", "repo"\n'
         '        ) VALUES (\n'
         '          $1, $2, $3, $4, $5,\n'
         '          $6, $7, $8, $9, $10,\n'
         '          $11, $12, $13, $14, $15\n'
         '        )\n'
         '      ',
  'parameters': ['at://did:web:yoro.gftd.ai/ai.gftd.apps.yoro.appRegistry/tasklist',
                 'tasklist',
                 'TaskList',
                 'Task approval',
                 '✅',
                 'Systems',
                 'https://tasklist.gftd.ai',
                 'did:web:tasklist.gftd.ai',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.gftd.ai',
                 'ai.gftd.apps.yoro.appRegistry',
                 'did:web:yoro.gftd.ai']}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
