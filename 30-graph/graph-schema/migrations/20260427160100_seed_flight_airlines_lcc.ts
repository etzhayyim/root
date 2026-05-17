import type { Kysely } from "kysely";
import { sql } from "kysely";

const ownerDid = "did:web:flight-offer.etzhayyim.com";
const createdAt = "2026-04-27T16:01:00Z";
const actorTag = "sys.bpmn.seed.flight-offer";

interface Airline {
  iata: string;
  icao: string;
  name: string;
  country: string;
  alliance: string;
}

// Phase 7 expansion — adds 12 airlines focused on LCCs + MENA / SE-Asia
// hubs not yet seeded by phase 6. New rows extend the registry; the existing
// broad-source coverage edges (amadeus / duffel / kiwi-tequila /
// travelpayouts-aviasales / skyscanner-affiliate) are extended in this seed
// so multi-source fan-out picks them up immediately.
const AIRLINES: Airline[] = [
  { iata: "FR", icao: "RYR", name: "Ryanair", country: "IE", alliance: "" },
  { iata: "U2", icao: "EZY", name: "easyJet", country: "GB", alliance: "" },
  { iata: "W6", icao: "WZZ", name: "Wizz Air", country: "HU", alliance: "" },
  { iata: "AK", icao: "AXM", name: "AirAsia", country: "MY", alliance: "" },
  { iata: "JQ", icao: "JST", name: "Jetstar Airways", country: "AU", alliance: "" },
  { iata: "5J", icao: "CEB", name: "Cebu Pacific", country: "PH", alliance: "" },
  { iata: "QZ", icao: "AWQ", name: "Indonesia AirAsia", country: "ID", alliance: "" },
  { iata: "MH", icao: "MAS", name: "Malaysia Airlines", country: "MY", alliance: "OneWorld" },
  { iata: "GA", icao: "GIA", name: "Garuda Indonesia", country: "ID", alliance: "SkyTeam" },
  { iata: "SV", icao: "SVA", name: "Saudia", country: "SA", alliance: "SkyTeam" },
  { iata: "MS", icao: "MSR", name: "EgyptAir", country: "EG", alliance: "Star Alliance" },
  { iata: "LX", icao: "SWR", name: "Swiss International", country: "CH", alliance: "Star Alliance" },
];

const BROAD_SOURCES = ["amadeus", "duffel", "kiwi-tequila", "travelpayouts-aviasales", "skyscanner-affiliate"];

function airlineVid(iata: string): string {
  return `at://${ownerDid}/ai.gftd.apps.flightOffer.airline/${iata}`;
}
function sourceVid(sourceId: string): string {
  return `at://${ownerDid}/ai.gftd.apps.flightOffer.source/${sourceId}`;
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

  for (const a of AIRLINES) {
    for (const src of BROAD_SOURCES) {
      const eid = edgeId(src, a.iata);
      await sql`
        INSERT INTO edge_flight_offer_source_covers_airline (
          edge_id, src_vertex_id, dst_vertex_id, source_id, iata_code, coverage_class,
          observed_at, created_at, sensitivity_ord, org_id, user_id, actor_id
        )
        SELECT ${eid}, ${sourceVid(src)}, ${airlineVid(a.iata)},
               ${src}, ${a.iata}, 'primary',
               '', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
        WHERE NOT EXISTS (SELECT 1 FROM edge_flight_offer_source_covers_airline WHERE edge_id = ${eid})
      `.execute(db);
    }
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const a of AIRLINES) {
    for (const src of BROAD_SOURCES) {
      const eid = edgeId(src, a.iata);
      await sql`DELETE FROM edge_flight_offer_source_covers_airline WHERE edge_id = ${eid}`.execute(db);
    }
    await sql`DELETE FROM vertex_airline WHERE vertex_id = ${airlineVid(a.iata)}`.execute(db);
  }
}
