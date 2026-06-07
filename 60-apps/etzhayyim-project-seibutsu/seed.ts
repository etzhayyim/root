/**
 * Seed catalog: register 7 preset taxa + traits derived from
 * `40-engine/kami-engine/kami-vegetation/src/taxonomy.rs`.
 *
 * Run:
 *   npx tsx 60-apps/etzhayyim-project-seibutsu/seed.ts
 *
 * Idempotent: createRecord with the same TID is rejected; this seed uses
 * GBIF-derived stable rkeys to deduplicate.
 */

import seed from "./seed/preset-taxa.json" with { type: "json" };

const PDS = process.env.PDS ?? "https://atproto.etzhayyim.com";
const ROOT_DID = process.env.ROOT_DID ?? "did:plc:y3nnbwowvrtamshornglr7fa";
const PROJECT_ID = "seibutsu";

// ADR-0023 P4: use etzhayyim_TOKEN (sk_live_*) Bearer instead of spoofable
// x-kotodama-verified header. Required: `export etzhayyim_TOKEN=$(etzhayyim auth token)`
// before running this script.
const etzhayyim_TOKEN = process.env.etzhayyim_TOKEN;
if (!etzhayyim_TOKEN) {
  throw new Error("etzhayyim_TOKEN env var required — run `export etzhayyim_TOKEN=$(etzhayyim auth token)` first");
}
const HEADERS = {
  "Content-Type": "application/json",
  "Authorization": `Bearer ${etzhayyim_TOKEN}`,
  "x-etzhayyim-org-id": "anon",
};

async function actorCreate(did: string, displayName: string, description: string): Promise<void> {
  const res = await fetch(`${PDS}/xrpc/com.etzhayyim.actor.create`, {
    method: "POST",
    headers: HEADERS,
    body: JSON.stringify({ did, projectId: PROJECT_ID, displayName, description, hasWorker: false }),
  });
  if (!res.ok) console.warn(`✗ actor.create ${did}: ${res.status} ${await res.text()}`);
  else console.log(`✓ actor: ${did}`);
}

async function createRecord(repo: string, collection: string, rkey: string, record: Record<string, unknown>): Promise<void> {
  const res = await fetch(`${PDS}/xrpc/com.atproto.repo.createRecord`, {
    method: "POST",
    headers: HEADERS,
    body: JSON.stringify({ repo, collection, rkey, record }),
  });
  if (!res.ok) console.warn(`✗ ${collection}/${rkey}: ${res.status} ${await res.text()}`);
  else console.log(`✓ ${collection}/${rkey}`);
}

interface SeedTaxon {
  taxon: { did: string; rank: string; scientificName: string; commonName?: string; parentDid?: string; authority?: string; gbifId?: string };
  traits: Record<string, unknown>;
}

async function main(): Promise<void> {
  const entries = (seed as { taxa: SeedTaxon[] }).taxa;
  console.log(`Seeding ${entries.length} taxa to ${PDS} (root: ${ROOT_DID})`);

  // 1) parent kingdom/division actors (for hasParent edges)
  const divisions = new Set<string>();
  for (const e of entries) if (e.taxon.parentDid) divisions.add(e.taxon.parentDid);
  for (const did of divisions) {
    const slug = did.split(":").pop() ?? did;
    await actorCreate(did, slug, `Higher rank taxon for seibutsu seed (${slug})`);
  }

  // 2) per-taxon actor + records
  for (const e of entries) {
    const { taxon, traits } = e;
    const slug = taxon.did.split(":").pop() ?? taxon.scientificName.toLowerCase();
    const rkey = slug;

    await actorCreate(taxon.did, taxon.scientificName, `${taxon.rank}: ${taxon.scientificName} (${taxon.commonName ?? "—"})`);

    await createRecord(ROOT_DID, "com.etzhayyim.apps.seibutsu.taxon", rkey, {
      ...taxon,
      createdAt: new Date().toISOString(),
      orgId: "anon", userId: "anon", actorId: PROJECT_ID,
    });

    await createRecord(ROOT_DID, "com.etzhayyim.apps.seibutsu.traits", rkey, {
      taxonDid: taxon.did,
      ...traits,
      createdAt: new Date().toISOString(),
      orgId: "anon", userId: "anon", actorId: PROJECT_ID,
    });
  }

  console.log(`\nDone. ${entries.length} taxa registered.`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
