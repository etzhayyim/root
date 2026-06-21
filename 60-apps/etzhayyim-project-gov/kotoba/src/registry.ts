/**
 * gov kotoba — agency + official + municipality public-reference registries +
 * coverage. AT PDS records (no RW). Officials FK→agency; agency parent (optional)
 * FK→agency. Citizen consultations (PII) are NOT modelled here — they stay etzhayyim.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  AGENCY_COLLECTION,
  LEVELS,
  MUNICIPALITY_COLLECTION,
  OFFICIAL_COLLECTION,
  agencyDidFor,
  agencyRkey,
  isNonNegInt,
  municipalityDidFor,
  municipalityRkey,
  officialDidFor,
  officialRkey,
  type AgencyRecord,
  type AgencyView,
  type CoverageInput,
  type CoverageOutput,
  type GetAgencyInput,
  type GetAgencyOutput,
  type ListAgenciesInput,
  type ListAgenciesOutput,
  type ListMunicipalitiesInput,
  type ListMunicipalitiesOutput,
  type ListOfficialsInput,
  type ListOfficialsOutput,
  type MunicipalityRecord,
  type MunicipalityView,
  type OfficialRecord,
  type OfficialView,
  type RecordOfficialInput,
  type RecordOfficialOutput,
  type RegisterAgencyInput,
  type RegisterAgencyOutput,
  type RegisterMunicipalityInput,
  type RegisterMunicipalityOutput,
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

// ─── Agency ─────────────────────────────────────────────────────────

export async function registerAgency(e: Etzhayyim, input: RegisterAgencyInput): Promise<RegisterAgencyOutput> {
  if (!input.agencyId || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  if (!LEVELS.has(input.level)) return { status: "rejected", error: "invalidLevel" };
  if (input.parentAgencyId && !(await exists(e, AGENCY_COLLECTION, agencyRkey(input.parentAgencyId)))) {
    return { status: "parentNotFound", error: `parentNotFound:${input.parentAgencyId}` };
  }
  const rkey = agencyRkey(input.agencyId);
  const existing = await e.read<AgencyRecord>({ collection: AGENCY_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", agencyUri: existing.records[0].uri, did: existing.records[0].value.did, agencyId: input.agencyId };
  }
  const did = agencyDidFor(input.agencyId);
  const record: AgencyRecord = {
    did,
    agencyId: input.agencyId,
    name: input.name,
    level: input.level,
    cofogCode: input.cofogCode,
    parentAgencyId: input.parentAgencyId,
    region: input.region,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: AGENCY_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", agencyUri: receipt.uri, did, agencyId: input.agencyId };
}

export async function getAgency(e: Etzhayyim, input: GetAgencyInput): Promise<GetAgencyOutput> {
  if (!input.agencyId) return { error: "invalidAgencyId" };
  const resp = await e.read<AgencyRecord>({ collection: AGENCY_COLLECTION, rkey: agencyRkey(input.agencyId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { agency: { ...r.value, agencyUri: r.uri } };
}

export async function listAgencies(e: Etzhayyim, input: ListAgenciesInput = {}): Promise<ListAgenciesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<AgencyRecord>({ collection: AGENCY_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: AgencyView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.level && v.level !== input.level) return false;
      if (input.cofogCode && v.cofogCode !== input.cofogCode) return false;
      if (input.region && v.region !== input.region) return false;
      if (input.parentAgencyId && v.parentAgencyId !== input.parentAgencyId) return false;
      if (q && !v.name.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, agencyUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Official ───────────────────────────────────────────────────────

export async function recordOfficial(e: Etzhayyim, input: RecordOfficialInput): Promise<RecordOfficialOutput> {
  if (!input.officialId || !input.agencyId || !input.name || !input.title) return { status: "rejected", error: "missingRequiredFields" };
  if (!(await exists(e, AGENCY_COLLECTION, agencyRkey(input.agencyId)))) {
    return { status: "agencyNotFound", error: `agencyNotFound:${input.agencyId}` };
  }
  const rkey = officialRkey(input.officialId);
  const existing = await e.read<OfficialRecord>({ collection: OFFICIAL_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", officialUri: existing.records[0].uri, did: existing.records[0].value.did, officialId: input.officialId };
  }
  const did = officialDidFor(input.officialId);
  const record: OfficialRecord = {
    did,
    officialId: input.officialId,
    agencyId: input.agencyId,
    name: input.name,
    title: input.title,
    term: input.term,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: OFFICIAL_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", officialUri: receipt.uri, did, officialId: input.officialId };
}

export async function listOfficials(e: Etzhayyim, input: ListOfficialsInput = {}): Promise<ListOfficialsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<OfficialRecord>({ collection: OFFICIAL_COLLECTION, cursor: input.cursor, limit });
  const items: OfficialView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.agencyId && v.agencyId !== input.agencyId) return false;
      if (input.title && v.title !== input.title) return false;
      return true;
    })
    .map((r) => ({ ...r.value, officialUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Municipality ───────────────────────────────────────────────────

export async function registerMunicipality(e: Etzhayyim, input: RegisterMunicipalityInput): Promise<RegisterMunicipalityOutput> {
  if (!input.municipalityId || !input.name || !input.prefecture) return { status: "rejected", error: "missingRequiredFields" };
  if (input.jisCode && !/^\d{5}$/.test(input.jisCode)) return { status: "rejected", error: "invalidJisCode" };
  if (input.population != null && !isNonNegInt(input.population)) return { status: "rejected", error: "populationMustBeNonNegInt" };
  const rkey = municipalityRkey(input.municipalityId);
  const existing = await e.read<MunicipalityRecord>({ collection: MUNICIPALITY_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", municipalityUri: existing.records[0].uri, did: existing.records[0].value.did, municipalityId: input.municipalityId };
  }
  const did = municipalityDidFor(input.municipalityId);
  const record: MunicipalityRecord = {
    did,
    municipalityId: input.municipalityId,
    name: input.name,
    prefecture: input.prefecture,
    jisCode: input.jisCode,
    population: input.population,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: MUNICIPALITY_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", municipalityUri: receipt.uri, did, municipalityId: input.municipalityId };
}

export async function listMunicipalities(e: Etzhayyim, input: ListMunicipalitiesInput = {}): Promise<ListMunicipalitiesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<MunicipalityRecord>({ collection: MUNICIPALITY_COLLECTION, cursor: input.cursor, limit });
  const items: MunicipalityView[] = resp.records
    .filter((r) => (input.prefecture ? r.value.prefecture === input.prefecture : true))
    .map((r) => ({ ...r.value, municipalityUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const agenciesByLevel: Record<string, number> = {};
  const agencyCount = await scanAll<AgencyRecord>(e, AGENCY_COLLECTION, maxScan, (v) => {
    agenciesByLevel[v.level] = (agenciesByLevel[v.level] ?? 0) + 1;
  });
  const officialCount = await scanAll<OfficialRecord>(e, OFFICIAL_COLLECTION, maxScan, () => {});
  let totalPopulation = 0;
  const municipalityCount = await scanAll<MunicipalityRecord>(e, MUNICIPALITY_COLLECTION, maxScan, (v) => {
    if (typeof v.population === "number") totalPopulation += v.population;
  });
  return {
    agencyCount,
    officialCount,
    municipalityCount,
    agenciesByLevel,
    totalPopulation,
    truncated: agencyCount >= maxScan || officialCount >= maxScan || municipalityCount >= maxScan,
  };
}
