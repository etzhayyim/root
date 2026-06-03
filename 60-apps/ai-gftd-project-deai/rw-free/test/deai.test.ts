import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerSpiritType,
  getSpiritType,
  listSpiritTypes,
  recordCohortStat,
  listCohortStats,
  recordProfile,
  listProfiles,
  getProfile,
  recordMatch,
  listMatches,
  getMatch,
  coverage,
} from "../src/index.js";

const OWNER = "did:web:decom.etzhayyim.ai";

describe("deai rw-free (Spirit-in-Physics, E2E split)", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: OWNER });
  });

  describe("spiritTypeCatalog (PLAINTEXT reference data)", () => {
    it("registers, dedups, validates, gets/lists; complementType is descriptive (mutual relation)", async () => {
      // Mutual complement pair — descriptive field, no circular FK.
      expect((await registerSpiritType(e, { spiritType: "Hero", traits: "mission/achieve/protect", complementType: "Caregiver" })).status).toBe("registered");
      expect((await registerSpiritType(e, { spiritType: "Caregiver", traits: "nurture/empathy/serve", complementType: "Hero" })).status).toBe("registered");
      // Dedup.
      expect((await registerSpiritType(e, { spiritType: "Hero", traits: "x", complementType: "Caregiver" })).status).toBe("alreadyExists");
      // Missing field.
      expect((await registerSpiritType(e, { spiritType: "Sage", traits: "", complementType: "Lover" })).status).toBe("rejected");
      // get + list.
      const got = await getSpiritType(e, { spiritType: "Caregiver" });
      expect(got.spiritType?.complementType).toBe("Hero");
      expect((await listSpiritTypes(e)).total).toBe(2);
      expect((await getSpiritType(e, { spiritType: "Nope" })).error).toBe("notFound");
    });
  });

  describe("cohortStat (PLAINTEXT anonymous aggregate + parent→child FK)", () => {
    it("records, dedups, validates, enforces FK on spiritType, lists/filters", async () => {
      // FK: spiritType must reference a registered catalog entry.
      expect((await recordCohortStat(e, { statId: "s0", spiritType: "Hero", participantCount: 120 })).status).toBe("rejected"); // catalog empty → unknownSpiritType
      await registerSpiritType(e, { spiritType: "Hero", traits: "t", complementType: "Caregiver" });
      await registerSpiritType(e, { spiritType: "Lover", traits: "t", complementType: "Sage" });
      expect((await recordCohortStat(e, { statId: "s1", spiritType: "Hero", participantCount: 120 })).status).toBe("recorded");
      expect((await recordCohortStat(e, { statId: "s1", spiritType: "Hero", participantCount: 120 })).status).toBe("alreadyExists");
      expect((await recordCohortStat(e, { statId: "sX", spiritType: "Hero", participantCount: -1 })).status).toBe("rejected");
      expect((await recordCohortStat(e, { statId: "sY", spiritType: "Sage", participantCount: 5 })).status).toBe("rejected"); // Sage not in catalog
      await recordCohortStat(e, { statId: "s2", spiritType: "Lover", participantCount: 80 });
      expect((await listCohortStats(e)).total).toBe(2);
      expect((await listCohortStats(e, { spiritType: "Hero" })).total).toBe(1);
    });
  });

  describe("spiritProfile (E2E-ENCRYPTED PII / biometric)", () => {
    it("seals via encryptedWrite, round-trips via encryptedRead, validates", async () => {
      const ok = await recordProfile(e, { profileId: "p1", subjectDid: "did:web:subj.example", spiritType: "Hero", cohortHash: "ab12", emotionVector: [10, 80, 50, 0, 99, 33, 21, 7, 64, 12] });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();
      // out-of-range emotion component (>100) rejected.
      expect((await recordProfile(e, { profileId: "pX", subjectDid: "d", spiritType: "Sage", cohortHash: "h", emotionVector: [200] })).status).toBe("rejected");
      const got = await getProfile(e, { profileId: "p1" });
      expect(got.profile?.subjectDid).toBe("did:web:subj.example");
      expect(got.profile?.emotionVector[1]).toBe(80);
      await recordProfile(e, { profileId: "p2", subjectDid: "did:web:s2", spiritType: "Lover", cohortHash: "cd34", emotionVector: [1, 2, 3] });
      expect((await listProfiles(e)).total).toBe(2);
      expect((await listProfiles(e, { spiritType: "Hero" })).total).toBe(1);
    });

    it("enforces read-cap: a non-recipient DID cannot decrypt the profile", async () => {
      await recordProfile(e, { profileId: "p1", subjectDid: "did:web:subj", spiritType: "Hero", cohortHash: "ab", emotionVector: [50] });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listProfiles(outsider)).total).toBe(0);
    });
  });

  describe("matchScore (E2E-ENCRYPTED confidential per-pair)", () => {
    it("seals, round-trips, validates, filters by subject DID", async () => {
      const ok = await recordMatch(e, { matchId: "m1", subjectDidA: "did:web:a", subjectDidB: "did:web:b", resonanceScore: 88, spiritCompatibility: 73 });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();
      expect((await recordMatch(e, { matchId: "mX", subjectDidA: "a", subjectDidB: "b", resonanceScore: 101, spiritCompatibility: 50 })).status).toBe("rejected");
      const got = await getMatch(e, { matchId: "m1" });
      expect(got.match?.resonanceScore).toBe(88);
      await recordMatch(e, { matchId: "m2", subjectDidA: "did:web:a", subjectDidB: "did:web:c", resonanceScore: 40, spiritCompatibility: 30 });
      expect((await listMatches(e)).total).toBe(2);
      expect((await listMatches(e, { subjectDid: "did:web:c" })).total).toBe(1);
    });

    it("grants read-cap to an explicit recipient", async () => {
      const partner = "did:web:partner.example";
      const r = await recordMatch(e, { matchId: "m1", subjectDidA: "did:web:a", subjectDidB: "did:web:b", resonanceScore: 60, spiritCompatibility: 60, recipients: [partner] });
      expect(r.status).toBe("recorded");
      expect((await listMatches(e)).total).toBe(1);
    });
  });

  describe("coverage rollup", () => {
    it("counts plaintext catalog/stats + E2E profiles/matches", async () => {
      await registerSpiritType(e, { spiritType: "Hero", traits: "t", complementType: "Caregiver" });
      await recordCohortStat(e, { statId: "s1", spiritType: "Hero", participantCount: 10 });
      await recordCohortStat(e, { statId: "s2", spiritType: "Hero", participantCount: 20 });
      await recordProfile(e, { profileId: "p1", subjectDid: "did:web:s", spiritType: "Hero", cohortHash: "h", emotionVector: [5] });
      await recordMatch(e, { matchId: "m1", subjectDidA: "did:web:a", subjectDidB: "did:web:b", resonanceScore: 50, spiritCompatibility: 50 });
      const cov = await coverage(e);
      expect(cov.spiritTypeCatalogCount).toBe(1);
      expect(cov.cohortStatCount).toBe(2);
      expect(cov.spiritProfileCount).toBe(1);
      expect(cov.matchScoreCount).toBe(1);
      expect(cov.statsBySpiritType?.Hero).toBe(2);
    });
  });
});
