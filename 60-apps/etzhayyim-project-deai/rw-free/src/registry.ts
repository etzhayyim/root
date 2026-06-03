/**
 * deai rw-free — registry (kotoba-E2E split).
 *
 * Plaintext path (spiritTypeCatalog, cohortStat): sdk.write / sdk.read —
 * public reference data + anonymous aggregates. Catalog FK (complementType)
 * validated via a catalog scan = exists().
 * E2E path (spiritProfile, matchScore): sdk.encryptedWrite / sdk.encryptedRead —
 * PII biometric-derived bodies sealed in the kotoba envelope (ADR-2605181100),
 * read-cap = owner DID. The substrate never sees emotion vectors / per-pair
 * scores in plaintext.
 *
 * Mirrors the intel reference shape (scanAll via encryptedRead + innerType
 * filter; get = scan + find by id).
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  CATALOG_COLLECTION,
  COHORT_STAT_COLLECTION,
  MATCH_INNER_TYPE,
  PROFILE_INNER_TYPE,
  catalogDidFor,
  catalogRkey,
  isPct,
  isPctVector,
  isUint,
  matchRkey,
  profileRkey,
  statDidFor,
  statRkey,
  type CohortStatRecord,
  type CohortStatView,
  type CoverageInput,
  type CoverageOutput,
  type GetMatchInput,
  type GetMatchOutput,
  type GetProfileInput,
  type GetProfileOutput,
  type GetSpiritTypeInput,
  type GetSpiritTypeOutput,
  type ListCohortStatsInput,
  type ListCohortStatsOutput,
  type ListMatchesInput,
  type ListMatchesOutput,
  type ListProfilesInput,
  type ListProfilesOutput,
  type ListSpiritTypesInput,
  type ListSpiritTypesOutput,
  type MatchScoreBody,
  type MatchScoreView,
  type RecordCohortStatInput,
  type RecordCohortStatOutput,
  type RecordMatchInput,
  type RecordMatchOutput,
  type RecordProfileInput,
  type RecordProfileOutput,
  type RegisterSpiritTypeInput,
  type RegisterSpiritTypeOutput,
  type SpiritProfileBody,
  type SpiritProfileView,
  type SpiritTypeCatalogRecord,
  type SpiritTypeCatalogView,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

// ─── Spirit type catalog (PLAINTEXT, reference data + FK) ────────────

async function catalogExists(e: Etzhayyim, spiritType: string): Promise<boolean> {
  const resp = await e
    .read<SpiritTypeCatalogRecord>({ collection: CATALOG_COLLECTION, rkey: catalogRkey(spiritType) })
    .catch(() => ({ records: [] }));
  return Boolean(resp.records[0]?.value);
}

export async function registerSpiritType(e: Etzhayyim, input: RegisterSpiritTypeInput): Promise<RegisterSpiritTypeOutput> {
  if (!input.spiritType || !input.traits || !input.complementType) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (await catalogExists(e, input.spiritType)) {
    const did = catalogDidFor(input.spiritType);
    return { status: "alreadyExists", did, spiritType: input.spiritType };
  }
  // complementType is a plain descriptive field. The deai complement relation is
  // mutual (Hero↔Caregiver, Sage↔Lover), so it cannot carry a non-circular
  // exists()-FK — neither side could be seeded first. The FK-via-exists() is
  // demonstrated instead on the non-circular parent→child edge
  // cohortStat.spiritType → spiritTypeCatalog (see recordCohortStat).
  const now = new Date().toISOString();
  const did = catalogDidFor(input.spiritType);
  const record: SpiritTypeCatalogRecord = {
    did,
    spiritType: input.spiritType,
    traits: input.traits,
    complementType: input.complementType,
    createdAt: now,
  };
  const receipt = await e.write({ collection: CATALOG_COLLECTION, record: record as unknown as Record<string, unknown>, rkey: catalogRkey(input.spiritType) });
  return { status: "registered", catalogUri: receipt.uri, did, spiritType: input.spiritType };
}

export async function getSpiritType(e: Etzhayyim, input: GetSpiritTypeInput): Promise<GetSpiritTypeOutput> {
  if (!input.spiritType) return { error: "invalidSpiritType" };
  const resp = await e
    .read<SpiritTypeCatalogRecord>({ collection: CATALOG_COLLECTION, rkey: catalogRkey(input.spiritType) })
    .catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r?.value) return { error: "notFound" };
  return { spiritType: { ...r.value, catalogUri: r.uri } };
}

export async function listSpiritTypes(e: Etzhayyim, input: ListSpiritTypesInput = {}): Promise<ListSpiritTypesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<SpiritTypeCatalogRecord>({ collection: CATALOG_COLLECTION, cursor: input.cursor, limit });
  const items: SpiritTypeCatalogView[] = resp.records.map((r) => ({ ...r.value, catalogUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Cohort stat (PLAINTEXT, anonymous aggregate) ────────────────────

export async function recordCohortStat(e: Etzhayyim, input: RecordCohortStatInput): Promise<RecordCohortStatOutput> {
  if (!input.statId || !input.spiritType) return { status: "rejected", error: "missingRequiredFields" };
  if (!isUint(input.participantCount)) return { status: "rejected", error: "invalidParticipantCount" };
  // FK: spiritType must reference a registered catalog entry (parent→child,
  // non-circular) — validated via exists().
  if (!(await catalogExists(e, input.spiritType))) return { status: "rejected", error: "unknownSpiritType" };
  const rkey = statRkey(input.statId);
  const existing = await e.read<CohortStatRecord>({ collection: COHORT_STAT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", statUri: existing.records[0].uri, did: existing.records[0].value.did, statId: input.statId };
  }
  const now = new Date().toISOString();
  const did = statDidFor(input.statId);
  const record: CohortStatRecord = {
    did,
    statId: input.statId,
    spiritType: input.spiritType,
    participantCount: input.participantCount,
    generatedAt: input.generatedAt ?? now,
    createdAt: now,
  };
  const receipt = await e.write({ collection: COHORT_STAT_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", statUri: receipt.uri, did, statId: input.statId };
}

export async function listCohortStats(e: Etzhayyim, input: ListCohortStatsInput = {}): Promise<ListCohortStatsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<CohortStatRecord>({ collection: COHORT_STAT_COLLECTION, cursor: input.cursor, limit });
  const items: CohortStatView[] = resp.records
    .filter((r) => !input.spiritType || r.value.spiritType === input.spiritType)
    .map((r) => ({ ...r.value, statUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Spirit profile (E2E-ENCRYPTED, PII / biometric) ─────────────────

export async function recordProfile(e: Etzhayyim, input: RecordProfileInput): Promise<RecordProfileOutput> {
  if (!input.profileId || !input.subjectDid || !input.spiritType || !input.cohortHash) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!isPctVector(input.emotionVector)) return { status: "rejected", error: "invalidEmotionVector" };
  const body: SpiritProfileBody = {
    profileId: input.profileId,
    subjectDid: input.subjectDid,
    spiritType: input.spiritType,
    cohortHash: input.cohortHash,
    emotionVector: input.emotionVector,
    assessedAt: input.assessedAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: PROFILE_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: profileRkey(input.profileId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, profileId: input.profileId };
}

async function scanProfiles(e: Etzhayyim, maxScan: number): Promise<SpiritProfileView[]> {
  const out: SpiritProfileView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<SpiritProfileBody>({ innerType: PROFILE_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listProfiles(e: Etzhayyim, input: ListProfilesInput = {}): Promise<ListProfilesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanProfiles(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((p) => !input.spiritType || p.spiritType === input.spiritType);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getProfile(e: Etzhayyim, input: GetProfileInput): Promise<GetProfileOutput> {
  if (!input.profileId) return { error: "invalidProfileId" };
  const all = await scanProfiles(e, DEFAULT_MAX_SCAN);
  const found = all.find((p) => p.profileId === input.profileId);
  if (!found) return { error: "notFound" };
  return { profile: found };
}

// ─── Match score (E2E-ENCRYPTED, confidential per-pair) ──────────────

export async function recordMatch(e: Etzhayyim, input: RecordMatchInput): Promise<RecordMatchOutput> {
  if (!input.matchId || !input.subjectDidA || !input.subjectDidB) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!isPct(input.resonanceScore)) return { status: "rejected", error: "invalidResonanceScore" };
  if (!isPct(input.spiritCompatibility)) return { status: "rejected", error: "invalidSpiritCompatibility" };
  const body: MatchScoreBody = {
    matchId: input.matchId,
    subjectDidA: input.subjectDidA,
    subjectDidB: input.subjectDidB,
    resonanceScore: input.resonanceScore,
    spiritCompatibility: input.spiritCompatibility,
    computedAt: input.computedAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: MATCH_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: matchRkey(input.matchId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, matchId: input.matchId };
}

async function scanMatches(e: Etzhayyim, maxScan: number): Promise<MatchScoreView[]> {
  const out: MatchScoreView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<MatchScoreBody>({ innerType: MATCH_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listMatches(e: Etzhayyim, input: ListMatchesInput = {}): Promise<ListMatchesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanMatches(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((m) => !input.subjectDid || m.subjectDidA === input.subjectDid || m.subjectDidB === input.subjectDid);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getMatch(e: Etzhayyim, input: GetMatchInput): Promise<GetMatchOutput> {
  if (!input.matchId) return { error: "invalidMatchId" };
  const all = await scanMatches(e, DEFAULT_MAX_SCAN);
  const found = all.find((m) => m.matchId === input.matchId);
  if (!found) return { error: "notFound" };
  return { match: found };
}

// ─── Coverage rollup ────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const statsBySpiritType: Record<string, number> = {};
  let spiritTypeCatalogCount = 0;
  let catalogCursor: string | undefined;
  while (spiritTypeCatalogCount < maxScan) {
    const page = await e.read<SpiritTypeCatalogRecord>({ collection: CATALOG_COLLECTION, cursor: catalogCursor, limit: PAGE_LIMIT });
    spiritTypeCatalogCount += page.records.length;
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    catalogCursor = page.cursor;
  }

  let cohortStatCount = 0;
  let statCursor: string | undefined;
  while (cohortStatCount < maxScan) {
    const page = await e.read<CohortStatRecord>({ collection: COHORT_STAT_COLLECTION, cursor: statCursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      statsBySpiritType[r.value.spiritType] = (statsBySpiritType[r.value.spiritType] ?? 0) + 1;
      cohortStatCount += 1;
    }
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    statCursor = page.cursor;
  }

  const spiritProfileCount = (await scanProfiles(e, maxScan)).length;
  const matchScoreCount = (await scanMatches(e, maxScan)).length;
  return {
    spiritTypeCatalogCount,
    cohortStatCount,
    spiritProfileCount,
    matchScoreCount,
    statsBySpiritType,
    truncated:
      spiritTypeCatalogCount >= maxScan ||
      cohortStatCount >= maxScan ||
      spiritProfileCount >= maxScan ||
      matchScoreCount >= maxScan,
  };
}
