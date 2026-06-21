import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerCompany,
  getCompany,
  listCompanies,
  addJobPosting,
  listJobPostings,
  coverage,
} from "../src/index.js";

describe("hrse kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:hrse.etzhayyim.com" });
  });

  describe("hiring company registry", () => {
    it("registers companies, reads, lists, searches", async () => {
      expect((await registerCompany(e, { companyId: "C-1", name: "SecureCorp KK", industry: "fintech", region: "JP-13", website: "https://securecorp.example" })).status).toBe("registered");
      expect((await getCompany(e, { companyId: "C-1" })).company?.region).toBe("JP-13");
      await registerCompany(e, { companyId: "C-2", name: "CloudGuard Ltd", region: "GB" });
      expect((await listCompanies(e, { region: "JP-13" })).total).toBe(1);
      expect((await listCompanies(e, { q: "cloud" })).total).toBe(1);
    });
  });

  describe("job postings FK to company", () => {
    beforeEach(async () => {
      await registerCompany(e, { companyId: "C-1", name: "SecureCorp", region: "JP-13" });
    });
    it("adds postings (FK→company, enums + comp-string validated), filters/searches", async () => {
      expect((await addJobPosting(e, { postingId: "J-1", companyId: "C-1", title: "Senior Penetration Tester", category: "pentest", seniority: "senior", engagementType: "contract", requiredSkills: ["Burp Suite", "OSCP", "web app"], compMinJpy: "8000000", compMaxJpy: "12000000", remote: true, postedAt: "2026-05-30" })).status).toBe("added");
      expect((await addJobPosting(e, { postingId: "J-X", companyId: "C-1", title: "x", category: "quantum" as any, seniority: "senior", engagementType: "contract", postedAt: "x" })).status).toBe("rejected"); // category
      expect((await addJobPosting(e, { postingId: "J-Y", companyId: "C-1", title: "y", category: "soc", seniority: "wizard" as any, engagementType: "contract", postedAt: "x" })).status).toBe("rejected"); // seniority
      expect((await addJobPosting(e, { postingId: "J-F", companyId: "C-1", title: "f", category: "soc", seniority: "mid", engagementType: "contract", compMinJpy: "5.5", postedAt: "x" })).status).toBe("rejected"); // comp float-string
      expect((await addJobPosting(e, { postingId: "J-G", companyId: "GHOST", title: "g", category: "soc", seniority: "mid", engagementType: "contract", postedAt: "x" })).status).toBe("companyNotFound");
      expect((await listJobPostings(e, { category: "pentest", remote: true })).total).toBe(1);
      expect((await listJobPostings(e, { q: "oscp" })).total).toBe(1); // skill hit
    });
    it("coverage rolls up companies + postings by category / seniority", async () => {
      await addJobPosting(e, { postingId: "J-1", companyId: "C-1", title: "A", category: "pentest", seniority: "senior", engagementType: "contract", postedAt: "2026-05-30" });
      await addJobPosting(e, { postingId: "J-2", companyId: "C-1", title: "B", category: "grc", seniority: "lead", engagementType: "full-time", postedAt: "2026-05-30" });
      const cov = await coverage(e);
      expect(cov.companyCount).toBe(1);
      expect(cov.jobPostingCount).toBe(2);
      expect(cov.postingsByCategory?.pentest).toBe(1);
      expect(cov.postingsBySeniority?.lead).toBe(1);
    });
  });
});
