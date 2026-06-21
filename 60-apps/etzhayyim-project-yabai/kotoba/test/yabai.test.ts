import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerIndicator,
  listIndicators,
  getIndicator,
  recordAssessment,
  listAssessments,
  getAssessment,
  coverage,
} from "../src/index.js";

const OWNER = "did:web:yabai.etzhayyim.com";

describe("yabai kotoba (kotoba-E2E split)", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: OWNER });
  });

  describe("threatIndicator (PLAINTEXT public CTI reference)", () => {
    it("records, dedups, validates, lists/filters, gets", async () => {
      expect((await registerIndicator(e, { indicatorId: "cve-2026-1", indicatorType: "cve", value: "CVE-2026-0001", severity: 75, source: "nvd" })).status).toBe("recorded");
      expect((await registerIndicator(e, { indicatorId: "cve-2026-1", indicatorType: "cve", value: "CVE-2026-0001", severity: 75, source: "nvd" })).status).toBe("alreadyExists");
      // severity out of 0-100 range → rejected (no-float / integer-pct guard)
      expect((await registerIndicator(e, { indicatorId: "bad", indicatorType: "cve", value: "x", severity: 200, source: "nvd" })).status).toBe("rejected");
      // bad indicator type → rejected
      expect((await registerIndicator(e, { indicatorId: "bad2", indicatorType: "xxx" as any, value: "x", severity: 10, source: "nvd" })).status).toBe("rejected");
      await registerIndicator(e, { indicatorId: "t1566", indicatorType: "mitre", value: "T1566", severity: 60, source: "mitre" });
      await registerIndicator(e, { indicatorId: "as135377", indicatorType: "asn", value: "AS135377", severity: 90, source: "yabai" });
      expect((await listIndicators(e)).total).toBe(3);
      expect((await listIndicators(e, { indicatorType: "cve" })).total).toBe(1);
      const got = await getIndicator(e, { indicatorId: "as135377" });
      expect(got.indicator?.value).toBe("AS135377");
      expect((await getIndicator(e, { indicatorId: "nope" })).error).toBe("notFound");
    });
  });

  describe("riskAssessment (E2E-ENCRYPTED CUI + LE per-subject scores)", () => {
    it("seals via encryptedWrite, round-trips via encryptedRead, validates", async () => {
      const ok = await recordAssessment(e, { assessmentId: "a1", subjectDid: "did:web:subj.example", riskScore: 92, band: "deny", confidence: 88, signals: ["SanctionHit", "AMLPattern"] });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();
      // riskScore>100 → rejected
      expect((await recordAssessment(e, { assessmentId: "aX", subjectDid: "d", riskScore: 200, band: "deny", confidence: 50 })).status).toBe("rejected");
      // bad band → rejected
      expect((await recordAssessment(e, { assessmentId: "aY", subjectDid: "d", riskScore: 50, band: "nope" as any, confidence: 50 })).status).toBe("rejected");
      const got = await getAssessment(e, { assessmentId: "a1" });
      expect(got.assessment?.subjectDid).toBe("did:web:subj.example");
      expect(got.assessment?.riskScore).toBe(92);
      expect(got.assessment?.signals).toContain("SanctionHit");
      await recordAssessment(e, { assessmentId: "a2", subjectDid: "did:web:s2", riskScore: 70, band: "monitor", confidence: 60 });
      expect((await listAssessments(e)).total).toBe(2);
      expect((await listAssessments(e, { band: "deny" })).total).toBe(1);
    });

    it("enforces read-cap: a non-recipient DID cannot decrypt the assessment", async () => {
      await recordAssessment(e, { assessmentId: "a1", subjectDid: "did:web:subj", riskScore: 92, band: "deny", confidence: 88 });
      // A different actor (no read-cap) is a distinct PDS view → zero records.
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listAssessments(outsider)).total).toBe(0);
    });

    it("grants read-cap to an explicit recipient", async () => {
      const partner = "did:web:partner.example";
      const r = await recordAssessment(e, { assessmentId: "a1", subjectDid: "did:web:subj", riskScore: 92, band: "deny", confidence: 88, recipients: [partner] });
      expect(r.status).toBe("recorded");
      expect((await listAssessments(e)).total).toBe(1);
    });
  });

  describe("coverage rollup", () => {
    it("counts plaintext indicators + E2E assessments", async () => {
      await registerIndicator(e, { indicatorId: "cve-1", indicatorType: "cve", value: "CVE-2026-1", severity: 50, source: "nvd" });
      await registerIndicator(e, { indicatorId: "cve-2", indicatorType: "cve", value: "CVE-2026-2", severity: 30, source: "nvd" });
      await registerIndicator(e, { indicatorId: "ioc-1", indicatorType: "ioc", value: "1.2.3.4", severity: 80, source: "yabai" });
      await recordAssessment(e, { assessmentId: "a1", subjectDid: "did:web:s", riskScore: 60, band: "monitor", confidence: 70 });
      const cov = await coverage(e);
      expect(cov.threatIndicatorCount).toBe(3);
      expect(cov.riskAssessmentCount).toBe(1);
      expect(cov.indicatorsByType?.cve).toBe(2);
      expect(cov.indicatorsByType?.ioc).toBe(1);
    });
  });
});
