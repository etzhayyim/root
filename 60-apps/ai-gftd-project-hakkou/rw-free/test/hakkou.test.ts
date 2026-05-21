import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerBatch,
  updateFermentStatus,
  getBatch,
  listBatches,
} from "../src/index.js";

describe("hakkou rw-free", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:hakkou.etzhayyim.com" });
  });

  describe("registerBatch", () => {
    it("registers a fermentation batch", async () => {
      const result = await registerBatch(e, {
        batchId: "batch-2024-001",
        batchType: "sake",
        startDate: "2024-01-01",
        targetEndDate: "2024-03-01",
      });

      expect(result.status).toBe("created");
      expect(result.batchUri).toBeDefined();
    });

    it("is idempotent on batchId", async () => {
      const input = {
        batchId: "batch-2024-001",
        batchType: "sake",
        startDate: "2024-01-01",
        targetEndDate: "2024-03-01",
      };

      const first = await registerBatch(e, input);
      expect(first.status).toBe("created");

      const second = await registerBatch(e, input);
      expect(second.status).toBe("alreadyExists");
    });
  });

  describe("updateFermentStatus", () => {
    beforeEach(async () => {
      await registerBatch(e, {
        batchId: "batch-2024-001",
        batchType: "sake",
        startDate: "2024-01-01",
        targetEndDate: "2024-03-01",
      });
    });

    it("transitions batch from pending to running", async () => {
      const result = await updateFermentStatus(e, {
        statusUpdateId: "update-1",
        batchId: "batch-2024-001",
        newStatus: "running",
      });

      expect(result.status).toBe("updated");
      expect(result.previousStatus).toBe("pending");
      expect(result.newStatus).toBe("running");
    });

    it("transitions batch from running to done", async () => {
      await updateFermentStatus(e, {
        statusUpdateId: "update-1",
        batchId: "batch-2024-001",
        newStatus: "running",
      });

      const result = await updateFermentStatus(e, {
        statusUpdateId: "update-2",
        batchId: "batch-2024-001",
        newStatus: "done",
      });

      expect(result.status).toBe("updated");
      expect(result.previousStatus).toBe("running");
      expect(result.newStatus).toBe("done");
    });

    it("rejects invalid status transitions", async () => {
      const result = await updateFermentStatus(e, {
        statusUpdateId: "update-invalid",
        batchId: "batch-2024-001",
        newStatus: "invalid-status",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("invalidStatus");
    });
  });

  describe("getBatch", () => {
    beforeEach(async () => {
      await registerBatch(e, {
        batchId: "batch-2024-001",
        batchType: "sake",
        startDate: "2024-01-01",
        targetEndDate: "2024-03-01",
      });
    });

    it("retrieves batch by id", async () => {
      const result = await getBatch(e, { batchId: "batch-2024-001" });

      expect(result.batch).toBeDefined();
      expect(result.batch?.batchType).toBe("sake");
      expect(result.batch?.batchId).toBe("batch-2024-001");
    });

    it("returns notFound for nonexistent batch", async () => {
      const result = await getBatch(e, { batchId: "nonexistent" });

      expect(result.error).toBe("notFound");
    });
  });

  describe("listBatches", () => {
    beforeEach(async () => {
      await registerBatch(e, {
        batchId: "batch-2024-001",
        batchType: "sake",
        startDate: "2024-01-01",
        targetEndDate: "2024-03-01",
      });
      await registerBatch(e, {
        batchId: "batch-2024-002",
        batchType: "miso",
        startDate: "2024-01-15",
        targetEndDate: "2024-12-31",
      });
    });

    it("lists all batches", async () => {
      const result = await listBatches(e, {});

      expect(result.items.length).toBeGreaterThanOrEqual(2);
    });

    it("filters by batchType", async () => {
      const result = await listBatches(e, { batchType: "sake" });

      expect(result.items.every((b) => b.batchType === "sake")).toBe(true);
    });
  });
});
