/**
 * media-gamers rw-free — publisher + developer + gameTitle + chartEntry
 * registries + coverage. AT PDS records (no RW). gameTitle FK→publisher+developer;
 * chartEntry FK→gameTitle. Public game-catalog open-data; guide-gen stays etzhayyim.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  CHART_ENTRY_COLLECTION,
  DEVELOPER_COLLECTION,
  GAME_TITLE_COLLECTION,
  PUBLISHER_COLLECTION,
  developerDidFor,
  developerRkey,
  entryDidFor,
  entryRkey,
  isUint,
  publisherDidFor,
  publisherRkey,
  titleDidFor,
  titleRkey,
  type ChartEntryRecord,
  type ChartEntryView,
  type CoverageInput,
  type CoverageOutput,
  type DeveloperRecord,
  type DeveloperView,
  type GameTitleRecord,
  type GameTitleView,
  type GetGameTitleInput,
  type GetGameTitleOutput,
  type ListChartEntriesInput,
  type ListChartEntriesOutput,
  type ListDevelopersInput,
  type ListDevelopersOutput,
  type ListGameTitlesInput,
  type ListGameTitlesOutput,
  type ListPublishersInput,
  type ListPublishersOutput,
  type PublisherRecord,
  type PublisherView,
  type RecordChartEntryInput,
  type RecordChartEntryOutput,
  type RegisterDeveloperInput,
  type RegisterDeveloperOutput,
  type RegisterGameTitleInput,
  type RegisterGameTitleOutput,
  type RegisterPublisherInput,
  type RegisterPublisherOutput,
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

// ─── Publisher ──────────────────────────────────────────────────────

export async function registerPublisher(e: Etzhayyim, input: RegisterPublisherInput): Promise<RegisterPublisherOutput> {
  if (!input.publisherId || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  const rkey = publisherRkey(input.publisherId);
  const existing = await e.read<PublisherRecord>({ collection: PUBLISHER_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", publisherUri: existing.records[0].uri, did: existing.records[0].value.did, publisherId: input.publisherId };
  }
  const did = publisherDidFor(input.publisherId);
  const record: PublisherRecord = { did, publisherId: input.publisherId, name: input.name, country: input.country, sourceUrl: input.sourceUrl, createdAt: new Date().toISOString() };
  const receipt = await e.write({ collection: PUBLISHER_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", publisherUri: receipt.uri, did, publisherId: input.publisherId };
}

export async function listPublishers(e: Etzhayyim, input: ListPublishersInput = {}): Promise<ListPublishersOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<PublisherRecord>({ collection: PUBLISHER_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: PublisherView[] = resp.records
    .filter((r) => (!input.country || r.value.country === input.country) && (!q || r.value.name.toLowerCase().includes(q)))
    .map((r) => ({ ...r.value, publisherUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Developer ──────────────────────────────────────────────────────

export async function registerDeveloper(e: Etzhayyim, input: RegisterDeveloperInput): Promise<RegisterDeveloperOutput> {
  if (!input.developerId || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  const rkey = developerRkey(input.developerId);
  const existing = await e.read<DeveloperRecord>({ collection: DEVELOPER_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", developerUri: existing.records[0].uri, did: existing.records[0].value.did, developerId: input.developerId };
  }
  const did = developerDidFor(input.developerId);
  const record: DeveloperRecord = { did, developerId: input.developerId, name: input.name, country: input.country, sourceUrl: input.sourceUrl, createdAt: new Date().toISOString() };
  const receipt = await e.write({ collection: DEVELOPER_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", developerUri: receipt.uri, did, developerId: input.developerId };
}

export async function listDevelopers(e: Etzhayyim, input: ListDevelopersInput = {}): Promise<ListDevelopersOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<DeveloperRecord>({ collection: DEVELOPER_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: DeveloperView[] = resp.records
    .filter((r) => (!input.country || r.value.country === input.country) && (!q || r.value.name.toLowerCase().includes(q)))
    .map((r) => ({ ...r.value, developerUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Game title ─────────────────────────────────────────────────────

export async function registerGameTitle(e: Etzhayyim, input: RegisterGameTitleInput): Promise<RegisterGameTitleOutput> {
  if (!input.titleId || !input.name || !input.slug) return { status: "rejected", error: "missingRequiredFields" };
  if (input.publisherId && !(await exists(e, PUBLISHER_COLLECTION, publisherRkey(input.publisherId)))) {
    return { status: "publisherNotFound", error: `publisherNotFound:${input.publisherId}` };
  }
  if (input.developerId && !(await exists(e, DEVELOPER_COLLECTION, developerRkey(input.developerId)))) {
    return { status: "developerNotFound", error: `developerNotFound:${input.developerId}` };
  }
  const rkey = titleRkey(input.titleId);
  const existing = await e.read<GameTitleRecord>({ collection: GAME_TITLE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", titleUri: existing.records[0].uri, did: existing.records[0].value.did, titleId: input.titleId };
  }
  const did = titleDidFor(input.titleId);
  const record: GameTitleRecord = {
    did,
    titleId: input.titleId,
    name: input.name,
    slug: input.slug.toLowerCase(),
    publisherId: input.publisherId,
    developerId: input.developerId,
    platforms: input.platforms,
    genre: input.genre,
    releaseDate: input.releaseDate,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: GAME_TITLE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", titleUri: receipt.uri, did, titleId: input.titleId };
}

export async function getGameTitle(e: Etzhayyim, input: GetGameTitleInput): Promise<GetGameTitleOutput> {
  if (!input.titleId) return { error: "invalidTitleId" };
  const resp = await e.read<GameTitleRecord>({ collection: GAME_TITLE_COLLECTION, rkey: titleRkey(input.titleId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { title: { ...r.value, titleUri: r.uri } };
}

export async function listGameTitles(e: Etzhayyim, input: ListGameTitlesInput = {}): Promise<ListGameTitlesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<GameTitleRecord>({ collection: GAME_TITLE_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: GameTitleView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.publisherId && v.publisherId !== input.publisherId) return false;
      if (input.developerId && v.developerId !== input.developerId) return false;
      if (input.genre && v.genre !== input.genre) return false;
      if (input.platform && !(v.platforms ?? []).includes(input.platform)) return false;
      if (q && !v.name.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, titleUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Chart entry ────────────────────────────────────────────────────

export async function recordChartEntry(e: Etzhayyim, input: RecordChartEntryInput): Promise<RecordChartEntryOutput> {
  if (!input.entryId || !input.chartName || !input.titleId) return { status: "rejected", error: "missingRequiredFields" };
  if (!isUint(input.rank)) return { status: "rejected", error: "rankMustBeUint" };
  if (!(await exists(e, GAME_TITLE_COLLECTION, titleRkey(input.titleId)))) {
    return { status: "titleNotFound", error: `titleNotFound:${input.titleId}` };
  }
  const rkey = entryRkey(input.entryId);
  const existing = await e.read<ChartEntryRecord>({ collection: CHART_ENTRY_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", entryUri: existing.records[0].uri, did: existing.records[0].value.did, entryId: input.entryId };
  }
  const did = entryDidFor(input.entryId);
  const record: ChartEntryRecord = {
    did,
    entryId: input.entryId,
    chartName: input.chartName,
    titleId: input.titleId,
    rank: input.rank,
    region: input.region,
    period: input.period,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: CHART_ENTRY_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", entryUri: receipt.uri, did, entryId: input.entryId };
}

export async function listChartEntries(e: Etzhayyim, input: ListChartEntriesInput = {}): Promise<ListChartEntriesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ChartEntryRecord>({ collection: CHART_ENTRY_COLLECTION, cursor: input.cursor, limit });
  const items: ChartEntryView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.chartName && v.chartName !== input.chartName) return false;
      if (input.titleId && v.titleId !== input.titleId) return false;
      if (input.region && v.region !== input.region) return false;
      if (input.period && v.period !== input.period) return false;
      return true;
    })
    .map((r) => ({ ...r.value, entryUri: r.uri }))
    .sort((a, b) => a.rank - b.rank);
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const titlesByGenre: Record<string, number> = {};
  const publisherCount = await scanAll<PublisherRecord>(e, PUBLISHER_COLLECTION, maxScan, () => {});
  const developerCount = await scanAll<DeveloperRecord>(e, DEVELOPER_COLLECTION, maxScan, () => {});
  const gameTitleCount = await scanAll<GameTitleRecord>(e, GAME_TITLE_COLLECTION, maxScan, (v) => {
    if (v.genre) titlesByGenre[v.genre] = (titlesByGenre[v.genre] ?? 0) + 1;
  });
  const chartEntryCount = await scanAll<ChartEntryRecord>(e, CHART_ENTRY_COLLECTION, maxScan, () => {});
  return {
    publisherCount,
    developerCount,
    gameTitleCount,
    chartEntryCount,
    titlesByGenre,
    truncated: publisherCount >= maxScan || developerCount >= maxScan || gameTitleCount >= maxScan || chartEntryCount >= maxScan,
  };
}
