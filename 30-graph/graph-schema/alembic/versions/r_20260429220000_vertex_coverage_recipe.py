"""Captured from Kysely migration 20260429220000_vertex_coverage_recipe."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429220000_vertex_coverage_recipe"
down_revision = 'r_20260429219100_seed_ads_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_coverage_recipe (\n'
         '      domain          text        NOT NULL,\n'
         "      authority_kind  text        NOT NULL DEFAULT 'world',\n"
         '      recipe_kind     text        NOT NULL,\n'
         '      source_url      text,\n'
         "      llm_tier        text        NOT NULL DEFAULT 'structured',\n"
         '      langgraph_id    text,\n'
         '      world_total     bigint      NOT NULL DEFAULT 0,\n'
         '      notes           text,\n'
         '      created_at      timestamptz NOT NULL DEFAULT now(),\n'
         '      PRIMARY KEY (domain, authority_kind)\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['crypto_asset_freeze',
                 'world',
                 'ingest',
                 'https://www.treasury.gov/ofac/downloads/sdn.xml',
                 'fast',
                 '',
                 100000,
                 'OFAC SDN XML — vertex_crypto_asset_freeze',
                 'crypto_asset_freeze',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['rare_earth_coverage',
                 'world',
                 'ingest',
                 'https://www.usgs.gov/centers/national-minerals-information-center/rare-earths-statistics-and-information',
                 'fast',
                 '',
                 350,
                 'USGS rare-earth mineral commodity stats',
                 'rare_earth_coverage',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['government_fund',
                 'world',
                 'ingest',
                 'https://www.swfinstitute.org/fund-rankings/sovereign-wealth-fund',
                 'fast',
                 '',
                 25000,
                 'SWF Institute global government fund list',
                 'government_fund',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['sovereign_fund',
                 'world',
                 'ingest',
                 'https://www.swfinstitute.org/fund-rankings/sovereign-wealth-fund',
                 'fast',
                 '',
                 250,
                 'SWF Institute sovereign fund rankings',
                 'sovereign_fund',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['mutual_fund',
                 'world',
                 'ingest',
                 'https://api.sec.gov/submissions',
                 'fast',
                 '',
                 150000,
                 'SEC EDGAR mutual fund filings',
                 'mutual_fund',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['investor_fund',
                 'world',
                 'ingest',
                 'https://efts.sec.gov/LATEST/search-index?dateRange=custom&startdt=2024-01-01&forms=13F-HR',
                 'fast',
                 '',
                 500000,
                 'SEC 13F institutional investor fund filings',
                 'investor_fund',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['pension_fund',
                 'world',
                 'ingest',
                 'https://www.oecd.org/finance/private-pensions/globalpensionstatistics.htm',
                 'fast',
                 '',
                 350000,
                 'OECD global pension fund statistics',
                 'pension_fund',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['private_fund',
                 'world',
                 'ingest',
                 'https://efts.sec.gov/LATEST/search-index?forms=PF',
                 'fast',
                 '',
                 300000,
                 'SEC Form PF private fund advisers',
                 'private_fund',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['adr',
                 'world',
                 'ingest',
                 'https://www.adr.org/sites/default/files/document_repository/AAA_Stats_2023.pdf',
                 'fast',
                 '',
                 1000000,
                 'AAA/ICC arbitration dispute registry',
                 'adr',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['business_person',
                 'world',
                 'generate',
                 'https://api.gleif.org/api/v1/lei-records',
                 'deep',
                 'business_person_synth_v1',
                 100000000,
                 'LEI → person facts → role extraction → DID synthesis',
                 'business_person',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['legal_aid',
                 'world',
                 'generate',
                 'https://www.ilagnet.org/joom/',
                 'mid',
                 'legal_aid_synth_v1',
                 10000000,
                 'ILAG legal aid organizations → multilingual profile synthesis',
                 'legal_aid',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['dmf',
                 'world',
                 'infer',
                 'https://ssa.gov/datafiles/access/dmf',
                 'structured',
                 '',
                 100000,
                 'Social Security Death Master File — classify + extract',
                 'dmf',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['cofog',
                 'world',
                 'infer',
                 'https://unstats.un.org/unsd/classifications/Econ/cofog',
                 'structured',
                 '',
                 6000,
                 'UN COFOG government function classifications',
                 'cofog',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['commodities',
                 'world',
                 'infer',
                 'https://data.nasdaq.com/api/v3/datasets/CHRIS',
                 'structured',
                 '',
                 5500,
                 'Commodity futures contracts — classify and normalize',
                 'commodities',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['photos',
                 'world',
                 'defer',
                 '',
                 'fast',
                 '',
                 5000000000000,
                 '5T images — no tractable ingest path; track with platform samples',
                 'photos',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['koutei_step',
                 'world',
                 'defer',
                 '',
                 'fast',
                 '',
                 1000000000000,
                 '1T manufacturing steps — customer-domain data, not public',
                 'koutei_step',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['kessai',
                 'world',
                 'defer',
                 '',
                 'fast',
                 '',
                 1000000000000,
                 '1T payment records — PII tier 3; no public ingest',
                 'kessai',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['sgtin',
                 'world',
                 'defer',
                 '',
                 'fast',
                 '',
                 1000000000000,
                 '1T RFID/SGTIN — supply chain private data',
                 'sgtin',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['invoice',
                 'world',
                 'defer',
                 '',
                 'fast',
                 '',
                 500000000000,
                 '500B invoices — private business data; sample via e-invoice APIs',
                 'invoice',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['receipt',
                 'world',
                 'defer',
                 '',
                 'fast',
                 '',
                 500000000000,
                 '500B receipts — private consumer data; PII tier 3',
                 'receipt',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['api_endpoint',
                 'world',
                 'defer',
                 '',
                 'fast',
                 '',
                 1000000000,
                 '1B API endpoints — discoverable only via crawl; site.etzhayyim.com dependency',
                 'api_endpoint',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['api_schema',
                 'world',
                 'defer',
                 '',
                 'fast',
                 '',
                 1000000000,
                 '1B OpenAPI schemas — crawl-dependent; deferred to site actor',
                 'api_schema',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['code_file',
                 'world',
                 'defer',
                 '',
                 'fast',
                 '',
                 100000000000,
                 '100B code files — GitHub/GitLab crawl; too large for batch',
                 'code_file',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['code_symbol',
                 'world',
                 'defer',
                 '',
                 'fast',
                 '',
                 50000000000,
                 '50B symbols — derived from code_file; deferred',
                 'code_symbol',
                 'world']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['sovereign',
                 'domain',
                 'ingest',
                 'https://www.un.org/en/about-us/member-states',
                 'fast',
                 '',
                 195000,
                 'UN member states rules — expand 390→195000 coverage',
                 'sovereign',
                 'domain']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['treaty',
                 'domain',
                 'ingest',
                 'https://ihl-databases.icrc.org/ihl',
                 'fast',
                 '',
                 5000,
                 'ICRC IHL treaty database — expand to 500 authority nodes',
                 'treaty',
                 'domain']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['family',
                 'domain',
                 'generate',
                 '',
                 'mid',
                 'family_law_synth_v1',
                 2000,
                 'Family law systems across 195 jurisdictions — LangGraph synthesis',
                 'family',
                 'domain']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['blockchain',
                 'domain',
                 'ingest',
                 'https://chainlist.org',
                 'fast',
                 '',
                 5000,
                 'Chainlist EVM networks + other blockchain authority nodes',
                 'blockchain',
                 'domain']},
 {'sql': '\n'
         '      INSERT INTO vertex_coverage_recipe (\n'
         '        domain, authority_kind, recipe_kind, source_url, llm_tier,\n'
         '        langgraph_id, world_total, notes, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         '        $4, $5, $6,\n'
         '        CAST($7 AS bigint), $8, now()\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_coverage_recipe\n'
         '        WHERE domain = $9 AND authority_kind = $10\n'
         '      )\n'
         '    ',
  'parameters': ['industry',
                 'domain',
                 'infer',
                 'https://www.iso.org/isic',
                 'structured',
                 '',
                 3000,
                 'ISIC/NAICS industry classification authority nodes',
                 'industry',
                 'domain']}]

DOWN = [{'sql': 'DROP TABLE IF EXISTS vertex_coverage_recipe', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
