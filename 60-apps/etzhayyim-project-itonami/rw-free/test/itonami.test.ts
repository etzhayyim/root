import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  defineEngine,
  setCertification,
  getEngine,
  listEngines,
  recordAssembly,
  listAssemblies,
  addProcurement,
  listProcurement,
  recordTest,
  listTests,
  coverage,
} from "../src/index.js";

describe("itonami rw-free", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:itonami.etzhayyim.com" });
  });

  describe("engine design + certification", () => {
    it("defines (integerized), reads, lists, advances cert; validates", async () => {
      expect((await defineEngine(e, { engineId: "CFM56-7B", designCode: "CFM56-7B", engineType: "turbofan", thrustRatingKn: 12100, massKg: 2380 })).status).toBe("defined");
      expect((await getEngine(e, { engineId: "CFM56-7B" })).engine?.certificationStatus).toBe("uncertified");
      expect((await defineEngine(e, { engineId: "X", designCode: "x", engineType: "warp" as any, thrustRatingKn: 1, massKg: 1 })).status).toBe("rejected");
      expect((await defineEngine(e, { engineId: "Y", designCode: "y", engineType: "turbofan", thrustRatingKn: 0, massKg: 1 })).status).toBe("rejected");
      expect((await setCertification(e, { engineId: "CFM56-7B", certificationStatus: "in_progress" })).newStatus).toBe("in_progress");
      expect((await setCertification(e, { engineId: "CFM56-7B", certificationStatus: "retired" })).newStatus).toBe("retired");
      expect((await setCertification(e, { engineId: "CFM56-7B", certificationStatus: "certified" })).status).toBe("rejected"); // retired
      expect((await listEngines(e, { engineType: "turbofan" })).total).toBe(1);
    });
  });

  describe("assembly / procurement / test against an engine", () => {
    beforeEach(async () => {
      await defineEngine(e, { engineId: "E-1", designCode: "CFM56-7B", engineType: "turbofan", thrustRatingKn: 12100, massKg: 2380 });
    });
    it("records assembly (FK→engine, per-mille), rejects bad permille/missing engine", async () => {
      expect((await recordAssembly(e, { assemblyId: "A-1", engineId: "E-1", phaseCode: "assembly", progressPermille: 650 })).status).toBe("recorded");
      expect((await recordAssembly(e, { assemblyId: "A-X", engineId: "E-1", phaseCode: "assembly", progressPermille: 1500 })).status).toBe("rejected");
      expect((await recordAssembly(e, { assemblyId: "A-X", engineId: "GHOST", phaseCode: "assembly", progressPermille: 100 })).status).toBe("engineNotFound");
      expect((await listAssemblies(e, { engineId: "E-1", phaseCode: "assembly" })).total).toBe(1);
    });
    it("adds procurement (UNSPSC/ISIC validated, FK→engine)", async () => {
      expect((await addProcurement(e, { itemId: "P-1", engineId: "E-1", unspscCode: "25171700", supplierIsicCode: "3030", quantity: 4, unitCostJpy: 1500000 })).status).toBe("added");
      expect((await addProcurement(e, { itemId: "P-X", engineId: "E-1", unspscCode: "123", supplierIsicCode: "3030", quantity: 1, unitCostJpy: 1 })).status).toBe("rejected"); // unspsc
      expect((await addProcurement(e, { itemId: "P-Y", engineId: "E-1", unspscCode: "25171700", supplierIsicCode: "30", quantity: 1, unitCostJpy: 1 })).status).toBe("rejected"); // isic
      expect((await listProcurement(e, { engineId: "E-1", supplierIsicCode: "3030" })).total).toBe(1);
    });
    it("records tests + coverage rolls up all four with derived totals", async () => {
      await recordTest(e, { testId: "T-1", engineId: "E-1", testType: "bench", outcomeCode: "pass", thrustAchievedKn: 12050, durationSeconds: 3600 });
      await recordTest(e, { testId: "T-2", engineId: "E-1", testType: "flight", outcomeCode: "conditional", thrustAchievedKn: 11900, durationSeconds: 7200 });
      expect((await listTests(e, { outcomeCode: "pass" })).total).toBe(1);
      await recordAssembly(e, { assemblyId: "A-1", engineId: "E-1", phaseCode: "testing", progressPermille: 800 });
      await addProcurement(e, { itemId: "P-1", engineId: "E-1", unspscCode: "25171700", supplierIsicCode: "3030", quantity: 4, unitCostJpy: 1500000 });
      const cov = await coverage(e);
      expect(cov.engineCount).toBe(1);
      expect(cov.assemblyCount).toBe(1);
      expect(cov.procurementCount).toBe(1);
      expect(cov.testCount).toBe(2);
      expect(cov.enginesByCertStatus?.uncertified).toBe(1);
      expect(cov.testsByOutcome?.pass).toBe(1);
      expect(cov.totalProcurementJpy).toBe(6000000); // 4 × 1,500,000
    });
  });
});
