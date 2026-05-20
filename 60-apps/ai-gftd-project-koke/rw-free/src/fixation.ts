/**
 * koke rw-free — fixation tier (slice 1, 4/4 canonical complete).
 *
 *   fixSignal       — primary fixation (rkey=fixation-{fixationId-slug})
 *   getFixation     — rkey-direct read
 *   listFixations   — cursor + inputKind/agentDid/released filter
 *   releaseCarbon   — mark fixation as released (state transition)
 *
 * Closes koke at canonical 4/4 in one slice (same pattern as ki).
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  fixationDid,
  fixationRkey,
  type FixationRecord,
  type FixationView,
  type FixSignalInput,
  type FixSignalOutput,
  type GetFixationInput,
  type GetFixationOutput,
  type ListFixationsInput,
  type ListFixationsOutput,
  type ReleaseCarbonInput,
  type ReleaseCarbonOutput,
} from "./types.js";

const FIXATION_COLLECTION = "ai.gftd.koke.fixation";

export async function fixSignal(
  e: Etzhayyim,
  input: FixSignalInput
): Promise<FixSignalOutput> {
  if (!input.fixationId || !input.inputKind || !input.rawRef || !input.signalHash) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!/^[a-f0-9]{64}$/i.test(input.signalHash)) {
    return { status: "rejected", error: "invalidSignalHash" };
  }
  const rkey = fixationRkey(input.fixationId);
  const existing = await e
    .read<FixationRecord>({ collection: FIXATION_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      fixationUri: existing.records[0].uri,
      signalHash: existing.records[0].value.signalHash,
      fixationId: input.fixationId,
    };
  }
  const did = fixationDid(input.fixationId);
  const now = new Date().toISOString();
  const record: FixationRecord = {
    did,
    fixationId: input.fixationId,
    inputKind: input.inputKind,
    rawRef: input.rawRef,
    signalHash: input.signalHash.toLowerCase(),
    released: false,
    agentDid: input.agentDid,
    fixedAt: now,
    createdAt: now,
  };
  const receipt = await e.write({
    collection: FIXATION_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "fixed",
    fixationUri: receipt.uri,
    vertexId: did,
    signalHash: input.signalHash.toLowerCase(),
    fixationId: input.fixationId,
  };
}

export async function getFixation(
  e: Etzhayyim,
  input: GetFixationInput
): Promise<GetFixationOutput> {
  if (!input.fixationId) return { error: "missingFixationId" };
  const resp = await e
    .read<FixationRecord>({
      collection: FIXATION_COLLECTION,
      rkey: fixationRkey(input.fixationId),
    })
    .catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  const view: FixationView = {
    ...r.value,
    fixationUri: r.uri,
    vertexId: r.value.did,
  };
  return { fixation: view };
}

export async function listFixations(
  e: Etzhayyim,
  input: ListFixationsInput = {}
): Promise<ListFixationsOutput> {
  const limit = Math.min(input.limit ?? 50, 100);
  const resp = await e.read<FixationRecord>({
    collection: FIXATION_COLLECTION,
    cursor: input.cursor,
    limit,
  });
  const items: FixationView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.inputKind && v.inputKind !== input.inputKind) return false;
      if (input.agentDid && v.agentDid !== input.agentDid) return false;
      if (typeof input.released === "boolean" && v.released !== input.released) {
        return false;
      }
      return true;
    })
    .map((r) => ({
      ...r.value,
      fixationUri: r.uri,
      vertexId: r.value.did,
    }));
  return { items, cursor: resp.cursor, total: items.length };
}

export async function releaseCarbon(
  e: Etzhayyim,
  input: ReleaseCarbonInput
): Promise<ReleaseCarbonOutput> {
  if (!input.fixationId) {
    return { status: "rejected", error: "missingFixationId" };
  }
  const rkey = fixationRkey(input.fixationId);
  const resp = await e
    .read<FixationRecord>({ collection: FIXATION_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  const existing = resp.records[0]?.value;
  if (!existing) return { status: "fixationNotFound" };
  if (existing.released) {
    return {
      status: "alreadyReleased",
      fixationUri: resp.records[0].uri,
      fixationId: input.fixationId,
      releasedAt: existing.releasedAt,
    };
  }
  const now = new Date().toISOString();
  const merged: FixationRecord = {
    ...existing,
    released: true,
    releasedAt: now,
  };
  const receipt = await e.write({
    collection: FIXATION_COLLECTION,
    record: merged as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "released",
    fixationUri: receipt.uri,
    fixationId: input.fixationId,
    releasedAt: now,
  };
}
