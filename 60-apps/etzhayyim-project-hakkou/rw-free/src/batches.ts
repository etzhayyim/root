/**
 * hakkou rw-free — batch tier.
 *
 *   registerBatch        — create a fermentation batch record
 *   getBatch             — retrieve batch by ID
 *   listBatches          — list batches with optional filter
 *   updateFermentStatus  — helper: transition batch status
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  batchDid,
  batchRkey,
  type BatchRecord,
  type BatchStatus,
  type BatchView,
  type GetBatchInput,
  type GetBatchOutput,
  type ListBatchesInput,
  type ListBatchesOutput,
  type RegisterBatchInput,
  type RegisterBatchOutput,
  type UpdateBatchStatusInput,
  type UpdateBatchStatusOutput,
} from "./types.js";

const BATCH_COLLECTION = "com.etzhayyim.hakkou.batch";

const VALID_STATUSES: BatchStatus[] = ["pending", "running", "done", "failed"];
const STATUS_TRANSITIONS: Record<BatchStatus, BatchStatus[]> = {
  pending: ["running"],
  running: ["done", "failed"],
  done: [],
  failed: [],
};

export async function registerBatch(
  e: Etzhayyim,
  input: RegisterBatchInput
): Promise<RegisterBatchOutput> {
  // Validation: required fields
  if (!input.batchId || !input.batchType || !input.startDate || !input.targetEndDate) {
    return { status: "rejected", error: "missingRequiredFields" };
  }

  // Validation: valid batch type
  const validTypes = ["sake", "miso", "koji", "vinegar"];
  if (!validTypes.includes(input.batchType)) {
    return { status: "rejected", error: "invalidBatchType" };
  }

  const rkey = batchRkey(input.batchId);

  // Check idempotency
  const existing = await e
    .read<BatchRecord>({ collection: BATCH_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      batchUri: existing.records[0].uri,
      batchId: input.batchId,
    };
  }

  const did = batchDid(input.batchId);
  const now = new Date().toISOString();
  const record: BatchRecord = {
    did,
    batchId: input.batchId,
    batchType: input.batchType,
    startDate: input.startDate,
    targetEndDate: input.targetEndDate,
    status: "pending",
    createdAt: now,
  };

  const receipt = await e.write({
    collection: BATCH_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });

  return {
    status: "created",
    batchUri: receipt.uri,
    batchId: input.batchId,
  };
}

export async function getBatch(
  e: Etzhayyim,
  input: GetBatchInput
): Promise<GetBatchOutput> {
  if (!input.batchId) {
    return { error: "missingBatchId" };
  }

  const resp = await e
    .read<BatchRecord>({
      collection: BATCH_COLLECTION,
      rkey: batchRkey(input.batchId),
    })
    .catch(() => ({ records: [] }));

  const r = resp.records[0];
  if (!r) return { error: "notFound" };

  const view: BatchView = {
    ...r.value,
    batchUri: r.uri,
    batchVertexId: r.value.did,
  };
  return { batch: view };
}

export async function listBatches(
  e: Etzhayyim,
  input: ListBatchesInput
): Promise<ListBatchesOutput> {
  const resp = await e
    .read<BatchRecord>({ collection: BATCH_COLLECTION })
    .catch(() => ({ records: [] }));

  const items: BatchView[] = resp.records
    .filter((r) => {
      if (input.batchType && r.value.batchType !== input.batchType) {
        return false;
      }
      return true;
    })
    .map((r) => ({
      ...r.value,
      batchUri: r.uri,
      batchVertexId: r.value.did,
    }));

  return { items };
}

export async function updateFermentStatus(
  e: Etzhayyim,
  input: UpdateBatchStatusInput
): Promise<UpdateBatchStatusOutput> {
  // Validation: required fields first
  if (!input.batchId || !input.newStatus) {
    return { status: "rejected", error: "missingRequiredFields" };
  }

  // Validation: check if status is valid
  if (!VALID_STATUSES.includes(input.newStatus)) {
    return { status: "rejected", error: "invalidStatus" };
  }

  const rkey = batchRkey(input.batchId);
  const resp = await e
    .read<BatchRecord>({ collection: BATCH_COLLECTION, rkey })
    .catch(() => ({ records: [] }));

  const existing = resp.records[0]?.value;
  if (!existing) {
    return { status: "rejected", error: "batchNotFound" };
  }

  // Validation: check valid transition
  const allowedNext = STATUS_TRANSITIONS[existing.status];
  if (!allowedNext.includes(input.newStatus)) {
    return { status: "rejected", error: "invalidStatusTransition" };
  }

  const merged: BatchRecord = {
    ...existing,
    status: input.newStatus,
  };

  await e.write({
    collection: BATCH_COLLECTION,
    record: merged as unknown as Record<string, unknown>,
    rkey,
  });

  return {
    status: "updated",
    previousStatus: existing.status,
    newStatus: input.newStatus,
  };
}
