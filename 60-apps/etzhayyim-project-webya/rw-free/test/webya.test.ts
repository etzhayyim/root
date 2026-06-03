import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerSite,
  getSite,
  listSites,
  registerTemplate,
  listTemplates,
  registerPage,
  listPages,
  registerJob,
  listJobs,
  registerDomain,
  listDomains,
  recordClientContact,
  listClientContacts,
  getClientContact,
  recordDisclosure,
  listDisclosures,
  getDisclosure,
  coverage,
} from "../src/index.js";

const OWNER = "did:web:webya.etzhayyim.com";

describe("webya rw-free (kotoba-E2E split)", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: OWNER });
  });

  describe("siteCatalog (PLAINTEXT public presence)", () => {
    it("records, dedups, validates, gets, lists/filters", async () => {
      expect((await registerSite(e, { siteId: "s1", siteName: "Yamada Law", professionKind: "law_firm", subdomain: "yamada-law-webya.etzhayyim.com", status: "published" })).status).toBe("recorded");
      expect((await registerSite(e, { siteId: "s1", siteName: "Yamada Law", professionKind: "law_firm", subdomain: "x" })).status).toBe("alreadyExists");
      expect((await registerSite(e, { siteId: "sX", siteName: "n", professionKind: "bogus" as any, subdomain: "x" })).status).toBe("rejected");
      await registerSite(e, { siteId: "s2", siteName: "Acme KK", professionKind: "general_company", subdomain: "acme-webya.etzhayyim.com", status: "draft" });
      const got = await getSite(e, { siteId: "s1" });
      expect(got.site?.siteName).toBe("Yamada Law");
      expect(got.site?.status).toBe("published");
      expect((await getSite(e, { siteId: "nope" })).error).toBe("notFound");
      expect((await listSites(e)).total).toBe(2);
      expect((await listSites(e, { professionKind: "law_firm" })).total).toBe(1);
      expect((await listSites(e, { status: "draft" })).total).toBe(1);
    });
  });

  describe("template + page + generationJob + domain (PLAINTEXT)", () => {
    it("registers templates and lists by profession", async () => {
      expect((await registerTemplate(e, { templateId: "t1", professionKind: "law_firm", pages: ["home", "fees"], htmlSkeleton: "<html></html>" })).status).toBe("recorded");
      expect((await registerTemplate(e, { templateId: "t1", professionKind: "law_firm", pages: [], htmlSkeleton: "x" })).status).toBe("alreadyExists");
      await registerTemplate(e, { templateId: "t2", professionKind: "general_company", pages: ["home"], htmlSkeleton: "<html></html>" });
      expect((await listTemplates(e)).total).toBe(2);
      expect((await listTemplates(e, { professionKind: "law_firm" })).total).toBe(1);
    });

    it("enforces page FK → site via exists(), lists by site", async () => {
      expect((await registerPage(e, { pageId: "p1", siteId: "ghost", slug: "home", title: "Home" })).status).toBe("rejected");
      await registerSite(e, { siteId: "s1", siteName: "Yamada Law", professionKind: "law_firm", subdomain: "y" });
      expect((await registerPage(e, { pageId: "p1", siteId: "s1", slug: "home", title: "Home", htmlContent: "<h1>hi</h1>", jsonLd: "{}" })).status).toBe("recorded");
      await registerPage(e, { pageId: "p2", siteId: "s1", slug: "fees", title: "Fees" });
      expect((await listPages(e, { siteId: "s1" })).total).toBe(2);
    });

    it("enforces job FK → site, validates integer counts, lists by status", async () => {
      expect((await registerJob(e, { jobId: "j1", siteId: "ghost" })).status).toBe("rejected");
      await registerSite(e, { siteId: "s1", siteName: "Yamada Law", professionKind: "law_firm", subdomain: "y" });
      expect((await registerJob(e, { jobId: "jX", siteId: "s1", llmCallsCount: -1 })).status).toBe("rejected");
      expect((await registerJob(e, { jobId: "j1", siteId: "s1", status: "succeeded", llmCallsCount: 7, revisionCount: 2 })).status).toBe("recorded");
      await registerJob(e, { jobId: "j2", siteId: "s1", status: "running" });
      expect((await listJobs(e, { siteId: "s1" })).total).toBe(2);
      expect((await listJobs(e, { status: "running" })).total).toBe(1);
    });

    it("enforces domain FK → site, stores public DNS proof tokens, filters by ssl", async () => {
      expect((await registerDomain(e, { domainId: "d1", siteId: "ghost", domain: "yamada-law.jp" })).status).toBe("rejected");
      await registerSite(e, { siteId: "s1", siteName: "Yamada Law", professionKind: "law_firm", subdomain: "y" });
      const r = await registerDomain(e, { domainId: "d1", siteId: "s1", domain: "yamada-law.jp", verificationTxtName: "_cf.yamada-law.jp", verificationTxtValue: "abc123", sslStatus: "pending" });
      expect(r.status).toBe("recorded");
      await registerDomain(e, { domainId: "d2", siteId: "s1", domain: "acme.jp", sslStatus: "active" });
      const list = await listDomains(e, { siteId: "s1" });
      expect(list.total).toBe(2);
      expect(list.items.find((x) => x.domainId === "d1")?.cnameTarget).toBe("proxy-webya.etzhayyim.com");
      expect((await listDomains(e, { sslStatus: "active" })).total).toBe(1);
    });
  });

  describe("clientContact (E2E-ENCRYPTED contact PII)", () => {
    it("seals via encryptedWrite, round-trips via encryptedRead, validates", async () => {
      const ok = await recordClientContact(e, { clientId: "c1", siteId: "s1", representativeName: "山田太郎", address: "東京都千代田区1-1-1", email: "yamada@example.jp", phone: "03-1234-5678", orgDid: "did:web:yamada.example" });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();
      expect((await recordClientContact(e, { clientId: "cX", siteId: "s1", representativeName: "", address: "" })).status).toBe("rejected");
      const got = await getClientContact(e, { clientId: "c1" });
      expect(got.contact?.representativeName).toBe("山田太郎");
      expect(got.contact?.phone).toBe("03-1234-5678");
      await recordClientContact(e, { clientId: "c2", siteId: "s2", representativeName: "佐藤花子", address: "大阪府大阪市2-2-2" });
      expect((await listClientContacts(e)).total).toBe(2);
      expect((await listClientContacts(e, { siteId: "s1" })).total).toBe(1);
    });

    it("enforces read-cap: a non-recipient DID sees zero client contacts", async () => {
      await recordClientContact(e, { clientId: "c1", siteId: "s1", representativeName: "山田太郎", address: "東京都" });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listClientContacts(outsider)).total).toBe(0);
    });

    it("grants read-cap to an explicit recipient", async () => {
      const partner = "did:web:partner.example";
      const r = await recordClientContact(e, { clientId: "c1", siteId: "s1", representativeName: "山田太郎", address: "東京都", recipients: [partner] });
      expect(r.status).toBe("recorded");
      expect((await listClientContacts(e)).total).toBe(1);
    });
  });

  describe("legalDisclosure (E2E-ENCRYPTED per-person regulated credentials)", () => {
    it("seals registration number, round-trips, validates", async () => {
      const ok = await recordDisclosure(e, { disclosureId: "ld1", siteId: "s1", professionKind: "law_firm", disclosureType: "registration_number", disclosureValue: "弁護士登録番号 12345", representativeName: "山田太郎", verifiedAt: "2026-06-01T00:00:00Z" });
      expect(ok.status).toBe("recorded");
      expect((await recordDisclosure(e, { disclosureId: "ldX", siteId: "s1", professionKind: "law_firm", disclosureType: "bogus" as any, disclosureValue: "x", representativeName: "y" })).status).toBe("rejected");
      expect((await recordDisclosure(e, { disclosureId: "ldY", siteId: "s1", professionKind: "bogus" as any, disclosureType: "registration_number", disclosureValue: "x", representativeName: "y" })).status).toBe("rejected");
      const got = await getDisclosure(e, { disclosureId: "ld1" });
      expect(got.disclosure?.disclosureValue).toBe("弁護士登録番号 12345");
      await recordDisclosure(e, { disclosureId: "ld2", siteId: "s2", professionKind: "accounting_firm", disclosureType: "association_name", disclosureValue: "東京税理士会", representativeName: "佐藤花子" });
      expect((await listDisclosures(e)).total).toBe(2);
      expect((await listDisclosures(e, { siteId: "s1" })).total).toBe(1);
    });

    it("enforces read-cap: outsider DID cannot decrypt disclosures", async () => {
      await recordDisclosure(e, { disclosureId: "ld1", siteId: "s1", professionKind: "law_firm", disclosureType: "registration_number", disclosureValue: "12345", representativeName: "山田太郎" });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listDisclosures(outsider)).total).toBe(0);
    });
  });

  describe("coverage rollup (countAll over both stores)", () => {
    it("counts plaintext collections + E2E records + sitesByStatus", async () => {
      await registerSite(e, { siteId: "s1", siteName: "A", professionKind: "law_firm", subdomain: "a", status: "published" });
      await registerSite(e, { siteId: "s2", siteName: "B", professionKind: "general_company", subdomain: "b", status: "published" });
      await registerSite(e, { siteId: "s3", siteName: "C", professionKind: "law_firm", subdomain: "c", status: "draft" });
      await registerTemplate(e, { templateId: "t1", professionKind: "law_firm", pages: ["home"], htmlSkeleton: "<html></html>" });
      await registerPage(e, { pageId: "p1", siteId: "s1", slug: "home", title: "Home" });
      await registerJob(e, { jobId: "j1", siteId: "s1", status: "succeeded" });
      await registerDomain(e, { domainId: "d1", siteId: "s1", domain: "a.jp" });
      await recordClientContact(e, { clientId: "c1", siteId: "s1", representativeName: "山田", address: "東京都" });
      await recordDisclosure(e, { disclosureId: "ld1", siteId: "s1", professionKind: "law_firm", disclosureType: "registration_number", disclosureValue: "12345", representativeName: "山田" });

      const cov = await coverage(e);
      expect(cov.siteCatalogCount).toBe(3);
      expect(cov.templateCount).toBe(1);
      expect(cov.pageCount).toBe(1);
      expect(cov.generationJobCount).toBe(1);
      expect(cov.domainCount).toBe(1);
      expect(cov.clientContactCount).toBe(1);
      expect(cov.legalDisclosureCount).toBe(1);
      expect(cov.sitesByStatus?.published).toBe(2);
      expect(cov.sitesByStatus?.draft).toBe(1);
    });
  });
});
