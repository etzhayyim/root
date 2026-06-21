/**
 * webpage kotoba — space + page authoring/publishing registries + coverage.
 * AT PDS records (no RW). Pages FK→space. First-party user-authored content;
 * publishing flips status + populates the public published-page directory.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  PAGE_COLLECTION,
  PAGE_STATUSES,
  SPACE_COLLECTION,
  isSlug,
  pageDidFor,
  pageRkey,
  spaceDidFor,
  spaceRkey,
  type CoverageInput,
  type CoverageOutput,
  type CreatePageInput,
  type CreatePageOutput,
  type GetPageInput,
  type GetPageOutput,
  type ListPagesInput,
  type ListPagesOutput,
  type ListSpacesInput,
  type ListSpacesOutput,
  type PageRecord,
  type PageView,
  type RegisterSpaceInput,
  type RegisterSpaceOutput,
  type SetPageStatusInput,
  type SetPageStatusOutput,
  type SpaceRecord,
  type SpaceView,
  type UpdatePageInput,
  type UpdatePageOutput,
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

// ─── Space ──────────────────────────────────────────────────────────

export async function registerSpace(e: Etzhayyim, input: RegisterSpaceInput): Promise<RegisterSpaceOutput> {
  if (!input.spaceId || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  const rkey = spaceRkey(input.spaceId);
  const existing = await e.read<SpaceRecord>({ collection: SPACE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", spaceUri: existing.records[0].uri, did: existing.records[0].value.did, spaceId: input.spaceId };
  }
  const did = spaceDidFor(input.spaceId);
  const record: SpaceRecord = {
    did,
    spaceId: input.spaceId,
    name: input.name,
    description: input.description,
    ownerDid: input.ownerDid,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: SPACE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", spaceUri: receipt.uri, did, spaceId: input.spaceId };
}

export async function listSpaces(e: Etzhayyim, input: ListSpacesInput = {}): Promise<ListSpacesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<SpaceRecord>({ collection: SPACE_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: SpaceView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.ownerDid && v.ownerDid !== input.ownerDid) return false;
      if (q && !v.name.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, spaceUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Page ───────────────────────────────────────────────────────────

export async function createPage(e: Etzhayyim, input: CreatePageInput): Promise<CreatePageOutput> {
  if (!input.pageId || !input.spaceId || !input.title || !input.slug) return { status: "rejected", error: "missingRequiredFields" };
  if (!isSlug(input.slug.toLowerCase())) return { status: "rejected", error: "invalidSlug" };
  if (!(await exists(e, SPACE_COLLECTION, spaceRkey(input.spaceId)))) {
    return { status: "spaceNotFound", error: `spaceNotFound:${input.spaceId}` };
  }
  const rkey = pageRkey(input.pageId);
  const existing = await e.read<PageRecord>({ collection: PAGE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", pageUri: existing.records[0].uri, did: existing.records[0].value.did, pageId: input.pageId };
  }
  const did = pageDidFor(input.pageId);
  const now = new Date().toISOString();
  const record: PageRecord = {
    did,
    pageId: input.pageId,
    spaceId: input.spaceId,
    title: input.title,
    slug: input.slug.toLowerCase(),
    body: input.body ?? "",
    status: "draft",
    tags: input.tags,
    createdAt: now,
    updatedAt: now,
  };
  const receipt = await e.write({ collection: PAGE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "created", pageUri: receipt.uri, did, pageId: input.pageId };
}

export async function updatePage(e: Etzhayyim, input: UpdatePageInput): Promise<UpdatePageOutput> {
  if (!input.pageId) return { status: "rejected", error: "invalidPageId" };
  const rkey = pageRkey(input.pageId);
  const resp = await e.read<PageRecord>({ collection: PAGE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  const page = resp.records[0]?.value;
  if (!page) return { status: "notFound", error: "pageNotFound" };
  const updated: PageRecord = {
    ...page,
    title: input.title ?? page.title,
    body: input.body ?? page.body,
    tags: input.tags ?? page.tags,
    updatedAt: new Date().toISOString(),
  };
  await e.write({ collection: PAGE_COLLECTION, record: updated as unknown as Record<string, unknown>, rkey });
  return { status: "updated", pageId: input.pageId };
}

export async function setPageStatus(e: Etzhayyim, input: SetPageStatusInput): Promise<SetPageStatusOutput> {
  if (!input.pageId || !PAGE_STATUSES.has(input.status)) return { status: "rejected", error: "invalidStatus" };
  const rkey = pageRkey(input.pageId);
  const resp = await e.read<PageRecord>({ collection: PAGE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  const page = resp.records[0]?.value;
  if (!page) return { status: "notFound", error: "pageNotFound" };
  const now = new Date().toISOString();
  const updated: PageRecord = {
    ...page,
    status: input.status,
    publishedAt: input.status === "published" ? input.publishedAt ?? page.publishedAt ?? now : page.publishedAt,
    updatedAt: now,
  };
  await e.write({ collection: PAGE_COLLECTION, record: updated as unknown as Record<string, unknown>, rkey });
  return { status: "updated", pageId: input.pageId, newStatus: input.status };
}

export async function getPage(e: Etzhayyim, input: GetPageInput): Promise<GetPageOutput> {
  if (!input.pageId) return { error: "invalidPageId" };
  const resp = await e.read<PageRecord>({ collection: PAGE_COLLECTION, rkey: pageRkey(input.pageId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { page: { ...r.value, pageUri: r.uri } };
}

export async function listPages(e: Etzhayyim, input: ListPagesInput = {}): Promise<ListPagesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<PageRecord>({ collection: PAGE_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: PageView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.spaceId && v.spaceId !== input.spaceId) return false;
      if (input.status && v.status !== input.status) return false;
      if (input.tag && !(v.tags ?? []).includes(input.tag)) return false;
      if (q) {
        const hay = [v.title, v.body].join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    })
    .map((r) => ({ ...r.value, pageUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const pagesByStatus: Record<string, number> = {};
  const spaceCount = await scanAll<SpaceRecord>(e, SPACE_COLLECTION, maxScan, () => {});
  const pageCount = await scanAll<PageRecord>(e, PAGE_COLLECTION, maxScan, (v) => {
    pagesByStatus[v.status] = (pagesByStatus[v.status] ?? 0) + 1;
  });
  return {
    spaceCount,
    pageCount,
    pagesByStatus,
    truncated: spaceCount >= maxScan || pageCount >= maxScan,
  };
}
