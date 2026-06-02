import type { Kysely } from "kysely";
import { sql } from "kysely";

const ownerDid = "did:web:flight-offer.etzhayyim.com";
const createdAt = "2026-04-27T15:01:00Z";
const actorTag = "sys.bpmn.seed.flight-offer";

interface Airline {
  iata: string;
  icao: string;
  name: string;
  country: string;
  alliance: string;
}

// Top 30 airlines by 2024 RPK (revenue passenger-kilometers). Order = rough
// global ranking; covers ~75% of scheduled commercial pax. Add more rows
// as ingest demand grows — schema is wide enough for the full IATA registry
// (~5000 codes).
const AIRLINES: Airline[] = [
  { iata: "AA", icao: "AAL", name: "American Airlines", country: "US", alliance: "OneWorld" },
  { iata: "DL", icao: "DAL", name: "Delta Air Lines", country: "US", alliance: "SkyTeam" },
  { iata: "UA", icao: "UAL", name: "United Airlines", country: "US", alliance: "Star Alliance" },
  { iata: "WN", icao: "SWA", name: "Southwest Airlines", country: "US", alliance: "" },
  { iata: "B6", icao: "JBU", name: "JetBlue Airways", country: "US", alliance: "" },
  { iata: "AS", icao: "ASA", name: "Alaska Airlines", country: "US", alliance: "OneWorld" },
  { iata: "AC", icao: "ACA", name: "Air Canada", country: "CA", alliance: "Star Alliance" },
  { iata: "LH", icao: "DLH", name: "Lufthansa", country: "DE", alliance: "Star Alliance" },
  { iata: "AF", icao: "AFR", name: "Air France", country: "FR", alliance: "SkyTeam" },
  { iata: "KL", icao: "KLM", name: "KLM Royal Dutch Airlines", country: "NL", alliance: "SkyTeam" },
  { iata: "BA", icao: "BAW", name: "British Airways", country: "GB", alliance: "OneWorld" },
  { iata: "IB", icao: "IBE", name: "Iberia", country: "ES", alliance: "OneWorld" },
  { iata: "AZ", icao: "ITY", name: "ITA Airways", country: "IT", alliance: "SkyTeam" },
  { iata: "AY", icao: "FIN", name: "Finnair", country: "FI", alliance: "OneWorld" },
  { iata: "VS", icao: "VIR", name: "Virgin Atlantic", country: "GB", alliance: "SkyTeam" },
  { iata: "TK", icao: "THY", name: "Turkish Airlines", country: "TR", alliance: "Star Alliance" },
  { iata: "EK", icao: "UAE", name: "Emirates", country: "AE", alliance: "" },
  { iata: "QR", icao: "QTR", name: "Qatar Airways", country: "QA", alliance: "OneWorld" },
  { iata: "EY", icao: "ETD", name: "Etihad Airways", country: "AE", alliance: "" },
  { iata: "SQ", icao: "SIA", name: "Singapore Airlines", country: "SG", alliance: "Star Alliance" },
  { iata: "CX", icao: "CPA", name: "Cathay Pacific", country: "HK", alliance: "OneWorld" },
  { iata: "TG", icao: "THA", name: "Thai Airways International", country: "TH", alliance: "Star Alliance" },
  { iata: "NH", icao: "ANA", name: "All Nippon Airways", country: "JP", alliance: "Star Alliance" },
  { iata: "JL", icao: "JAL", name: "Japan Airlines", country: "JP", alliance: "OneWorld" },
  { iata: "KE", icao: "KAL", name: "Korean Air", country: "KR", alliance: "SkyTeam" },
  { iata: "OZ", icao: "AAR", name: "Asiana Airlines", country: "KR", alliance: "Star Alliance" },
  { iata: "QF", icao: "QFA", name: "Qantas", country: "AU", alliance: "OneWorld" },
  { iata: "CZ", icao: "CSN", name: "China Southern", country: "CN", alliance: "" },
  { iata: "MU", icao: "CES", name: "China Eastern", country: "CN", alliance: "SkyTeam" },
  { iata: "CA", icao: "CCA", name: "Air China", country: "CN", alliance: "Star Alliance" },
];

