import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerSource,
  setSourceStatus,
  listSources,
  ingestArticle,
  getArticle,
  listArticles,
  coverage,
} from "../src/index.js";

describe("news rw-free", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:news.etzhayyim.com" });
  });

  describe("source registry", () => {
    it("registers sources (lang + type validated), status lifecycle, lists", async () => {
      expect((await registerSource(e, { sourceId: "nhk", sourceName: "NHK News", sourceUrl: "https://www3.nhk.or.jp", feedUrl: "https://www3.nhk.or.jp/rss", lang: "ja", sourceType: "rss" })).status).toBe("registered");
      expect((await registerSource(e, { sourceId: "x", sourceName: "x", sourceUrl: "u", lang: "jpn", sourceType: "rss" })).status).toBe("rejected"); // lang 3-letter
      expect((await registerSource(e, { sourceId: "y", sourceName: "y", sourceUrl: "u", lang: "en", sourceType: "telepathy" as any })).status).toBe("rejected"); // type
      await registerSource(e, { sourceId: "reuters", sourceName: "Reuters", sourceUrl: "https://reuters.com", lang: "en", sourceType: "rss" });
      expect((await setSourceStatus(e, { sourceId: "reuters", status: "paused" })).newStatus).toBe("paused");
      expect((await setSourceStatus(e, { sourceId: "ghost", status: "active" })).status).toBe("notFound");
      expect((await listSources(e, { lang: "ja", status: "active" })).total).toBe(1);
      expect((await listSources(e, { q: "reuters" })).total).toBe(1);
    });
  });

  describe("articles FK→source", () => {
    beforeEach(async () => {
      await registerSource(e, { sourceId: "nhk", sourceName: "NHK", sourceUrl: "https://nhk.or.jp", lang: "ja", sourceType: "rss" });
    });
    it("ingests articles (FK→source, lang + quality 0-100 validated), reads, filters", async () => {
      expect((await ingestArticle(e, { articleId: "a-1", sourceId: "nhk", title: "速報: ...", lang: "ja", url: "https://nhk.or.jp/a1", category: "politics", qualityScore: 88, translatedTitle: "Breaking: ...", translatedLang: "en" })).status).toBe("ingested");
      expect((await getArticle(e, { articleId: "a-1" })).article?.qualityScore).toBe(88);
      expect((await ingestArticle(e, { articleId: "a-Q", sourceId: "nhk", title: "x", lang: "ja", url: "u", qualityScore: 150 })).status).toBe("rejected"); // quality > 100
      expect((await ingestArticle(e, { articleId: "a-L", sourceId: "nhk", title: "x", lang: "japanese" as any, url: "u" })).status).toBe("rejected"); // lang
      expect((await ingestArticle(e, { articleId: "a-G", sourceId: "ghost", title: "x", lang: "ja", url: "u" })).status).toBe("sourceNotFound");
      await ingestArticle(e, { articleId: "a-2", sourceId: "nhk", title: "low", lang: "ja", url: "u2", category: "sports", qualityScore: 40 });
      expect((await listArticles(e, { category: "politics" })).total).toBe(1);
      expect((await listArticles(e, { minQuality: 80 })).total).toBe(1);
      expect((await listArticles(e, { q: "速報" })).total).toBe(1);
    });
    it("coverage rolls up sources + articles by status / lang", async () => {
      await ingestArticle(e, { articleId: "a-1", sourceId: "nhk", title: "t", lang: "ja", url: "u" });
      const cov = await coverage(e);
      expect(cov.sourceCount).toBe(1);
      expect(cov.articleCount).toBe(1);
      expect(cov.sourcesByStatus?.active).toBe(1);
      expect(cov.articlesByLang?.ja).toBe(1);
    });
  });
});
