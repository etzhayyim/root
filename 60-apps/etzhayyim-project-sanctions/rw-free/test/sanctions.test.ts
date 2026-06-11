import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerListUpdate,
  listListUpdates,
  addEntry,
  getEntry,
  listEntries,
  coverage,
} from "../src/index.js";

const SRC = "https://sanctionslistservice.ofac.treas.gov/example";

describe("sanctions rw-free", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:sanctions.etzhayyim.com" });
  });

  describe("list-update tracking", () => {
    it("registers refresh snapshots (source + uint changeCount validated), lists by source", async () => {
      expect((await registerListUpdate(e, { updateId: "U-1", listSource: "OFAC-SDN", listVersion: "2026.06.01", changeCount: 42, fetchedAt: "2026-06-01T00:00:00Z", sourceUrl: SRC })).status).toBe("registered");
      expect((await registerListUpdate(e, { updateId: "U-X", listSource: "BOGUS" as any, listVersion: "1", changeCount: 0, fetchedAt: "x", sourceUrl: SRC })).status).toBe("rejected"); // source
      expect((await registerListUpdate(e, { updateId: "U-Y", listSource: "EU", listVersion: "1", changeCount: -1, fetchedAt: "x", sourceUrl: SRC })).status).toBe("rejected"); // changeCount
      expect((await registerListUpdate(e, { updateId: "U-1", listSource: "OFAC-SDN", listVersion: "2026.06.01", changeCount: 42, fetchedAt: "x", sourceUrl: SRC })).status).toBe("alreadyExists");
      expect((await listListUpdates(e, { listSource: "OFAC-SDN" })).total).toBe(1);
    });
  });

  describe("sanction entries", () => {
    beforeEach(async () => {
      await registerListUpdate(e, { updateId: "U-1", listSource: "OFAC-SDN", listVersion: "2026.06.01", changeCount: 1, fetchedAt: "2026-06-01T00:00:00Z", sourceUrl: SRC });
    });
    it("adds entries (FK→listUpdate, source/type/country validated), reads", async () => {
      expect((await addEntry(e, { entryId: "E-1", listSource: "OFAC-SDN", entityName: "ACME SHIPPING LLC", entityType: "entity", country: "ru", program: "UKRAINE-EO13662", aliases: ["ACME LLC"], identifiers: ["IMO 1234567"], updateId: "U-1", sourceUrl: SRC })).status).toBe("added");
      expect((await getEntry(e, { entryId: "E-1" })).entry?.country).toBe("RU");
      expect((await addEntry(e, { entryId: "E-X", listSource: "EU", entityName: "x", entityType: "alien" as any, sourceUrl: SRC })).status).toBe("rejected"); // entityType
      expect((await addEntry(e, { entryId: "E-Z", listSource: "EU", entityName: "z", entityType: "entity", country: "RUS", sourceUrl: SRC })).status).toBe("rejected"); // country 3-letter
      expect((await addEntry(e, { entryId: "E-G", listSource: "EU", entityName: "g", entityType: "entity", updateId: "GHOST", sourceUrl: SRC })).status).toBe("listUpdateNotFound");
    });
    it("lists/filters by source/type/country and searches name+alias", async () => {
      await addEntry(e, { entryId: "E-1", listSource: "OFAC-SDN", entityName: "ACME SHIPPING LLC", entityType: "entity", country: "RU", aliases: ["BETA TRADING"], sourceUrl: SRC });
      await addEntry(e, { entryId: "E-2", listSource: "OFAC-SDN", entityName: "Ivan Petrov", entityType: "individual", country: "RU", sourceUrl: SRC });
      expect((await listEntries(e, { entityType: "entity" })).total).toBe(1);
      expect((await listEntries(e, { country: "ru" })).total).toBe(2);
      expect((await listEntries(e, { q: "beta" })).total).toBe(1); // alias hit
      expect((await listEntries(e, { q: "petrov" })).total).toBe(1);
    });
    it("coverage rolls up entries + list-updates by source/type", async () => {
      await addEntry(e, { entryId: "E-1", listSource: "OFAC-SDN", entityName: "A Co", entityType: "entity", sourceUrl: SRC });
      await addEntry(e, { entryId: "E-2", listSource: "EU", entityName: "B Person", entityType: "individual", sourceUrl: SRC });
      const cov = await coverage(e);
      expect(cov.entryCount).toBe(2);
      expect(cov.listUpdateCount).toBe(1);
      expect(cov.entriesByListSource?.["OFAC-SDN"]).toBe(1);
      expect(cov.entriesByType?.individual).toBe(1);
    });
  });
});
