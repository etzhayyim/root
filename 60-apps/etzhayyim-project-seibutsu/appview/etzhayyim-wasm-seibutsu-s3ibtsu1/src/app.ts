import {
  asAgentTool,
  createWorkerExport,
  createKyselyDb,
  nowISO,
  str,
  withCapabilityTags,
  withOCELEvent,
  type ComAtprotoSyncSubscribeReposCommit,
  type HostSDK,
  genID,
  nsid,
  parseLexiconInput,
} from "@etzhayyim/kotodama-host-sdk";

const APP_SLUG = "seibutsu";
let actorDID = "";
const SEIBUTSU_TAXON_TABLE = "vertex_seibutsu_taxon";
const SEIBUTSU_TRAITS_TABLE = "vertex_seibutsu_traits";

type JsonRow = Record<string, unknown>;

const db = () => createKyselyDb();

function toSnakeCase(s: string): string {
  return s.replace(/[A-Z]/g, (m) => `_${m.toLowerCase()}`);
}

function pickField(row: JsonRow, field: string): unknown {
  if (row[field] !== undefined) return row[field];
  const snake = toSnakeCase(field);
  if (row[snake] !== undefined) return row[snake];
  return undefined;
}

function assignIfPresent(out: JsonRow, key: string, value: unknown): void {
  if (value !== undefined) out[key] = value;
}

function normalizeTaxonRow(row: JsonRow): JsonRow {
  const out: JsonRow = {};
  assignIfPresent(out, "did", pickField(row, "taxonDid") ?? pickField(row, "did") ?? pickField(row, "taxonId"));
  assignIfPresent(out, "rank", pickField(row, "rank"));
  assignIfPresent(out, "scientificName", pickField(row, "scientificName"));
  assignIfPresent(out, "authority", pickField(row, "authority"));
  assignIfPresent(out, "commonName", pickField(row, "commonName"));
  assignIfPresent(out, "parentDid", pickField(row, "parentDid") ?? pickField(row, "parentTaxonId"));
  assignIfPresent(out, "gbifId", pickField(row, "gbifId"));
  assignIfPresent(out, "ncbiTaxonId", pickField(row, "ncbiTaxonId"));
  assignIfPresent(out, "wikidataQid", pickField(row, "wikidataQid"));
  assignIfPresent(out, "createdAt", pickField(row, "createdAt"));
  assignIfPresent(out, "orgId", pickField(row, "orgId"));
  assignIfPresent(out, "userId", pickField(row, "userId"));
  assignIfPresent(out, "actorId", pickField(row, "actorId"));
  return out;
}

function normalizeTraitsRow(row: JsonRow): JsonRow {
  const out: JsonRow = {};
  assignIfPresent(out, "taxonDid", pickField(row, "taxonDid") ?? pickField(row, "taxonId"));
  assignIfPresent(out, "division", pickField(row, "division"));
  assignIfPresent(out, "habit", pickField(row, "habit"));
  assignIfPresent(out, "arrangement", pickField(row, "arrangement"));
  assignIfPresent(out, "leafShape", pickField(row, "leafShape"));
  assignIfPresent(out, "canopy", pickField(row, "canopy"));
  assignIfPresent(out, "heightRange", pickField(row, "heightRange"));
  assignIfPresent(out, "stemRadiusBase", pickField(row, "stemRadiusBase"));
  assignIfPresent(out, "stemRadiusTop", pickField(row, "stemRadiusTop"));
  assignIfPresent(out, "leafCount", pickField(row, "leafCount"));
  assignIfPresent(out, "leafSize", pickField(row, "leafSize"));
  assignIfPresent(out, "colorBase", pickField(row, "colorBase"));
  assignIfPresent(out, "colorTip", pickField(row, "colorTip"));
  assignIfPresent(out, "createdAt", pickField(row, "createdAt"));
  assignIfPresent(out, "orgId", pickField(row, "orgId"));
  assignIfPresent(out, "userId", pickField(row, "userId"));
  assignIfPresent(out, "actorId", pickField(row, "actorId"));
  return out;
}

