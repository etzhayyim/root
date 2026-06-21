/**
 * open-cofog kotoba — COFOG entry registry (register/get/list/coverage).
 * AT PDS records (no RW). Replaces the per-class JSON + worker index with an
 * AT-PDS taxonomy; level/division/parent are derived from the code.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  ENTRY_COLLECTION,
  cofogLevel,
  entryDid,
  entryRkey,
  isValidCofogCode,
  parentOf,
  type CofogEntry,
  type CofogLevel,
  type CofogView,
  type CoverageInput,
  type CoverageOutput,
  type GetEntryInput,
  type GetEntryOutput,
  type ListEntriesInput,
  type ListEntriesOutput,
  type RegisterEntryInput,
  type RegisterEntryOutput,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;
const COFOG_PUBLISHED_AT_DEFAULT = "1999-01-01T00:00:00Z"; // COFOG 1999

export async function registerEntry(
  e: Etzhayyim,
  input: RegisterEntryInput
): Promise<RegisterEntryOutput> {
  if (!input.code || !input.titleEn) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!isValidCofogCode(input.code)) {
    return { status: "rejected", error: "invalidCofogCode" };
  }

  const rkey = entryRkey(input.code);
  const existing = await e
    .read<CofogEntry>({ collection: ENTRY_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      entryUri: existing.records[0].uri,
      did: existing.records[0].value.did,
      code: input.code,
    };
  }

  const did = entryDid(input.code);
  const record: CofogEntry = {
    did,
    code: input.code,
    titleEn: input.titleEn,
    level: cofogLevel(input.code),
    division: input.code.slice(0, 2),
    parent: parentOf(input.code),
    description: input.description,
    source: input.source,
    publishedAt: input.publishedAt ?? COFOG_PUBLISHED_AT_DEFAULT,
  };
  const receipt = await e.write({
    collection: ENTRY_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return { status: "registered", entryUri: receipt.uri, did, code: input.code };
}

export async function getEntry(
  e: Etzhayyim,
  input: GetEntryInput
): Promise<GetEntryOutput> {
  if (!input.code || !isValidCofogCode(input.code)) {
    return { error: "invalidCofogCode" };
  }
  const resp = await e
    .read<CofogView>({ collection: ENTRY_COLLECTION, rkey: entryRkey(input.code) })
    .catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { entry: { ...r.value, entryUri: r.uri } };
}

export async function listEntries(
  e: Etzhayyim,
  input: ListEntriesInput = {}
): Promise<ListEntriesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<CofogView>({
    collection: ENTRY_COLLECTION,
    cursor: input.cursor,
    limit,
  });
  const items: CofogView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.level && v.level !== input.level) return false;
      if (input.division && v.division !== input.division) return false;
      return true;
    })
    .map((r) => ({ ...r.value, entryUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

export async function coverage(
  e: Etzhayyim,
  input: CoverageInput = {}
): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  let cursor: string | undefined;
  let scanned = 0;
  const byLevel: Record<string, number> = {};
  const byDivision: Record<string, number> = {};
  while (scanned < maxScan) {
    const page = await e.read<CofogView>({
      collection: ENTRY_COLLECTION,
      cursor,
      limit: PAGE_LIMIT,
    });
    for (const r of page.records) {
      if (scanned >= maxScan) break;
      const v = r.value;
      byLevel[v.level as CofogLevel] = (byLevel[v.level as CofogLevel] ?? 0) + 1;
      byDivision[v.division] = (byDivision[v.division] ?? 0) + 1;
      scanned += 1;
    }
    if (scanned >= maxScan || !page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return { total: scanned, byLevel, byDivision, truncated: scanned >= maxScan };
}
