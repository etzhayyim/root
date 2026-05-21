import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import { submitPaper, getPaper } from "@etzhayyim/kiyo-rw-free";
import { InMemoryProjector, kiyoProjector } from "@etzhayyim/mst-projector";

describe("mst-projector end-to-end kiyo indexing", () => {
  let e: any;
  let projector: InMemoryProjector;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:multi-actor.test" });
    // Initialize in-memory projector with kiyo configuration
    projector = new InMemoryProjector(kiyoProjector);
  });

  it("indexes kiyo papers via projector and queries by text search", async () => {
    // Submit 3 papers with varied content
    const paper1 = await submitPaper(e, {
      paperId: "kiyo:2026:p1",
      title: "Bonsai Cultivation and AI: A Symbiotic Growth Model",
      authors: ["Alice", "Bob"],
      status: "published",
      field: "botany",
      language: "en",
      abstract: "Explores bonsai growth as metaphor for AI ecosystem design",
    });
    expect(paper1.status).toBe("submitted");
    expect(paper1.did).toBeDefined();

    const paper2 = await submitPaper(e, {
      paperId: "kiyo:2026:p2",
      title: "Distributed Ledger Architecture for Legal Tech",
      authors: ["Charlie"],
      status: "published",
      field: "computer-science",
      language: "en",
      abstract: "AT Protocol usage in decentralized law firm management",
    });
    expect(paper2.status).toBe("submitted");

    const paper3 = await submitPaper(e, {
      paperId: "kiyo:2026:p3",
      title: "Fermentation and Knowledge Synthesis",
      authors: ["Diana"],
      status: "draft",
      field: "philosophy",
      language: "ja",
      abstract: "論文は発酵プロセスの知識への応用を探索する",
    });
    expect(paper3.status).toBe("submitted");

    // Simulate projector commit processing
    // (in test env, directly invoke processCommit without firehose)
    await projector.processCommit({
      collection: "ai.gftd.kiyo.paper",
      rkey: "kiyo:2026:p1",
      value: paper1,
    });
    await projector.processCommit({
      collection: "ai.gftd.kiyo.paper",
      rkey: "kiyo:2026:p2",
      value: paper2,
    });
    await projector.processCommit({
      collection: "ai.gftd.kiyo.paper",
      rkey: "kiyo:2026:p3",
      value: paper3,
    });

    // Query by text search for "bonsai"
    const textSearch = await projector.queryTextSearch({
      collection: "ai.gftd.kiyo.paper",
      query: "bonsai",
    });
    expect(textSearch.matchCount).toBeGreaterThanOrEqual(1);

    // Query by attribute (status = "published")
    const attrQuery = await projector.queryAttribute({
      collection: "ai.gftd.kiyo.paper",
      attribute: "status",
      value: "published",
    });
    expect(attrQuery.matchCount).toBe(2);

    // Query by aggregate (group by status)
    const aggQuery = await projector.queryAggregate({
      collection: "ai.gftd.kiyo.paper",
      groupBy: "status",
    });
    expect(aggQuery.groups).toBeDefined();
    expect(aggQuery.groups.length).toBeGreaterThanOrEqual(1);
  });
});
