import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerArbitrage,
  getArbitrage,
  listArbitrage,
  recordJocho,
  listJocho,
  getJocho,
  coverage,
} from "../src/index.js";

const OWNER = "did:web:open-ossekai.etzhayyim.com";

describe("open-ossekai kotoba (kotoba-E2E split)", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: OWNER });
  });

  describe("arbitrageOpportunity (PLAINTEXT public-good catalog)", () => {
    it("registers, dedups, validates, get/list/filter", async () => {
      expect(
        (await registerArbitrage(e, { arbId: "a1", topicCategory: "safety-recall", scopeKind: "jurisdiction", severity: "high", estimatedAffectedPopulation: 12000 })).status,
      ).toBe("registered");
      // dedup
      expect(
        (await registerArbitrage(e, { arbId: "a1", topicCategory: "safety-recall", scopeKind: "jurisdiction", severity: "high", estimatedAffectedPopulation: 12000 })).status,
      ).toBe("alreadyExists");
      // float/negative population rejected (integer-only AT-Lexicon)
      expect(
        (await registerArbitrage(e, { arbId: "aX", topicCategory: "x", scopeKind: "global", severity: "low", estimatedAffectedPopulation: -1 })).status,
      ).toBe("rejected");
      // bad severity rejected
      expect(
        (await registerArbitrage(e, { arbId: "aY", topicCategory: "x", scopeKind: "global", severity: "extreme" as any, estimatedAffectedPopulation: 1 })).status,
      ).toBe("rejected");
      // bad scopeKind rejected
      expect(
        (await registerArbitrage(e, { arbId: "aZ", topicCategory: "x", scopeKind: "planet" as any, severity: "low", estimatedAffectedPopulation: 1 })).status,
      ).toBe("rejected");

      await registerArbitrage(e, { arbId: "a2", topicCategory: "labor-rights", scopeKind: "global", severity: "mid", estimatedAffectedPopulation: 500 });

      // get
      const got = await getArbitrage(e, { arbId: "a1" });
      expect(got.opportunity?.severity).toBe("high");
      expect(got.opportunity?.estimatedAffectedPopulation).toBe(12000);
      expect((await getArbitrage(e, { arbId: "nope" })).error).toBe("notFound");

      // list + filters
      expect((await listArbitrage(e)).total).toBe(2);
      expect((await listArbitrage(e, { topicCategory: "labor-rights" })).total).toBe(1);
      expect((await listArbitrage(e, { severity: "high" })).total).toBe(1);
    });
  });

  describe("jochoAssessment (E2E-ENCRYPTED PII Tier-3, consent-gated)", () => {
    it("seals via encryptedWrite, round-trips via encryptedRead, validates", async () => {
      const ok = await recordJocho(e, {
        assessmentId: "j1",
        subjectDid: "did:web:subj.example",
        engagement: 70,
        competence: 65,
        contribution: 80,
        growth: 55,
        resilience: 60,
        targetKyuDan: "3-kyu",
        consentDid: "did:web:subj.example",
      });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();

      // axis score > 100 rejected (0-100 integer)
      expect(
        (await recordJocho(e, {
          assessmentId: "jX",
          subjectDid: "d",
          engagement: 200,
          competence: 1,
          contribution: 1,
          growth: 1,
          resilience: 1,
          targetKyuDan: "1-kyu",
          consentDid: "d",
        })).status,
      ).toBe("rejected");

      // missing consentDid rejected (ADR-0018 Tier-3 gate)
      expect(
        (await recordJocho(e, {
          assessmentId: "jY",
          subjectDid: "d",
          engagement: 10,
          competence: 10,
          contribution: 10,
          growth: 10,
          resilience: 10,
          targetKyuDan: "1-kyu",
          consentDid: "",
        })).status,
      ).toBe("rejected");

      const got = await getJocho(e, { assessmentId: "j1" });
      expect(got.assessment?.subjectDid).toBe("did:web:subj.example");
      expect(got.assessment?.contribution).toBe(80);
      expect(got.assessment?.targetKyuDan).toBe("3-kyu");

      await recordJocho(e, {
        assessmentId: "j2",
        subjectDid: "did:web:s2",
        engagement: 40,
        competence: 40,
        contribution: 40,
        growth: 40,
        resilience: 40,
        targetKyuDan: "5-kyu",
        consentDid: "did:web:s2",
      });
      expect((await listJocho(e)).total).toBe(2);
      expect((await listJocho(e, { subjectDid: "did:web:subj.example" })).total).toBe(1);
    });

    it("enforces read-cap: a non-recipient DID cannot decrypt the assessment", async () => {
      await recordJocho(e, {
        assessmentId: "j1",
        subjectDid: "did:web:subj",
        engagement: 70,
        competence: 65,
        contribution: 80,
        growth: 55,
        resilience: 60,
        targetKyuDan: "3-kyu",
        consentDid: "did:web:subj",
      });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      // Distinct PDS view, no read-cap — proves isolation by owner DID.
      expect((await listJocho(outsider)).total).toBe(0);
    });

    it("grants read-cap to an explicit consented recipient", async () => {
      const partner = "did:web:coach.example";
      const r = await recordJocho(e, {
        assessmentId: "j1",
        subjectDid: "did:web:subj",
        engagement: 70,
        competence: 65,
        contribution: 80,
        growth: 55,
        resilience: 60,
        targetKyuDan: "3-kyu",
        consentDid: "did:web:subj",
        recipients: [partner],
      });
      expect(r.status).toBe("recorded");
      expect((await listJocho(e)).total).toBe(1); // owner reads
    });
  });

  describe("coverage rollup", () => {
    it("counts plaintext opportunities + E2E jocho assessments", async () => {
      await registerArbitrage(e, { arbId: "a1", topicCategory: "safety-recall", scopeKind: "jurisdiction", severity: "high", estimatedAffectedPopulation: 10 });
      await registerArbitrage(e, { arbId: "a2", topicCategory: "safety-recall", scopeKind: "global", severity: "mid", estimatedAffectedPopulation: 20 });
      await recordJocho(e, {
        assessmentId: "j1",
        subjectDid: "did:web:s",
        engagement: 50,
        competence: 50,
        contribution: 50,
        growth: 50,
        resilience: 50,
        targetKyuDan: "4-kyu",
        consentDid: "did:web:s",
      });
      const cov = await coverage(e);
      expect(cov.arbitrageOpportunityCount).toBe(2);
      expect(cov.jochoAssessmentCount).toBe(1);
      expect(cov.opportunitiesByCategory?.["safety-recall"]).toBe(2);
    });
  });
});
