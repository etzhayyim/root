/**
 * saiban rw-free — court + judge + jurisdiction-map public-reference registries
 * + coverage. AT PDS records (no RW). Judges / jurisdiction-maps FK→court; court
 * parent (optional) FK→court. Public judicial reference only — jiken/trialEvent
 * (party PII) stay etzhayyim.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  COURT_COLLECTION,
  JMAP_COLLECTION,
  JUDGE_COLLECTION,
  LEVELS,
  MATTER_TYPES,
  TITLES,
  courtDidFor,
  courtRkey,
  isJurisdiction,
  jmapDidFor,
  jmapRkey,
  judgeDidFor,
  judgeRkey,
  type AddJudgeInput,
  type AddJudgeOutput,
  type CourtRecord,
  type CourtView,
  type CoverageInput,
  type CoverageOutput,
  type GetCourtInput,
  type GetCourtOutput,
  type JudgeRecord,
  type JudgeView,
  type JurisdictionMapRecord,
  type JurisdictionMapView,
  type ListCourtsInput,
  type ListCourtsOutput,
  type ListJudgesInput,
  type ListJudgesOutput,
  type ListJurisdictionMapsInput,
  type ListJurisdictionMapsOutput,
  type MapJurisdictionInput,
  type MapJurisdictionOutput,
  type RegisterCourtInput,
  type RegisterCourtOutput,
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

// ─── Court ──────────────────────────────────────────────────────────

export async function registerCourt(e: Etzhayyim, input: RegisterCourtInput): Promise<RegisterCourtOutput> {
  if (!input.courtId || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  const jurisdiction = input.jurisdiction?.toUpperCase();
  if (!isJurisdiction(jurisdiction ?? "")) return { status: "rejected", error: "invalidJurisdiction" };
  if (!LEVELS.has(input.level)) return { status: "rejected", error: "invalidLevel" };
  if (input.parentCourtId && !(await exists(e, COURT_COLLECTION, courtRkey(input.parentCourtId)))) {
    return { status: "parentNotFound", error: `parentNotFound:${input.parentCourtId}` };
  }
  const rkey = courtRkey(input.courtId);
  const existing = await e.read<CourtRecord>({ collection: COURT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", courtUri: existing.records[0].uri, did: existing.records[0].value.did, courtId: input.courtId };
  }
  const did = courtDidFor(input.courtId);
  const record: CourtRecord = {
    did,
    courtId: input.courtId,
    name: input.name,
    jurisdiction: jurisdiction!,
    level: input.level,
    parentCourtId: input.parentCourtId,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: COURT_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", courtUri: receipt.uri, did, courtId: input.courtId };
}

export async function getCourt(e: Etzhayyim, input: GetCourtInput): Promise<GetCourtOutput> {
  if (!input.courtId) return { error: "invalidCourtId" };
  const resp = await e.read<CourtRecord>({ collection: COURT_COLLECTION, rkey: courtRkey(input.courtId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { court: { ...r.value, courtUri: r.uri } };
}

export async function listCourts(e: Etzhayyim, input: ListCourtsInput = {}): Promise<ListCourtsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<CourtRecord>({ collection: COURT_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const jurisdiction = input.jurisdiction?.toUpperCase();
  const items: CourtView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (jurisdiction && v.jurisdiction !== jurisdiction) return false;
      if (input.level && v.level !== input.level) return false;
      if (input.parentCourtId && v.parentCourtId !== input.parentCourtId) return false;
      if (q && !v.name.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, courtUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Judge ──────────────────────────────────────────────────────────

export async function addJudge(e: Etzhayyim, input: AddJudgeInput): Promise<AddJudgeOutput> {
  if (!input.judgeId || !input.courtId || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  if (!TITLES.has(input.title)) return { status: "rejected", error: "invalidTitle" };
  if (!(await exists(e, COURT_COLLECTION, courtRkey(input.courtId)))) {
    return { status: "courtNotFound", error: `courtNotFound:${input.courtId}` };
  }
  const rkey = judgeRkey(input.judgeId);
  const existing = await e.read<JudgeRecord>({ collection: JUDGE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", judgeUri: existing.records[0].uri, did: existing.records[0].value.did, judgeId: input.judgeId };
  }
  const did = judgeDidFor(input.judgeId);
  const record: JudgeRecord = {
    did,
    judgeId: input.judgeId,
    courtId: input.courtId,
    name: input.name,
    title: input.title,
    appointedDate: input.appointedDate,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: JUDGE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", judgeUri: receipt.uri, did, judgeId: input.judgeId };
}

export async function listJudges(e: Etzhayyim, input: ListJudgesInput = {}): Promise<ListJudgesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<JudgeRecord>({ collection: JUDGE_COLLECTION, cursor: input.cursor, limit });
  const items: JudgeView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.courtId && v.courtId !== input.courtId) return false;
      if (input.title && v.title !== input.title) return false;
      return true;
    })
    .map((r) => ({ ...r.value, judgeUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Jurisdiction map ───────────────────────────────────────────────

export async function mapJurisdiction(e: Etzhayyim, input: MapJurisdictionInput): Promise<MapJurisdictionOutput> {
  if (!input.mappingId || !input.courtId || !input.scope) return { status: "rejected", error: "missingRequiredFields" };
  if (!MATTER_TYPES.has(input.matterType)) return { status: "rejected", error: "invalidMatterType" };
  if (!(await exists(e, COURT_COLLECTION, courtRkey(input.courtId)))) {
    return { status: "courtNotFound", error: `courtNotFound:${input.courtId}` };
  }
  const rkey = jmapRkey(input.mappingId);
  const existing = await e.read<JurisdictionMapRecord>({ collection: JMAP_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", mappingUri: existing.records[0].uri, did: existing.records[0].value.did, mappingId: input.mappingId };
  }
  const did = jmapDidFor(input.mappingId);
  const record: JurisdictionMapRecord = {
    did,
    mappingId: input.mappingId,
    courtId: input.courtId,
    scope: input.scope,
    matterType: input.matterType,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: JMAP_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "mapped", mappingUri: receipt.uri, did, mappingId: input.mappingId };
}

export async function listJurisdictionMaps(e: Etzhayyim, input: ListJurisdictionMapsInput = {}): Promise<ListJurisdictionMapsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<JurisdictionMapRecord>({ collection: JMAP_COLLECTION, cursor: input.cursor, limit });
  const items: JurisdictionMapView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.courtId && v.courtId !== input.courtId) return false;
      if (input.matterType && v.matterType !== input.matterType) return false;
      return true;
    })
    .map((r) => ({ ...r.value, mappingUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const courtsByJurisdiction: Record<string, number> = {};
  const courtsByLevel: Record<string, number> = {};
  const courtCount = await scanAll<CourtRecord>(e, COURT_COLLECTION, maxScan, (v) => {
    courtsByJurisdiction[v.jurisdiction] = (courtsByJurisdiction[v.jurisdiction] ?? 0) + 1;
    courtsByLevel[v.level] = (courtsByLevel[v.level] ?? 0) + 1;
  });
  const judgeCount = await scanAll<JudgeRecord>(e, JUDGE_COLLECTION, maxScan, () => {});
  const jurisdictionMapCount = await scanAll<JurisdictionMapRecord>(e, JMAP_COLLECTION, maxScan, () => {});
  return {
    courtCount,
    judgeCount,
    jurisdictionMapCount,
    courtsByJurisdiction,
    courtsByLevel,
    truncated: courtCount >= maxScan || judgeCount >= maxScan || jurisdictionMapCount >= maxScan,
  };
}
