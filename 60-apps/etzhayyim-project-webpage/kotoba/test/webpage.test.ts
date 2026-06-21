import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerSpace,
  listSpaces,
  createPage,
  updatePage,
  setPageStatus,
  getPage,
  listPages,
  coverage,
} from "../src/index.js";

describe("webpage kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:webpage.etzhayyim.com" });
  });

  describe("space + page authoring", () => {
    it("registers spaces, creates pages (FK→space, slug-validated), reads", async () => {
      expect((await registerSpace(e, { spaceId: "S-1", name: "Docs Site", ownerDid: "did:web:alice" })).status).toBe("registered");
      expect((await createPage(e, { pageId: "P-1", spaceId: "S-1", title: "Getting Started", slug: "getting-started", body: "# Hello" })).status).toBe("created");
      expect((await createPage(e, { pageId: "P-X", spaceId: "S-1", title: "x", slug: "Bad Slug!", body: "" })).status).toBe("rejected"); // slug
      expect((await createPage(e, { pageId: "P-G", spaceId: "GHOST", title: "g", slug: "g", body: "" })).status).toBe("spaceNotFound");
      expect((await getPage(e, { pageId: "P-1" })).page?.status).toBe("draft"); // starts draft
      expect((await listSpaces(e, { ownerDid: "did:web:alice" })).total).toBe(1);
    });
  });

  describe("update + publish lifecycle", () => {
    beforeEach(async () => {
      await registerSpace(e, { spaceId: "S-1", name: "Site" });
      await createPage(e, { pageId: "P-1", spaceId: "S-1", title: "Draft", slug: "draft", body: "old", tags: ["news"] });
    });
    it("updates body/title, flips status draft→published→archived", async () => {
      expect((await updatePage(e, { pageId: "P-1", title: "Final", body: "new body" })).status).toBe("updated");
      expect((await getPage(e, { pageId: "P-1" })).page?.body).toBe("new body");
      expect((await updatePage(e, { pageId: "GHOST", body: "x" })).status).toBe("notFound");
      expect((await setPageStatus(e, { pageId: "P-1", status: "published" })).newStatus).toBe("published");
      expect((await getPage(e, { pageId: "P-1" })).page?.publishedAt).toBeTruthy();
      expect((await setPageStatus(e, { pageId: "P-1", status: "galactic" as any })).status).toBe("rejected");
      expect((await listPages(e, { status: "published" })).total).toBe(1);
      expect((await listPages(e, { tag: "news" })).total).toBe(1);
      expect((await listPages(e, { q: "new body" })).total).toBe(1);
    });
    it("coverage rolls up spaces + pages by status", async () => {
      await createPage(e, { pageId: "P-2", spaceId: "S-1", title: "Two", slug: "two", body: "b" });
      await setPageStatus(e, { pageId: "P-2", status: "published" });
      const cov = await coverage(e);
      expect(cov.spaceCount).toBe(1);
      expect(cov.pageCount).toBe(2);
      expect(cov.pagesByStatus?.draft).toBe(1);
      expect(cov.pagesByStatus?.published).toBe(1);
    });
  });
});
