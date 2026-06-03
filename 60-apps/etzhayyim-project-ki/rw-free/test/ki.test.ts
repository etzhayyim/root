import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  synthesize,
  bloom,
  mapRoute,
  getStatus,
} from "../src/index.js";

describe("ki rw-free", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:ki.etzhayyim.com" });
  });

  describe("synthesize", () => {
    it("synthesizes artifact from existing absorbId", async () => {
      // First create (absorb would typically create the absorb record)
      const result = await synthesize(e, {
        synthesizeId: "syn-1",
        absorbId: "absorb-1",
        name: "Synthesized Artifact",
      });

      expect(result.status).toBe("created");
      expect(result.synthesizeUri).toBeDefined();
    });

    it("rejects synthesize when absorbId does not exist", async () => {
      const result = await synthesize(e, {
        synthesizeId: "syn-1",
        absorbId: "nonexistent-absorb",
        name: "Synthesized Artifact",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("absorbNotFound");
    });

    it("is idempotent on synthesizeId", async () => {
      const input = {
        synthesizeId: "syn-1",
        absorbId: "absorb-1",
        name: "Synthesized Artifact",
      };

      const first = await synthesize(e, input);
      expect(first.status).toBe("created");

      const second = await synthesize(e, input);
      expect(second.status).toBe("alreadyExists");
    });
  });

  describe("bloom", () => {
    beforeEach(async () => {
      await synthesize(e, {
        synthesizeId: "syn-1",
        absorbId: "absorb-1",
        name: "Synthesized Artifact",
      });
    });

    it("blooms artifact with valid artifactId", async () => {
      const result = await bloom(e, {
        bloomId: "bloom-1",
        synthesizeId: "syn-1",
        artifactId: "artifact-1",
      });

      expect(result.status).toBe("bloomed");
      expect(result.bloomUri).toBeDefined();
    });

    it("rejects bloom without existing synthesizeId", async () => {
      const result = await bloom(e, {
        bloomId: "bloom-1",
        synthesizeId: "nonexistent-synthesize",
        artifactId: "artifact-1",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("synthesizeNotFound");
    });
  });

  describe("mapRoute", () => {
    it("maps route with valid endpoints", async () => {
      const result = await mapRoute(e, {
        routeId: "route-1",
        source: "10.0.0.0/8",
        destination: "192.168.0.0/16",
        gateway: "10.0.0.1",
      });

      expect(result.status).toBe("mapped");
      expect(result.routeUri).toBeDefined();
    });

    it("is idempotent on routeId", async () => {
      const input = {
        routeId: "route-1",
        source: "10.0.0.0/8",
        destination: "192.168.0.0/16",
        gateway: "10.0.0.1",
      };

      const first = await mapRoute(e, input);
      expect(first.status).toBe("mapped");

      const second = await mapRoute(e, input);
      expect(second.status).toBe("alreadyMapped");
    });
  });

  describe("getStatus", () => {
    beforeEach(async () => {
      await synthesize(e, {
        synthesizeId: "syn-1",
        absorbId: "absorb-1",
        name: "Synthesized Artifact",
      });
      await bloom(e, {
        bloomId: "bloom-1",
        synthesizeId: "syn-1",
        artifactId: "artifact-1",
      });
    });

    it("retrieves status of synthesize operation", async () => {
      const result = await getStatus(e, { synthesizeId: "syn-1" });

      expect(result.status).toBe("created");
      expect(result.synthesizeUri).toBeDefined();
    });

    it("returns not found for nonexistent synthesizeId", async () => {
      const result = await getStatus(e, { synthesizeId: "nonexistent" });

      expect(result.error).toBe("synthesizeNotFound");
    });

    it("supports querying bloom status", async () => {
      const result = await getStatus(e, { bloomId: "bloom-1" });

      expect(result.status).toBe("bloomed");
      expect(result.bloomUri).toBeDefined();
    });
  });
});
