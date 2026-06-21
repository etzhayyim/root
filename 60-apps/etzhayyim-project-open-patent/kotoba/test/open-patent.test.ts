import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  ingestPatent,
  getPatent,
  listPatents,
  addCitation,
  listCitations,
  synthesizeSeed,
  publishSeed,
  listSeeds,
  addNoveltyReport,
  listNoveltyReports,
  coverage,
} from "../src/index.js";

const SRC = "https://patents.google.com/patent/US10123456B2";

describe("open-patent kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:open-patent.etzhayyim.com" });
  });

  describe("patents + citations", () => {
    it("ingests (jurisdiction validated), reads, lists, citations FK→patent", async () => {
      expect((await ingestPatent(e, { patentId: "P-1", publicationNumber: "us10123456b2", title: "Widget cooling system", jurisdiction: "us", status: "granted", sourceUrl: SRC })).status).toBe("ingested");
      expect((await getPatent(e, { patentId: "P-1" })).patent?.publicationNumber).toBe("US10123456B2");
      expect((await ingestPatent(e, { patentId: "P-X", publicationNumber: "x", title: "y", jurisdiction: "USA", status: "granted", sourceUrl: SRC })).status).toBe("rejected"); // 3-letter
      await ingestPatent(e, { patentId: "P-2", publicationNumber: "JP2026000001A", title: "冷却装置", jurisdiction: "JP", status: "published", sourceUrl: SRC });
      expect((await listPatents(e, { jurisdiction: "US" })).total).toBe(1);
      expect((await listPatents(e, { q: "cooling" })).total).toBe(1);
      expect((await addCitation(e, { citationId: "C-1", citingPatentId: "P-1", citedRef: "us9000000b1", citationType: "examiner" })).status).toBe("added");
      expect((await addCitation(e, { citationId: "C-X", citingPatentId: "GHOST", citedRef: "x", citationType: "other" })).status).toBe("patentNotFound");
      expect((await listCitations(e, { citingPatentId: "P-1", citationType: "examiner" })).total).toBe(1);
    });
  });

  describe("invention seeds + novelty (open IP)", () => {
    it("synthesizes seeds, publishes, adds novelty reports (FK→seed, per-mille)", async () => {
      expect((await synthesizeSeed(e, { seedId: "S-1", title: "Self-cooling widget v2", description: "...", basisRefs: ["US10123456B2"] })).status).toBe("synthesized");
      expect((await publishSeed(e, { seedId: "S-1" })).newStatus).toBe("published");
      expect((await publishSeed(e, { seedId: "S-1" })).status).toBe("rejected");
      expect((await listSeeds(e, { status: "published" })).total).toBe(1);
      expect((await addNoveltyReport(e, { reportId: "N-1", seedId: "S-1", noveltyPermille: 820, priorArtRefs: ["US9000000B1"], summary: "Distinct over prior art" })).status).toBe("added");
      expect((await addNoveltyReport(e, { reportId: "N-X", seedId: "S-1", noveltyPermille: 1500 })).status).toBe("rejected"); // permille
      expect((await addNoveltyReport(e, { reportId: "N-Y", seedId: "GHOST", noveltyPermille: 500 })).status).toBe("seedNotFound");
      expect((await listNoveltyReports(e, { seedId: "S-1" })).total).toBe(1);
    });
    it("coverage rolls up the four collections", async () => {
      await ingestPatent(e, { patentId: "P-1", publicationNumber: "US10123456B2", title: "X", jurisdiction: "US", status: "granted", sourceUrl: SRC });
      await synthesizeSeed(e, { seedId: "S-1", title: "Seed", description: "d" });
      await addNoveltyReport(e, { reportId: "N-1", seedId: "S-1", noveltyPermille: 700 });
      const cov = await coverage(e);
      expect(cov.patentCount).toBe(1);
      expect(cov.seedCount).toBe(1);
      expect(cov.noveltyCount).toBe(1);
      expect(cov.patentsByJurisdiction?.US).toBe(1);
      expect(cov.seedsByStatus?.draft).toBe(1);
    });
  });
});
