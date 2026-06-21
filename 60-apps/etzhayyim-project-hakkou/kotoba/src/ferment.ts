/**
 * hakkou kotoba — ferment tier (slice 1, 2/2 canonical + 1 helper).
 *
 *   startFerment        — enqueue a fermentation job (rkey=ferment-{fermentId-slug})
 *   getFerment          — rkey-direct read
 *   updateFermentStatus — helper: transition status (pending→running→done/failed)
 *
 * Closes hakkou at canonical 2/2 in one slice. State transitions are
 * driven by the LangServer pod (per ADR-2605111200) which writes via
 * updateFermentStatus after each phase of the ferment pipeline.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  fermentDid,
  fermentRkey,
  type FermentRunRecord,
  type FermentRunView,
  type GetFermentInput,
  type GetFermentOutput,
  type StartFermentInput,
  type StartFermentOutput,
  type UpdateFermentStatusInput,
  type UpdateFermentStatusOutput,
} from "./types.js";

const FERMENT_COLLECTION = "com.etzhayyim.hakkou.ferment";

export async function startFerment(
  e: Etzhayyim,
  input: StartFermentInput
): Promise<StartFermentOutput> {
  if (
    !input.fermentId ||
    !input.agentDid ||
    !input.inputKind ||
    !input.inputRef ||
    !input.outputKind
  ) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const rkey = fermentRkey(input.fermentId);
  const existing = await e
    .read<FermentRunRecord>({ collection: FERMENT_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      fermentVertexId: existing.records[0].value.did,
      fermentId: input.fermentId,
      fermentUri: existing.records[0].uri,
    };
  }
  const did = fermentDid(input.fermentId);
  const now = new Date().toISOString();
  const record: FermentRunRecord = {
    did,
    fermentId: input.fermentId,
    agentDid: input.agentDid,
    inputKind: input.inputKind,
    inputRef: input.inputRef,
    outputKind: input.outputKind,
    status: "pending",
    sourceFixationDid: input.sourceFixationDid,
    startedAt: now,
    createdAt: now,
  };
  const receipt = await e.write({
    collection: FERMENT_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "started",
    fermentVertexId: did,
    fermentId: input.fermentId,
    fermentUri: receipt.uri,
  };
}

export async function getFerment(
  e: Etzhayyim,
  input: GetFermentInput
): Promise<GetFermentOutput> {
  if (!input.fermentId) return { error: "missingFermentId" };
  const resp = await e
    .read<FermentRunRecord>({
      collection: FERMENT_COLLECTION,
      rkey: fermentRkey(input.fermentId),
    })
    .catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  const view: FermentRunView = {
    ...r.value,
    fermentUri: r.uri,
    fermentVertexId: r.value.did,
  };
  return { ferment: view };
}

export async function updateFermentStatus(
  e: Etzhayyim,
  input: UpdateFermentStatusInput
): Promise<UpdateFermentStatusOutput> {
  if (!input.fermentId || !input.status) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const rkey = fermentRkey(input.fermentId);
  const resp = await e
    .read<FermentRunRecord>({ collection: FERMENT_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  const existing = resp.records[0]?.value;
  if (!existing) return { status: "fermentNotFound" };
  const now = new Date().toISOString();
  const merged: FermentRunRecord = {
    ...existing,
    status: input.status,
    resultRef: input.resultRef ?? existing.resultRef,
    completedAt: input.status === "done" ? now : existing.completedAt,
    failedAt: input.status === "failed" ? now : existing.failedAt,
    errorReason: input.errorReason ?? existing.errorReason,
  };
  const receipt = await e.write({
    collection: FERMENT_COLLECTION,
    record: merged as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "updated",
    fermentUri: receipt.uri,
    fermentId: input.fermentId,
    newStatus: input.status,
  };
}
