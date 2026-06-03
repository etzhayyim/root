import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import { storeSpore, listSpores, germinate } from "../src/index.js";

describe("houshi rw-free", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:houshi.etzhayyim.com" });
  });

  describe("storeSpore", () => {
    it("stores a spore with valid input", async () => {
      const result = await storeSpore(e, {
        sporeVertexId: "spore-001",
        custodianDid: "did:plc:custodian",
        originAgentDid: "did:plc:origin",
        quorumN: 2,
        blobCbor: "cbor-data-here-256-bytes".padEnd(256, "x"),
        revivalKeyHint: "hint-1234",
      });

      expect(result.status).toBe("registered");
      expect(result.sporeUri).toBeDefined();
      expect(result.did).toBeDefined();
      expect(result.sporeVertexId).toBe("spore-001");
    });

    it("rejects spore with missing required fields", async () => {
      const result = await storeSpore(e, {
        sporeVertexId: "",
        custodianDid: "did:plc:custodian",
        originAgentDid: "did:plc:origin",
        quorumN: 2,
        blobCbor: "data",
        revivalKeyHint: "hint",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("missingRequiredFields");
    });

    it("rejects spore with quorumN < 1", async () => {
      const result = await storeSpore(e, {
        sporeVertexId: "spore-002",
        custodianDid: "did:plc:custodian",
        originAgentDid: "did:plc:origin",
        quorumN: 0,
        blobCbor: "data",
        revivalKeyHint: "hint",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("quorumNMinimumOne");
    });

    it("is idempotent on sporeVertexId", async () => {
      const input = {
        sporeVertexId: "spore-dup",
        custodianDid: "did:plc:custodian",
        originAgentDid: "did:plc:origin",
        quorumN: 1,
        blobCbor: "x".repeat(256),
        revivalKeyHint: "hint",
      };

      const first = await storeSpore(e, input);
      expect(first.status).toBe("registered");
      const firstUri = first.sporeUri;

      const second = await storeSpore(e, input);
      expect(second.status).toBe("alreadyExists");
      expect(second.sporeUri).toBe(firstUri);
    });
  });

  describe("listSpores", () => {
    beforeEach(async () => {
      await storeSpore(e, {
        sporeVertexId: "spore-a",
        custodianDid: "did:plc:alice",
        originAgentDid: "did:plc:agent-1",
        quorumN: 1,
        blobCbor: "x".repeat(256),
        revivalKeyHint: "hint-a",
      });
      await storeSpore(e, {
        sporeVertexId: "spore-b",
        custodianDid: "did:plc:bob",
        originAgentDid: "did:plc:agent-1",
        quorumN: 2,
        blobCbor: "y".repeat(256),
        revivalKeyHint: "hint-b",
      });
      await storeSpore(e, {
        sporeVertexId: "spore-c",
        custodianDid: "did:plc:alice",
        originAgentDid: "did:plc:agent-2",
        quorumN: 1,
        blobCbor: "z".repeat(256),
        revivalKeyHint: "hint-c",
      });
    });

    it("lists all spores", async () => {
      const result = await listSpores(e, {});

      expect(result.spores.length).toBe(3);
      expect(result.total).toBe(3);
    });

    it("filters spores by custodianDid", async () => {
      const result = await listSpores(e, { custodianDid: "did:plc:alice" });

      expect(result.spores.length).toBe(2);
      expect(result.spores.every((s) => s.custodyCount >= 1)).toBe(true);
    });

    it("filters spores by originAgentDid", async () => {
      const result = await listSpores(e, { originAgentDid: "did:plc:agent-1" });

      expect(result.spores.length).toBe(2);
      expect(result.spores.every((s) => s.originAgentDid === "did:plc:agent-1")).toBe(true);
    });

    it("excludes germinated spores by default", async () => {
      await germinate(e, {
        sporeVertexId: "spore-a",
        revivalKey: "key-a",
        newAgentDid: "did:plc:kobo-a",
      });

      const result = await listSpores(e, {});

      // spore-a is germinated, so should be excluded
      expect(result.spores.length).toBe(2);
      expect(result.spores.every((s) => !s.germinatedAt)).toBe(true);
    });

    it("includes germinated spores with includeGerminated=true", async () => {
      await germinate(e, {
        sporeVertexId: "spore-b",
        revivalKey: "key-b",
        newAgentDid: "did:plc:kobo-b",
      });

      const result = await listSpores(e, { includeGerminated: true });

      expect(result.spores.length).toBe(3);
      const germinated = result.spores.find((s) => s.vertexId === "spore-b");
      expect(germinated?.germinatedAt).toBeDefined();
    });

    it("respects limit parameter", async () => {
      const result = await listSpores(e, { limit: 2 });

      expect(result.spores.length).toBeLessThanOrEqual(2);
    });
  });

  describe("germinate", () => {
    beforeEach(async () => {
      await storeSpore(e, {
        sporeVertexId: "spore-test",
        custodianDid: "did:plc:custodian",
        originAgentDid: "did:plc:origin",
        quorumN: 1,
        blobCbor: "x".repeat(256),
        revivalKeyHint: "test-hint",
      });
    });

    it("germinates an existing spore", async () => {
      const result = await germinate(e, {
        sporeVertexId: "spore-test",
        revivalKey: "actual-key",
        newAgentDid: "did:plc:new-agent",
      });

      expect(result.status).toBe("germinated");
      expect(result.agentVertexId).toBe("kobo-spore-test");
      expect(result.agentDid).toBe("did:plc:new-agent");
      expect(result.germinatedAt).toBeDefined();
      expect(result.prionsRestored).toBeGreaterThan(0);
    });

    it("rejects germinate with missing required fields", async () => {
      const result = await germinate(e, {
        sporeVertexId: "",
        revivalKey: "key",
        newAgentDid: "did:plc:agent",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("missingRequiredFields");
    });

    it("returns sporeNotFound for non-existent spore", async () => {
      const result = await germinate(e, {
        sporeVertexId: "spore-missing",
        revivalKey: "key",
        newAgentDid: "did:plc:agent",
      });

      expect(result.status).toBe("sporeNotFound");
    });

    it("is idempotent on sporeVertexId (second germinate returns alreadyGerminated)", async () => {
      const first = await germinate(e, {
        sporeVertexId: "spore-test",
        revivalKey: "key-1",
        newAgentDid: "did:plc:agent-1",
      });

      expect(first.status).toBe("germinated");

      const second = await germinate(e, {
        sporeVertexId: "spore-test",
        revivalKey: "key-2",
        newAgentDid: "did:plc:agent-2",
      });

      expect(second.status).toBe("alreadyGerminated");
      expect(second.germinatedAt).toBe(first.germinatedAt);
    });

    it("computes prionsRestored from blobCbor length", async () => {
      const result = await germinate(e, {
        sporeVertexId: "spore-test",
        revivalKey: "key",
        newAgentDid: "did:plc:agent",
      });

      // blobCbor is "x".repeat(256), so prionsRestored = 256 / 128 = 2
      expect(result.prionsRestored).toBe(2);
    });
  });

  describe("integration: spore lifecycle", () => {
    it("stores, lists, and germinates a spore", async () => {
      const storeResult = await storeSpore(e, {
        sporeVertexId: "lifecycle-spore",
        custodianDid: "did:plc:curator",
        originAgentDid: "did:plc:origin-agent",
        quorumN: 1,
        blobCbor: "data".padEnd(512, "x"),
        revivalKeyHint: "hint-lifecycle",
      });

      expect(storeResult.status).toBe("registered");

      const listResult = await listSpores(e, {
        custodianDid: "did:plc:curator",
      });

      expect(listResult.spores.length).toBe(1);
      expect(listResult.spores[0]?.vertexId).toBe("lifecycle-spore");
      expect(listResult.spores[0]?.germinatedAt).toBeUndefined();

      const germResult = await germinate(e, {
        sporeVertexId: "lifecycle-spore",
        revivalKey: "final-key",
        newAgentDid: "did:plc:kobo-agent",
      });

      expect(germResult.status).toBe("germinated");

      const finalList = await listSpores(e, {
        custodianDid: "did:plc:curator",
        includeGerminated: true,
      });

      const final = finalList.spores[0];
      expect(final?.germinatedAt).toBe(germResult.germinatedAt);
    });
  });
});
