/**
 * web4 kotoba — registry.
 *
 * Plaintext path (modelManifest, expert, marketStat): sdk.write / sdk.read —
 * public model catalog + aggregate market snapshots. FK expert.modelId →
 * modelManifest via exists() (read + check; mock has no exists()).
 *
 * E2E path (providerRegistration, inferenceJob, ccLedgerEntry): sdk.encryptedWrite /
 * sdk.encryptedRead — provider PII + commercial terms, private request content,
 * and Compute Credit ledger movements sealed in the kotoba envelope
 * (ADR-2605181100), read-cap = owner DID + explicit recipients.
 *
 * The GPU/LLM inference EXECUTION, the fiat on-ramp settlement for CC purchases,
 * and the 100B-scale S3 expert-weight archive stay etzhayyim (consumed via
 * consent-capability); only their catalog metadata + ledger DATA migrate here.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  CC_LEDGER_ENTRY_INNER_TYPE,
  EXPERT_COLLECTION,
  INFERENCE_JOB_INNER_TYPE,
  MARKET_STAT_COLLECTION,
  MODEL_MANIFEST_COLLECTION,
  PROVIDER_REGISTRATION_INNER_TYPE,
  isDecimalString,
  isPermille,
  isUint,
  manifestDidFor,
  slugRkey,
  type AccountBalanceInput,
  type AccountBalanceOutput,
  type CcLedgerEntryBody,
  type CcLedgerEntryView,
  type CoverageInput,
  type CoverageOutput,
  type ExpertRecord,
  type ExpertView,
  type GetExpertInput,
  type GetExpertOutput,
  type GetJobInput,
  type GetJobOutput,
  type GetProviderInput,
  type GetProviderOutput,
  type InferenceJobBody,
  type InferenceJobView,
  type ListExpertsInput,
  type ListExpertsOutput,
  type ListJobsInput,
  type ListJobsOutput,
  type ListLedgerInput,
  type ListLedgerOutput,
  type ListMarketStatsInput,
  type ListMarketStatsOutput,
  type ListModelManifestsInput,
  type ListModelManifestsOutput,
  type ListProvidersInput,
  type ListProvidersOutput,
  type MarketStatRecord,
  type MarketStatView,
  type ModelManifestRecord,
  type ModelManifestView,
  type PostLedgerEntryInput,
  type PostLedgerEntryOutput,
  type ProviderRegistrationBody,
  type ProviderRegistrationView,
  type RecordMarketStatInput,
  type RecordMarketStatOutput,
  type RegisterExpertInput,
  type RegisterExpertOutput,
  type RegisterModelManifestInput,
  type RegisterModelManifestOutput,
  type RegisterProviderInput,
  type RegisterProviderOutput,
  type SubmitInferenceInput,
  type SubmitInferenceOutput,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

// ─── Model manifest (PLAINTEXT) ─────────────────────────────────────

export async function registerModelManifest(e: Etzhayyim, input: RegisterModelManifestInput): Promise<RegisterModelManifestOutput> {
  if (!input.modelId || !input.quant) return { status: "rejected", error: "missingRequiredFields" };
  if (!isUint(input.expertSetCount) || !isUint(input.totalSizeBytes)) return { status: "rejected", error: "invalidSizeOrCount" };
  const rkey = slugRkey("model", input.modelId);
  const existing = await e.read<ModelManifestRecord>({ collection: MODEL_MANIFEST_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", manifestUri: existing.records[0].uri, did: existing.records[0].value.did, modelId: input.modelId };
  }
  const now = new Date().toISOString();
  const did = manifestDidFor(input.modelId);
  const record: ModelManifestRecord = {
    did,
    modelId: input.modelId,
    expertSetCount: input.expertSetCount,
    quant: input.quant,
    totalSizeBytes: input.totalSizeBytes,
    publishedAt: input.publishedAt ?? now,
    createdAt: now,
  };
  const receipt = await e.write({ collection: MODEL_MANIFEST_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", manifestUri: receipt.uri, did, modelId: input.modelId };
}

export async function listModelManifests(e: Etzhayyim, input: ListModelManifestsInput = {}): Promise<ListModelManifestsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ModelManifestRecord>({ collection: MODEL_MANIFEST_COLLECTION, cursor: input.cursor, limit });
  const items: ModelManifestView[] = resp.records
    .filter((r) => !input.quant || r.value.quant === input.quant)
    .map((r) => ({ ...r.value, manifestUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Plaintext FK helper (exists via read; mock has no exists()) ─────

async function modelManifestExists(e: Etzhayyim, modelId: string): Promise<boolean> {
  const rkey = slugRkey("model", modelId);
  const r = await e.read<ModelManifestRecord>({ collection: MODEL_MANIFEST_COLLECTION, rkey }).catch(() => ({ records: [] }));
  return Boolean(r.records[0]?.value);
}

// ─── Expert (PLAINTEXT, FK → modelManifest) ─────────────────────────

export async function registerExpert(e: Etzhayyim, input: RegisterExpertInput): Promise<RegisterExpertOutput> {
  if (!input.expertKey || !input.modelId || !input.quant || !input.blobPath) return { status: "rejected", error: "missingRequiredFields" };
  if (!isUint(input.expertId) || !isUint(input.sizeBytes)) return { status: "rejected", error: "invalidExpertIdOrSize" };
  if (!(await modelManifestExists(e, input.modelId))) return { status: "rejected", error: "unknownModelId" };
  const rkey = slugRkey("expert", input.expertKey);
  const existing = await e.read<ExpertRecord>({ collection: EXPERT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", expertUri: existing.records[0].uri, did: existing.records[0].value.did, expertKey: input.expertKey };
  }
  const now = new Date().toISOString();
  const did = `${manifestDidFor(input.modelId)}:expert:${input.expertId}`;
  const record: ExpertRecord = {
    did,
    expertKey: input.expertKey,
    modelId: input.modelId,
    expertId: input.expertId,
    quant: input.quant,
    sizeBytes: input.sizeBytes,
    blobPath: input.blobPath,
    createdAt: now,
  };
  const receipt = await e.write({ collection: EXPERT_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", expertUri: receipt.uri, did, expertKey: input.expertKey };
}

export async function getExpert(e: Etzhayyim, input: GetExpertInput): Promise<GetExpertOutput> {
  if (!input.expertKey) return { error: "invalidExpertKey" };
  const rkey = slugRkey("expert", input.expertKey);
  const r = await e.read<ExpertRecord>({ collection: EXPERT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  const hit = r.records[0];
  if (!hit?.value) return { error: "notFound" };
  return { expert: { ...hit.value, expertUri: hit.uri } };
}

export async function listExperts(e: Etzhayyim, input: ListExpertsInput = {}): Promise<ListExpertsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ExpertRecord>({ collection: EXPERT_COLLECTION, cursor: input.cursor, limit });
  const items: ExpertView[] = resp.records
    .filter((r) => !input.modelId || r.value.modelId === input.modelId)
    .map((r) => ({ ...r.value, expertUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Market stat (PLAINTEXT, aggregate) ─────────────────────────────

export async function recordMarketStat(e: Etzhayyim, input: RecordMarketStatInput): Promise<RecordMarketStatOutput> {
  if (!input.snapshotId) return { status: "rejected", error: "missingRequiredFields" };
  if (!isUint(input.onlineProviders) || !isUint(input.activeJobs)) return { status: "rejected", error: "invalidCounts" };
  if (!isDecimalString(input.medianExecPriceCc)) return { status: "rejected", error: "invalidMedianExecPriceCc" };
  const rkey = slugRkey("stat", input.snapshotId);
  const existing = await e.read<MarketStatRecord>({ collection: MARKET_STAT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", snapshotUri: existing.records[0].uri, did: existing.records[0].value.did, snapshotId: input.snapshotId };
  }
  const now = new Date().toISOString();
  const did = `${manifestDidFor("market")}:snapshot:${input.snapshotId.toLowerCase()}`;
  const record: MarketStatRecord = {
    did,
    snapshotId: input.snapshotId,
    onlineProviders: input.onlineProviders,
    activeJobs: input.activeJobs,
    medianExecPriceCc: input.medianExecPriceCc,
    capturedAt: input.capturedAt ?? now,
    createdAt: now,
  };
  const receipt = await e.write({ collection: MARKET_STAT_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", snapshotUri: receipt.uri, did, snapshotId: input.snapshotId };
}

export async function listMarketStats(e: Etzhayyim, input: ListMarketStatsInput = {}): Promise<ListMarketStatsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<MarketStatRecord>({ collection: MARKET_STAT_COLLECTION, cursor: input.cursor, limit });
  const items: MarketStatView[] = resp.records.map((r) => ({ ...r.value, snapshotUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Provider registration (E2E, PII + commercial terms) ────────────

export async function registerProvider(e: Etzhayyim, input: RegisterProviderInput): Promise<RegisterProviderOutput> {
  if (!input.providerKey || !input.providerDid || !input.deviceFingerprint) return { status: "rejected", error: "missingRequiredFields" };
  if (!isUint(input.assignedExpertId)) return { status: "rejected", error: "invalidAssignedExpertId" };
  if (!isDecimalString(input.availabilityFeeCc) || !isDecimalString(input.executionFeeCc)) return { status: "rejected", error: "invalidFeeCc" };
  const reputationPermille = input.reputationPermille ?? 500;
  if (!isPermille(reputationPermille)) return { status: "rejected", error: "invalidReputationPermille" };
  const body: ProviderRegistrationBody = {
    providerKey: input.providerKey,
    providerDid: input.providerDid,
    deviceFingerprint: input.deviceFingerprint,
    assignedExpertId: input.assignedExpertId,
    availabilityFeeCc: input.availabilityFeeCc,
    executionFeeCc: input.executionFeeCc,
    reputationPermille,
    registeredAt: input.registeredAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: PROVIDER_REGISTRATION_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: slugRkey("provider", input.providerKey),
  });
  return { status: "registered", uri: receipt.uri, keyId: receipt.keyId, providerKey: input.providerKey };
}

async function scanProviders(e: Etzhayyim, maxScan: number): Promise<ProviderRegistrationView[]> {
  const out: ProviderRegistrationView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<ProviderRegistrationBody>({ innerType: PROVIDER_REGISTRATION_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listProviders(e: Etzhayyim, input: ListProvidersInput = {}): Promise<ListProvidersOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanProviders(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((p) => input.assignedExpertId === undefined || p.assignedExpertId === input.assignedExpertId);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getProvider(e: Etzhayyim, input: GetProviderInput): Promise<GetProviderOutput> {
  if (!input.providerKey) return { error: "invalidProviderKey" };
  const all = await scanProviders(e, DEFAULT_MAX_SCAN);
  const found = all.find((p) => p.providerKey === input.providerKey);
  if (!found) return { error: "notFound" };
  return { provider: found };
}

// ─── Inference job (E2E, private request content) ───────────────────

export async function submitInference(e: Etzhayyim, input: SubmitInferenceInput): Promise<SubmitInferenceOutput> {
  if (!input.jobId || !input.requesterDid || !input.modelId || !input.prompt) return { status: "rejected", error: "missingRequiredFields" };
  if (input.latencyMs !== undefined && !isUint(input.latencyMs)) return { status: "rejected", error: "invalidLatencyMs" };
  const body: InferenceJobBody = {
    jobId: input.jobId,
    requesterDid: input.requesterDid,
    modelId: input.modelId,
    prompt: input.prompt,
    result: input.result,
    assignedProviderKey: input.assignedProviderKey,
    status: input.status ?? "queued",
    latencyMs: input.latencyMs,
    submittedAt: input.submittedAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: INFERENCE_JOB_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: slugRkey("job", input.jobId),
  });
  return { status: "submitted", uri: receipt.uri, keyId: receipt.keyId, jobId: input.jobId };
}

async function scanJobs(e: Etzhayyim, maxScan: number): Promise<InferenceJobView[]> {
  const out: InferenceJobView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<InferenceJobBody>({ innerType: INFERENCE_JOB_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listJobs(e: Etzhayyim, input: ListJobsInput = {}): Promise<ListJobsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanJobs(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((j) => !input.status || j.status === input.status);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getJob(e: Etzhayyim, input: GetJobInput): Promise<GetJobOutput> {
  if (!input.jobId) return { error: "invalidJobId" };
  const all = await scanJobs(e, DEFAULT_MAX_SCAN);
  const found = all.find((j) => j.jobId === input.jobId);
  if (!found) return { error: "notFound" };
  return { job: found };
}

// ─── CC ledger entry (E2E, ledger movement / tx-history) ────────────

export async function postLedgerEntry(e: Etzhayyim, input: PostLedgerEntryInput): Promise<PostLedgerEntryOutput> {
  if (!input.entryId || !input.accountDid || !input.reason) return { status: "rejected", error: "missingRequiredFields" };
  if (input.direction !== "credit" && input.direction !== "debit") return { status: "rejected", error: "invalidDirection" };
  if (!isDecimalString(input.amountCc) || !isDecimalString(input.balanceAfterCc)) return { status: "rejected", error: "invalidAmountCc" };
  const body: CcLedgerEntryBody = {
    entryId: input.entryId,
    accountDid: input.accountDid,
    direction: input.direction,
    amountCc: input.amountCc,
    balanceAfterCc: input.balanceAfterCc,
    reason: input.reason,
    refKey: input.refKey,
    postedAt: input.postedAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: CC_LEDGER_ENTRY_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: slugRkey("ledger", input.entryId),
  });
  return { status: "posted", uri: receipt.uri, keyId: receipt.keyId, entryId: input.entryId };
}

async function scanLedger(e: Etzhayyim, maxScan: number): Promise<CcLedgerEntryView[]> {
  const out: CcLedgerEntryView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<CcLedgerEntryBody>({ innerType: CC_LEDGER_ENTRY_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listLedger(e: Etzhayyim, input: ListLedgerInput = {}): Promise<ListLedgerOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanLedger(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter(
    (l) => (!input.accountDid || l.accountDid === input.accountDid) && (!input.direction || l.direction === input.direction),
  );
  return { items: filtered.slice(0, limit), total: filtered.length };
}

/**
 * Derive an account balance from the E2E ledger: latest posted balanceAfterCc
 * for the account (tx-history → balance, owner-scoped). The fiat on-ramp that
 * funds purchases stays etzhayyim; only the ledger DATA lives here.
 */
