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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/etzhayyim',
                 'etzhayyim',
                 'etzhayyim',
                 'etzhayyim portal',
                 '🌐',
                 'Orgs',
                 'https://etzhayyim.com',
                 'did:web:etzhayyim.com',
                 'active',
                 'organization',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/kiyome',
                 'kiyome',
                 'Kiyome',
                 'SMS phishing analysis & threat intelligence',
                 '🔍',
                 'Services',
                 'https://smishing.etzhayyim.com',
                 'did:web:smishing.etzhayyim.com:actor:kiyome',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/harai',
                 'harai',
                 'Harai',
                 'Smishing enforcement & takedown coordinator',
                 '🚫',
                 'Services',
                 'https://smishing.etzhayyim.com',
                 'did:web:smishing.etzhayyim.com:actor:harai',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/news',
                 'news',
                 'News',
                 'AI-driven news portal',
                 '📰',
                 'Services',
                 'https://news.etzhayyim.com',
                 'did:web:news.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/search',
                 'search',
                 'Search',
                 'Unified search and discovery',
                 '🔎',
                 'Services',
                 'https://search.etzhayyim.com',
                 'did:web:search.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/6ir',
                 '6ir',
                 '6IR',
                 '6IR analytics',
                 '🧠',
                 'Services',
                 'https://6ir.etzhayyim.com',
                 'did:web:6ir.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/maps',
                 'maps',
                 'Maps',
                 'Spatial maps and geolocation',
                 '🗺️',
                 'Services',
                 'https://maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/kareyanagi',
                 'kareyanagi',
                 'Kareyanagi',
                 'Mold eradication platform with IoT sensors and maps integration',
                 '🦠',
                 'Services',
                 'https://kareyanagi.etzhayyim.com',
                 'did:web:kareyanagi.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/drive',
                 'drive',
                 'Drive',
                 'Cloud storage',
                 '📁',
                 'Services',
                 'https://drive.etzhayyim.com',
                 'did:web:drive.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/organizer',
                 'organizer',
                 'Organizer',
                 'Upload anything — AI auto-classifies, tags, and organizes',
                 '🗂️',
                 'Services',
                 'https://organizer.etzhayyim.com',
                 'did:web:organizer.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/sheets',
                 'sheets',
                 'Sheets',
                 'Spreadsheets',
                 '📊',
                 'Services',
                 'https://sheets.etzhayyim.com',
                 'did:web:sheets.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/docs',
                 'docs',
                 'Docs',
                 'Documentation',
                 '📝',
                 'Services',
                 'https://docs.etzhayyim.com',
                 'did:web:docs.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/mailer',
                 'mailer',
                 'Mailer',
                 'Email client',
                 '📧',
                 'Services',
                 'https://mailer.etzhayyim.com',
                 'did:web:mailer.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/gmail',
                 'gmail',
                 'Gmail',
                 'Gmail sync + AI triage + contact DID messenger bridge',
                 '✉️',
                 'Services',
                 'https://gmail.etzhayyim.com',
                 'did:web:gmail.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/outlook',
                 'outlook',
                 'Outlook',
                 'Outlook sync + calendar + contact DID bridge',
                 '📬',
                 'Services',
                 'https://outlook.etzhayyim.com',
                 'did:web:outlook.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/oshikatsu',
                 'oshikatsu',
                 'Oshikatsu',
                 'Career support',
                 '🍚',
                 'Services',
                 'https://oshikatsu.etzhayyim.com',
                 'did:web:oshikatsu.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/oshinobi',
                 'oshinobi',
                 'Oshinobi',
                 'Creator subscription platform (tiers, tips, posts)',
                 '🥷',
                 'Services',
                 'https://oshinobi.etzhayyim.com',
                 'did:web:oshinobi.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/calendar',
                 'calendar',
                 'Calendar',
                 'Calendar',
                 '📅',
                 'Services',
                 'https://calendar.etzhayyim.com',
                 'did:web:calendar.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/forms',
                 'forms',
                 'Forms',
                 'Forms builder',
                 '📋',
                 'Services',
                 'https://forms.etzhayyim.com',
                 'did:web:forms.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/threads',
                 'threads',
                 'Matrix',
                 'Matrix messaging',
                 '💬',
                 'Services',
                 'https://etzhayyim.com',
                 'did:web:etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/hub',
                 'hub',
                 'Hub',
                 'Git-compatible project hub',
                 '🏠',
                 'Services',
                 'https://hub.etzhayyim.com',
                 'did:web:hub.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/translate',
                 'translate',
                 'Translate',
                 'Translation service',
                 '🌍',
                 'Services',
                 'https://translate.etzhayyim.com',
                 'did:web:translate.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/images',
                 'images',
                 'Images',
                 'Image processing',
                 '🖼️',
                 'Services',
                 'https://images.etzhayyim.com',
                 'did:web:images.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/videos',
                 'videos',
                 'Videos',
                 'Video platform',
                 '🎬',
                 'Services',
                 'https://douga.etzhayyim.com',
                 'did:web:douga.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/videos-legacy',
                 'videos-legacy',
                 'Videos2',
                 'Video platform',
                 '🎥',
                 'Services',
                 'https://videos.etzhayyim.com',
                 'did:web:videos.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/music',
                 'music',
                 'Music',
                 'Music streaming',
                 '🎵',
                 'Services',
                 'https://music.etzhayyim.com',
                 'did:web:music.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/manga',
                 'manga',
                 'Manga',
                 'Manga reader',
                 '📚',
                 'Services',
                 'https://manga.etzhayyim.com',
                 'did:web:manga.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/anime',
                 'anime',
                 'Anime',
                 'Anime platform',
                 '🎞️',
                 'Services',
                 'https://anime.etzhayyim.com',
                 'did:web:anime.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/games',
                 'games',
                 'Games',
                 'Games',
                 '🎮',
                 'Services',
                 'https://games.etzhayyim.com',
                 'did:web:games.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/narou',
                 'narou',
                 'Narou',
                 'Novel platform',
                 '📖',
                 'Services',
                 'https://narou.etzhayyim.com',
                 'did:web:narou.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/cards',
                 'cards',
                 'Cards',
                 'Stripe Issuing cards',
                 '💳',
                 'Services',
                 'https://cards.etzhayyim.com',
                 'did:web:cards.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/tenki',
                 'tenki',
                 'Tenki',
                 'Weather',
                 '🌤️',
                 'Services',
                 'https://tenki.etzhayyim.com',
                 'did:web:tenki.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/yadoya',
                 'yadoya',
                 'Yadoya',
                 'Lodging and stays',
                 '🏨',
                 'Services',
                 'https://yadoya.etzhayyim.com',
                 'did:web:yadoya.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/fleamarket',
                 'fleamarket',
                 'FleaMarket',
                 'Marketplace',
                 '🛍️',
                 'Services',
                 'https://fleamarket.etzhayyim.com',
                 'did:web:fleamarket.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/okaimono',
                 'okaimono',
                 'Shopping',
                 'Shopping',
                 '🛒',
                 'Services',
                 'https://okaimono.etzhayyim.com',
                 'did:web:okaimono.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/briefing',
                 'briefing',
                 'Briefing',
                 'Content briefing',
                 '📑',
                 'Services',
                 'https://briefing.etzhayyim.com',
                 'did:web:briefing.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/tsukuru',
                 'tsukuru',
                 'Tsukuru',
                 'Factory-direct ordering platform',
                 '🏭',
                 'Services',
                 'https://tsukuru.etzhayyim.com',
                 'did:web:tsukuru.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/cowork',
                 'cowork',
                 'Cowork',
                 'Co-working',
                 '👥',
                 'Services',
                 'https://cowork.etzhayyim.com',
                 'did:web:cowork.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/shigotoba',
                 'shigotoba',
                 'Shigotoba',
                 'Job board',
                 '💼',
                 'Services',
                 'https://shigotoba.etzhayyim.com',
                 'did:web:shigotoba.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/scheduler',
                 'scheduler',
                 'Scheduler',
                 'Scheduler and automation',
                 '⏰',
                 'Services',
                 'https://scheduler.etzhayyim.com',
                 'did:web:scheduler.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/web4',
                 'web4',
                 'Web4',
                 'Web4 / GCC token',
                 '🔗',
                 'Services',
                 'https://web4.etzhayyim.com',
                 'did:web:web4.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/society6',
                 'society6',
                 'Society6',
                 'COFOG access and Society6 policy portal',
                 '🏛️',
                 'Services',
                 'https://society6.etzhayyim.com',
                 'did:web:society6.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/lawfirm',
                 'lawfirm',
                 'Law Firm',
                 'Law firm client portal',
                 '⚖️',
                 'Services',
                 'https://lawfirm.etzhayyim.com',
                 'did:web:lawfirm.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/lawyer',
                 'lawyer',
                 'Lawyer',
                 'Lawyer workspace',
                 '👨\u200d⚖️',
                 'Services',
                 'https://lawyer.etzhayyim.com',
                 'did:web:lawyer.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/ekyc',
                 'ekyc',
                 'eKYC',
                 'Identity verification',
                 '🪪',
                 'Services',
                 'https://ekyc.etzhayyim.com',
                 'did:web:ekyc.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/shomeisyashin',
                 'shomeisyashin',
                 'ID Photo',
                 'AI証明写真メーカー',
                 '📸',
                 'Services',
                 'https://shomeisyashin.etzhayyim.com',
                 'did:web:shomeisyashin.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/global',
                 'global',
                 'Global',
                 'Global services',
                 '🌏',
                 'Services',
                 'https://global.etzhayyim.com',
                 'did:web:global.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/worlds',
                 'worlds',
                 'Worlds',
                 'Virtual worlds',
                 '🌌',
                 'Services',
                 'https://worlds.etzhayyim.com',
                 'did:web:worlds.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/pachinko',
                 'pachinko',
                 'Pachinko',
                 'Pachinko simulation',
                 '🎰',
                 'Services',
                 'https://pachinko.etzhayyim.com',
                 'did:web:pachinko.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/casino',
                 'casino',
                 'Casino',
                 'World casino directory',
                 '🎲',
                 'Services',
                 'https://casino.etzhayyim.com',
                 'did:web:casino.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/oshiete',
                 'oshiete',
                 'Oshiete',
                 'Q&A platform',
                 '❓',
                 'Services',
                 'https://oshiete.etzhayyim.com',
                 'did:web:oshiete.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/webpage',
                 'webpage',
                 'Webpage',
                 'Web page crawl and text extraction',
                 '🌐',
                 'Services',
                 'https://webpage.etzhayyim.com',
                 'did:web:webpage.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/marketer',
                 'marketer',
                 'Marketer',
                 'Marketing tools',
                 '📣',
                 'Services',
                 'https://marketer.etzhayyim.com',
                 'did:web:marketer.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/omikuji',
                 'omikuji',
                 'Omikuji',
                 'Fortune telling',
                 '🎋',
                 'Services',
                 'https://omikuji.etzhayyim.com',
                 'did:web:omikuji.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/aima',
                 'aima',
                 'AIMA',
                 'AI models',
                 '🤖',
                 'Services',
                 'https://aima.etzhayyim.com',
                 'did:web:aima.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/robot',
                 'robot',
                 'Robot',
                 'Robot automation',
                 '🦾',
                 'Services',
                 'https://robot.etzhayyim.com',
                 'did:web:robot.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/wire',
                 'wire',
                 'Wire',
                 'Messaging',
                 '📡',
                 'Services',
                 'https://wire.etzhayyim.com',
                 'did:web:wire.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/lawfirm-admin',
                 'lawfirm-admin',
                 'LF Admin',
                 'Law firm admin',
                 '🏛️',
                 'Services',
                 'https://lawfirm-admin.etzhayyim.com',
                 'did:web:lawfirm-admin.etzhayyim.com',
                 'active',
                 'service',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/performers',
                 'performers',
                 'Performers',
                 'Platform dashboard',
                 '🚀',
                 'Systems',
                 'https://etzhayyim.com',
                 'did:web:etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/analytics',
                 'analytics',
                 'Analytics',
                 'Analytics dashboard',
                 '📈',
                 'Systems',
                 'https://analytics.etzhayyim.com',
                 'did:web:analytics.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/ops',
                 'ops',
                 'Ops',
                 'Project operations',
                 '⚙️',
                 'Systems',
                 'https://ops.etzhayyim.com',
                 'did:web:ops.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/sre',
                 'sre',
                 'SRE',
                 'Site reliability',
                 '🔧',
                 'Systems',
                 'https://sre.etzhayyim.com',
                 'did:web:sre.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/os',
                 'os',
                 'OS',
                 'Operating system UI',
                 '🖥️',
                 'Systems',
                 'https://os.etzhayyim.com',
                 'did:web:os.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/po',
                 'po',
                 'PO',
                 'Projection operator',
                 '📐',
                 'Systems',
                 'https://po.etzhayyim.com',
                 'did:web:po.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/gov',
                 'gov',
                 'Gov',
                 'Governance',
                 '🏢',
                 'Systems',
                 'https://gov.etzhayyim.com',
                 'did:web:gov.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/resources',
                 'resources',
                 'Resources',
                 'JSON-LD/RDF resources',
                 '🗄️',
                 'Systems',
                 'https://resources.etzhayyim.com',
                 'did:web:resources.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/completer',
                 'completer',
                 'Completer',
                 'Code completion',
                 '✏️',
                 'Systems',
                 'https://completer.etzhayyim.com',
                 'did:web:completer.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/har',
                 'har',
                 'HAR',
                 'HAR viewer',
                 '🗂️',
                 'Systems',
                 'https://har.etzhayyim.com',
                 'did:web:har.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/provider-pod',
                 'provider-pod',
                 'Provider',
                 'Provider pod marketplace',
                 '📦',
                 'Systems',
                 'https://provider-pod.etzhayyim.com',
                 'did:web:provider-pod.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/ge',
                 'ge',
                 'GE',
                 'General education',
                 '🎓',
                 'Systems',
                 'https://ge.etzhayyim.com',
                 'did:web:ge.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/lo',
                 'lo',
                 'LO',
                 'Learning objects',
                 '🧩',
                 'Systems',
                 'https://lo.etzhayyim.com',
                 'did:web:lo.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/tia',
                 'tia',
                 'TIA',
                 'TIA assistant',
                 '🎙️',
                 'Systems',
                 'https://tia.etzhayyim.com',
                 'did:web:tia.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/wvme',
                 'wvme',
                 'WVME',
                 'WVME platform',
                 '🎛️',
                 'Systems',
                 'https://wvme.etzhayyim.com',
                 'did:web:wvme.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']},
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
  'parameters': ['at://did:web:yoro.etzhayyim.com/com.etzhayyim.apps.yoro.appRegistry/tasklist',
                 'tasklist',
                 'TaskList',
                 'Task approval',
                 '✅',
                 'Systems',
                 'https://tasklist.etzhayyim.com',
                 'did:web:tasklist.etzhayyim.com',
                 'active',
                 'system',
                 'public',
                 0,
                 'did:web:yoro.etzhayyim.com',
                 'com.etzhayyim.apps.yoro.appRegistry',
                 'did:web:yoro.etzhayyim.com']}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