interface Source {
  sourceId: string;
  sourceType: "gds" | "gds_ndc" | "metasearch" | "direct_ndc" | "scrape" | "stub";
  adapterKey: string;
  baseUrl: string;
  authScheme: "oauth2_client_credentials" | "bearer" | "api_key" | "none";
  authEnvKey: string;
  cadenceMinutes: number;
  rateLimitRpm: number;
  airlinesCount: number;
  coverageNote: string;
  status: "active" | "stub" | "planned";
}

const SOURCES: Source[] = [
  {
    sourceId: "amadeus",
    sourceType: "gds",
    adapterKey: "amadeus",
    baseUrl: "https://test.api.amadeus.com",
    authScheme: "oauth2_client_credentials",
    authEnvKey: "AMADEUS_CLIENT_ID,AMADEUS_CLIENT_SECRET",
    cadenceMinutes: 360,
    rateLimitRpm: 10,
    airlinesCount: 440,
    coverageNote: "Amadeus Self-Service Flight Offers Search v2. Full GDS coverage.",
    status: "active",
  },
  {
    sourceId: "duffel",
    sourceType: "gds_ndc",
    adapterKey: "duffel",
    baseUrl: "https://api.duffel.com",
    authScheme: "bearer",
    authEnvKey: "DUFFEL_API_KEY",
    cadenceMinutes: 360,
    rateLimitRpm: 60,
    airlinesCount: 380,
    coverageNote: "Duffel air offer requests v2. NDC + GDS aggregator.",
    status: "active",
  },
  {
    sourceId: "kiwi-tequila",
    sourceType: "metasearch",
    adapterKey: "kiwi",
    baseUrl: "https://api.tequila.kiwi.com",
    authScheme: "api_key",
    authEnvKey: "KIWI_TEQUILA_API_KEY",
    cadenceMinutes: 360,
    rateLimitRpm: 30,
    airlinesCount: 750,
    coverageNote: "Kiwi.com Tequila Search API. Metasearch incl. virtual interlining.",
    status: "stub",
  },
  {
    sourceId: "travelpayouts-aviasales",
    sourceType: "metasearch",
    adapterKey: "travelpayouts",
    baseUrl: "https://api.travelpayouts.com",
    authScheme: "api_key",
    authEnvKey: "TRAVELPAYOUTS_TOKEN",
    cadenceMinutes: 720,
    rateLimitRpm: 60,
    airlinesCount: 700,
    coverageNote: "Travelpayouts (Aviasales) data API. Cheapest cached prices.",
    status: "stub",
  },
  {
    sourceId: "skyscanner-affiliate",
    sourceType: "metasearch",
    adapterKey: "skyscanner",
    baseUrl: "https://partners.api.skyscanner.net",
    authScheme: "api_key",
    authEnvKey: "SKYSCANNER_API_KEY",
    cadenceMinutes: 720,
    rateLimitRpm: 20,
    airlinesCount: 1200,
    coverageNote: "Skyscanner B2B Affiliate API. Highest carrier breadth; B2B only.",
    status: "planned",
  },
  {
    sourceId: "ana-ndc",
    sourceType: "direct_ndc",
    adapterKey: "anaNdc",
    baseUrl: "https://ndc.ana.co.jp",
    authScheme: "oauth2_client_credentials",
    authEnvKey: "ANA_NDC_CLIENT_ID,ANA_NDC_CLIENT_SECRET",
    cadenceMinutes: 240,
    rateLimitRpm: 30,
    airlinesCount: 1,
    coverageNote: "ANA Direct NDC. Marketing carrier NH only.",
    status: "planned",
  },
  {
    sourceId: "jal-ndc",
    sourceType: "direct_ndc",
    adapterKey: "jalNdc",
    baseUrl: "https://ndc.jal.co.jp",
    authScheme: "oauth2_client_credentials",
    authEnvKey: "JAL_NDC_CLIENT_ID,JAL_NDC_CLIENT_SECRET",
    cadenceMinutes: 240,
    rateLimitRpm: 30,
    airlinesCount: 1,
    coverageNote: "JAL Direct NDC. Marketing carrier JL only.",
    status: "planned",
  },
  {
    sourceId: "stub",
    sourceType: "stub",
    adapterKey: "stub",
    baseUrl: "",
    authScheme: "none",
    authEnvKey: "",
    cadenceMinutes: 60,
    rateLimitRpm: 600,
    airlinesCount: 3,
    coverageNote: "Deterministic fixture (NH/JL/SQ). Dev-only fallback.",
    status: "active",
  },
];

