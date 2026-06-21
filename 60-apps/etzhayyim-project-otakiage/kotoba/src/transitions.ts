/**
 * otakiage kotoba — state transitions (slice 2, +5 → 8/10).
 *
 *   requestReuse   — record a reuse request (rkey=reuse-{itemId}-{requester-slug})
 *   handover       — terminal transition: reuse_open → handed_over
 *   expire         — automatic transition: reuse_open → reuse_expired
 *                    (Then to ritual_pending if mode=reuse_then_ritual)
 *   requestRitual  — record a ritual request (rkey=ritual-req-{itemId})
 *   ritualize      — terminal transition: ritual_pending → ritualized
 *                    (Issues certificateUri at this point)
 *
 * Each transition re-emits the ItemRecord with updated status + timestamps
 * by overwriting the rkey. Records of the requests themselves live in
 * separate collections (reuseRequest, ritualRequest) for audit.
 *
 * Transition guards enforce the state machine — invalid transitions
 * (e.g. ritualize on handed_over) return rejected with reason.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  itemRkey,
  OTAKIAGE_DID_PREFIX,
  idSlug,
  type ExpireInput,
  type ExpireOutput,
  type HandoverInput,
  type HandoverOutput,
  type ItemRecord,
  type RequestReuseInput,
  type RequestReuseOutput,
  type RequestRitualInput,
  type RequestRitualOutput,
  type ReuseRequestRecord,
  type RitualizeInput,
  type RitualizeOutput,
  type RitualRequestRecord,
} from "./types.js";

const ITEM_COLLECTION = "com.etzhayyim.otakiage.item";
const REUSE_REQUEST_COLLECTION = "com.etzhayyim.otakiage.reuseRequest";
const RITUAL_REQUEST_COLLECTION = "com.etzhayyim.otakiage.ritualRequest";

function reuseRequestRkey(itemId: string, requesterDid: string): string {
  return `reuse-${idSlug(itemId)}-${idSlug(requesterDid)}`;
}

function ritualRequestRkey(itemId: string): string {
  return `ritual-req-${idSlug(itemId)}`;
}

async function loadItem(
  e: Etzhayyim,
  itemId: string
): Promise<{ record: ItemRecord; uri: string } | undefined> {
  const resp = await e
    .read<ItemRecord>({
      collection: ITEM_COLLECTION,
      rkey: itemRkey(itemId),
    })
    .catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return undefined;
  return { record: r.value, uri: r.uri };
}

// ─── requestReuse ───────────────────────────────────────────────────

export async function requestReuse(
  e: Etzhayyim,
  input: RequestReuseInput
): Promise<RequestReuseOutput> {
  if (!input.itemId || !input.requesterDid) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const loaded = await loadItem(e, input.itemId);
  if (!loaded) return { status: "rejected", error: "itemNotFound" };
  if (loaded.record.status !== "reuse_open") {
    return {
      status: "rejected",
      error: `invalidState:${loaded.record.status}`,
    };
  }

  const rkey = reuseRequestRkey(input.itemId, input.requesterDid);
  const existing = await e
    .read<ReuseRequestRecord>({
      collection: REUSE_REQUEST_COLLECTION,
      rkey,
    })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      reuseRequestUri: existing.records[0].uri,
      itemId: input.itemId,
      requesterDid: input.requesterDid,
    };
  }
  const now = new Date().toISOString();
  const record: ReuseRequestRecord = {
    itemId: input.itemId,
    requesterDid: input.requesterDid,
    message: input.message,
    requestedAt: now,
    createdAt: now,
  };
  const receipt = await e.write({
    collection: REUSE_REQUEST_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "registered",
    reuseRequestUri: receipt.uri,
    itemId: input.itemId,
    requesterDid: input.requesterDid,
  };
}

// ─── handover ───────────────────────────────────────────────────────

export async function handover(
  e: Etzhayyim,
  input: HandoverInput
): Promise<HandoverOutput> {
  if (!input.itemId || !input.recipientDid) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const loaded = await loadItem(e, input.itemId);
  if (!loaded) return { status: "rejected", error: "itemNotFound" };
  if (loaded.record.status !== "reuse_open") {
    return {
      status: "rejected",
      error: `invalidState:${loaded.record.status}`,
    };
  }
  const now = new Date().toISOString();
  const merged: ItemRecord = {
    ...loaded.record,
    status: "handed_over",
    handedOverAt: now,
    handedOverToDid: input.recipientDid,
  };
  const receipt = await e.write({
    collection: ITEM_COLLECTION,
    record: merged as unknown as Record<string, unknown>,
    rkey: itemRkey(input.itemId),
  });
  return {
    status: "handed_over",
    itemUri: receipt.uri,
    itemId: input.itemId,
    recipientDid: input.recipientDid,
  };
}

// ─── expire ─────────────────────────────────────────────────────────

export async function expire(
  e: Etzhayyim,
  input: ExpireInput
): Promise<ExpireOutput> {
  if (!input.itemId) return { status: "rejected", error: "missingItemId" };
  const loaded = await loadItem(e, input.itemId);
  if (!loaded) return { status: "rejected", error: "itemNotFound" };
  if (loaded.record.status !== "reuse_open") {
    return {
      status: "rejected",
      error: `invalidState:${loaded.record.status}`,
    };
  }
  const now = new Date().toISOString();
  // mode=reuse_then_ritual cascades through to ritual_pending immediately.
  const goesToRitual = loaded.record.mode === "reuse_then_ritual";
  const merged: ItemRecord = {
    ...loaded.record,
    status: goesToRitual ? "ritual_pending" : "reuse_expired",
    reuseExpiredAt: now,
    ritualPendingAt: goesToRitual ? now : undefined,
  };
  const receipt = await e.write({
    collection: ITEM_COLLECTION,
    record: merged as unknown as Record<string, unknown>,
    rkey: itemRkey(input.itemId),
  });
  return {
    status: merged.status === "ritual_pending" ? "ritual_pending" : "reuse_expired",
    itemUri: receipt.uri,
    itemId: input.itemId,
  };
}

// ─── requestRitual ──────────────────────────────────────────────────

export async function requestRitual(
  e: Etzhayyim,
  input: RequestRitualInput
): Promise<RequestRitualOutput> {
  if (!input.itemId) return { status: "rejected", error: "missingItemId" };
  const loaded = await loadItem(e, input.itemId);
  if (!loaded) return { status: "rejected", error: "itemNotFound" };
  // Allowed if reuse_expired (with mode=reuse_only escalating to ritual,
  // operator-driven) or already ritual_pending.
  if (
    loaded.record.status !== "reuse_expired" &&
    loaded.record.status !== "ritual_pending" &&
    loaded.record.status !== "submitted"
  ) {
    return {
      status: "rejected",
      error: `invalidState:${loaded.record.status}`,
    };
  }
  const rkey = ritualRequestRkey(input.itemId);
  const existing = await e
    .read<RitualRequestRecord>({
      collection: RITUAL_REQUEST_COLLECTION,
      rkey,
    })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      ritualRequestUri: existing.records[0].uri,
      itemId: input.itemId,
    };
  }
  const now = new Date().toISOString();
  const record: RitualRequestRecord = {
    itemId: input.itemId,
    requesterDid: input.requesterDid ?? loaded.record.ownerDid,
    matsuriDid: input.matsuriDid,
    notes: input.notes,
    requestedAt: now,
    createdAt: now,
  };
  const receipt = await e.write({
    collection: RITUAL_REQUEST_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });

  // If item is still in reuse_expired / submitted, transition to ritual_pending.
  if (loaded.record.status !== "ritual_pending") {
    const merged: ItemRecord = {
      ...loaded.record,
      status: "ritual_pending",
      ritualPendingAt: now,
    };
    await e.write({
      collection: ITEM_COLLECTION,
      record: merged as unknown as Record<string, unknown>,
      rkey: itemRkey(input.itemId),
    });
  }

  return {
    status: "registered",
    ritualRequestUri: receipt.uri,
    itemId: input.itemId,
  };
}

// ─── ritualize ──────────────────────────────────────────────────────

export async function ritualize(
  e: Etzhayyim,
  input: RitualizeInput
): Promise<RitualizeOutput> {
  if (!input.itemId || !input.certificateUri) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const loaded = await loadItem(e, input.itemId);
  if (!loaded) return { status: "rejected", error: "itemNotFound" };
  if (loaded.record.status !== "ritual_pending") {
    return {
      status: "rejected",
      error: `invalidState:${loaded.record.status}`,
    };
  }
  const now = new Date().toISOString();
  const merged: ItemRecord = {
    ...loaded.record,
    status: "ritualized",
    ritualizedAt: now,
    certificateUri: input.certificateUri,
  };
  const receipt = await e.write({
    collection: ITEM_COLLECTION,
    record: merged as unknown as Record<string, unknown>,
    rkey: itemRkey(input.itemId),
  });
  return {
    status: "ritualized",
    itemUri: receipt.uri,
    itemId: input.itemId,
    certificateUri: input.certificateUri,
  };
}

// re-export prefix for downstream callers that need it.
export { OTAKIAGE_DID_PREFIX };
