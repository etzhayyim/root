/**
 * houshi kotoba — sporulation system (3/3 canonical lexicons).
 *
 * 3 procedures matching the canonical lexicon surface:
 *   storeSpore  — register spore blob with initial custodian
 *   listSpores  — query spores by custodian DID or origin agent DID
 *   germinate   — revive dormant spore into active kobo agent
 *
 * storeSpore → germinate is the canonical revival flow. listSpores queries
 * the live spore inventory (filtered by ownership/origin).
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  germinateDid,
  germinateRkey,
  sporeDid,
  sporeRkey,
  type GerminateInput,
  type GerminateOutput,
  type GerminateRecord,
  type SporeListInput,
  type SporeListItem,
  type SporeListOutput,
  type SporeRecord,
  type StoreSporeInput,
  type StoreSporeOutput,
} from "./types.js";

const SPORE_COLLECTION = "com.etzhayyim.houshi.spore";
const GERMINATE_COLLECTION = "com.etzhayyim.houshi.germinate";

const PAGE_LIMIT = 100;

/**
 * Stage 1: storeSpore. Register a dormant spore blob in custody.
 * The spore is initially held by one custodian but references the
 * full custody chain (quorumN participants required to germinate).
 */
export async function storeSpore(
  e: Etzhayyim,
  input: StoreSporeInput
): Promise<StoreSporeOutput> {
  if (!input.sporeVertexId || !input.custodianDid || !input.originAgentDid || !input.blobCbor) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (input.quorumN < 1) {
    return { status: "rejected", error: "quorumNMinimumOne" };
  }
  const rkey = sporeRkey(input.sporeVertexId);
  const existing = await e
    .read<SporeRecord>({ collection: SPORE_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      sporeUri: existing.records[0].uri,
      sporeVertexId: input.sporeVertexId,
      did: existing.records[0].value.did,
    };
  }
  const now = new Date().toISOString();
  const record: SporeRecord = {
    did: sporeDid(input.sporeVertexId),
    sporeVertexId: input.sporeVertexId,
    originAgentDid: input.originAgentDid,
    quorumN: input.quorumN,
    custodyChain: [input.custodianDid],
    blobCbor: input.blobCbor,
    revivalKeyHint: input.revivalKeyHint,
    createdAt: now,
  };
  const receipt = await e.write({
    collection: SPORE_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "registered",
    sporeUri: receipt.uri,
    sporeVertexId: input.sporeVertexId,
    did: record.did,
  };
}

/**
 * Stage 2: listSpores. Query the inventory of live spore records
 * filtered by custodian DID or origin agent DID. Supports pagination.
 * By default excludes already-germinated spores; includeGerminated=true
 * returns all regardless of germination status.
 */
export async function listSpores(
  e: Etzhayyim,
  input: SporeListInput
): Promise<SporeListOutput> {
  const offset = input.offset ?? 0;
  const limit = Math.min(input.limit ?? 50, PAGE_LIMIT);
  const includeGerminated = input.includeGerminated ?? false;

  let cursor: string | undefined;
  let scanned = 0;
  const matching: SporeListItem[] = [];
  const MAX_SCAN = 5_000;

  while (scanned < MAX_SCAN) {
    const page = await e.read<SporeRecord>({
      collection: SPORE_COLLECTION,
      cursor,
      limit: PAGE_LIMIT,
    });

    for (const r of page.records) {
      const rec = r.value;
      const matchesCustodian =
        !input.custodianDid || rec.custodyChain.includes(input.custodianDid);
      const matchesOrigin =
        !input.originAgentDid || rec.originAgentDid === input.originAgentDid;
      const isGerminated = !!rec.germinatedAt;

      if (
        matchesCustodian &&
        matchesOrigin &&
        (includeGerminated || !isGerminated)
      ) {
        matching.push({
          vertexId: rec.sporeVertexId,
          originAgentDid: rec.originAgentDid,
          quorumN: rec.quorumN,
          custodyCount: rec.custodyChain.length,
          germinatedAt: rec.germinatedAt,
          createdAt: rec.createdAt,
        });
      }
    }

    scanned += page.records.length;
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }

  const total = matching.length;
  const sliced = matching.slice(offset, offset + limit);

  return {
    spores: sliced,
    total,
    offset,
    limit,
  };
}

/**
 * Stage 3: germinate. Revive a dormant spore into an active kobo agent.
 * Requires matching revivalKey (validated client-side against revivalKeyHint).
 * Records the germination timestamp and creates a GerminateRecord for audit.
 *
 * In production, revivalKey validation and kobo agent spawn are pod-side
 * (per ADR-2605111200) — this function records the state transition.
 */
export async function germinate(
  e: Etzhayyim,
  input: GerminateInput
): Promise<GerminateOutput> {
  if (!input.sporeVertexId || !input.revivalKey || !input.newAgentDid) {
    return { status: "rejected", error: "missingRequiredFields" };
  }

  const sporeRk = sporeRkey(input.sporeVertexId);
  const sporeResp = await e
    .read<SporeRecord>({ collection: SPORE_COLLECTION, rkey: sporeRk })
    .catch(() => ({ records: [] }));

  if (!sporeResp.records[0]?.value) {
    return { status: "sporeNotFound" };
  }

  const spore = sporeResp.records[0].value;
  if (spore.germinatedAt) {
    return {
      status: "alreadyGerminated",
      agentVertexId: `kobo-${spore.sporeVertexId}`,
      agentDid: input.newAgentDid,
      germinatedAt: spore.germinatedAt,
    };
  }

  const gRkey = germinateRkey(input.sporeVertexId);
  const gExisting = await e
    .read<GerminateRecord>({ collection: GERMINATE_COLLECTION, rkey: gRkey })
    .catch(() => ({ records: [] }));
  if (gExisting.records[0]?.value) {
    return {
      status: "alreadyGerminated",
      agentVertexId: `kobo-${input.sporeVertexId}`,
      agentDid: gExisting.records[0].value.newAgentDid,
      germinatedAt: gExisting.records[0].value.germinatedAt,
    };
  }

  const now = new Date().toISOString();
  const prionsRestored = Math.floor(spore.blobCbor.length / 128);

  const germRecord: GerminateRecord = {
    did: germinateDid(input.sporeVertexId),
    sporeVertexId: input.sporeVertexId,
    newAgentDid: input.newAgentDid,
    prionsRestored,
    germinatedAt: now,
    createdAt: now,
  };

  const receipt = await e.write({
    collection: GERMINATE_COLLECTION,
    record: germRecord as unknown as Record<string, unknown>,
    rkey: gRkey,
  });

  // Stamp germinatedAt on the source spore so listSpores can filter it.
  await e.write({
    collection: SPORE_COLLECTION,
    record: { ...spore, germinatedAt: now } as unknown as Record<string, unknown>,
    rkey: sporeRk,
  });

  return {
    status: "germinated",
    agentVertexId: `kobo-${input.sporeVertexId}`,
    agentDid: input.newAgentDid,
    prionsRestored,
    germinatedAt: now,
  };
}
