/**
 * sanctions rw-free — listUpdate + sanctionEntry registries + coverage.
 * AT PDS records (no RW). Entries FK→listUpdate (optional provenance edge).
 * Public consolidated sanctions-list reference only; screening stays etzhayyim.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  ENTITY_TYPES,
  LIST_SOURCES,
  LIST_UPDATE_COLLECTION,
  SANCTION_ENTRY_COLLECTION,
  entryDidFor,
  entryRkey,
  isCountryCode,
  isUint,
  updateDidFor,
  updateRkey,
  type AddEntryInput,
  type AddEntryOutput,
  type CoverageInput,
  type CoverageOutput,
  type GetEntryInput,
  type GetEntryOutput,
  type ListEntriesInput,
  type ListEntriesOutput,
  type ListListUpdatesInput,
  type ListListUpdatesOutput,
  type ListUpdateRecord,
  type ListUpdateView,
  type RegisterListUpdateInput,
  type RegisterListUpdateOutput,
  type SanctionEntryRecord,
  type SanctionEntryView,
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

// ─── List update ────────────────────────────────────────────────────

export async function registerListUpdate(e: Etzhayyim, input: RegisterListUpdateInput): Promise<RegisterListUpdateOutput> {
  if (!input.updateId || !input.listVersion || !input.fetchedAt || !input.sourceUrl) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!LIST_SOURCES.has(input.listSource)) return { status: "rejected", error: "invalidListSource" };
  if (!isUint(input.changeCount)) return { status: "rejected", error: "changeCountMustBeUint" };
  const rkey = updateRkey(input.updateId);
  const existing = await e.read<ListUpdateRecord>({ collection: LIST_UPDATE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", updateUri: existing.records[0].uri, did: existing.records[0].value.did, updateId: input.updateId };
  }
  const did = updateDidFor(input.updateId);
  const record: ListUpdateRecord = {
    did,
    updateId: input.updateId,
    listSource: input.listSource,
    listVersion: input.listVersion,
    changeCount: input.changeCount,
    fetchedAt: input.fetchedAt,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: LIST_UPDATE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", updateUri: receipt.uri, did, updateId: input.updateId };
}

export async function listListUpdates(e: Etzhayyim, input: ListListUpdatesInput = {}): Promise<ListListUpdatesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ListUpdateRecord>({ collection: LIST_UPDATE_COLLECTION, cursor: input.cursor, limit });
  const items: ListUpdateView[] = resp.records
    .filter((r) => !input.listSource || r.value.listSource === input.listSource)
    .map((r) => ({ ...r.value, updateUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Sanction entry ─────────────────────────────────────────────────

export async function addEntry(e: Etzhayyim, input: AddEntryInput): Promise<AddEntryOutput> {
  if (!input.entryId || !input.entityName || !input.sourceUrl) return { status: "rejected", error: "missingRequiredFields" };
  if (!LIST_SOURCES.has(input.listSource)) return { status: "rejected", error: "invalidListSource" };
  if (!ENTITY_TYPES.has(input.entityType)) return { status: "rejected", error: "invalidEntityType" };
  if (input.country && !isCountryCode(input.country.toUpperCase())) return { status: "rejected", error: "invalidCountry" };
  if (input.updateId && !(await exists(e, LIST_UPDATE_COLLECTION, updateRkey(input.updateId)))) {
    return { status: "listUpdateNotFound", error: `listUpdateNotFound:${input.updateId}` };
  }
  const rkey = entryRkey(input.entryId);
  const existing = await e.read<SanctionEntryRecord>({ collection: SANCTION_ENTRY_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", entryUri: existing.records[0].uri, did: existing.records[0].value.did, entryId: input.entryId };
  }
  const did = entryDidFor(input.entryId);
  const record: SanctionEntryRecord = {
    did,
    entryId: input.entryId,
    listSource: input.listSource,
    entityName: input.entityName,
    entityType: input.entityType,
    country: input.country?.toUpperCase(),
    program: input.program,
    aliases: input.aliases,
    identifiers: input.identifiers,
    listedDate: input.listedDate,
    updateId: input.updateId,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: SANCTION_ENTRY_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", entryUri: receipt.uri, did, entryId: input.entryId };
}

export async function getEntry(e: Etzhayyim, input: GetEntryInput): Promise<GetEntryOutput> {
  if (!input.entryId) return { error: "invalidEntryId" };
  const resp = await e.read<SanctionEntryRecord>({ collection: SANCTION_ENTRY_COLLECTION, rkey: entryRkey(input.entryId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { entry: { ...r.value, entryUri: r.uri } };
}

export async function listEntries(e: Etzhayyim, input: ListEntriesInput = {}): Promise<ListEntriesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<SanctionEntryRecord>({ collection: SANCTION_ENTRY_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const country = input.country?.toUpperCase();
  const items: SanctionEntryView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.listSource && v.listSource !== input.listSource) return false;
      if (input.entityType && v.entityType !== input.entityType) return false;
      if (country && v.country !== country) return false;
      if (input.program && v.program !== input.program) return false;
      if (q) {
        const hay = [v.entityName, ...(v.aliases ?? [])].join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    })
    .map((r) => ({ ...r.value, entryUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const entriesByListSource: Record<string, number> = {};
  const entriesByType: Record<string, number> = {};
  const entryCount = await scanAll<SanctionEntryRecord>(e, SANCTION_ENTRY_COLLECTION, maxScan, (v) => {
    entriesByListSource[v.listSource] = (entriesByListSource[v.listSource] ?? 0) + 1;
    entriesByType[v.entityType] = (entriesByType[v.entityType] ?? 0) + 1;
  });
  const listUpdateCount = await scanAll<ListUpdateRecord>(e, LIST_UPDATE_COLLECTION, maxScan, () => {});
  return {
    entryCount,
    listUpdateCount,
    entriesByListSource,
    entriesByType,
    truncated: entryCount >= maxScan || listUpdateCount >= maxScan,
  };
}
