import type { Kysely } from "kysely";
import { sql } from "kysely";

// Phase 10'' — mint app.bsky.actor.profile rows for the chain DIDs
// referenced by mv_yadoya_chain_coverage. This closes the loop on the
// sankey: the chain side of every (yadoya → chain) edge is now
// discoverable in vertex_profile, so resource-flow.etzhayyim.com can render
// readable counterparty labels instead of raw DIDs.
//
// We resolve display_name + description from the canonical roster
// (ADR-0028, hospitality CLAUDE.md §Chain) rather than reading the
// upstream emitter's profile (which the Worker has not yet published).
//
// Idempotent: NOT EXISTS guard on vertex_id. Forward-only — if a chain
// later publishes its own app.bsky.actor.profile, that row supersedes
// this seed by being a different vertex_id (per-actor rkey).

type ChainSeed = { slug: string; displayName: string; description: string };

const HOSPITALITY = "did:web:hospitality.etzhayyim.com";
const CREATED_AT = "2026-04-28T17:00:00Z";
const ACTOR_TAG = "sys.seed.hospitality-chain-profile";

const CHAINS: ChainSeed[] = [
  { slug: "marriott",   displayName: "Marriott International",       description: "Global hotel chain (ISIC I5510). Brands: Marriott, Sheraton, Westin, Ritz-Carlton, JW Marriott." },
  { slug: "hilton",     displayName: "Hilton Worldwide",             description: "Global hotel chain (ISIC I5510). Brands: Hilton, Conrad, Waldorf Astoria, DoubleTree, Hampton." },
  { slug: "hyatt",      displayName: "Hyatt Hotels Corporation",     description: "Global hotel chain (ISIC I5510). Brands: Park Hyatt, Grand Hyatt, Hyatt Regency, Andaz." },
  { slug: "ihg",        displayName: "InterContinental Hotels Group", description: "Global hotel chain (ISIC I5510). Brands: InterContinental, Holiday Inn, Crowne Plaza, Kimpton." },
  { slug: "accor",      displayName: "Accor",                        description: "Global hotel chain (ISIC I5510). Brands: Sofitel, Mercure, Novotel, ibis, Raffles." },
  { slug: "wyndham",    displayName: "Wyndham Hotels & Resorts",     description: "Global hotel chain (ISIC I5510)." },
  { slug: "choice",     displayName: "Choice Hotels International",  description: "Global hotel chain (ISIC I5510). Brands: Comfort Inn, Quality Inn." },
  { slug: "hoshino",    displayName: "星野リゾート (Hoshino Resorts)", description: "Japanese hotel chain (ISIC I5510). Brands: 星のや, リゾナーレ, OMO, BEB." },
  { slug: "prince",     displayName: "プリンスホテル (Prince Hotels)", description: "Japanese hotel chain (ISIC I5510)." },
  { slug: "tokyu-stay", displayName: "東急ステイ (Tokyu Stay)",       description: "Japanese hotel chain (ISIC I5510)." },
  { slug: "apa",        displayName: "アパホテル (APA Hotel)",         description: "Japanese hotel chain (ISIC I5510)." },
  { slug: "route-inn",  displayName: "ルートイン (Route Inn)",         description: "Japanese hotel chain (ISIC I5510)." },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const c of CHAINS) {
    const did = `${HOSPITALITY}:actor:chain:${c.slug}`;
    const vid = `at://${did}/app.bsky.actor.profile/self`;
    const handle = `chain-${c.slug}.hospitality.etzhayyim.com`;
    await sql`
      INSERT INTO vertex_profile (
        vertex_id, sensitivity_ord, owner_did,
        did, repo, handle, display_name, description,
        collection, rkey, created_at
      )
      SELECT
        ${vid}, 1, ${HOSPITALITY},
        ${did}, ${did}, ${handle}, ${c.displayName}, ${c.description},
        'app.bsky.actor.profile', 'self', ${CREATED_AT}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_profile WHERE vertex_id = ${vid}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_profile
    WHERE owner_did = ${HOSPITALITY}
      AND handle LIKE 'chain-%.hospitality.etzhayyim.com'
      AND created_at = ${CREATED_AT}
  `.execute(db);
}
