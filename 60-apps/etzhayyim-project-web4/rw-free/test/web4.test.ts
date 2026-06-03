import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerModelManifest,
  listModelManifests,
  registerExpert,
  getExpert,
  listExperts,
  recordMarketStat,
  listMarketStats,
  registerProvider,
  listProviders,
  getProvider,
  submitInference,
  listJobs,
  getJob,
  postLedgerEntry,
  listLedger,
  accountBalance,
  coverage,
} from "../src/index.js";

const OWNER = "did:web:web4.etzhayyim.com";
const MODEL = "etzhayyim/etzhayyim-distributed-moe-260222";

describe("web4 rw-free (browser-MoE marketplace E2E split)", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: OWNER });
  });

  describe("modelManifest + expert (PLAINTEXT public catalog, FK)", () => {
    it("registers manifests, dedups, validates, lists/filters by quant", async () => {
      expect((await registerModelManifest(e, { modelId: MODEL, expertSetCount: 32, quant: "int4", totalSizeBytes: 1056 })).status).toBe("registered");
      expect((await registerModelManifest(e, { modelId: MODEL, expertSetCount: 32, quant: "int4", totalSizeBytes: 1056 })).status).toBe("alreadyExists");
      expect((await registerModelManifest(e, { modelId: "x", expertSetCount: -1, quant: "int4", totalSizeBytes: 1 })).status).toBe("rejected");
      await registerModelManifest(e, { modelId: "etzhayyim/ti2v", expertSetCount: 32, quant: "int8", totalSizeBytes: 2000 });
      expect((await listModelManifests(e)).total).toBe(2);
      expect((await listModelManifests(e, { quant: "int4" })).total).toBe(1);
    });

    it("registers experts, dedups, gets, lists/filters by model", async () => {
      await registerModelManifest(e, { modelId: MODEL, expertSetCount: 32, quant: "int4", totalSizeBytes: 1056 });
      const ok = await registerExpert(e, { expertKey: "e0", modelId: MODEL, expertId: 0, quant: "int4", sizeBytes: 33, blobPath: "models/qwen3-30b-a3b/experts/set-000.bin" });
      expect(ok.status).toBe("registered");
      expect((await registerExpert(e, { expertKey: "e0", modelId: MODEL, expertId: 0, quant: "int4", sizeBytes: 33, blobPath: "x" })).status).toBe("alreadyExists");
      await registerExpert(e, { expertKey: "e1", modelId: MODEL, expertId: 1, quant: "int4", sizeBytes: 33, blobPath: "models/qwen3-30b-a3b/experts/set-001.bin" });
      expect((await getExpert(e, { expertKey: "e0" })).expert?.expertId).toBe(0);
      expect((await getExpert(e, { expertKey: "none" })).error).toBe("notFound");
      expect((await listExperts(e, { modelId: MODEL })).total).toBe(2);
    });

    it("rejects expert with unknown modelId (FK via exists())", async () => {
      const r = await registerExpert(e, { expertKey: "orphan", modelId: "ghost/model", expertId: 0, quant: "int4", sizeBytes: 33, blobPath: "x" });
      expect(r.status).toBe("rejected");
      expect(r.error).toBe("unknownModelId");
    });
  });

  describe("marketStat (PLAINTEXT aggregate snapshot, DID-free)", () => {
    it("records, dedups, validates decimal price, lists", async () => {
      expect((await recordMarketStat(e, { snapshotId: "s1", onlineProviders: 12, activeJobs: 3, medianExecPriceCc: "0.25" })).status).toBe("recorded");
      expect((await recordMarketStat(e, { snapshotId: "s1", onlineProviders: 12, activeJobs: 3, medianExecPriceCc: "0.25" })).status).toBe("alreadyExists");
      expect((await recordMarketStat(e, { snapshotId: "sX", onlineProviders: 1, activeJobs: 1, medianExecPriceCc: "abc" })).status).toBe("rejected");
      await recordMarketStat(e, { snapshotId: "s2", onlineProviders: 8, activeJobs: 1, medianExecPriceCc: "0.30" });
      expect((await listMarketStats(e)).total).toBe(2);
    });
  });

  describe("providerRegistration (E2E-ENCRYPTED PII + commercial terms)", () => {
    it("seals via encryptedWrite, round-trips, validates permille reputation", async () => {
      const ok = await registerProvider(e, { providerKey: "p1", providerDid: "did:web:alice", deviceFingerprint: "wgpu-abc", assignedExpertId: 0, availabilityFeeCc: "0.01", executionFeeCc: "0.20", reputationPermille: 720 });
      expect(ok.status).toBe("registered");
      expect(ok.keyId).toBeTruthy();
      expect((await registerProvider(e, { providerKey: "pX", providerDid: "d", deviceFingerprint: "f", assignedExpertId: 0, availabilityFeeCc: "0.01", executionFeeCc: "0.20", reputationPermille: 2000 })).status).toBe("rejected"); // permille>1000
      expect((await registerProvider(e, { providerKey: "pY", providerDid: "d", deviceFingerprint: "f", assignedExpertId: 0, availabilityFeeCc: "x", executionFeeCc: "0.20" })).status).toBe("rejected"); // bad fee
      const got = await getProvider(e, { providerKey: "p1" });
      expect(got.provider?.providerDid).toBe("did:web:alice");
      expect(got.provider?.reputationPermille).toBe(720);
      await registerProvider(e, { providerKey: "p2", providerDid: "did:web:bob", deviceFingerprint: "wgpu-def", assignedExpertId: 1, availabilityFeeCc: "0.02", executionFeeCc: "0.25" });
      expect((await listProviders(e)).total).toBe(2);
      expect((await listProviders(e, { assignedExpertId: 1 })).total).toBe(1);
    });

    it("enforces read-cap: a non-recipient DID cannot decrypt provider records", async () => {
      await registerProvider(e, { providerKey: "p1", providerDid: "did:web:alice", deviceFingerprint: "wgpu-abc", assignedExpertId: 0, availabilityFeeCc: "0.01", executionFeeCc: "0.20" });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listProviders(outsider)).total).toBe(0);
    });
  });

  describe("inferenceJob (E2E-ENCRYPTED private request content)", () => {
    it("seals job, round-trips, validates latency, gets, lists/filters by status", async () => {
      const ok = await submitInference(e, { jobId: "j1", requesterDid: "did:web:carol", modelId: MODEL, prompt: "hello", status: "queued" });
      expect(ok.status).toBe("submitted");
      expect((await submitInference(e, { jobId: "jX", requesterDid: "d", modelId: MODEL, prompt: "p", latencyMs: -5 })).status).toBe("rejected");
      await submitInference(e, { jobId: "j2", requesterDid: "did:web:dave", modelId: MODEL, prompt: "world", result: "ok", status: "done", latencyMs: 850 });
      const got = await getJob(e, { jobId: "j2" });
      expect(got.job?.result).toBe("ok");
      expect(got.job?.latencyMs).toBe(850);
      expect((await listJobs(e)).total).toBe(2);
      expect((await listJobs(e, { status: "done" })).total).toBe(1);
    });

    it("read-cap: requester content is invisible to a non-recipient", async () => {
      await submitInference(e, { jobId: "j1", requesterDid: "did:web:carol", modelId: MODEL, prompt: "secret" });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listJobs(outsider)).total).toBe(0);
    });
  });

  describe("ccLedgerEntry (E2E-ENCRYPTED ledger / tx-history + balance)", () => {
    it("posts entries, validates direction + decimal, lists/filters, derives balance", async () => {
      const acct = "did:web:carol";
      expect((await postLedgerEntry(e, { entryId: "L1", accountDid: acct, direction: "credit", amountCc: "100.00", balanceAfterCc: "100.00", reason: "purchase" })).status).toBe("posted");
      expect((await postLedgerEntry(e, { entryId: "LX", accountDid: acct, direction: "sideways", amountCc: "1", balanceAfterCc: "1", reason: "x" })).status).toBe("rejected");
      expect((await postLedgerEntry(e, { entryId: "LY", accountDid: acct, direction: "debit", amountCc: "nope", balanceAfterCc: "1", reason: "x" })).status).toBe("rejected");
      await postLedgerEntry(e, { entryId: "L2", accountDid: acct, direction: "debit", amountCc: "0.20", balanceAfterCc: "99.80", reason: "execution", refKey: "j1" });
      await postLedgerEntry(e, { entryId: "L3", accountDid: "did:web:dave", direction: "credit", amountCc: "50.00", balanceAfterCc: "50.00", reason: "purchase" });
      expect((await listLedger(e, { accountDid: acct })).total).toBe(2);
      expect((await listLedger(e, { accountDid: acct, direction: "debit" })).total).toBe(1);
      const bal = await accountBalance(e, { accountDid: acct });
      expect(bal.balanceCc).toBe("99.80");
      expect(bal.entryCount).toBe(2);
      expect((await accountBalance(e, { accountDid: "did:web:nobody" })).entryCount).toBe(0);
    });

    it("read-cap: ledger entries are invisible to a non-recipient", async () => {
      await postLedgerEntry(e, { entryId: "L1", accountDid: "did:web:carol", direction: "credit", amountCc: "100.00", balanceAfterCc: "100.00", reason: "purchase" });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listLedger(outsider)).total).toBe(0);
    });
  });

  describe("coverage rollup", () => {
    it("counts plaintext catalog + E2E provider/job/ledger", async () => {
      await registerModelManifest(e, { modelId: MODEL, expertSetCount: 32, quant: "int4", totalSizeBytes: 1056 });
      await registerExpert(e, { expertKey: "e0", modelId: MODEL, expertId: 0, quant: "int4", sizeBytes: 33, blobPath: "a" });
      await registerExpert(e, { expertKey: "e1", modelId: MODEL, expertId: 1, quant: "int4", sizeBytes: 33, blobPath: "b" });
      await recordMarketStat(e, { snapshotId: "s1", onlineProviders: 2, activeJobs: 1, medianExecPriceCc: "0.25" });
      await registerProvider(e, { providerKey: "p1", providerDid: "did:web:alice", deviceFingerprint: "f", assignedExpertId: 0, availabilityFeeCc: "0.01", executionFeeCc: "0.20" });
      await submitInference(e, { jobId: "j1", requesterDid: "did:web:carol", modelId: MODEL, prompt: "p" });
      await postLedgerEntry(e, { entryId: "L1", accountDid: "did:web:carol", direction: "credit", amountCc: "100.00", balanceAfterCc: "100.00", reason: "purchase" });
      const cov = await coverage(e);
      expect(cov.modelManifestCount).toBe(1);
      expect(cov.expertCount).toBe(2);
      expect(cov.marketStatCount).toBe(1);
      expect(cov.providerRegistrationCount).toBe(1);
      expect(cov.inferenceJobCount).toBe(1);
      expect(cov.ccLedgerEntryCount).toBe(1);
      expect(cov.expertsByModel?.[MODEL]).toBe(2);
    });
  });
});
