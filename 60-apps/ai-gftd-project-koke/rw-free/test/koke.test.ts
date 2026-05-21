import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerCarbon,
  releaseCarbon,
  recordOffset,
  listOffsets,
} from "../src/index.js";

describe("koke rw-free", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:koke.etzhayyim.com" });
  });

  describe("registerCarbon", () => {
    it("registers a carbon credit batch", async () => {
      const result = await registerCarbon(e, {
        batchId: "batch-2024-001",
        totalCredits: 1000,
        vintage: 2024,
        methodology: "solar-pv",
      });

      expect(result.status).toBe("created");
      expect(result.batchUri).toBeDefined();
    });

    it("is idempotent on batchId", async () => {
      const input = {
        batchId: "batch-2024-001",
        totalCredits: 1000,
        vintage: 2024,
        methodology: "solar-pv",
      };

      const first = await registerCarbon(e, input);
      expect(first.status).toBe("created");

      const second = await registerCarbon(e, input);
      expect(second.status).toBe("alreadyExists");
    });
  });

  describe("releaseCarbon", () => {
    beforeEach(async () => {
      await registerCarbon(e, {
        batchId: "batch-2024-001",
        totalCredits: 1000,
        vintage: 2024,
        methodology: "solar-pv",
      });
    });

    it("releases carbon credits from batch", async () => {
      const result = await releaseCarbon(e, {
        releaseId: "release-1",
        batchId: "batch-2024-001",
        releasedCredits: 500,
      });

      expect(result.status).toBe("released");
      expect(result.releaseUri).toBeDefined();
    });

    it("is idempotent on releaseId (second call returns alreadyReleased)", async () => {
      const input = {
        releaseId: "release-1",
        batchId: "batch-2024-001",
        releasedCredits: 500,
      };

      const first = await releaseCarbon(e, input);
      expect(first.status).toBe("released");

      const second = await releaseCarbon(e, input);
      expect(second.status).toBe("alreadyReleased");
    });
  });

  describe("recordOffset", () => {
    beforeEach(async () => {
      await registerCarbon(e, {
        batchId: "batch-2024-001",
        totalCredits: 1000,
        vintage: 2024,
        methodology: "solar-pv",
      });
      await releaseCarbon(e, {
        releaseId: "release-1",
        batchId: "batch-2024-001",
        releasedCredits: 500,
      });
    });

    it("records an offset using released credits", async () => {
      const result = await recordOffset(e, {
        offsetId: "offset-1",
        releaseId: "release-1",
        offsetCredits: 100,
        project: "solar-farm-xyz",
      });

      expect(result.status).toBe("recorded");
      expect(result.offsetUri).toBeDefined();
    });

    it("is idempotent on offsetId", async () => {
      const input = {
        offsetId: "offset-1",
        releaseId: "release-1",
        offsetCredits: 100,
        project: "solar-farm-xyz",
      };

      const first = await recordOffset(e, input);
      expect(first.status).toBe("recorded");

      const second = await recordOffset(e, input);
      expect(second.status).toBe("alreadyRecorded");
    });
  });

  describe("listOffsets", () => {
    beforeEach(async () => {
      await registerCarbon(e, {
        batchId: "batch-2024-001",
        totalCredits: 1000,
        vintage: 2024,
        methodology: "solar-pv",
      });
      await releaseCarbon(e, {
        releaseId: "release-1",
        batchId: "batch-2024-001",
        releasedCredits: 500,
      });
      await recordOffset(e, {
        offsetId: "offset-1",
        releaseId: "release-1",
        offsetCredits: 100,
        project: "solar-farm-xyz",
      });
      await recordOffset(e, {
        offsetId: "offset-2",
        releaseId: "release-1",
        offsetCredits: 150,
        project: "wind-farm-abc",
      });
    });

    it("lists all offsets", async () => {
      const result = await listOffsets(e, {});

      expect(result.items.length).toBeGreaterThanOrEqual(2);
    });

    it("filters by project", async () => {
      const result = await listOffsets(e, { project: "solar-farm-xyz" });

      expect(
        result.items.every((o) => o.project === "solar-farm-xyz")
      ).toBe(true);
    });
  });
});