// Coverage edges: each broad source covers all 30 airlines unless single-carrier;
// stub covers NH/JL/SQ; ANA/JAL NDC cover only their own marketing carrier.
function buildCoverage(): Array<{ sourceId: string; iata: string; coverageClass: string }> {
  const out: Array<{ sourceId: string; iata: string; coverageClass: string }> = [];
  const broadSources = ["amadeus", "duffel", "kiwi-tequila", "travelpayouts-aviasales", "skyscanner-affiliate"];
  for (const src of broadSources) {
    for (const a of AIRLINES) {
      out.push({ sourceId: src, iata: a.iata, coverageClass: "primary" });
    }
  }
  out.push({ sourceId: "ana-ndc", iata: "NH", coverageClass: "exclusive" });
  out.push({ sourceId: "jal-ndc", iata: "JL", coverageClass: "exclusive" });
  for (const iata of ["NH", "JL", "SQ"]) {
    out.push({ sourceId: "stub", iata, coverageClass: "fixture" });
  }
  return out;
}

function airlineVid(iata: string): string {
  return `at://${ownerDid}/com.etzhayyim.apps.flightOffer.airline/${iata}`;
}
function sourceVid(sourceId: string): string {
  return `at://${ownerDid}/com.etzhayyim.apps.flightOffer.source/${sourceId}`;
}
function edgeId(sourceId: string, iata: string): string {
  return `${sourceVid(sourceId)}|covers|${airlineVid(iata)}`;
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const a of AIRLINES) {
    const vid = airlineVid(a.iata);
    await sql`
      INSERT INTO vertex_airline (
        vertex_id, iata_code, icao_code, name, country_code, alliance,
        accepts_ndc, ingest_status, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT ${vid}, ${a.iata}, ${a.icao}, ${a.name}, ${a.country}, ${a.alliance},
             'unknown', 'discovered', ${createdAt},
             1, ${ownerDid}, ${ownerDid}, ${actorTag}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_airline WHERE vertex_id = ${vid})
    `.execute(db);
  }

  for (const s of SOURCES) {
    const vid = sourceVid(s.sourceId);
    await sql`
      INSERT INTO vertex_flight_offer_source (
        vertex_id, source_id, source_type, adapter_key, base_url,
        auth_scheme, auth_env_key, cadence_minutes, rate_limit_rpm,
        airlines_count, coverage_note, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT ${vid}, ${s.sourceId}, ${s.sourceType}, ${s.adapterKey}, ${s.baseUrl},
             ${s.authScheme}, ${s.authEnvKey},
             CAST(${s.cadenceMinutes} AS bigint), CAST(${s.rateLimitRpm} AS bigint),
             CAST(${s.airlinesCount} AS bigint), ${s.coverageNote}, ${s.status}, ${createdAt},
             1, ${ownerDid}, ${ownerDid}, ${actorTag}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_flight_offer_source WHERE vertex_id = ${vid})
    `.execute(db);
  }

  for (const c of buildCoverage()) {
    const eid = edgeId(c.sourceId, c.iata);
    await sql`
      INSERT INTO edge_flight_offer_source_covers_airline (
        edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,
        observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT ${eid}, ${sourceVid(c.sourceId)}, ${airlineVid(c.iata)},
             ${c.sourceId}, ${c.iata}, ${c.coverageClass},
             '', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
      WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE edge_id = ${eid})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const c of buildCoverage()) {
    const eid = edgeId(c.sourceId, c.iata);
    await sql`DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = ${eid}`.execute(db);
  }
  for (const s of SOURCES) {
    await sql`DELETE FROM vertex_flight_offer_source WHERE vertex_id = ${sourceVid(s.sourceId)}`.execute(db);
  }
  for (const a of AIRLINES) {
    await sql`DELETE FROM vertex_airline WHERE vertex_id = ${airlineVid(a.iata)}`.execute(db);
  }
}
