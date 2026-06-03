import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerEmitter,
  listEmitters,
  recordFlow,
  listFlows,
  recordAnomaly,
  reviewAnomaly,
  listAnomalies,
  coverage,
} from "../src/index.js";

const GOV = "did:web:gov-jpn.etzhayyim.com";
const LE = "did:web:legal-entity.etzhayyim.com:entity:acme";

describe("resource-flow rw-free", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:resource-flow.etzhayyim.com" });
  });

  describe("emitter registry", () => {
    it("registers emitters (sourceType + flowClasses validated), lists", async () => {
      expect((await registerEmitter(e, { emitterDid: GOV, label: "Japan Gov", sourceType: "gov", flowClasses: ["currency", "personnel"] })).status).toBe("registered");
      expect((await registerEmitter(e, { emitterDid: "did:x", label: "x", sourceType: "alien" as any })).status).toBe("rejected"); // sourceType
      expect((await registerEmitter(e, { emitterDid: "did:y", label: "y", sourceType: "gov", flowClasses: ["bogus" as any] })).status).toBe("rejected"); // flowClass
      await registerEmitter(e, { emitterDid: LE, label: "Acme KK", sourceType: "legalEntity" });
      expect((await listEmitters(e, { sourceType: "gov" })).total).toBe(1);
      expect((await listEmitters(e, { q: "acme" })).total).toBe(1);
    });
  });

  describe("flow edges FK to emitter", () => {
    beforeEach(async () => {
      await registerEmitter(e, { emitterDid: GOV, label: "Japan Gov", sourceType: "gov" });
    });
    it("records flows (FK→emitter, class + amount-string validated)", async () => {
      expect((await recordFlow(e, { flowId: "F-1", flowClass: "currency", sourceDid: GOV, counterpartyDid: LE, amount: "5000000000", unit: "JPY", observedAt: "2026-05-30" })).status).toBe("recorded");
      expect((await recordFlow(e, { flowId: "F-X", flowClass: "antimatter" as any, sourceDid: GOV, counterpartyDid: LE, amount: "1", observedAt: "x" })).status).toBe("rejected"); // class
      expect((await recordFlow(e, { flowId: "F-F", flowClass: "currency", sourceDid: GOV, counterpartyDid: LE, amount: "12.5", observedAt: "x" })).status).toBe("rejected"); // float-string
      expect((await recordFlow(e, { flowId: "F-G", flowClass: "currency", sourceDid: "did:web:ghost", counterpartyDid: LE, amount: "1", observedAt: "x" })).status).toBe("emitterNotFound");
      expect((await listFlows(e, { flowClass: "currency", sourceDid: GOV })).total).toBe(1);
    });
  });

  describe("anomalies + review + coverage", () => {
    beforeEach(async () => {
      await registerEmitter(e, { emitterDid: GOV, label: "Japan Gov", sourceType: "gov" });
    });
    it("records anomaly (FK→emitter), reviews (ACK/DIS/ESC), filters", async () => {
      expect((await recordAnomaly(e, { anomalyId: "A-1", flowClass: "currency", sourceDid: GOV, severity: "high", description: "spike vs baseline", detectedAt: "2026-06-01" })).status).toBe("recorded");
      expect((await recordAnomaly(e, { anomalyId: "A-X", flowClass: "currency", sourceDid: GOV, severity: "extreme" as any, description: "x", detectedAt: "x" })).status).toBe("rejected"); // severity
      expect((await recordAnomaly(e, { anomalyId: "A-G", flowClass: "currency", sourceDid: "did:web:ghost", severity: "low", description: "x", detectedAt: "x" })).status).toBe("emitterNotFound");
      expect((await reviewAnomaly(e, { anomalyId: "A-1", reviewStatus: "escalated" })).newStatus).toBe("escalated");
      expect((await reviewAnomaly(e, { anomalyId: "GHOST", reviewStatus: "acked" })).status).toBe("notFound");
      expect((await listAnomalies(e, { reviewStatus: "escalated" })).total).toBe(1);
      expect((await listAnomalies(e, { reviewStatus: "open" })).total).toBe(0);
    });
    it("coverage rolls up emitters/flows/anomalies by class/severity", async () => {
      await recordFlow(e, { flowId: "F-1", flowClass: "currency", sourceDid: GOV, counterpartyDid: LE, amount: "100", observedAt: "2026-05-30" });
      await recordAnomaly(e, { anomalyId: "A-1", flowClass: "currency", sourceDid: GOV, severity: "critical", description: "x", detectedAt: "2026-06-01" });
      const cov = await coverage(e);
      expect(cov.emitterCount).toBe(1);
      expect(cov.flowCount).toBe(1);
      expect(cov.anomalyCount).toBe(1);
      expect(cov.flowsByClass?.currency).toBe(1);
      expect(cov.anomaliesBySeverity?.critical).toBe(1);
    });
  });
});
