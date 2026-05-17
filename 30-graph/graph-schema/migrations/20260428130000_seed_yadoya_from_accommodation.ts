import type { Kysely } from "kysely";
import { sql } from "kysely";

// yadoya Phase 4 — backfill vertex_yadoya_hotel from vertex_accommodation
// (OSM ingest, 828K rows) and bridge into the hospitality cluster
// (ADR-0028) by minting did:web:hospitality.etzhayyim.com:actor:property:{osm-id}
// profile rows + edge_yadoya_property_to_chain links.
//
// Scope (V1, MVP): 10 JP pilot cities × type ∈ {hotel, hostel, guest_house}
// capped at 200 rows total. Full-world expansion is gated behind ADR-0028
// reverse-toposort R1→R2→R3→R4 and is intentionally out of scope here.
//
// Idempotency: every INSERT is guarded by NOT EXISTS on vertex_id, so the
// migration can be re-applied safely. RisingWave does NOT honor PK upsert
// semantics for these custom tables (CLAUDE.md note), so the explicit guard
// is load-bearing.
//
// Pre-flight (CLAUDE.md §MV Memory Safety Guardrails):
//   - Cap is hard-coded to 200 rows — trivial for streaming actor / coverage MV
//   - No MV is added by this migration; consumers re-use mv_yadoya_catalog_coverage (20260428120000)

const PILOT_CITIES = [
  "Tokyo", "Osaka", "Kyoto", "Fukuoka", "Sapporo",
  "Nagoya", "Yokohama", "Kobe", "Sendai", "Hiroshima",
];
const PILOT_TYPES = ["hotel", "hostel", "guest_house"];
const ROW_CAP = 200;
const CREATED_AT = "2026-04-28T13:00:00Z";
const OWNER_DID = "did:web:yadoya.etzhayyim.com";
const HOSPITALITY_DID = "did:web:hospitality.etzhayyim.com";
const ACTOR_TAG = "sys.seed.yadoya-from-accommodation";

export async function up(db: Kysely<unknown>): Promise<void> {
  const cityList = sql.join(PILOT_CITIES.map((c) => sql`${c}`));
  const typeList = sql.join(PILOT_TYPES.map((t) => sql`${t}`));

  await sql`
    INSERT INTO vertex_yadoya_hotel (
      vertex_id, sensitivity_ord, owner_did,
      hotel_slug, osm_id, chain_did, property_did,
      name, country, region, city, lat, lon,
      isic_code, price_jpy_min, price_jpy_max, capacity_rooms,
      lang_codes, source_url, status,
      created_at, org_id, user_id, actor_id
    )
    SELECT
      'at://' || ${OWNER_DID} || '/ai.gftd.apps.yadoya.hotel/' || a.osm_id,
      1, ${OWNER_DID},
      a.osm_id,
      a.osm_id,
      NULL,
      ${HOSPITALITY_DID} || ':actor:property:' || a.osm_id,
      COALESCE(a.name, 'unknown-' || a.osm_id),
      COALESCE(a.country, 'JP'),
      'asia',
      a.city,
      a.lat,
      a.lon,
      'I5510',
      CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
      a.rooms,
      'ja,en',
      a.source_url,
      'published',
      ${CREATED_AT}, 'anon', 'anon', ${ACTOR_TAG}
    FROM vertex_accommodation a
    WHERE a.city IN (${cityList})
      AND a.type IN (${typeList})
      AND a.osm_id IS NOT NULL
      AND a.name IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM vertex_yadoya_hotel y
        WHERE y.vertex_id = 'at://' || ${OWNER_DID} || '/ai.gftd.apps.yadoya.hotel/' || a.osm_id
      )
    LIMIT ${sql.raw(String(ROW_CAP))}
  `.execute(db);

  // Mint hospitality property profile rows for every newly-seeded hotel.
  // vertex_profile is a public projection of app.bsky.actor.profile records
  // (ADR-0019), so we keep these to cohort-aggregate "hospitality property"
  // shape — DID + display_name + description + handle.
  await sql`
    INSERT INTO vertex_profile (
      vertex_id, sensitivity_ord, owner_did,
      did, repo, handle, display_name, description,
      collection, rkey, created_at
    )
    SELECT
      'at://' || y.property_did || '/app.bsky.actor.profile/self',
      1, ${HOSPITALITY_DID},
      y.property_did,
      y.property_did,
      'property-' || y.osm_id || '.hospitality.etzhayyim.com',
      y.name,
      'Hospitality property (OSM ' || y.osm_id || ', ' || y.city || ', ' || y.country || ')',
      'app.bsky.actor.profile',
      'self',
      ${CREATED_AT}
    FROM vertex_yadoya_hotel y
    WHERE y.actor_id = ${ACTOR_TAG}
      AND y.property_did IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM vertex_profile p
        WHERE p.vertex_id = 'at://' || y.property_did || '/app.bsky.actor.profile/self'
      )
  `.execute(db);

  // edge yadoya hotel → hospitality property profile (role: property-of)
  await sql`
    INSERT INTO edge_yadoya_property_to_chain (
      edge_id, sensitivity_ord, owner_did,
      src_vid, dst_vid, role,
      created_at, org_id, user_id, actor_id
    )
    SELECT
      'edge:yadoya:' || y.osm_id || ':property',
      1, ${OWNER_DID},
      y.vertex_id,
      'at://' || y.property_did || '/app.bsky.actor.profile/self',
      'property-of',
      ${CREATED_AT}, 'anon', 'anon', ${ACTOR_TAG}
    FROM vertex_yadoya_hotel y
    WHERE y.actor_id = ${ACTOR_TAG}
      AND y.property_did IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM edge_yadoya_property_to_chain e
        WHERE e.edge_id = 'edge:yadoya:' || y.osm_id || ':property'
      )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM edge_yadoya_property_to_chain WHERE actor_id = ${ACTOR_TAG}`.execute(db);
  // vertex_profile rows minted here are identified by owner_did + handle prefix
  await sql`DELETE FROM vertex_profile WHERE owner_did = ${HOSPITALITY_DID} AND handle LIKE 'property-%.hospitality.etzhayyim.com'`.execute(db);
  await sql`DELETE FROM vertex_yadoya_hotel WHERE actor_id = ${ACTOR_TAG}`.execute(db);
}