async function selectFirstByColumn(table: string, column: string, value: string): Promise<JsonRow | null> {
  try {
    const row = await db()
      .selectFrom(table as any)
      .selectAll()
      .where(column as any, "=", value)
      .limit(1)
      .executeTakeFirst();
    return (row as JsonRow | undefined) ?? null;
  } catch {
    return null;
  }
}

// ── Read helpers (Tier 2 domain reads via kagami) ──

async function getTaxonByDid(did: string): Promise<JsonRow | null> {
  const row = await selectFirstByColumn(SEIBUTSU_TAXON_TABLE, "taxon_did", did)
    ?? await selectFirstByColumn(SEIBUTSU_TAXON_TABLE, "taxon_id", did)
    ?? await selectFirstByColumn(SEIBUTSU_TAXON_TABLE, "did", did);
  return row ? normalizeTaxonRow(row) : null;
}

async function getTraitsByTaxonDid(taxonDid: string): Promise<JsonRow | null> {
  const row = await selectFirstByColumn(SEIBUTSU_TRAITS_TABLE, "taxon_did", taxonDid)
    ?? await selectFirstByColumn(SEIBUTSU_TRAITS_TABLE, "taxonDid", taxonDid);
  return row ? normalizeTraitsRow(row) : null;
}

async function resolveLineage(did: string, max = 16): Promise<JsonRow[]> {
  const chain: JsonRow[] = [];
  let cur: string | undefined = did;
  for (let i = 0; i < max && cur; i++) {
    const t = await getTaxonByDid(cur);
    if (!t) break;
    chain.unshift(t);
    cur = typeof t.parentDid === "string" ? t.parentDid : undefined;
  }
  return chain;
}

// ── Commands ──

async function cmdGetProfile(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.seibutsu.getProfile", body);
  const did = str(args.did ?? "");
  if (!did) return { error: "did required" };
  const taxon = await getTaxonByDid(did);
  if (!taxon) return { error: "not found" };
  const traits = await getTraitsByTaxonDid(did);
  const lineage = await resolveLineage(did);
  return { taxon, traits, lineage };
}

async function cmdRenderProfile(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.seibutsu.renderProfile", body);
  const did = str(args.did ?? "");
  if (!did) return { error: "did required" };
  const taxon = await getTaxonByDid(did);
  const traits = await getTraitsByTaxonDid(did);
  if (!taxon || !traits) return { error: "not found" };
  return {
    commonName: taxon.commonName ?? taxon.scientificName,
    division: traits.division,
    habit: traits.habit,
    arrangement: traits.arrangement ?? "none",
    leafShape: traits.leafShape,
    canopy: traits.canopy,
    heightRange: traits.heightRange,
    stemRadiusBase: traits.stemRadiusBase ?? 0,
    stemRadiusTop: traits.stemRadiusTop ?? 0,
    leafCount: traits.leafCount ?? 0,
    leafSize: traits.leafSize ?? 0,
    colorBase: traits.colorBase,
    colorTip: traits.colorTip,
  };
}

async function cmdRegisterTaxon(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.seibutsu.taxon", body);
  const did = str(args.did ?? "");
  const rank = str(args.rank ?? "");
  const scientificName = str(args.scientificName ?? "");
  if (!did || !rank || !scientificName) return { error: "did, rank, scientificName required" };
  const rkey = str(args.did ?? "") || genID("taxon");
  await db().insertInto("vertex_seibutsu_taxon" as any).values({
    vertex_id: `at://${actorDID || "did:web:seibutsu.etzhayyim.com"}/com.etzhayyim.apps.seibutsu.taxon/${rkey}`,
    sensitivity_ord: 2,
    owner_did: actorDID || "did:web:seibutsu.etzhayyim.com",
    did,
    rank,
    scientific_name: scientificName,
    created_at: nowISO(),
    actor_id: APP_SLUG,
  }).execute();
  return { did, status: "registered" };
}

async function cmdDeriveTraits(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.seibutsu.traits", body);
  const taxonDid = str(args.taxonDid ?? "");
  if (!taxonDid) return { error: "taxonDid required" };
  const rkey = taxonDid.replace(/[^a-z0-9-]/gi, "-");
  await db().insertInto("vertex_seibutsu_traits" as any).values({
    vertex_id: `at://${actorDID || "did:web:seibutsu.etzhayyim.com"}/com.etzhayyim.apps.seibutsu.traits/${rkey}`,
    sensitivity_ord: 2,
    owner_did: actorDID || "did:web:seibutsu.etzhayyim.com",
    taxon_did: taxonDid,
    created_at: nowISO(),
    actor_id: APP_SLUG,
  }).execute();
  return { taxonDid, status: "stored" };
}

