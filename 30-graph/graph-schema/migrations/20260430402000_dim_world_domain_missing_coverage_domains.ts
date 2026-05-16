import { Kysely, sql } from "kysely";

/**
 * Add 27 domains that exist in vertex_coverage_recipe but were missing
 * from dim_world_domain, preventing them from appearing in mv_world_coverage_live.
 *
 * Tier 1 (data already in mv_world_record_per_host):
 *   gov_org, gov_municipality → gov (516K records)
 *   food_product              → food (563K records)
 *   drug_product              → pharma (368K records)
 *   blockchain_actor          → blockchain (2.5K records)
 *
 * Tier 2 (app_host exists, ingest pipeline planned):
 *   trademark, work           → chizai
 *   legal_aid                 → npo
 *   investor_fund, mutual_fund, pension_fund, private_fund → securities
 *   government_fund, sovereign_fund → public-fund
 *   adr, family               → bengoshi / life-event
 *   game_actor, game_item     → media-gamers
 *   energy_facility           → energy
 *   crypto_asset_freeze       → sanctions
 *   rare_earth_coverage       → mine
 *   gtin_product              → gtin
 *   industry                  → isic
 *   dns_observation           → dns
 *   business_person           → legal-entity
 *   spatial, transport        → maps
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES
      ('gov_org',            'gov',          500000,         'government agencies (Wikidata P31=Q7366)',           'governance'),
      ('gov_municipality',   'gov',          500000,         'municipalities and local governments (global)',      'governance'),
      ('food_product',       'food',         1000000,        'food products (USDA FoodData Central + Open Food Facts)', 'food'),
      ('drug_product',       'pharma',       200000,         'drug products (FDA NDC bulk)',                       'pharma'),
      ('blockchain_actor',   'blockchain',   100000000,      'active blockchain addresses (Bitcoin + Ethereum)',   'blockchain'),
      ('trademark',          'chizai',       40000000,       'trademarks (WIPO Global Brand Database)',            'ip'),
      ('work',               'chizai',       10000000,       'public works (ISNI + Creative Commons registry)',    'ip'),
      ('legal_aid',          'npo',          10000000,       'legal aid organizations (ILAG)',                     'legal'),
      ('investor_fund',      'securities',   500000,         'institutional investor funds (SEC 13F)',             'finance'),
      ('mutual_fund',        'securities',   150000,         'mutual funds (SEC EDGAR)',                           'finance'),
      ('pension_fund',       'securities',   350000,         'pension funds (OECD global statistics)',             'finance'),
      ('private_fund',       'securities',   300000,         'private funds (SEC Form PF)',                        'finance'),
      ('government_fund',    'public-fund',  25000,          'government investment funds (SWF Institute)',        'finance'),
      ('sovereign_fund',     'public-fund',  250,            'sovereign wealth funds (SWF Institute rankings)',   'finance'),
      ('adr',                'bengoshi',     1000000,        'arbitration and mediation disputes (AAA/ICC)',       'legal'),
      ('family',             'life-event',   2000,           'family law systems across 195 jurisdictions',        'legal'),
      ('game_actor',         'media-gamers', 200000,         'game companies (IGDB publishers/developers)',        'entertainment'),
      ('game_item',          'media-gamers', 500000,         'game titles (IGDB)',                                 'entertainment'),
      ('energy_facility',    'energy',       100000,         'power plants and energy facilities (EIA + IAEA)',   'energy'),
      ('crypto_asset_freeze','sanctions',    100000,         'frozen crypto assets (OFAC SDN XML)',                'sanctions'),
      ('rare_earth_coverage','mine',         350,            'rare earth mineral commodity stats (USGS)',          'mining'),
      ('gtin_product',       'gtin',         1000000000,     'barcoded products (GS1 GEPIR)',                      'commerce'),
      ('industry',           'isic',         3000,           'industry classification authority nodes (ISIC/NAICS)', 'classification'),
      ('dns_observation',    'dns',          400000000,      'passive DNS observations (Rapid7 FDNS)',             'security'),
      ('business_person',    'legal-entity', 100000000,      'business persons (LEI person role synthesis)',       'identity'),
      ('spatial',            'maps',         1000000000,     'spatial features and POIs (OpenStreetMap)',          'geography'),
      ('transport',          'maps',         50000000,       'public transit stops and routes (GTFS)',             'transport')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM dim_world_domain
    WHERE domain IN (
      'gov_org', 'gov_municipality', 'food_product', 'drug_product',
      'blockchain_actor', 'trademark', 'work', 'legal_aid',
      'investor_fund', 'mutual_fund', 'pension_fund', 'private_fund',
      'government_fund', 'sovereign_fund', 'adr', 'family',
      'game_actor', 'game_item', 'energy_facility', 'crypto_asset_freeze',
      'rare_earth_coverage', 'gtin_product', 'industry', 'dns_observation',
      'business_person', 'spatial', 'transport'
    )
  `.execute(db);
}
