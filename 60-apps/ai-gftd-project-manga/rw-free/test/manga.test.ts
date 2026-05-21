import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  createTitle,
  createChapter,
  publishChapter,
  updateChapterStatus,
  listChapters,
  submitFromNarou,
} from "../src/index.js";

describe("manga rw-free", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:manga.etzhayyim.com" });
  });

  describe("createTitle + createChapter", () => {
    beforeEach(async () => {
      await createTitle(e, {
        title_id: "bleach-arc1",
        title: "Bleach",
      });
    });

    it("creates chapter under existing title", async () => {
      const result = await createChapter(e, {
        title_id: "bleach-arc1",
        chapter_num: 1,
        episode_title: "Chapter 1",
      });

      expect(result.status).toBe("registered");
      expect(result.chapter_uri).toBeDefined();
    });

    it("rejects chapter without title", async () => {
      const result = await createChapter(e, {
        title_id: "nonexistent",
        chapter_num: 1,
        episode_title: "Chapter 1",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("titleNotFound");
    });
  });

  describe("publishChapter state machine invariant", () => {
    beforeEach(async () => {
      await createTitle(e, {
        title_id: "aot",
        title: "Attack on Titan",
      });
      await createChapter(e, {
        title_id: "aot",
        chapter_num: 1,
        episode_title: "Ep 1",
      });
    });

    it("publishChapter succeeds from draft state", async () => {
      const result = await publishChapter(e, {
        chapter_id: "aot-ch1",
      });

      expect(result.status).toBe("published");
      expect(result.chapter_id).toBe("aot-ch1");
    });

    it("publishChapter succeeds from in_review state", async () => {
      await updateChapterStatus(e, {
        chapter_id: "aot-ch1",
        status: "in_review",
      });

      const result = await publishChapter(e, {
        chapter_id: "aot-ch1",
      });

      expect(result.status).toBe("published");
    });

    it("publishChapter rejects from archived state", async () => {
      await updateChapterStatus(e, {
        chapter_id: "aot-ch1",
        status: "archived",
      });

      const result = await publishChapter(e, {
        chapter_id: "aot-ch1",
      });

      expect(result.status).toBe("invalidState");
    });

    it("idempotent: publishChapter twice returns published", async () => {
      const first = await publishChapter(e, { chapter_id: "aot-ch1" });
      expect(first.status).toBe("published");

      const second = await publishChapter(e, { chapter_id: "aot-ch1" });
      expect(second.status).toBe("published");
    });
  });

  describe("submitFromNarou creates title with Narou source", () => {
    it("submitFromNarou creates Title record", async () => {
      const result = await submitFromNarou(e, {
        narou_title_id: "n123456",
        title: "Web Novel Title",
      });

      expect(result.status).toBe("registered");
      expect(result.title_id).toBeDefined();
    });

    it("submitFromNarou creates chapter if narou_chapter_id provided", async () => {
      const result = await submitFromNarou(e, {
        narou_title_id: "n654321",
        title: "Another Novel",
        narou_chapter_id: "ch1",
        episode_title: "First Chapter",
      });

      expect(result.status).toBe("registered");
      expect(result.chapter_id).toBeDefined();
    });
  });

  describe("listChapters filter by status", () => {
    beforeEach(async () => {
      await createTitle(e, { title_id: "jjk", title: "Jujutsu Kaisen" });
      await createChapter(e, {
        title_id: "jjk",
        chapter_num: 1,
        episode_title: "Ch1",
      });
      await createChapter(e, {
        title_id: "jjk",
        chapter_num: 2,
        episode_title: "Ch2",
      });
      await updateChapterStatus(e, {
        chapter_id: "jjk-ch2",
        status: "published",
      });
    });

    it("lists chapters by title_id", async () => {
      const result = await listChapters(e, { title_id: "jjk" });
      expect(result.chapters.length).toBe(2);
    });

    it("filters chapters by status", async () => {
      const result = await listChapters(e, {
        title_id: "jjk",
        status: "published",
      });
      expect(result.chapters.length).toBe(1);
      expect(result.chapters[0]?.status).toBe("published");
    });
  });
});
