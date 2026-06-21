import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  recordResearch,
  getResearch,
  concludeResearch,
  listResearch,
  defineCapability,
  listCapabilities,
  proposeAction,
  setActionStatus,
  listActions,
  coverage,
} from "../src/index.js";

describe("public-kafun-bokumetsu kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:kafun-bokumetsu.etzhayyim.com" });
  });

  describe("research + capabilities", () => {
    it("records research (category validated), reads, concludes, lists; defines capabilities", async () => {
      expect((await recordResearch(e, { researchId: "R-1", category: "pollen-source", title: "スギ植林削減" })).status).toBe("recorded");
      expect((await getResearch(e, { researchId: "R-1" })).research?.status).toBe("open");
      expect((await recordResearch(e, { researchId: "R-X", category: "weather" as any, title: "x" })).status).toBe("rejected");
      await recordResearch(e, { researchId: "R-2", category: "medical", title: "免疫療法" });
      expect((await listResearch(e, { category: "medical" })).total).toBe(1);
      expect((await listResearch(e, { q: "スギ" })).total).toBe(1);
      expect((await concludeResearch(e, { researchId: "R-1" })).status).toBe("concluded");
      expect((await concludeResearch(e, { researchId: "R-1" })).status).toBe("rejected");
      expect((await defineCapability(e, { capabilityId: "CAP-1", name: "drone-spraying" })).status).toBe("defined");
      expect((await listCapabilities(e)).total).toBe(1);
    });
  });

  describe("actions (FK→research + capability map)", () => {
    beforeEach(async () => {
      await recordResearch(e, { researchId: "R-1", category: "technology", title: "ドローン散布" });
      await defineCapability(e, { capabilityId: "CAP-1", name: "drone-spraying" });
    });
    it("proposes actions, rejects missing research; advances status with terminal guard", async () => {
      expect((await proposeAction(e, { actionId: "A-1", title: "雄花抑制剤散布", researchId: "R-1", capabilityRefs: ["CAP-1"] })).status).toBe("proposed");
      expect((await proposeAction(e, { actionId: "A-X", title: "x", researchId: "GHOST" })).status).toBe("researchNotFound");
      expect((await setActionStatus(e, { actionId: "A-1", status: "inProgress" })).newStatus).toBe("inProgress");
      expect((await setActionStatus(e, { actionId: "A-1", status: "done" })).newStatus).toBe("done");
      expect((await setActionStatus(e, { actionId: "A-1", status: "proposed" })).status).toBe("rejected"); // terminal
      expect((await listActions(e, { researchId: "R-1", status: "done" })).total).toBe(1);
      expect((await listActions(e, { capabilityRef: "CAP-1" })).total).toBe(1);
    });
    it("coverage rolls up the three collections", async () => {
      await proposeAction(e, { actionId: "A-1", title: "x", researchId: "R-1" });
      const cov = await coverage(e);
      expect(cov.researchCount).toBe(1);
      expect(cov.actionCount).toBe(1);
      expect(cov.capabilityCount).toBe(1);
      expect(cov.researchByCategory?.technology).toBe(1);
      expect(cov.actionsByStatus?.proposed).toBe(1);
    });
  });
});
