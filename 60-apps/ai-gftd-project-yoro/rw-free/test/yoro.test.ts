import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  projectEntity,
  productResearch,
  activitySeen,
  shinkaEvolution,
  shinkaKnowledge,
  ingestProductCategory,
  listApps,
  health,
  stats,
  listPosts,
  listProductResearch,
  listActivities,
  getActivityTrace,
  markSeen,
  getTimeline,
  getAuthorFeed,
  getPostThread,
  getRankedFeed,
  getDiscoverFeed,
  getFollowers,
  getFollows,
  getProfile,
  searchActors,
} from "../src/index.js";

describe("yoro rw-free", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:yoro.etzhayyim.com" });
  });

  describe("registry (root namespace)", () => {
    it("health returns ok status with actor name", async () => {
      const result = await health(e);

      expect(result.ok).toBe(true);
      expect(result.app).toBe("yoro");
      expect(result.ts).toBeDefined();
    });

    it("projectEntity is idempotent on entityId", async () => {
      const first = await projectEntity(e, {
        projectId: "proj-1",
        entityType: "task",
        entityId: "task-123",
      });

      expect(first.uri).toBeDefined();
      expect(first.rkey).toBeDefined();

      const second = await projectEntity(e, {
        projectId: "proj-1",
        entityType: "task",
        entityId: "task-123",
      });

      expect(second.uri).toBe(first.uri);
      expect(second.rkey).toBe(first.rkey);
    });

    it("productResearch validates required fields", async () => {
      const result = await productResearch(e, {
        jobId: "job-1",
        query: "laptop deals",
        retailers: ["amazon", "bestbuy"],
        totalOffers: 42,
      });

      expect(result.uri).toBeDefined();
      expect(result.rkey).toBe("research-job-1");
    });

    it("activitySeen writes and returns uri", async () => {
      const result = await activitySeen(e, { objectId: "obj-456" });

      expect(result.uri).toBeDefined();
      expect(result.rkey).toBe("seen-obj-456");
    });

    it("shinkaEvolution stores evolution data", async () => {
      const evolutionData = { generation: 1, fitness: 0.95 };
      const result = await shinkaEvolution(e, {
        nanoid: "nano-001",
        evolutionData,
      });

      expect(result.uri).toBeDefined();
      expect(result.rkey).toBe("evo-nano-001");
    });

    it("shinkaKnowledge stores knowledge data", async () => {
      const knowledgeData = { topic: "machine-learning", level: 3 };
      const result = await shinkaKnowledge(e, {
        nanoid: "nano-001",
        knowledgeData,
      });

      expect(result.uri).toBeDefined();
      expect(result.rkey).toBe("know-nano-001");
    });

    it("ingestProductCategory enqueues job", async () => {
      const result = await ingestProductCategory(e, {
        category: "electronics",
        source: "marketplace-api",
      });

      expect(result.status).toBe("enqueued");
      expect(result.jobId).toBeDefined();
      expect(result.researchVertexId).toBeDefined();
    });

    it("listApps returns empty array", async () => {
      const result = await listApps(e, { limit: 10 });

      expect(result.items).toEqual([]);
      expect(result.total).toBe(0);
    });

    it("stats returns counts with timestamp", async () => {
      const result = await stats(e);

      expect(result.posts).toBe(0);
      expect(result.profiles).toBe(0);
      expect(result.ts).toBeDefined();
    });

    it("listPosts returns empty array", async () => {
      const result = await listPosts(e, { limit: 20 });

      expect(result.items).toEqual([]);
      expect(result.count).toBe(0);
    });

    it("listProductResearch returns paginated empty result", async () => {
      const result = await listProductResearch(e, {
        limit: 25,
        offset: 0,
      });

      expect(result.items).toEqual([]);
      expect(result.total).toBe(0);
      expect(result.offset).toBe(0);
      expect(result.limit).toBe(25);
    });
  });

  describe("activity namespace", () => {
    it("listActivities returns empty events", async () => {
      const result = await listActivities(e, {
        limit: 10,
        objectTypes: "post",
      });

      expect(result.events).toEqual([]);
      expect(result.cursor).toBeUndefined();
    });

    it("listActivities respects cursor parameter", async () => {
      const result = await listActivities(e, {
        cursor: "cursor-123",
      });

      expect(result.cursor).toBe("cursor-123");
    });

    it("getActivityTrace returns empty trace", async () => {
      const result = await getActivityTrace(e, {
        objectType: "post",
        objectId: "post-789",
      });

      expect(result.trace).toEqual([]);
    });

    it("markSeen returns rkey and uri", async () => {
      const result = await markSeen(e, {});

      expect(result.rkey).toBeDefined();
      expect(result.rkey).toMatch(/^seen-\d+$/);
      expect(result.uri).toBeDefined();
      expect(result.uri).toContain("com.etzhayyim.yoro.activitySeen");
      expect(result.cid).toBe("bafyref");
    });
  });

  describe("feed namespace", () => {
    it("getTimeline returns empty feed", async () => {
      const result = await getTimeline(e, { limit: 30 });

      expect(result.feed).toEqual([]);
      expect(result.cursor).toBeUndefined();
    });

    it("getAuthorFeed returns empty feed", async () => {
      const result = await getAuthorFeed(e, {
        actor: "did:plc:author-123",
      });

      expect(result.feed).toEqual([]);
      expect(result.cursor).toBeUndefined();
    });

    it("getPostThread returns empty thread object", async () => {
      const result = await getPostThread(e, {
        uri: "at://did/collection/rkey",
      });

      expect(result.thread).toEqual({});
    });

    it("getRankedFeed returns empty feed", async () => {
      const result = await getRankedFeed(e, { limit: 30 });

      expect(result.feed).toEqual([]);
      expect(result.cursor).toBeUndefined();
      expect(result.debug).toBeUndefined();
    });

    it("getRankedFeed includes debug when requested", async () => {
      const result = await getRankedFeed(e, {
        limit: 30,
        debug: true,
      });

      expect(result.feed).toEqual([]);
      expect(result.debug).toBeDefined();
      expect(result.debug?.candidateCount).toBe(0);
      expect(result.debug?.hardGateDropped).toBe(0);
    });

    it("getDiscoverFeed returns empty feed", async () => {
      const result = await getDiscoverFeed(e, { limit: 50 });

      expect(result.feed).toEqual([]);
      expect(result.cursor).toBeUndefined();
    });

    it("getFollowers returns empty followers array", async () => {
      const result = await getFollowers(e, {
        actor: "did:plc:subject-456",
        limit: 100,
      });

      expect(result.followers).toEqual([]);
      expect(result.cursor).toBeUndefined();
      expect(result.subject).toBeUndefined();
    });

    it("getFollows returns empty follows array", async () => {
      const result = await getFollows(e, {
        actor: "did:plc:actor-789",
      });

      expect(result.follows).toEqual([]);
      expect(result.cursor).toBeUndefined();
    });

    it("getProfile returns notFound error", async () => {
      const result = await getProfile(e, {
        actor: "did:plc:nonexistent",
      });

      expect(result.profile).toBeUndefined();
      expect(result.error).toBe("not found");
    });

    it("searchActors returns empty actors array", async () => {
      const result = await searchActors(e, { q: "alice", limit: 25 });

      expect(result.actors).toEqual([]);
      expect(result.cursor).toBeUndefined();
    });
  });
});
