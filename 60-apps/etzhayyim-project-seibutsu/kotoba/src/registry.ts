/**
 * seibutsu kotoba — taxon + traits + observation registries + coverage.
 * AT PDS records (no RW). Taxon self-ref parent FK; traits & observations FK→taxon.
 * Public biodiversity open-data only; image-identification AI compute stays etzhayyim.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  HABITS,
  OBSERVATION_COLLECTION,
  TAXON_COLLECTION,
  TAXON_RANKS,
  TRAITS_COLLECTION,
  isH3Cell,
  isUint,
  observationDidFor,
  observationRkey,
  taxonDidFor,
  taxonRkey,
  traitsDidFor,
  traitsRkey,
  type CoverageInput,
  type CoverageOutput,
  type DeriveTraitsInput,
  type DeriveTraitsOutput,
  type GetTaxonInput,
  type GetTaxonOutput,
  type IngestObservationInput,
  type IngestObservationOutput,
  type ListObservationsInput,
  type ListObservationsOutput,
  type ListTaxaInput,
  type ListTaxaOutput,
  type ListTraitsInput,
  type ListTraitsOutput,
  type ObservationRecord,
  type ObservationView,
  type RegisterTaxonInput,
  type RegisterTaxonOutput,
  type TaxonRecord,
  type TaxonView,
  type TraitsRecord,
  type TraitsView,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

async function exists(e: Etzhayyim, collection: string, rkey: string): Promise<boolean> {
  const resp = await e.read({ collection, rkey }).catch(() => ({ records: [] }));
  return Boolean(resp.records[0]?.value);
}

async function scanAll<T>(e: Etzhayyim, collection: string, maxScan: number, onRow: (v: T) => void): Promise<number> {
  let cursor: string | undefined;
  let scanned = 0;
  while (scanned < maxScan) {
    const page = await e.read<T>({ collection, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      if (scanned >= maxScan) break;
      onRow(r.value);
      scanned += 1;
    }
    if (scanned >= maxScan || !page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return scanned;
}

// ─── Taxon ──────────────────────────────────────────────────────────

export async function registerTaxon(e: Etzhayyim, input: RegisterTaxonInput): Promise<RegisterTaxonOutput> {
  if (!input.taxonId || !input.scientificName) return { status: "rejected", error: "missingRequiredFields" };
  if (!TAXON_RANKS.has(input.rank)) return { status: "rejected", error: "invalidRank" };
  if (input.parentTaxonId && !(await exists(e, TAXON_COLLECTION, taxonRkey(input.parentTaxonId)))) {
    return { status: "parentNotFound", error: `parentNotFound:${input.parentTaxonId}` };
  }
  const rkey = taxonRkey(input.taxonId);
  const existing = await e.read<TaxonRecord>({ collection: TAXON_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", taxonUri: existing.records[0].uri, did: existing.records[0].value.did, taxonId: input.taxonId };
  }
  const did = taxonDidFor(input.taxonId);
  const record: TaxonRecord = {
    did,
    taxonId: input.taxonId,
    rank: input.rank,
    scientificName: input.scientificName,
    commonName: input.commonName,
    parentTaxonId: input.parentTaxonId,
    gbifId: input.gbifId,
    ncbiId: input.ncbiId,
    wikidataId: input.wikidataId,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: TAXON_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", taxonUri: receipt.uri, did, taxonId: input.taxonId };
}

export async function getTaxon(e: Etzhayyim, input: GetTaxonInput): Promise<GetTaxonOutput> {
  if (!input.taxonId) return { error: "invalidTaxonId" };
  const resp = await e.read<TaxonRecord>({ collection: TAXON_COLLECTION, rkey: taxonRkey(input.taxonId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { taxon: { ...r.value, taxonUri: r.uri } };
}

export async function listTaxa(e: Etzhayyim, input: ListTaxaInput = {}): Promise<ListTaxaOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<TaxonRecord>({ collection: TAXON_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: TaxonView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.rank && v.rank !== input.rank) return false;
      if (input.parentTaxonId && v.parentTaxonId !== input.parentTaxonId) return false;
      if (q) {
        const hay = [v.scientificName, v.commonName ?? ""].join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    })
    .map((r) => ({ ...r.value, taxonUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Traits ─────────────────────────────────────────────────────────

export async function deriveTraits(e: Etzhayyim, input: DeriveTraitsInput): Promise<DeriveTraitsOutput> {
  if (!input.traitId || !input.taxonId) return { status: "rejected", error: "missingRequiredFields" };
  if (!HABITS.has(input.habit)) return { status: "rejected", error: "invalidHabit" };
  if (input.matureHeightCm != null && !isUint(input.matureHeightCm)) return { status: "rejected", error: "matureHeightCmMustBeUint" };
  if (input.lifespanYears != null && !isUint(input.lifespanYears)) return { status: "rejected", error: "lifespanYearsMustBeUint" };
  if (!(await exists(e, TAXON_COLLECTION, taxonRkey(input.taxonId)))) {
    return { status: "taxonNotFound", error: `taxonNotFound:${input.taxonId}` };
  }
  const rkey = traitsRkey(input.traitId);
  const existing = await e.read<TraitsRecord>({ collection: TRAITS_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", traitsUri: existing.records[0].uri, did: existing.records[0].value.did, traitId: input.traitId };
  }
  const did = traitsDidFor(input.traitId);
  const record: TraitsRecord = {
    did,
    traitId: input.traitId,
    taxonId: input.taxonId,
    habit: input.habit,
    matureHeightCm: input.matureHeightCm,
    lifespanYears: input.lifespanYears,
    hardinessZone: input.hardinessZone,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: TRAITS_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "derived", traitsUri: receipt.uri, did, traitId: input.traitId };
}

export async function listTraits(e: Etzhayyim, input: ListTraitsInput = {}): Promise<ListTraitsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<TraitsRecord>({ collection: TRAITS_COLLECTION, cursor: input.cursor, limit });
  const items: TraitsView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.taxonId && v.taxonId !== input.taxonId) return false;
      if (input.habit && v.habit !== input.habit) return false;
      return true;
    })
    .map((r) => ({ ...r.value, traitsUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Observation ────────────────────────────────────────────────────

export async function ingestObservation(e: Etzhayyim, input: IngestObservationInput): Promise<IngestObservationOutput> {
  if (!input.observationId || !input.taxonId || !input.observedAt) return { status: "rejected", error: "missingRequiredFields" };
  if (input.geoH3 && !isH3Cell(input.geoH3.toLowerCase())) return { status: "rejected", error: "invalidH3Cell" };
  if (!(await exists(e, TAXON_COLLECTION, taxonRkey(input.taxonId)))) {
    return { status: "taxonNotFound", error: `taxonNotFound:${input.taxonId}` };
  }
  const rkey = observationRkey(input.observationId);
  const existing = await e.read<ObservationRecord>({ collection: OBSERVATION_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", observationUri: existing.records[0].uri, did: existing.records[0].value.did, observationId: input.observationId };
  }
  const did = observationDidFor(input.observationId);
  const record: ObservationRecord = {
    did,
    observationId: input.observationId,
    taxonId: input.taxonId,
    observedAt: input.observedAt,
    geoH3: input.geoH3?.toLowerCase(),
    observerHandle: input.observerHandle,
    imageUrl: input.imageUrl,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: OBSERVATION_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "ingested", observationUri: receipt.uri, did, observationId: input.observationId };
}

export async function listObservations(e: Etzhayyim, input: ListObservationsInput = {}): Promise<ListObservationsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ObservationRecord>({ collection: OBSERVATION_COLLECTION, cursor: input.cursor, limit });
  const geoH3 = input.geoH3?.toLowerCase();
  const items: ObservationView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.taxonId && v.taxonId !== input.taxonId) return false;
      if (geoH3 && v.geoH3 !== geoH3) return false;
      if (input.observerHandle && v.observerHandle !== input.observerHandle) return false;
      return true;
    })
    .map((r) => ({ ...r.value, observationUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const taxaByRank: Record<string, number> = {};
  const taxonCount = await scanAll<TaxonRecord>(e, TAXON_COLLECTION, maxScan, (v) => {
    taxaByRank[v.rank] = (taxaByRank[v.rank] ?? 0) + 1;
  });
  const traitsCount = await scanAll<TraitsRecord>(e, TRAITS_COLLECTION, maxScan, () => {});
  const observationCount = await scanAll<ObservationRecord>(e, OBSERVATION_COLLECTION, maxScan, () => {});
  return {
    taxonCount,
    traitsCount,
    observationCount,
    taxaByRank,
    truncated: taxonCount >= maxScan || traitsCount >= maxScan || observationCount >= maxScan,
  };
}
