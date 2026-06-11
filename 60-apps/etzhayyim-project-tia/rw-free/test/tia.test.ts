import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerPlatform,
  getPlatform,
  listPlatforms,
  registerAccount,
  listAccounts,
  getAccount,
  recordDetection,
  listDetections,
  coverage,
} from "../src/index.js";

const OWNER = "did:web:tia.etzhayyim.com";

describe("tia rw-free (kotoba-E2E split)", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: OWNER });
  });

  describe("protectedPlatform (PLAINTEXT public catalog)", () => {
    it("registers, dedups, validates, lists/filters", async () => {
      expect((await registerPlatform(e, { platformType: "x", displayName: "X (Twitter)", seekUrl: "https://x.com/search" })).status).toBe("registered");
      expect((await registerPlatform(e, { platformType: "x", displayName: "X (Twitter)", seekUrl: "https://x.com/search" })).status).toBe("alreadyExists");
      expect((await registerPlatform(e, { platformType: "bad", displayName: "Bad", seekUrl: "ftp://nope" })).status).toBe("rejected");
      await registerPlatform(e, { platformType: "linkedin", displayName: "LinkedIn", seekUrl: "https://linkedin.com/search" });
      expect((await listPlatforms(e)).total).toBe(2);
      expect((await listPlatforms(e, { platformType: "x" })).total).toBe(1);
    });

    it("gets a single platform by type", async () => {
      await registerPlatform(e, { platformType: "instagram", displayName: "Instagram", seekUrl: "https://instagram.com/s" });
      const got = await getPlatform(e, { platformType: "instagram" });
      expect(got.platform?.displayName).toBe("Instagram");
      expect((await getPlatform(e, { platformType: "missing" })).error).toBe("notFound");
    });
  });

  describe("protectedAccount (E2E-ENCRYPTED PII)", () => {
    it("seals via encryptedWrite, round-trips via encryptedRead, validates", async () => {
      const ok = await registerAccount(e, {
        accountId: "a1",
        ownerDid: OWNER,
        platformType: "x",
        accountName: "Alice Example",
        userId: "@alice",
        accountUrl: "https://x.com/alice",
      });
      expect(ok.status).toBe("registered");
      expect(ok.keyId).toBeTruthy();
      // invalid account URL → rejected
      expect((await registerAccount(e, { accountId: "aX", ownerDid: OWNER, platformType: "x", accountName: "n", userId: "u", accountUrl: "javascript:1" })).status).toBe("rejected");
      // missing required field → rejected
      expect((await registerAccount(e, { accountId: "aY", ownerDid: OWNER, platformType: "x", accountName: "", userId: "u" })).status).toBe("rejected");
      const got = await getAccount(e, { accountId: "a1" });
      expect(got.account?.accountName).toBe("Alice Example");
      expect(got.account?.userId).toBe("@alice");
      await registerAccount(e, { accountId: "a2", ownerDid: OWNER, platformType: "linkedin", accountName: "Bob", userId: "bob" });
      expect((await listAccounts(e)).total).toBe(2);
      expect((await listAccounts(e, { platformType: "x" })).total).toBe(1);
    });

    it("enforces read-cap: a non-recipient DID cannot decrypt accounts", async () => {
      await registerAccount(e, { accountId: "a1", ownerDid: OWNER, platformType: "x", accountName: "Alice", userId: "@alice" });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listAccounts(outsider)).total).toBe(0);
    });

    it("grants read-cap to an explicit recipient", async () => {
      const partner = "did:web:partner.example";
      const r = await registerAccount(e, { accountId: "a1", ownerDid: OWNER, platformType: "x", accountName: "Alice", userId: "@alice", recipients: [partner] });
      expect(r.status).toBe("registered");
      expect((await listAccounts(e)).total).toBe(1);
    });
  });

  describe("detectionResult (E2E-ENCRYPTED threat intel)", () => {
    it("seals findings, round-trips, validates score as integer 0-100, FK-filters", async () => {
      const ok = await recordDetection(e, { detectionId: "d1", internetAccountId: "a1", platformType: "x", similarityScore: 92, suspectUrl: "https://x.com/fake-alice" });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();
      // score out of 0-100 → rejected (no float)
      expect((await recordDetection(e, { detectionId: "dX", internetAccountId: "a1", platformType: "x", similarityScore: 150 })).status).toBe("rejected");
      // bad suspect URL → rejected
      expect((await recordDetection(e, { detectionId: "dY", internetAccountId: "a1", platformType: "x", similarityScore: 50, suspectUrl: "not-a-url" })).status).toBe("rejected");
      await recordDetection(e, { detectionId: "d2", internetAccountId: "a2", platformType: "linkedin", similarityScore: 30 });
      expect((await listDetections(e)).total).toBe(2);
      expect((await listDetections(e, { internetAccountId: "a1" })).total).toBe(1);
    });
  });

  describe("coverage rollup", () => {
    it("counts plaintext platforms + E2E accounts + E2E detections", async () => {
      await registerPlatform(e, { platformType: "x", displayName: "X", seekUrl: "https://x.com/s" });
      await registerPlatform(e, { platformType: "linkedin", displayName: "LinkedIn", seekUrl: "https://linkedin.com/s" });
      await registerAccount(e, { accountId: "a1", ownerDid: OWNER, platformType: "x", accountName: "Alice", userId: "@alice" });
      await registerAccount(e, { accountId: "a2", ownerDid: OWNER, platformType: "x", accountName: "Ann", userId: "@ann" });
      await recordDetection(e, { detectionId: "d1", internetAccountId: "a1", platformType: "x", similarityScore: 88 });
      const cov = await coverage(e);
      expect(cov.protectedPlatformCount).toBe(2);
      expect(cov.protectedAccountCount).toBe(2);
      expect(cov.detectionResultCount).toBe(1);
      expect(cov.accountsByPlatform?.x).toBe(2);
    });
  });
});