export async function accountBalance(e: Etzhayyim, input: AccountBalanceInput): Promise<AccountBalanceOutput> {
  if (!input.accountDid) return { accountDid: "", entryCount: 0, error: "invalidAccountDid" };
  const all = await scanLedger(e, DEFAULT_MAX_SCAN);
  const entries = all.filter((l) => l.accountDid === input.accountDid);
  if (entries.length === 0) return { accountDid: input.accountDid, entryCount: 0 };
  // scanLedger preserves insertion order; the last entry holds the latest balance.
  const latest = entries[entries.length - 1];
  return { accountDid: input.accountDid, balanceCc: latest.balanceAfterCc, entryCount: entries.length };
}

// ─── Coverage rollup (plaintext + E2E countAll) ─────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);

  const expertsByModel: Record<string, number> = {};

  const countPlain = async (collection: string, onRow?: (v: ExpertRecord) => void): Promise<number> => {
    let total = 0;
    let cursor: string | undefined;
    while (total < maxScan) {
      const page = await e.read<ExpertRecord>({ collection, cursor, limit: PAGE_LIMIT });
      if (onRow) for (const r of page.records) onRow(r.value);
      total += page.records.length;
      if (!page.cursor || page.records.length < PAGE_LIMIT) break;
      cursor = page.cursor;
    }
    return total;
  };

  const modelManifestCount = await countPlain(MODEL_MANIFEST_COLLECTION);
  const expertCount = await countPlain(EXPERT_COLLECTION, (v) => {
    expertsByModel[v.modelId] = (expertsByModel[v.modelId] ?? 0) + 1;
  });
  const marketStatCount = await countPlain(MARKET_STAT_COLLECTION);

  const providerRegistrationCount = (await scanProviders(e, maxScan)).length;
  const inferenceJobCount = (await scanJobs(e, maxScan)).length;
  const ccLedgerEntryCount = (await scanLedger(e, maxScan)).length;

  return {
    modelManifestCount,
    expertCount,
    marketStatCount,
    providerRegistrationCount,
    inferenceJobCount,
    ccLedgerEntryCount,
    expertsByModel,
    truncated:
      modelManifestCount >= maxScan ||
      expertCount >= maxScan ||
      marketStatCount >= maxScan ||
      providerRegistrationCount >= maxScan ||
      inferenceJobCount >= maxScan ||
      ccLedgerEntryCount >= maxScan,
  };
}