async function cmdIngestObservation(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.seibutsu.observation", body);
  const taxonDid = str(args.taxonDid ?? "");
  const observerDid = str(args.observerDid ?? "");
  if (!taxonDid || !observerDid) return { error: "taxonDid, observerDid required" };
  const id = genID("obs");
  await db().insertInto("vertex_seibutsu_observation" as any).values({
    vertex_id: `at://${actorDID || "did:web:seibutsu.etzhayyim.com"}/com.etzhayyim.apps.seibutsu.observation/${id}`,
    sensitivity_ord: 2,
    owner_did: actorDID || "did:web:seibutsu.etzhayyim.com",
    id,
    taxon_did: taxonDid,
    observer_did: observerDid,
    observed_at: str(args.observedAt ?? nowISO()),
    created_at: nowISO(),
    actor_id: APP_SLUG,
  }).execute();
  return { id, status: "ingested" };
}

// ── Reactive pipeline (Layer 1) ──

function handleComAtprotoSyncSubscribeReposCommit(
  _sdk: HostSDK,
  commit: ComAtprotoSyncSubscribeReposCommit,
): { ok: true; detail: string } {
  if (commit.action !== "create") return { ok: true, detail: "skip non-create" };
  const collection = str(commit.collection ?? "");
  switch (collection) {
    case "com.etzhayyim.apps.seibutsu.taxon":
      return { ok: true, detail: "taxon registered (derive: optional researcher-bio-gene lookup)" };
    case "com.etzhayyim.apps.seibutsu.traits":
      return { ok: true, detail: "traits stored (derive: stream-taxa cache invalidate)" };
    case "com.etzhayyim.apps.seibutsu.observation":
      return { ok: true, detail: "observation ingested (derive: app.bsky.feed.post sighting)" };
    default:
      return { ok: true, detail: "commit accepted" };
  }
}

export { handleComAtprotoSyncSubscribeReposCommit };

export default createWorkerExport((sdk) => {
  actorDID = sdk.pds.selfRepo ?? "";
  sdk.app
    .command(nsid("com.etzhayyim.apps.seibutsu.getProfile"), (_, b) => cmdGetProfile(sdk, b),
      asAgentTool("Resolve a taxon DID to taxon record + traits + parent lineage"),
      withCapabilityTags("query", "bio", "taxonomy"),
    )
    .command(nsid("com.etzhayyim.apps.seibutsu.renderProfile"), (_, b) => cmdRenderProfile(sdk, b),
      asAgentTool("Resolve a taxon DID to a kami-vegetation TaxonomicProfile JSON for engine ingestion"),
      withCapabilityTags("query", "bio", "engine"),
    )
    .command(nsid("com.etzhayyim.apps.seibutsu.taxon"), (_, b) => cmdRegisterTaxon(sdk, b),
      asAgentTool("Register a biological taxon as an actor record (rank, scientific name, parent DID, GBIF/NCBI/Wikidata refs)"),
      withCapabilityTags("write", "bio", "taxonomy"),
      withOCELEvent("seibutsu.taxon.register"),
    )
    .command(nsid("com.etzhayyim.apps.seibutsu.traits"), (_, b) => cmdDeriveTraits(sdk, b),
      asAgentTool("Store procedural-generation traits for a taxon (kami-vegetation TaxonomicProfile mirror)"),
      withCapabilityTags("write", "bio", "engine"),
    )
    .command(nsid("com.etzhayyim.apps.seibutsu.observation"), (_, b) => cmdIngestObservation(sdk, b),
      asAgentTool("Ingest an individual organism observation (geo-h3, observer DID, image)"),
      withCapabilityTags("write", "bio", "observation"),
      withOCELEvent("seibutsu.observation.ingest"),
    );
  sdk.app.onCommit((commit) => handleComAtprotoSyncSubscribeReposCommit(sdk, commit));
});
