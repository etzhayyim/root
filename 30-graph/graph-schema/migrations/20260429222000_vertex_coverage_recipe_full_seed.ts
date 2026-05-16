/**
 * Coverage recipe full seed — classify all remaining dim_world_domain entries.
 *
 * Phase 1 (20260429220000) seeded 30 explicit rows.
 * This migration:
 *   1. Adds explicit ingest/infer/generate recipes for actionable high-regret domains.
 *   2. Bulk-defers all remaining dim_world_domain entries not yet in vertex_coverage_recipe.
 *
 * RisingWave compat: upsert via WHERE NOT EXISTS (RW rejects upsert syntax).
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

// ── helpers ───────────────────────────────────────────────────────────────────

const NOW = sql`now()`;

async function seedIfAbsent(
  db: Kysely<unknown>,
  rows: Array<{
    domain: string;
    authority_kind?: string;
    recipe_kind: "ingest" | "infer" | "generate" | "hybrid" | "defer";
    source_url?: string;
    llm_tier?: string;
    langgraph_id?: string;
    world_total?: number;
    notes?: string;
  }>,
): Promise<void> {
  for (const row of rows) {
    const ak = row.authority_kind ?? "world";
    const domain = row.domain;
    const recipeKind = row.recipe_kind;
    const sourceUrl = row.source_url ?? "";
    const llmTier = row.llm_tier ?? "";
    const langgraphId = row.langgraph_id ?? "";
    const worldTotal = row.world_total ?? 0;
    const notes = row.notes ?? "";
    await sql`
      INSERT INTO vertex_coverage_recipe
        (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, world_total, notes, created_at)
      SELECT
        ${domain},
        ${ak},
        ${recipeKind},
        ${sourceUrl},
        ${llmTier},
        ${langgraphId},
        CAST(${worldTotal} AS bigint),
        ${notes},
        now()
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_coverage_recipe
        WHERE domain = ${domain}
          AND authority_kind = ${ak}
      )
    `.execute(db);
  }
}

// ── up ────────────────────────────────────────────────────────────────────────

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── 1. Ingest: public data feeds ──────────────────────────────────────────
  await seedIfAbsent(db, [
    // global company registry
    {
      domain: "legal_entity",
      recipe_kind: "ingest",
      source_url: "https://api.gleif.org/api/v1/lei-records",
      world_total: 200_000_000,
      notes: "GLEIF LEI bulk feed; active legal entities globally",
    },
    // maritime fleet
    {
      domain: "vessel",
      recipe_kind: "ingest",
      source_url: "https://www.marinetraffic.com/",
      world_total: 90_000,
      notes: "IMO GISIS + AIS public vessel registry",
    },
    // aviation fleet
    {
      domain: "aircraft",
      recipe_kind: "ingest",
      source_url: "https://openflights.org/data.html",
      world_total: 200_000,
      notes: "ICAO + OpenFlights aircraft register; already partially loaded via maps BPMN",
    },
    // intellectual property
    {
      domain: "patent",
      recipe_kind: "ingest",
      source_url: "https://bulkdata.uspto.gov/",
      world_total: 100_000_000,
      notes: "USPTO bulk XML + EPO OPS",
    },
    {
      domain: "trademark",
      recipe_kind: "ingest",
      source_url: "https://branddb.wipo.int/",
      world_total: 40_000_000,
      notes: "WIPO Global Brand Database",
    },
    {
      domain: "work",
      recipe_kind: "ingest",
      source_url: "https://isni.org/",
      world_total: 10_000_000,
      notes: "ISNI + Creative Commons public works registry",
    },
    // product barcodes
    {
      domain: "gtin_product",
      recipe_kind: "ingest",
      source_url: "https://www.gs1.org/services/verified-by-gs1",
      world_total: 1_000_000_000,
      notes: "GS1 GEPIR public barcode lookup",
    },
    // internet infrastructure
    {
      domain: "dns_observation",
      recipe_kind: "ingest",
      source_url: "https://opendata.rapid7.com/sonar.fdns_v2/",
      world_total: 400_000_000,
      notes: "Rapid7 FDNS passive DNS open dataset",
    },
    // hospitality
    {
      domain: "accommodation",
      recipe_kind: "ingest",
      source_url: "https://api.openstreetmap.org/",
      world_total: 500_000,
      notes: "OpenStreetMap amenity=hotel/hostel/guest_house",
    },
    {
      domain: "hotel",
      recipe_kind: "ingest",
      source_url: "https://api.openstreetmap.org/",
      world_total: 700_000,
      notes: "OSM tourism=hotel; covered by accommodation ingest",
    },
    {
      domain: "minpaku",
      recipe_kind: "ingest",
      source_url: "https://www.mlit.go.jp/kankocho/minpaku/",
      world_total: 50_000,
      notes: "Japan MLIT minpaku (民泊) public registry",
    },
    {
      domain: "ryokan",
      recipe_kind: "ingest",
      source_url: "https://www.ryokan.or.jp/",
      world_total: 20_000,
      notes: "Japan Ryokan Association public registry",
    },
    // gaming media
    {
      domain: "game_actor",
      recipe_kind: "ingest",
      source_url: "https://api.igdb.com/v4/companies",
      world_total: 200_000,
      notes: "IGDB companies API — publishers/developers",
    },
    {
      domain: "game_item",
      recipe_kind: "ingest",
      source_url: "https://api.igdb.com/v4/games",
      world_total: 500_000,
      notes: "IGDB games API — titles as items",
    },
    // talent
    {
      domain: "occupation_code",
      recipe_kind: "ingest",
      source_url: "https://www.ilo.org/ilostat-files/ISCO/newdocs-08-2012/ISCO-08/ISCO-08%20EN.pdf",
      world_total: 500,
      notes: "ILO ISCO-08 + ESCO occupation taxonomy — already loaded",
    },
    {
      domain: "skill_taxonomy",
      recipe_kind: "ingest",
      source_url: "https://esco.ec.europa.eu/en/about-esco/escodownload",
      world_total: 14_000,
      notes: "ESCO skill taxonomy download — already partially loaded",
    },
    {
      domain: "job_posting",
      recipe_kind: "ingest",
      source_url: "https://indeed.com/",
      world_total: 100_000_000,
      notes: "Public job board aggregation; partial via LinkedIn/Indeed feeds",
    },
    {
      domain: "talent_cohort_stat",
      recipe_kind: "ingest",
      source_url: "https://ilostat.ilo.org/data/",
      world_total: 100_000,
      notes: "ILO ILOSTAT bulk statistics download — already partially loaded",
    },
    // blockchain
    {
      domain: "blockchain_actor",
      recipe_kind: "ingest",
      source_url: "https://blockchain.info/",
      world_total: 100_000_000,
      notes: "Public blockchain address registry (Bitcoin + Ethereum active addresses)",
    },
    // transport
    {
      domain: "transport",
      recipe_kind: "ingest",
      source_url: "https://transitfeeds.com/",
      world_total: 50_000_000,
      notes: "GTFS public transit feeds — already loaded via maps BPMN R/P7D",
    },
    // maps / spatial
    {
      domain: "spatial",
      recipe_kind: "ingest",
      source_url: "https://www.openstreetmap.org/",
      world_total: 1_000_000_000,
      notes: "OpenStreetMap POI + feature data",
    },
    // cybersecurity (malak domains) — CTI open feeds
    {
      domain: "apt_group",
      recipe_kind: "ingest",
      source_url: "https://attack.mitre.org/groups/",
      world_total: 300_000,
      notes: "MITRE ATT&CK groups + CISA known threat actors",
    },
    {
      domain: "exploit_kit",
      recipe_kind: "ingest",
      source_url: "https://abuse.ch/",
      world_total: 300_000,
      notes: "abuse.ch URLhaus + MalwareBazaar public feed",
    },
    {
      domain: "ransomware_family",
      recipe_kind: "ingest",
      source_url: "https://id-ransomware.malwarehunterteam.com/",
      world_total: 300_000,
      notes: "ID Ransomware + MITRE ATT&CK malware catalog",
    },
    {
      domain: "cybercrime_group",
      recipe_kind: "ingest",
      source_url: "https://attack.mitre.org/groups/",
      world_total: 300_000,
      notes: "MITRE ATT&CK groups — financially motivated",
    },
    {
      domain: "malicious_registrar",
      recipe_kind: "ingest",
      source_url: "https://www.spamhaus.org/",
      world_total: 300_000,
      notes: "Spamhaus Domain Block List + SURBL public feed",
    },
    {
      domain: "bulletproof_host",
      recipe_kind: "ingest",
      source_url: "https://www.spamhaus.org/",
      world_total: 300_000,
      notes: "Spamhaus CBL + Team Cymru ASN reputation feeds",
    },
    // pharmaceutical
    {
      domain: "drug_product",
      recipe_kind: "ingest",
      source_url: "https://open.fda.gov/apis/drug/ndc/",
      world_total: 200_000,
      notes: "FDA NDC bulk download — already loaded in classification migrations",
    },
    // energy / oil (public registers)
    {
      domain: "oil_company",
      recipe_kind: "ingest",
      source_url: "https://www.sec.gov/cgi-bin/browse-edgar",
      world_total: 200,
      notes: "SEC EDGAR energy sector + IEA national oil company registry",
    },
    {
      domain: "oil_refinery",
      recipe_kind: "ingest",
      source_url: "https://www.eia.gov/petroleum/refinerycapacity/",
      world_total: 2_000,
      notes: "EIA refinery capacity report — public annual data",
    },
    {
      domain: "crude_grade",
      recipe_kind: "ingest",
      source_url: "https://www.eia.gov/",
      world_total: 300,
      notes: "EIA + ICE benchmark crude grade registry",
    },
    {
      domain: "pricing_benchmark",
      recipe_kind: "ingest",
      source_url: "https://www.eia.gov/",
      world_total: 100,
      notes: "EIA energy price benchmark data — already partially loaded",
    },
    // natural science
    {
      domain: "rare_earth_coverage",
      recipe_kind: "ingest",
      source_url: "https://minerals.usgs.gov/minerals/pubs/mcs/",
      world_total: 17,
      notes: "USGS Mineral Commodity Summaries — already seeded in Phase 1",
    },
  ]);

  // ── 2. Infer: SQL UDF + LLM classification ────────────────────────────────
  await seedIfAbsent(db, [
    // oil supply chain (infer from IEA/OPEC reports + LLM)
    {
      domain: "oil_field",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 10_000,
      notes: "Infer from IEA World Energy Outlook + USGS oil/gas field database",
    },
    {
      domain: "oil_basin",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 2_000,
      notes: "Infer from USGS/OPEC geological basin reports",
    },
    {
      domain: "oil_pipeline",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 5_000,
      notes: "Infer from IEA energy infrastructure maps + EIA pipeline data",
    },
    {
      domain: "oil_terminal",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 1_000,
      notes: "Infer from port authority databases + IEA oil storage data",
    },
    {
      domain: "oil_trade",
      recipe_kind: "infer",
      llm_tier: "deep",
      world_total: 5_000_000,
      notes: "Infer from UN Comtrade HS2709/2710 trade flows + IEA oil market report",
    },
    {
      domain: "oil_cargo",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 2_000_000,
      notes: "Infer from AIS vessel tracking + Lloyd's port call data",
    },
    // Japanese professional registries
    {
      domain: "bengoshi",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 45_000,
      notes: "Infer from JFBA public directory (https://www.bengoshi.or.jp/)",
    },
    {
      domain: "judge",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 3_000,
      notes: "Infer from Japan Supreme Court public judge roster",
    },
    // media / entertainment
    {
      domain: "ongakuka",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 50_000,
      notes: "Infer from MusicBrainz artist database + JASRAC public data",
    },
    // government taxonomy
    {
      domain: "gov_org",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 500_000,
      notes: "Infer from Wikidata P31=Q7366 (government agency) SPARQL",
    },
    {
      domain: "gov_municipality",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 500_000,
      notes: "Infer from Wikidata P31=Q15284 (municipality) SPARQL",
    },
    // food / nutrition (public databases)
    {
      domain: "food_product",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 1_000_000,
      notes: "Infer from USDA FoodData Central + Open Food Facts",
    },
    // energy
    {
      domain: "energy_facility",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 100_000,
      notes: "Infer from EIA power plant database + IAEA nuclear registry",
    },
    // mining
    {
      domain: "mine",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 50_000,
      notes: "Infer from USGS MRDS mine register + SNL Metals mining database",
    },
    // natural persons (partial — limited public coverage)
    {
      domain: "natural_person",
      recipe_kind: "infer",
      llm_tier: "fast",
      world_total: 8_000_000_000,
      notes: "Infer notable persons from Wikidata P31=Q5 (human) — partial coverage only",
    },
  ]);

  // ── 3. Generate: multi-hop LangGraph synthesis ────────────────────────────
  await seedIfAbsent(db, [
    // sovereign + treaty authority kinds already seeded as domain authority in Phase 1
    // add world authority for key domains needing synthesis
    {
      domain: "adr",
      recipe_kind: "generate",
      langgraph_id: "adr_synth_v1",
      world_total: 500_000,
      notes: "ADR case synthesis from AAA/ICC/ICSID public case databases",
    },
  ]);

  // ── 4. Bulk defer: all remaining dim_world_domain entries ─────────────────
  // Any domain in dim_world_domain not yet classified → defer.
  // This covers private enterprise IoT (shokuhin_lot, building_*, nimotsu, etc.)
  // and any future domains added to dim_world_domain.
  // dim_world_domain columns: domain, app_host, world_total, unit, sector (no authority_kind).
  await sql`
    INSERT INTO vertex_coverage_recipe
      (domain, authority_kind, recipe_kind, source_url, llm_tier, langgraph_id, world_total, notes, created_at)
    SELECT
      d.domain,
      'world',
      'defer',
      '',
      '',
      '',
      d.world_total,
      'auto-deferred: no actionable public ingest path identified',
      now()
    FROM dim_world_domain d
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_coverage_recipe r
      WHERE r.domain = d.domain AND r.authority_kind = 'world'
    )
  `.execute(db);

  // mv_coverage_gap_minimax is a streaming MV — auto-updates within seconds.
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Remove only the rows added by this migration — keep Phase 1 explicit rows.
  // The bulk-defer rows are identified by the auto-deferred note.
  await sql`
    DELETE FROM vertex_coverage_recipe
    WHERE notes = 'auto-deferred: no actionable public ingest path identified'
      AND authority_kind = 'world'
  `.execute(db);

  // Remove explicitly seeded rows from this migration (those not in Phase 1).
  const phase2Domains = [
    "legal_entity", "vessel", "aircraft", "patent", "trademark", "work",
    "gtin_product", "dns_observation", "accommodation", "hotel", "minpaku", "ryokan",
    "game_actor", "game_item", "occupation_code", "skill_taxonomy", "job_posting",
    "talent_cohort_stat", "blockchain_actor", "transport", "spatial",
    "apt_group", "exploit_kit", "ransomware_family", "cybercrime_group",
    "malicious_registrar", "bulletproof_host", "drug_product",
    "oil_company", "oil_refinery", "crude_grade", "pricing_benchmark",
    "oil_field", "oil_basin", "oil_pipeline", "oil_terminal", "oil_trade", "oil_cargo",
    "bengoshi", "judge", "ongakuka", "gov_org", "gov_municipality",
    "food_product", "energy_facility", "mine", "natural_person", "adr",
  ];

  for (const domain of phase2Domains) {
    await sql`
      DELETE FROM vertex_coverage_recipe WHERE domain = ${domain} AND authority_kind = 'world'
    `.execute(db);
  }

}
