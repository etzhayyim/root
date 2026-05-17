/**
 * vertex_coverage_recipe — Von Neumann stored-program memory for coverage gap bridge.
 *
 * Each row classifies one (domain) into a recipe_kind that drives BPMN routing:
 *   ingest   — pure HTTP pull (OFAC SDN, GLEIF, gov open data …)
 *   infer    — SQL classify + LLM structured tier (fast/structured)
 *   generate — LangGraph multi-hop synthesis (business_person, legal_aid …)
 *   hybrid   — ingest first, then re-classify with LLM
 *   defer    — world_total too large; no actionable ingest path today
 *
 * The BPMN coverageGapBridge.bpmn reads this table via coverage.gap.scan
 * (minimax-regret SELECT ORDER BY world_total*(1-coverage) DESC LIMIT 1).
 *
 * SQL UDF classify_coverage_recipe(domain text) and MV mv_coverage_gap_minimax
 * are created in the next migration (20260429220100).
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // Table: stored-program recipe memory
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_coverage_recipe (
      domain          text        NOT NULL,
      authority_kind  text        NOT NULL DEFAULT 'world',
      recipe_kind     text        NOT NULL,
      source_url      text,
      llm_tier        text        NOT NULL DEFAULT 'structured',
      langgraph_id    text,
      world_total     bigint      NOT NULL DEFAULT 0,
      notes           text,
      created_at      timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY (domain, authority_kind)
    )
  `.execute(db);

  // Seed: zero-coverage and high-regret domains classified

  type Row = {
    domain: string;
    authority_kind: string;
    recipe_kind: string;
    source_url: string;
    llm_tier: string;
    langgraph_id: string;
    world_total: number;
    notes: string;
  };

  const seeds: Row[] = [
    // ── INGEST: pure data pulls ─────────────────────────────────────────────
    {
      domain: "crypto_asset_freeze",
      authority_kind: "world",
      recipe_kind: "ingest",
      source_url: "https://www.treasury.gov/ofac/downloads/sdn.xml",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 100_000,
      notes: "OFAC SDN XML — vertex_crypto_asset_freeze",
    },
    {
      domain: "rare_earth_coverage",
      authority_kind: "world",
      recipe_kind: "ingest",
      source_url: "https://www.usgs.gov/centers/national-minerals-information-center/rare-earths-statistics-and-information",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 350,
      notes: "USGS rare-earth mineral commodity stats",
    },
    {
      domain: "government_fund",
      authority_kind: "world",
      recipe_kind: "ingest",
      source_url: "https://www.swfinstitute.org/fund-rankings/sovereign-wealth-fund",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 25_000,
      notes: "SWF Institute global government fund list",
    },
    {
      domain: "sovereign_fund",
      authority_kind: "world",
      recipe_kind: "ingest",
      source_url: "https://www.swfinstitute.org/fund-rankings/sovereign-wealth-fund",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 250,
      notes: "SWF Institute sovereign fund rankings",
    },
    {
      domain: "mutual_fund",
      authority_kind: "world",
      recipe_kind: "ingest",
      source_url: "https://api.sec.gov/submissions",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 150_000,
      notes: "SEC EDGAR mutual fund filings",
    },
    {
      domain: "investor_fund",
      authority_kind: "world",
      recipe_kind: "ingest",
      source_url: "https://efts.sec.gov/LATEST/search-index?dateRange=custom&startdt=2024-01-01&forms=13F-HR",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 500_000,
      notes: "SEC 13F institutional investor fund filings",
    },
    {
      domain: "pension_fund",
      authority_kind: "world",
      recipe_kind: "ingest",
      source_url: "https://www.oecd.org/finance/private-pensions/globalpensionstatistics.htm",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 350_000,
      notes: "OECD global pension fund statistics",
    },
    {
      domain: "private_fund",
      authority_kind: "world",
      recipe_kind: "ingest",
      source_url: "https://efts.sec.gov/LATEST/search-index?forms=PF",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 300_000,
      notes: "SEC Form PF private fund advisers",
    },
    {
      domain: "adr",
      authority_kind: "world",
      recipe_kind: "ingest",
      source_url: "https://www.adr.org/sites/default/files/document_repository/AAA_Stats_2023.pdf",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 1_000_000,
      notes: "AAA/ICC arbitration dispute registry",
    },

    // ── GENERATE: LangGraph multi-hop synthesis ──────────────────────────────
    {
      domain: "business_person",
      authority_kind: "world",
      recipe_kind: "generate",
      source_url: "https://api.gleif.org/api/v1/lei-records",
      llm_tier: "deep",
      langgraph_id: "business_person_synth_v1",
      world_total: 100_000_000,
      notes: "LEI → person facts → role extraction → DID synthesis",
    },
    {
      domain: "legal_aid",
      authority_kind: "world",
      recipe_kind: "generate",
      source_url: "https://www.ilagnet.org/joom/",
      llm_tier: "mid",
      langgraph_id: "legal_aid_synth_v1",
      world_total: 10_000_000,
      notes: "ILAG legal aid organizations → multilingual profile synthesis",
    },

    // ── INFER: SQL UDF classify + LLM structured ─────────────────────────────
    {
      domain: "dmf",
      authority_kind: "world",
      recipe_kind: "infer",
      source_url: "https://ssa.gov/datafiles/access/dmf",
      llm_tier: "structured",
      langgraph_id: "",
      world_total: 100_000,
      notes: "Social Security Death Master File — classify + extract",
    },
    {
      domain: "cofog",
      authority_kind: "world",
      recipe_kind: "infer",
      source_url: "https://unstats.un.org/unsd/classifications/Econ/cofog",
      llm_tier: "structured",
      langgraph_id: "",
      world_total: 6_000,
      notes: "UN COFOG government function classifications",
    },
    {
      domain: "commodities",
      authority_kind: "world",
      recipe_kind: "infer",
      source_url: "https://data.nasdaq.com/api/v3/datasets/CHRIS",
      llm_tier: "structured",
      langgraph_id: "",
      world_total: 5_500,
      notes: "Commodity futures contracts — classify and normalize",
    },

    // ── DEFER: world_total too large for actionable ingest ───────────────────
    {
      domain: "photos",
      authority_kind: "world",
      recipe_kind: "defer",
      source_url: "",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 5_000_000_000_000,
      notes: "5T images — no tractable ingest path; track with platform samples",
    },
    {
      domain: "koutei_step",
      authority_kind: "world",
      recipe_kind: "defer",
      source_url: "",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 1_000_000_000_000,
      notes: "1T manufacturing steps — customer-domain data, not public",
    },
    {
      domain: "kessai",
      authority_kind: "world",
      recipe_kind: "defer",
      source_url: "",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 1_000_000_000_000,
      notes: "1T payment records — PII tier 3; no public ingest",
    },
    {
      domain: "sgtin",
      authority_kind: "world",
      recipe_kind: "defer",
      source_url: "",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 1_000_000_000_000,
      notes: "1T RFID/SGTIN — supply chain private data",
    },
    {
      domain: "invoice",
      authority_kind: "world",
      recipe_kind: "defer",
      source_url: "",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 500_000_000_000,
      notes: "500B invoices — private business data; sample via e-invoice APIs",
    },
    {
      domain: "receipt",
      authority_kind: "world",
      recipe_kind: "defer",
      source_url: "",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 500_000_000_000,
      notes: "500B receipts — private consumer data; PII tier 3",
    },
    {
      domain: "api_endpoint",
      authority_kind: "world",
      recipe_kind: "defer",
      source_url: "",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 1_000_000_000,
      notes: "1B API endpoints — discoverable only via crawl; site.etzhayyim.com dependency",
    },
    {
      domain: "api_schema",
      authority_kind: "world",
      recipe_kind: "defer",
      source_url: "",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 1_000_000_000,
      notes: "1B OpenAPI schemas — crawl-dependent; deferred to site actor",
    },
    {
      domain: "code_file",
      authority_kind: "world",
      recipe_kind: "defer",
      source_url: "",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 100_000_000_000,
      notes: "100B code files — GitHub/GitLab crawl; too large for batch",
    },
    {
      domain: "code_symbol",
      authority_kind: "world",
      recipe_kind: "defer",
      source_url: "",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 50_000_000_000,
      notes: "50B symbols — derived from code_file; deferred",
    },

    // ── INGEST: domain authority chain kinds ─────────────────────────────────
    {
      domain: "sovereign",
      authority_kind: "domain",
      recipe_kind: "ingest",
      source_url: "https://www.un.org/en/about-us/member-states",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 195000,
      notes: "UN member states rules — expand 390→195000 coverage",
    },
    {
      domain: "treaty",
      authority_kind: "domain",
      recipe_kind: "ingest",
      source_url: "https://ihl-databases.icrc.org/ihl",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 5000,
      notes: "ICRC IHL treaty database — expand to 500 authority nodes",
    },
    {
      domain: "family",
      authority_kind: "domain",
      recipe_kind: "generate",
      source_url: "",
      llm_tier: "mid",
      langgraph_id: "family_law_synth_v1",
      world_total: 2000,
      notes: "Family law systems across 195 jurisdictions — LangGraph synthesis",
    },
    {
      domain: "blockchain",
      authority_kind: "domain",
      recipe_kind: "ingest",
      source_url: "https://chainlist.org",
      llm_tier: "fast",
      langgraph_id: "",
      world_total: 5000,
      notes: "Chainlist EVM networks + other blockchain authority nodes",
    },
    {
      domain: "industry",
      authority_kind: "domain",
      recipe_kind: "infer",
      source_url: "https://www.iso.org/isic",
      llm_tier: "structured",
      langgraph_id: "",
      world_total: 3000,
      notes: "ISIC/NAICS industry classification authority nodes",
    },
  ];

  for (const row of seeds) {
    await sql`
      INSERT INTO vertex_coverage_recipe (
        domain, authority_kind, recipe_kind, source_url, llm_tier,
        langgraph_id, world_total, notes, created_at
      )
      SELECT
        ${row.domain}, ${row.authority_kind}, ${row.recipe_kind},
        ${row.source_url}, ${row.llm_tier}, ${row.langgraph_id},
        CAST(${row.world_total} AS bigint), ${row.notes}, now()
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_coverage_recipe
        WHERE domain = ${row.domain} AND authority_kind = ${row.authority_kind}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_coverage_recipe`.execute(db);
}
