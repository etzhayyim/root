"""Captured from Kysely migration 20260429222000_vertex_coverage_recipe_full_seed."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429222000_vertex_coverage_recipe_full_seed"
down_revision = 'r_20260429221000_seed_wellbecoming_process_mining_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['legal_entity',
                 'world',
                 'ingest',
                 'https://api.gleif.org/api/v1/lei-records',
                 '',
                 '',
                 200000000,
                 'GLEIF LEI bulk feed; active legal entities globally',
                 'legal_entity',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['vessel',
                 'world',
                 'ingest',
                 'https://www.marinetraffic.com/',
                 '',
                 '',
                 90000,
                 'IMO GISIS + AIS public vessel registry',
                 'vessel',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['aircraft',
                 'world',
                 'ingest',
                 'https://openflights.org/data.html',
                 '',
                 '',
                 200000,
                 'ICAO + OpenFlights aircraft register; already partially loaded via maps BPMN',
                 'aircraft',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['patent',
                 'world',
                 'ingest',
                 'https://bulkdata.uspto.gov/',
                 '',
                 '',
                 100000000,
                 'USPTO bulk XML + EPO OPS',
                 'patent',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['trademark',
                 'world',
                 'ingest',
                 'https://branddb.wipo.int/',
                 '',
                 '',
                 40000000,
                 'WIPO Global Brand Database',
                 'trademark',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['work',
                 'world',
                 'ingest',
                 'https://isni.org/',
                 '',
                 '',
                 10000000,
                 'ISNI + Creative Commons public works registry',
                 'work',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['gtin_product',
                 'world',
                 'ingest',
                 'https://www.gs1.org/services/verified-by-gs1',
                 '',
                 '',
                 1000000000,
                 'GS1 GEPIR public barcode lookup',
                 'gtin_product',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['dns_observation',
                 'world',
                 'ingest',
                 'https://opendata.rapid7.com/sonar.fdns_v2/',
                 '',
                 '',
                 400000000,
                 'Rapid7 FDNS passive DNS open dataset',
                 'dns_observation',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['accommodation',
                 'world',
                 'ingest',
                 'https://api.openstreetmap.org/',
                 '',
                 '',
                 500000,
                 'OpenStreetMap amenity=hotel/hostel/guest_house',
                 'accommodation',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['hotel',
                 'world',
                 'ingest',
                 'https://api.openstreetmap.org/',
                 '',
                 '',
                 700000,
                 'OSM tourism=hotel; covered by accommodation ingest',
                 'hotel',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['minpaku',
                 'world',
                 'ingest',
                 'https://www.mlit.go.jp/kankocho/minpaku/',
                 '',
                 '',
                 50000,
                 'Japan MLIT minpaku (民泊) public registry',
                 'minpaku',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['ryokan',
                 'world',
                 'ingest',
                 'https://www.ryokan.or.jp/',
                 '',
                 '',
                 20000,
                 'Japan Ryokan Association public registry',
                 'ryokan',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['game_actor',
                 'world',
                 'ingest',
                 'https://api.igdb.com/v4/companies',
                 '',
                 '',
                 200000,
                 'IGDB companies API — publishers/developers',
                 'game_actor',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['game_item',
                 'world',
                 'ingest',
                 'https://api.igdb.com/v4/games',
                 '',
                 '',
                 500000,
                 'IGDB games API — titles as items',
                 'game_item',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['occupation_code',
                 'world',
                 'ingest',
                 'https://www.ilo.org/ilostat-files/ISCO/newdocs-08-2012/ISCO-08/ISCO-08%20EN.pdf',
                 '',
                 '',
                 500,
                 'ILO ISCO-08 + ESCO occupation taxonomy — already loaded',
                 'occupation_code',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['skill_taxonomy',
                 'world',
                 'ingest',
                 'https://esco.ec.europa.eu/en/about-esco/escodownload',
                 '',
                 '',
                 14000,
                 'ESCO skill taxonomy download — already partially loaded',
                 'skill_taxonomy',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['job_posting',
                 'world',
                 'ingest',
                 'https://indeed.com/',
                 '',
                 '',
                 100000000,
                 'Public job board aggregation; partial via LinkedIn/Indeed feeds',
                 'job_posting',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['talent_cohort_stat',
                 'world',
                 'ingest',
                 'https://ilostat.ilo.org/data/',
                 '',
                 '',
                 100000,
                 'ILO ILOSTAT bulk statistics download — already partially loaded',
                 'talent_cohort_stat',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['blockchain_actor',
                 'world',
                 'ingest',
                 'https://blockchain.info/',
                 '',
                 '',
                 100000000,
                 'Public blockchain address registry (Bitcoin + Ethereum active addresses)',
                 'blockchain_actor',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['transport',
                 'world',
                 'ingest',
                 'https://transitfeeds.com/',
                 '',
                 '',
                 50000000,
                 'GTFS public transit feeds — already loaded via maps BPMN R/P7D',
                 'transport',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['spatial',
                 'world',
                 'ingest',
                 'https://www.openstreetmap.org/',
                 '',
                 '',
                 1000000000,
                 'OpenStreetMap POI + feature data',
                 'spatial',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['apt_group',
                 'world',
                 'ingest',
                 'https://attack.mitre.org/groups/',
                 '',
                 '',
                 300000,
                 'MITRE ATT&CK groups + CISA known threat actors',
                 'apt_group',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['exploit_kit',
                 'world',
                 'ingest',
                 'https://abuse.ch/',
                 '',
                 '',
                 300000,
                 'abuse.ch URLhaus + MalwareBazaar public feed',
                 'exploit_kit',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['ransomware_family',
                 'world',
                 'ingest',
                 'https://id-ransomware.malwarehunterteam.com/',
                 '',
                 '',
                 300000,
                 'ID Ransomware + MITRE ATT&CK malware catalog',
                 'ransomware_family',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['cybercrime_group',
                 'world',
                 'ingest',
                 'https://attack.mitre.org/groups/',
                 '',
                 '',
                 300000,
                 'MITRE ATT&CK groups — financially motivated',
                 'cybercrime_group',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['malicious_registrar',
                 'world',
                 'ingest',
                 'https://www.spamhaus.org/',
                 '',
                 '',
                 300000,
                 'Spamhaus Domain Block List + SURBL public feed',
                 'malicious_registrar',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['bulletproof_host',
                 'world',
                 'ingest',
                 'https://www.spamhaus.org/',
                 '',
                 '',
                 300000,
                 'Spamhaus CBL + Team Cymru ASN reputation feeds',
                 'bulletproof_host',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['drug_product',
                 'world',
                 'ingest',
                 'https://open.fda.gov/apis/drug/ndc/',
                 '',
                 '',
                 200000,
                 'FDA NDC bulk download — already loaded in classification migrations',
                 'drug_product',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['oil_company',
                 'world',
                 'ingest',
                 'https://www.sec.gov/cgi-bin/browse-edgar',
                 '',
                 '',
                 200,
                 'SEC EDGAR energy sector + IEA national oil company registry',
                 'oil_company',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['oil_refinery',
                 'world',
                 'ingest',
                 'https://www.eia.gov/petroleum/refinerycapacity/',
                 '',
                 '',
                 2000,
                 'EIA refinery capacity report — public annual data',
                 'oil_refinery',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['crude_grade',
                 'world',
                 'ingest',
                 'https://www.eia.gov/',
                 '',
                 '',
                 300,
                 'EIA + ICE benchmark crude grade registry',
                 'crude_grade',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['pricing_benchmark',
                 'world',
                 'ingest',
                 'https://www.eia.gov/',
                 '',
                 '',
                 100,
                 'EIA energy price benchmark data — already partially loaded',
                 'pricing_benchmark',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['rare_earth_coverage',
                 'world',
                 'ingest',
                 'https://minerals.usgs.gov/minerals/pubs/mcs/',
                 '',
                 '',
                 17,
                 'USGS Mineral Commodity Summaries — already seeded in Phase 1',
                 'rare_earth_coverage',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['oil_field',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 10000,
                 'Infer from IEA World Energy Outlook + USGS oil/gas field database',
                 'oil_field',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['oil_basin',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 2000,
                 'Infer from USGS/OPEC geological basin reports',
                 'oil_basin',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['oil_pipeline',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 5000,
                 'Infer from IEA energy infrastructure maps + EIA pipeline data',
                 'oil_pipeline',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['oil_terminal',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 1000,
                 'Infer from port authority databases + IEA oil storage data',
                 'oil_terminal',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['oil_trade',
                 'world',
                 'infer',
                 '',
                 'deep',
                 '',
                 5000000,
                 'Infer from UN Comtrade HS2709/2710 trade flows + IEA oil market report',
                 'oil_trade',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['oil_cargo',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 2000000,
                 "Infer from AIS vessel tracking + Lloyd's port call data",
                 'oil_cargo',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['bengoshi',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 45000,
                 'Infer from JFBA public directory (https://www.bengoshi.or.jp/)',
                 'bengoshi',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['judge',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 3000,
                 'Infer from Japan Supreme Court public judge roster',
                 'judge',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['ongakuka',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 50000,
                 'Infer from MusicBrainz artist database + JASRAC public data',
                 'ongakuka',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['gov_org',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 500000,
                 'Infer from Wikidata P31=Q7366 (government agency) SPARQL',
                 'gov_org',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['gov_municipality',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 500000,
                 'Infer from Wikidata P31=Q15284 (municipality) SPARQL',
                 'gov_municipality',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['food_product',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 1000000,
                 'Infer from USDA FoodData Central + Open Food Facts',
                 'food_product',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['energy_facility',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 100000,
                 'Infer from EIA power plant database + IAEA nuclear registry',
                 'energy_facility',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['mine',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 50000,
                 'Infer from USGS MRDS mine register + SNL Metals mining database',
                 'mine',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['natural_person',
                 'world',
                 'infer',
                 '',
                 'fast',
                 '',
                 8000000000,
                 'Infer notable persons from Wikidata P31=Q5 (human) — partial coverage only',
                 'natural_person',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe\n'
         '        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '      SELECT\n'
         '        $1,\n'
         '        $2,\n'
         '        $3,\n'
         '        $4,\n'
         '        $5,\n'
         '        $6,\n'
         '        CAST($7 AS bigint),\n'
         '        $8,\n'
         '        now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9\n'
         '          AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['adr',
                 'world',
                 'generate',
                 '',
                 '',
                 'adr_synth_v1',
                 500000,
                 'ADR case synthesis from AAA/ICC/ICSID public case databases',
                 'adr',
                 'world']},
 {'sql': '\n'
         '    INSERT INTO vertex_coverage_recipe\n'
         '      (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, '
         'world_total, notes, created_at)\n'
         '    SELECT\n'
         '      d.domain,\n'
         "      'world',\n"
         "      'defer',\n"
         "      '',\n"
         "      '',\n"
         "      '',\n"
         '      d.world_total,\n'
         "      'auto-deferred: no actionable public ingest path identified',\n"
         '      now()\n'
         '    FROM dim_world_domain d\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_coverage_recipe r\n'
         "      WHERE r.domain = d.domain AND r.authority_kind = 'world'\n"
         '    )\n'
         '  ',
  'parameters': []}]

DOWN = [{'sql': '\n'
         '    DELETE FROM vertex_coverage_recipe\n'
         "    WHERE notes = 'auto-deferred: no actionable public ingest path identified'\n"
         "      AND authority_kind = 'world'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['legal_entity']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['vessel']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['aircraft']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['patent']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['trademark']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['work']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['gtin_product']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['dns_observation']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['accommodation']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['hotel']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['minpaku']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['ryokan']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['game_actor']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['game_item']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['occupation_code']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['skill_taxonomy']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['job_posting']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['talent_cohort_stat']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['blockchain_actor']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['transport']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['spatial']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['apt_group']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['exploit_kit']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['ransomware_family']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['cybercrime_group']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['malicious_registrar']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['bulletproof_host']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['drug_product']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['oil_company']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['oil_refinery']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['crude_grade']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['pricing_benchmark']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['oil_field']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['oil_basin']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['oil_pipeline']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['oil_terminal']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['oil_trade']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['oil_cargo']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['bengoshi']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['judge']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['ongakuka']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['gov_org']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['gov_municipality']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['food_product']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['energy_facility']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['mine']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['natural_person']},
 {'sql': '\n'
         "      DELETE FROM vertex_coverage_recipe WHERE domain = $1 AND authority_kind = 'world'\n"
         '    ',
  'parameters': ['adr']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
