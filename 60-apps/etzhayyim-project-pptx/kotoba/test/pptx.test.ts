import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  createPresentation,
  getPresentation,
  listPresentations,
  addSlide,
  listSlides,
  addShape,
  listShapes,
  addTextRun,
  listTextRuns,
  coverage,
} from "../src/index.js";

const CID = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi";
const OWNER = "did:web:user.example.com";

describe("pptx kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:pptx.etzhayyim.com" });
  });

  describe("presentation + slides", () => {
    it("creates presentation, reads, lists by visibility + search, adds slides (FK)", async () => {
      expect((await createPresentation(e, { presentationId: "P-1", title: "Q3 Deck", ownerDid: OWNER, visibility: "public", sourceCid: CID })).status).toBe("created");
      expect((await getPresentation(e, { presentationId: "P-1" })).presentation?.visibility).toBe("public");
      expect((await createPresentation(e, { presentationId: "P-X", title: "x", ownerDid: "nope" })).status).toBe("rejected");
      expect((await listPresentations(e, { visibility: "public" })).total).toBe(1);
      expect((await listPresentations(e, { q: "q3" })).total).toBe(1);
      expect((await addSlide(e, { slideId: "S-1", presentationId: "P-1", slideIndex: 0, layout: "title" })).status).toBe("added");
      expect((await addSlide(e, { slideId: "S-X", presentationId: "P-1", slideIndex: -1 })).status).toBe("rejected");
      expect((await addSlide(e, { slideId: "S-Y", presentationId: "GHOST", slideIndex: 0 })).status).toBe("presentationNotFound");
      expect((await listSlides(e, { presentationId: "P-1" })).total).toBe(1);
    });
  });

  describe("shapes + text runs (document tree)", () => {
    beforeEach(async () => {
      await createPresentation(e, { presentationId: "P-1", title: "Deck", ownerDid: OWNER });
      await addSlide(e, { slideId: "S-1", presentationId: "P-1", slideIndex: 0 });
    });
    it("adds shapes (EMU geometry, FK→slide), rejects bad geometry/type/missing slide", async () => {
      expect((await addShape(e, { shapeId: "SH-1", slideId: "S-1", shapeType: "text", xEmu: 914400, yEmu: 914400, widthEmu: 5486400, heightEmu: 1828800 })).status).toBe("added");
      expect((await addShape(e, { shapeId: "SH-2", slideId: "S-1", shapeType: "image", xEmu: 0, yEmu: 0, widthEmu: 100, heightEmu: 100, contentCid: CID })).status).toBe("added");
      expect((await addShape(e, { shapeId: "SH-X", slideId: "S-1", shapeType: "warp" as any, xEmu: 0, yEmu: 0, widthEmu: 1, heightEmu: 1 })).status).toBe("rejected");
      expect((await addShape(e, { shapeId: "SH-Y", slideId: "S-1", shapeType: "text", xEmu: -1, yEmu: 0, widthEmu: 1, heightEmu: 1 })).status).toBe("rejected");
      expect((await addShape(e, { shapeId: "SH-Z", slideId: "GHOST", shapeType: "text", xEmu: 0, yEmu: 0, widthEmu: 1, heightEmu: 1 })).status).toBe("slideNotFound");
      expect((await listShapes(e, { slideId: "S-1", shapeType: "image" })).total).toBe(1);
    });
    it("adds text runs (FK→shape, half-point font); coverage rolls up the tree", async () => {
      await addShape(e, { shapeId: "SH-1", slideId: "S-1", shapeType: "text", xEmu: 0, yEmu: 0, widthEmu: 100, heightEmu: 100 });
      expect((await addTextRun(e, { runId: "R-1", shapeId: "SH-1", text: "Hello", bold: true, fontHalfPt: 48 })).status).toBe("added");
      expect((await addTextRun(e, { runId: "R-X", shapeId: "GHOST", text: "x" })).status).toBe("shapeNotFound");
      expect((await listTextRuns(e, { shapeId: "SH-1" })).total).toBe(1);
      const cov = await coverage(e);
      expect(cov.presentationCount).toBe(1);
      expect(cov.slideCount).toBe(1);
      expect(cov.shapeCount).toBe(1);
      expect(cov.textRunCount).toBe(1);
      expect(cov.presentationsByVisibility?.private).toBe(1);
      expect(cov.shapesByType?.text).toBe(1);
    });
  });
});
