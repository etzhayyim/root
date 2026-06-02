/**
 * koke rw-free — carbon credit management (4/4 canonical complete).
 *
 *   registerCarbon  — create batch (rkey=batch-{batchId-slug}, idempotent)
 *   releaseCarbon   — create release from batch (rkey=release-{releaseId-slug}, idempotent)
 *   recordOffset    — create offset from release (rkey=offset-{offsetId-slug}, idempotent)
 *   listOffsets     — cursor + project filter
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  batchRkey,
  releaseRkey,
  offsetRkey,
  type CarbonBatchRecord,
  type ReleaseRecord,
  type OffsetRecord,
  type RegisterCarbonInput,
  type RegisterCarbonOutput,
  type ReleaseCarbonInput,
  type ReleaseCarbonOutput,
  type RecordOffsetInput,
  type RecordOffsetOutput,
  type ListOffsetsInput,
  type ListOffsetsOutput,
} from "./types.js";

const BATCH_COLLECTION = "com.etzhayyim.koke.batch";
const RELEASE_COLLECTION = "com.etzhayyim.koke.release";
const OFFSET_COLLECTION = "com.etzhayyim.koke.offset";

export async function registerCarbon(
  e: Etzhayyim,
  input: RegisterCarbonInput
): Promise<RegisterCarbonOutput> {
  // Validation: missing required fields
  if (!input.batchId || !input.totalCredits || !input.vintage || !input.methodology) {
    return { status: "rejected", error: "missingRequiredFields" };
  }

  const rkey = batchRkey(input.batchId);

  // Idempotency check
  const existing = await e
    .read<CarbonBatchRecord>({ collection: BATCH_COLLECTION, rkey })
    .catch(() => ({ records: [] }));

  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      batchUri: existing.records[0].uri,
    };
  }

  const now = new Date().toISOString();
  const record: CarbonBatchRecord = {
    batchId: input.batchId,
    totalCredits: input.totalCredits,
    vintage: input.vintage,
    methodology: input.methodology,
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
  };
}

export async function releaseCarbon(
  e: Etzhayyim,
  input: ReleaseCarbonInput
): Promise<ReleaseCarbonOutput> {
  // Validation: missing required fields (before checking idempotency)
  if (!input.releaseId || !input.batchId || !input.releasedCredits) {
    return { status: "rejected", error: "missingRequiredFields" };
  }

  const rkey = releaseRkey(input.releaseId);

  // Idempotency check
  const existing = await e
    .read<ReleaseRecord>({ collection: RELEASE_COLLECTION, rkey })
    .catch(() => ({ records: [] }));

  if (existing.records[0]?.value) {
    return {
      status: "alreadyReleased",
      releaseUri: existing.records[0].uri,
    };
  }

  const now = new Date().toISOString();
  const record: ReleaseRecord = {
    releaseId: input.releaseId,
    batchId: input.batchId,
    releasedCredits: input.releasedCredits,
    createdAt: now,
  };

  const receipt = await e.write({
    collection: RELEASE_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });

  return {
    status: "released",
    releaseUri: receipt.uri,
  };
}

export async function recordOffset(
  e: Etzhayyim,
  input: RecordOffsetInput
): Promise<RecordOffsetOutput> {
  // Validation: missing required fields (before checking idempotency)
  if (!input.offsetId || !input.releaseId || !input.offsetCredits || !input.project) {
    return { status: "rejected", error: "missingRequiredFields" };
  }

  const rkey = offsetRkey(input.offsetId);

  // Idempotency check
  const existing = await e
    .read<OffsetRecord>({ collection: OFFSET_COLLECTION, rkey })
    .catch(() => ({ records: [] }));

  if (existing.records[0]?.value) {
    return {
      status: "alreadyRecorded",
      offsetUri: existing.records[0].uri,
    };
  }

  const now = new Date().toISOString();
  const record: OffsetRecord = {
    offsetId: input.offsetId,
    releaseId: input.releaseId,
    offsetCredits: input.offsetCredits,
    project: input.project,
    createdAt: now,
  };

  const receipt = await e.write({
    collection: OFFSET_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });

  return {
    status: "recorded",
    offsetUri: receipt.uri,
  };
}

export async function listOffsets(
  e: Etzhayyim,
  input: ListOffsetsInput = {}
): Promise<ListOffsetsOutput> {
  const limit = Math.min(input.limit ?? 50, 100);
  const resp = await e.read<OffsetRecord>({
    collection: OFFSET_COLLECTION,
    cursor: input.cursor,
    limit,
  });

  const items: OffsetRecord[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.project && v.project !== input.project) return false;
      return true;
    })
    .map((r) => r.value);

  return { items, cursor: resp.cursor };
}
