import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerTaxon,
  getTaxon,
  listTaxa,
  deriveTraits,
  listTraits,
  ingestObservation,
  listObservations,
  coverage,
} from "../src/index.js";

const SRC = "https://www.gbif.org/species/example";

describe("seibutsu kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:seibutsu.etzhayyim.com" });
  });

  describe("taxon hierarchy", () => {
    it("registers taxa (self-ref parent FK), validates rank, reads, searches", async () => {
      expect((await registerTaxon(e, { taxonId: "T-PLANTAE", rank: "kingdom", scientificName: "Plantae" })).status).toBe("registered");
      expect((await registerTaxon(e, { taxonId: "T-BAMBOO", rank: "genus", scientificName: "Phyllostachys", commonName: "Running bamboo", parentTaxonId: "T-PLANTAE", gbifId: "2704179" })).status).toBe("registered");
      expect((await registerTaxon(e, { taxonId: "T-X", rank: "phylogenetic" as any, scientificName: "x" })).status).toBe("rejected"); // rank
      expect((await registerTaxon(e, { taxonId: "T-Y", rank: "species", scientificName: "y", parentTaxonId: "GHOST" })).status).toBe("parentNotFound");
      expect((await getTaxon(e, { taxonId: "T-BAMBOO" })).taxon?.gbifId).toBe("2704179");
      expect((await listTaxa(e, { rank: "genus" })).total).toBe(1);
      expect((await listTaxa(e, { parentTaxonId: "T-PLANTAE" })).total).toBe(1);
      expect((await listTaxa(e, { q: "bamboo" })).total).toBe(1); // common name hit
    });
  });

  describe("traits + observations", () => {
    beforeEach(async () => {
      await registerTaxon(e, { taxonId: "T-BAMBOO", rank: "genus", scientificName: "Phyllostachys" });
    });
    it("derives traits (FK→taxon, integer cm/years, habit validated)", async () => {
      expect((await deriveTraits(e, { traitId: "TR-1", taxonId: "T-BAMBOO", habit: "grass", matureHeightCm: 2000, lifespanYears: 60, hardinessZone: "7b" })).status).toBe("derived");
      expect((await deriveTraits(e, { traitId: "TR-X", taxonId: "T-BAMBOO", habit: "alien" as any })).status).toBe("rejected"); // habit
      expect((await deriveTraits(e, { traitId: "TR-F", taxonId: "T-BAMBOO", habit: "grass", matureHeightCm: 12.5 as any })).status).toBe("rejected"); // float
      expect((await deriveTraits(e, { traitId: "TR-G", taxonId: "GHOST", habit: "grass" })).status).toBe("taxonNotFound");
      expect((await listTraits(e, { taxonId: "T-BAMBOO", habit: "grass" })).total).toBe(1);
    });
    it("ingests observations (FK→taxon, H3 geo, public observer handle)", async () => {
      expect((await ingestObservation(e, { observationId: "O-1", taxonId: "T-BAMBOO", observedAt: "2026-05-30", geoH3: "8928308280fffff", observerHandle: "naturalist.bsky.social", imageUrl: "https://img/1.jpg" })).status).toBe("ingested");
      expect((await ingestObservation(e, { observationId: "O-X", taxonId: "T-BAMBOO", observedAt: "2026-05-30", geoH3: "not-an-h3-cell!" })).status).toBe("rejected"); // h3
      expect((await ingestObservation(e, { observationId: "O-G", taxonId: "GHOST", observedAt: "2026-05-30" })).status).toBe("taxonNotFound");
      expect((await listObservations(e, { taxonId: "T-BAMBOO" })).total).toBe(1);
      expect((await listObservations(e, { observerHandle: "naturalist.bsky.social" })).total).toBe(1);
    });
    it("coverage rolls up taxa/traits/observations by rank", async () => {
      await registerTaxon(e, { taxonId: "T-FUNGI", rank: "kingdom", scientificName: "Fungi" });
      await deriveTraits(e, { traitId: "TR-1", taxonId: "T-BAMBOO", habit: "grass" });
      await ingestObservation(e, { observationId: "O-1", taxonId: "T-BAMBOO", observedAt: "2026-05-30" });
      const cov = await coverage(e);
      expect(cov.taxonCount).toBe(2);
      expect(cov.traitsCount).toBe(1);
      expect(cov.observationCount).toBe(1);
      expect(cov.taxaByRank?.kingdom).toBe(1);
      expect(cov.taxaByRank?.genus).toBe(1);
    });
  });
});
