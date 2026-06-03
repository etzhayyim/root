import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  recordProjection,
  listProjections,
  createIncident,
  listIncidents,
  getIncident,
  requestFreeze,
  listRequests,
  coverage,
} from "../src/index.js";

const OWNER = "did:web:crypto-asset-freeze.etzhayyim.com";

describe("crypto-asset-freeze rw-free (kotoba-E2E split)", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: OWNER });
  });

  describe("incidentProjection (PLAINTEXT public aggregate)", () => {
    it("records, dedups, validates, lists/filters by chain+status", async () => {
      expect((await recordProjection(e, { projectionId: "p1", chain: "eth", status: "open", incidentCount: 1200 })).status).toBe("recorded");
      expect((await recordProjection(e, { projectionId: "p1", chain: "eth", status: "open", incidentCount: 1200 })).status).toBe("alreadyExists");
      expect((await recordProjection(e, { projectionId: "pX", chain: "eth", status: "open", incidentCount: -1 })).status).toBe("rejected");
      expect((await recordProjection(e, { projectionId: "pY", chain: "", status: "open", incidentCount: 1 })).status).toBe("rejected");
      await recordProjection(e, { projectionId: "p2", chain: "tron", status: "frozen", incidentCount: 500 });
      expect((await listProjections(e)).total).toBe(2);
      expect((await listProjections(e, { chain: "eth" })).total).toBe(1);
      expect((await listProjections(e, { status: "frozen" })).total).toBe(1);
    });
  });

  describe("freezeIncident (E2E-ENCRYPTED CUI/LE)", () => {
    it("seals via encryptedWrite, round-trips via encryptedRead, validates", async () => {
      const ok = await createIncident(e, {
        incidentId: "INC-1",
        sourceCaseId: "YABAI-9001",
        sourceApp: "yabai",
        chain: "eth",
        priority: 90,
        walletAddresses: ["0xabc", "0xdef"],
        courtOrderCid: "bafycourt1",
      });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();
      expect(ok.walletCount).toBe(2);
      // priority > 100 rejected
      expect((await createIncident(e, { incidentId: "INCx", sourceCaseId: "c", sourceApp: "a", chain: "eth", priority: 200, walletAddresses: ["0x1"] })).status).toBe("rejected");
      // empty wallet set rejected
      expect((await createIncident(e, { incidentId: "INCy", sourceCaseId: "c", sourceApp: "a", chain: "eth", priority: 10, walletAddresses: [] })).status).toBe("rejected");
      // round-trip get
      const got = await getIncident(e, { incidentId: "INC-1" });
      expect(got.incident?.sourceCaseId).toBe("YABAI-9001");
      expect(got.incident?.walletAddresses).toEqual(["0xabc", "0xdef"]);
      expect(got.incident?.priority).toBe(90);
      expect((await getIncident(e, { incidentId: "nope" })).error).toBe("notFound");
      // list + filter
      await createIncident(e, { incidentId: "INC-2", sourceCaseId: "c2", sourceApp: "sanctions", chain: "tron", priority: 50, walletAddresses: ["Txyz"], status: "frozen" });
      expect((await listIncidents(e)).total).toBe(2);
      expect((await listIncidents(e, { chain: "eth" })).total).toBe(1);
      expect((await listIncidents(e, { status: "frozen" })).total).toBe(1);
    });

    it("enforces read-cap: a non-recipient DID cannot decrypt incidents", async () => {
      await createIncident(e, { incidentId: "INC-1", sourceCaseId: "c", sourceApp: "a", chain: "eth", priority: 80, walletAddresses: ["0xabc"] });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listIncidents(outsider)).total).toBe(0);
    });

    it("grants read-cap to an explicit LE-agency recipient", async () => {
      const agency = "did:web:fbi.le.example";
      const r = await createIncident(e, { incidentId: "INC-1", sourceCaseId: "c", sourceApp: "a", chain: "eth", priority: 80, walletAddresses: ["0xabc"], recipients: [agency] });
      expect(r.status).toBe("recorded");
      expect((await listIncidents(e)).total).toBe(1);
    });
  });

  describe("freezeRequest (E2E-ENCRYPTED CUI/LE)", () => {
    it("seals, round-trips, validates, filters by incidentId+exchange", async () => {
      const ok = await requestFreeze(e, { requestId: "REQ-1", incidentId: "INC-1", exchange: "binance", walletAddress: "0xabc", chain: "eth" });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();
      // missing wallet rejected
      expect((await requestFreeze(e, { requestId: "REQx", incidentId: "INC-1", exchange: "binance", walletAddress: "" })).status).toBe("rejected");
      // missing required fields rejected
      expect((await requestFreeze(e, { requestId: "REQy", incidentId: "", exchange: "binance", walletAddress: "0x1" })).status).toBe("rejected");
      await requestFreeze(e, { requestId: "REQ-2", incidentId: "INC-2", exchange: "kraken", walletAddress: "Txyz" });
      expect((await listRequests(e)).total).toBe(2);
      expect((await listRequests(e, { incidentId: "INC-1" })).total).toBe(1);
      expect((await listRequests(e, { exchange: "kraken" })).total).toBe(1);
    });
  });

  describe("coverage rollup", () => {
    it("counts plaintext projections + E2E incidents + E2E requests", async () => {
      await recordProjection(e, { projectionId: "p1", chain: "eth", status: "open", incidentCount: 10 });
      await recordProjection(e, { projectionId: "p2", chain: "eth", status: "frozen", incidentCount: 20 });
      await createIncident(e, { incidentId: "INC-1", sourceCaseId: "c", sourceApp: "a", chain: "eth", priority: 70, walletAddresses: ["0xabc"] });
      await requestFreeze(e, { requestId: "REQ-1", incidentId: "INC-1", exchange: "binance", walletAddress: "0xabc" });
      const cov = await coverage(e);
      expect(cov.incidentProjectionCount).toBe(2);
      expect(cov.freezeIncidentCount).toBe(1);
      expect(cov.freezeRequestCount).toBe(1);
      expect(cov.projectionsByChain?.eth).toBe(2);
    });
  });
});
