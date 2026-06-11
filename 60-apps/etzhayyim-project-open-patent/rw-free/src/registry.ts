/**
 * open-patent rw-free — patent + citation + inventionSeed + noveltyReport
 * registries + coverage. AT PDS records (no RW). Citations FK→patent; novelty
 * reports FK→inventionSeed. Public patent open-data + open IP generation.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  CITATION_COLLECTION,
  CITATION_TYPES,
  NOVELTY_COLLECTION,
  PATENT_COLLECTION,
  PATENT_STATUSES,
  SEED_COLLECTION,
  citationDidFor,
  citationRkey,
  isJurisdiction,
  isPermille,
  noveltyDidFor,
  noveltyRkey,
  patentDidFor,
  patentRkey,
  seedDidFor,
  seedRkey,
  type AddCitationInput,
  type AddCitationOutput,
  type AddNoveltyReportInput,
  type AddNoveltyReportOutput,
  type CitationRecord,
  type CitationView,
  type CoverageInput,
  type CoverageOutput,
  type GetPatentInput,
  type GetPatentOutput,
  type IngestPatentInput,
  type IngestPatentOutput,
  type ListCitationsInput,
  type ListCitationsOutput,
  type ListNoveltyReportsInput,
  type ListNoveltyReportsOutput,
  type ListPatentsInput,
  type ListPatentsOutput,
  type ListSeedsInput,
  type ListSeedsOutput,
  type NoveltyRecord,
  type NoveltyView,
  type PatentRecord,
  type PatentView,
  type PublishSeedInput,
  type PublishSeedOutput,
  type SeedRecord,
  type SeedView,
  type SynthesizeSeedInput,
  type SynthesizeSeedOutput,
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

// ─── Patent ─────────────────────────────────────────────────────────

export async function ingestPatent(e: Etzhayyim, input: IngestPatentInput): Promise<IngestPatentOutput> {
  if (!input.patentId || !input.publicationNumber || !input.title || !input.sourceUrl) return { status: "rejected", error: "missingRequiredFields" };
  const jurisdiction = input.jurisdiction?.toUpperCase();
  if (!isJurisdiction(jurisdiction ?? "")) return { status: "rejected", error: "invalidJurisdiction" };
  if (!PATENT_STATUSES.has(input.status)) return { status: "rejected", error: "invalidStatus" };
  const rkey = patentRkey(input.patentId);
  const existing = await e.read<PatentRecord>({ collection: PATENT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", patentUri: existing.records[0].uri, did: existing.records[0].value.did, patentId: input.patentId };
  }
  const did = patentDidFor(input.patentId);
  const record: PatentRecord = {
    did,
    patentId: input.patentId,
    publicationNumber: input.publicationNumber.toUpperCase(),
    title: input.title,
    jurisdiction: jurisdiction!,
    kindCode: input.kindCode,
    filedDate: input.filedDate,
    grantedDate: input.grantedDate,
    status: input.status,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: PATENT_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "ingested", patentUri: receipt.uri, did, patentId: input.patentId };
}

export async function getPatent(e: Etzhayyim, input: GetPatentInput): Promise<GetPatentOutput> {
  if (!input.patentId) return { error: "invalidPatentId" };
  const resp = await e.read<PatentRecord>({ collection: PATENT_COLLECTION, rkey: patentRkey(input.patentId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { patent: { ...r.value, patentUri: r.uri } };
}

export async function listPatents(e: Etzhayyim, input: ListPatentsInput = {}): Promise<ListPatentsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<PatentRecord>({ collection: PATENT_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const jurisdiction = input.jurisdiction?.toUpperCase();
  const items: PatentView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (jurisdiction && v.jurisdiction !== jurisdiction) return false;
      if (input.status && v.status !== input.status) return false;
      if (q && !v.title.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, patentUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Citation ───────────────────────────────────────────────────────

export async function addCitation(e: Etzhayyim, input: AddCitationInput): Promise<AddCitationOutput> {
  if (!input.citationId || !input.citingPatentId || !input.citedRef) return { status: "rejected", error: "missingRequiredFields" };
  if (!CITATION_TYPES.has(input.citationType)) return { status: "rejected", error: "invalidCitationType" };
  if (!(await exists(e, PATENT_COLLECTION, patentRkey(input.citingPatentId)))) {
    return { status: "patentNotFound", error: `patentNotFound:${input.citingPatentId}` };
  }
  const rkey = citationRkey(input.citationId);
  const existing = await e.read<CitationRecord>({ collection: CITATION_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", citationUri: existing.records[0].uri, did: existing.records[0].value.did, citationId: input.citationId };
  }
  const did = citationDidFor(input.citationId);
  const record: CitationRecord = {
    did,
    citationId: input.citationId,
    citingPatentId: input.citingPatentId,
    citedRef: input.citedRef.toUpperCase(),
    citationType: input.citationType,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: CITATION_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", citationUri: receipt.uri, did, citationId: input.citationId };
}

export async function listCitations(e: Etzhayyim, input: ListCitationsInput = {}): Promise<ListCitationsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<CitationRecord>({ collection: CITATION_COLLECTION, cursor: input.cursor, limit });
  const citedRef = input.citedRef?.toUpperCase();
  const items: CitationView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.citingPatentId && v.citingPatentId !== input.citingPatentId) return false;
      if (citedRef && v.citedRef !== citedRef) return false;
      if (input.citationType && v.citationType !== input.citationType) return false;
      return true;
    })
    .map((r) => ({ ...r.value, citationUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Invention seed ─────────────────────────────────────────────────

export async function synthesizeSeed(e: Etzhayyim, input: SynthesizeSeedInput): Promise<SynthesizeSeedOutput> {
  if (!input.seedId || !input.title || !input.description) return { status: "rejected", error: "missingRequiredFields" };
  const rkey = seedRkey(input.seedId);
  const existing = await e.read<SeedRecord>({ collection: SEED_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", seedUri: existing.records[0].uri, did: existing.records[0].value.did, seedId: input.seedId };
  }
  const did = seedDidFor(input.seedId);
  const record: SeedRecord = {
    did,
    seedId: input.seedId,
    title: input.title,
    description: input.description,
    basisRefs: (input.basisRefs ?? []).map((s) => s.toUpperCase()),
    status: "draft",
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: SEED_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "synthesized", seedUri: receipt.uri, did, seedId: input.seedId };
}

export async function publishSeed(e: Etzhayyim, input: PublishSeedInput): Promise<PublishSeedOutput> {
  if (!input.seedId) return { status: "rejected", error: "invalidSeedId" };
  const rkey = seedRkey(input.seedId);
  const resp = await e.read<SeedRecord>({ collection: SEED_COLLECTION, rkey }).catch(() => ({ records: [] }));
  const seed = resp.records[0]?.value;
  if (!seed) return { status: "notFound", error: "seedNotFound" };
  if (seed.status === "published") return { status: "rejected", error: "alreadyPublished" };
  await e.write({ collection: SEED_COLLECTION, record: { ...seed, status: "published" } as unknown as Record<string, unknown>, rkey });
  return { status: "published", seedId: input.seedId, newStatus: "published" };
}

export async function listSeeds(e: Etzhayyim, input: ListSeedsInput = {}): Promise<ListSeedsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<SeedRecord>({ collection: SEED_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: SeedView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.status && v.status !== input.status) return false;
      if (q && !v.title.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, seedUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Novelty report ─────────────────────────────────────────────────

export async function addNoveltyReport(e: Etzhayyim, input: AddNoveltyReportInput): Promise<AddNoveltyReportOutput> {
  if (!input.reportId || !input.seedId) return { status: "rejected", error: "missingRequiredFields" };
  if (!isPermille(input.noveltyPermille)) return { status: "rejected", error: "noveltyPermilleMustBe0to1000" };
  if (!(await exists(e, SEED_COLLECTION, seedRkey(input.seedId)))) {
    return { status: "seedNotFound", error: `seedNotFound:${input.seedId}` };
  }
  const rkey = noveltyRkey(input.reportId);
  const existing = await e.read<NoveltyRecord>({ collection: NOVELTY_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", reportUri: existing.records[0].uri, did: existing.records[0].value.did, reportId: input.reportId };
  }
  const did = noveltyDidFor(input.reportId);
  const record: NoveltyRecord = {
    did,
    reportId: input.reportId,
    seedId: input.seedId,
    noveltyPermille: input.noveltyPermille,
    priorArtRefs: (input.priorArtRefs ?? []).map((s) => s.toUpperCase()),
    summary: input.summary,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: NOVELTY_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", reportUri: receipt.uri, did, reportId: input.reportId };
}

export async function listNoveltyReports(e: Etzhayyim, input: ListNoveltyReportsInput = {}): Promise<ListNoveltyReportsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<NoveltyRecord>({ collection: NOVELTY_COLLECTION, cursor: input.cursor, limit });
  const items: NoveltyView[] = resp.records
    .filter((r) => (input.seedId ? r.value.seedId === input.seedId : true))
    .map((r) => ({ ...r.value, reportUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const patentsByJurisdiction: Record<string, number> = {};
  const patentCount = await scanAll<PatentRecord>(e, PATENT_COLLECTION, maxScan, (v) => {
    patentsByJurisdiction[v.jurisdiction] = (patentsByJurisdiction[v.jurisdiction] ?? 0) + 1;
  });
  const citationCount = await scanAll<CitationRecord>(e, CITATION_COLLECTION, maxScan, () => {});
  const seedsByStatus: Record<string, number> = {};
  const seedCount = await scanAll<SeedRecord>(e, SEED_COLLECTION, maxScan, (v) => {
    seedsByStatus[v.status] = (seedsByStatus[v.status] ?? 0) + 1;
  });
  const noveltyCount = await scanAll<NoveltyRecord>(e, NOVELTY_COLLECTION, maxScan, () => {});
  return {
    patentCount,
    citationCount,
    seedCount,
    noveltyCount,
    patentsByJurisdiction,
    seedsByStatus,
    truncated: patentCount >= maxScan || citationCount >= maxScan || seedCount >= maxScan || noveltyCount >= maxScan,
  };
}
