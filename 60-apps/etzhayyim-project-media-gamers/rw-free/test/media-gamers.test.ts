import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerPublisher,
  listPublishers,
  registerDeveloper,
  listDevelopers,
  registerGameTitle,
  getGameTitle,
  listGameTitles,
  recordChartEntry,
  listChartEntries,
  coverage,
} from "../src/index.js";

const SRC = "https://www.igdb.com/example";

describe("media-gamers rw-free", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:media-gamers.etzhayyim.com" });
  });

  describe("publisher / developer / game title", () => {
    it("registers publisher+developer, then game title (FK→both), rejects missing FK", async () => {
      expect((await registerPublisher(e, { publisherId: "nintendo", name: "Nintendo", country: "JP", sourceUrl: SRC })).status).toBe("registered");
      expect((await registerDeveloper(e, { developerId: "nintendo-epd", name: "Nintendo EPD", country: "JP" })).status).toBe("registered");
      expect((await registerGameTitle(e, { titleId: "totk", name: "Tears of the Kingdom", slug: "tears-of-the-kingdom", publisherId: "nintendo", developerId: "nintendo-epd", platforms: ["Switch"], genre: "action-adventure", sourceUrl: SRC })).status).toBe("registered");
      expect((await getGameTitle(e, { titleId: "totk" })).title?.slug).toBe("tears-of-the-kingdom");
      expect((await registerGameTitle(e, { titleId: "x", name: "x", slug: "x", publisherId: "ghost" })).status).toBe("publisherNotFound");
      expect((await registerGameTitle(e, { titleId: "y", name: "y", slug: "y", developerId: "ghost" })).status).toBe("developerNotFound");
      expect((await listPublishers(e, { country: "JP" })).total).toBe(1);
      expect((await listDevelopers(e, { q: "epd" })).total).toBe(1);
      expect((await listGameTitles(e, { publisherId: "nintendo", platform: "Switch" })).total).toBe(1);
      expect((await listGameTitles(e, { q: "kingdom" })).total).toBe(1);
    });
  });

  describe("chart entries FK→game title + coverage", () => {
    beforeEach(async () => {
      await registerGameTitle(e, { titleId: "totk", name: "TOTK", slug: "totk", genre: "action-adventure" });
      await registerGameTitle(e, { titleId: "fc24", name: "EA FC 24", slug: "fc24", genre: "sports" });
    });
    it("records chart entries (FK→title, uint rank), rank-ordered list, rejects missing title", async () => {
      expect((await recordChartEntry(e, { entryId: "c-2", chartName: "JP-weekly", titleId: "fc24", rank: 2, region: "JP", period: "2026-W22", sourceUrl: SRC })).status).toBe("recorded");
      expect((await recordChartEntry(e, { entryId: "c-1", chartName: "JP-weekly", titleId: "totk", rank: 1, region: "JP", period: "2026-W22" })).status).toBe("recorded");
      expect((await recordChartEntry(e, { entryId: "c-F", chartName: "x", titleId: "totk", rank: 1.5 as any })).status).toBe("rejected"); // float
      expect((await recordChartEntry(e, { entryId: "c-G", chartName: "x", titleId: "ghost", rank: 1 })).status).toBe("titleNotFound");
      const chart = await listChartEntries(e, { chartName: "JP-weekly" });
      expect(chart.total).toBe(2);
      expect(chart.items[0].rank).toBe(1); // rank-ordered
    });
    it("coverage rolls up the catalog by genre", async () => {
      await recordChartEntry(e, { entryId: "c-1", chartName: "JP-weekly", titleId: "totk", rank: 1 });
      const cov = await coverage(e);
      expect(cov.gameTitleCount).toBe(2);
      expect(cov.chartEntryCount).toBe(1);
      expect(cov.titlesByGenre?.sports).toBe(1);
      expect(cov.titlesByGenre?.["action-adventure"]).toBe(1);
    });
  });
});
