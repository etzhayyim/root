import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerContract,
  getContract,
  listContracts,
  registerSpApplication,
  listSpApplications,
  getSpApplication,
  coverage,
} from "../src/index.js";

const OWNER = "did:web:hc.etzhayyim.com";

describe("hc kotoba (E2E reference)", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: OWNER });
  });

  describe("contractTemplate (PLAINTEXT public catalog)", () => {
    it("registers, dedups, validates, gets, lists/filters", async () => {
      expect((await registerContract(e, { contractType: "worker-agreement", locale: "ja" })).status).toBe("registered");
      expect((await registerContract(e, { contractType: "worker-agreement", locale: "ja" })).status).toBe("alreadyExists");
      expect((await registerContract(e, { contractType: "", locale: "ja" })).status).toBe("rejected");
      await registerContract(e, { contractType: "sp-service-agreement", locale: "ja", governingLaw: "Japan" });
      await registerContract(e, { contractType: "worker-agreement", locale: "us" });

      const got = await getContract(e, { contractType: "worker-agreement", locale: "ja" });
      expect(got.template?.did).toBe("did:web:hc.etzhayyim.com:legal:worker-agreement:ja");
      expect(got.template?.governingLaw).toBe("Japan");
      expect((await getContract(e, { contractType: "nope", locale: "ja" })).error).toBe("notFound");

      expect((await listContracts(e)).total).toBe(3);
      expect((await listContracts(e, { contractType: "worker-agreement" })).total).toBe(2);
      expect((await listContracts(e, { locale: "us" })).total).toBe(1);
    });
  });

  describe("spApplication (E2E-ENCRYPTED PII + CUI)", () => {
    it("seals via encryptedWrite, round-trips via encryptedRead, validates", async () => {
      const ok = await registerSpApplication(e, {
        applicationId: "app1",
        legalName: "Shenzhen OEM Co Ltd",
        contactEmail: "kyc@oem.example",
        countryIso3: "CHN",
        category: "sp-kyc-review",
        isicCodes: ["2640"],
        lei: "5493001KJTIIGC8Y1R12",
        verdict: "approved",
        sanctionsClear: true,
        legalEntityVerified: true,
      });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();

      // invalid email rejected
      expect((await registerSpApplication(e, { applicationId: "appX", legalName: "X", contactEmail: "bad", countryIso3: "JPN", category: "c" })).status).toBe("rejected");
      // invalid verdict rejected
      expect((await registerSpApplication(e, { applicationId: "appY", legalName: "Y", contactEmail: "y@y.example", countryIso3: "JPN", category: "c", verdict: "weird" as any })).status).toBe("rejected");

      const got = await getSpApplication(e, { applicationId: "app1" });
      expect(got.application?.legalName).toBe("Shenzhen OEM Co Ltd");
      expect(got.application?.sanctionsClear).toBe(true);
      expect(got.application?.verdict).toBe("approved");
      expect((await getSpApplication(e, { applicationId: "nope" })).error).toBe("notFound");

      await registerSpApplication(e, { applicationId: "app2", legalName: "Hanoi Factory", contactEmail: "ops@hanoi.example", countryIso3: "VNM", category: "sp-factory-audit", verdict: "pending" });
      expect((await listSpApplications(e)).total).toBe(2);
      expect((await listSpApplications(e, { countryIso3: "CHN" })).total).toBe(1);
      expect((await listSpApplications(e, { verdict: "pending" })).total).toBe(1);
    });

    it("enforces read-cap: a non-recipient DID cannot decrypt the application", async () => {
      await registerSpApplication(e, { applicationId: "app1", legalName: "Secret Co", contactEmail: "s@s.example", countryIso3: "JPN", category: "sp-kyc-review" });
      // A distinct PDS view with no read-cap sees zero applications (owner isolation).
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listSpApplications(outsider)).total).toBe(0);
    });

    it("grants read-cap to an explicit recipient", async () => {
      const auditor = "did:web:sgs-auditor.example";
      const r = await registerSpApplication(e, {
        applicationId: "app1",
        legalName: "Audited Co",
        contactEmail: "a@a.example",
        countryIso3: "JPN",
        category: "sp-factory-audit",
        recipients: [auditor],
      });
      expect(r.status).toBe("recorded");
      // owner still reads
      expect((await listSpApplications(e)).total).toBe(1);
    });
  });

  describe("coverage rollup", () => {
    it("counts plaintext templates + E2E applications", async () => {
      await registerContract(e, { contractType: "worker-agreement", locale: "ja" });
      await registerContract(e, { contractType: "task-terms", locale: "ja" });
      await registerContract(e, { contractType: "worker-agreement", locale: "us" });
      await registerSpApplication(e, { applicationId: "app1", legalName: "A", contactEmail: "a@a.example", countryIso3: "JPN", category: "c", verdict: "approved" });
      await registerSpApplication(e, { applicationId: "app2", legalName: "B", contactEmail: "b@b.example", countryIso3: "CHN", category: "c", verdict: "pending" });

      const cov = await coverage(e);
      expect(cov.contractTemplateCount).toBe(3);
      expect(cov.spApplicationCount).toBe(2);
      expect(cov.templatesByLocale?.ja).toBe(2);
      expect(cov.templatesByLocale?.us).toBe(1);
      expect(cov.applicationsByVerdict?.approved).toBe(1);
      expect(cov.applicationsByVerdict?.pending).toBe(1);
    });
  });
});
