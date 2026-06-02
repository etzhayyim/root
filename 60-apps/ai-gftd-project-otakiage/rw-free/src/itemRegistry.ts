/**
 * otakiage rw-free — item tier (slice 1, 3/10).
 *
 *   submitItem   — initial item submission, status → submitted → reuse_open
 *                  (rkey=item-{itemId-slug}, idempotent)
 *   getItem      — rkey-direct read
 *   listItems    — cursor + status/mode/ownerDid/category filter
 *
 * Initial state transition handled inline (submitted → reuse_open with
 * 30-day TTL by default; mode=ritual_only skips reuse_open and goes
 * directly to ritual_pending).
 *
 * Subsequent state transitions (handover / expire / ritualize) ship in
 * follow-up slices (separate functions per transition for clarity).
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  itemDid,
  itemRkey,
  REUSE_DEFAULT_TTL_MS,
  type GetItemInput,
  type GetItemOutput,
  type ItemRecord,
  type ItemStatus,
  type ItemView,
  type ListItemsInput,
  type ListItemsOutput,
  type SubmitItemInput,
  type SubmitItemOutput,
} from "./types.js";

const ITEM_COLLECTION = "com.etzhayyim.otakiage.item";

export async function submitItem(
  e: Etzhayyim,
  input: SubmitItemInput
): Promise<SubmitItemOutput> {
  if (!input.itemId || !input.ownerDid || !input.title || !input.mode) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const rkey = itemRkey(input.itemId);
  const existing = await e
    .read<ItemRecord>({ collection: ITEM_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      itemUri: existing.records[0].uri,
      did: existing.records[0].value.did,
      itemId: input.itemId,
      itemStatus: existing.records[0].value.status,
    };
  }
  const now = new Date();
  const nowIso = now.toISOString();

  // Initial state transition: submitted → reuse_open (or ritual_pending
  // for ritual_only mode).
  let itemStatus: ItemStatus;
  let reuseOpenAt: string | undefined;
  let reuseDeadlineAt: string | undefined;
  let ritualPendingAt: string | undefined;
  if (input.mode === "ritual_only") {
    itemStatus = "ritual_pending";
    ritualPendingAt = nowIso;
  } else {
    itemStatus = "reuse_open";
    reuseOpenAt = nowIso;
    reuseDeadlineAt =
      input.reuseDeadlineAt ??
      new Date(now.getTime() + REUSE_DEFAULT_TTL_MS).toISOString();
  }

  const record: ItemRecord = {
    did: itemDid(input.itemId),
    itemId: input.itemId,
    ownerDid: input.ownerDid,
    title: input.title,
    description: input.description,
    category: input.category,
    mode: input.mode,
    status: itemStatus,
    submittedAt: nowIso,
    reuseOpenAt,
    reuseDeadlineAt,
    ritualPendingAt,
    locationHint: input.locationHint,
    imageCids: input.imageCids,
    createdAt: nowIso,
  };
  const receipt = await e.write({
    collection: ITEM_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "registered",
    itemUri: receipt.uri,
    did: record.did,
    itemId: input.itemId,
    itemStatus,
  };
}

export async function getItem(
  e: Etzhayyim,
  input: GetItemInput
): Promise<GetItemOutput> {
  if (!input.itemId) return { error: "missingItemId" };
  const resp = await e
    .read<ItemRecord>({
      collection: ITEM_COLLECTION,
      rkey: itemRkey(input.itemId),
    })
    .catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  const view: ItemView = { ...r.value, itemUri: r.uri };
  return { item: view };
}

export async function listItems(
  e: Etzhayyim,
  input: ListItemsInput = {}
): Promise<ListItemsOutput> {
  const limit = Math.min(input.limit ?? 50, 100);
  const resp = await e.read<ItemRecord>({
    collection: ITEM_COLLECTION,
    cursor: input.cursor,
    limit,
  });
  const items: ItemView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.status && v.status !== input.status) return false;
      if (input.mode && v.mode !== input.mode) return false;
      if (input.ownerDid && v.ownerDid !== input.ownerDid) return false;
      if (input.category && v.category !== input.category) return false;
      return true;
    })
    .map((r) => ({ ...r.value, itemUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}
