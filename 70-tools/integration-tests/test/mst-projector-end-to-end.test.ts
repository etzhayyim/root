import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import { submitPaper, getPaper } from "@etzhayyim/kiyo-kotoba";

// TODO: mst-projector InMemoryProjector pending Phase 3 implementation (ADR-2605212000).
// Test refactored to use direct kiyo API calls without projector queries.
describe("kiyo paper submission", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:multi-actor.test" });
  });

  it("submits papers with updated authorDids field (kiyo Phase E)", async () => {
    // Submit 3 papers with varied content
    const paper1 = await submitPaper(e, {
      paperId: "kiyo:2026:p1",
      title: "Bonsai Cultivation and AI: A Symbiotic Growth Model",
      authorDids: ["did:web:alice.etzhayyim.com", "did:web:bob.etzhayyim.com"],
      field: "botany",
      language: "en",
      abstract: "Explores bonsai growth as metaphor for AI ecosystem design",
    });
    expect(paper1.status).toBe("registered");
    expect(paper1.did).toBeDefined();

    const paper2 = await submitPaper(e, {
      paperId: "kiyo:2026:p2",
      title: "Distributed Ledger Architecture for Legal Tech",
      authorDids: ["did:web:charlie.etzhayyim.com"],
      field: "computer-science",
      language: "en",
      abstract: "AT Protocol usage in decentralized law firm management",
    });
    expect(paper2.status).toBe("registered");

    const paper3 = await submitPaper(e, {
      paperId: "kiyo:2026:p3",
      title: "Fermentation and Knowledge Synthesis",
      authorDids: ["did:web:diana.etzhayyim.com"],
      field: "philosophy",
      language: "ja",
      abstract: "論文は発酵プロセスの知識への応用を探索する",
    });
    expect(paper3.status).toBe("registered");

    // Verify papers are accessible
    const retrieved1 = await getPaper(e, { paperId: "kiyo:2026:p1" });
    expect(retrieved1.paper).toBeDefined();
    expect(retrieved1.paper?.paperId).toBe("kiyo:2026:p1");

    const retrieved2 = await getPaper(e, { paperId: "kiyo:2026:p2" });
    expect(retrieved2.paper).toBeDefined();
    expect(retrieved2.paper?.authorDids).toContain("did:web:charlie.etzhayyim.com");

    // Verify paper metadata
    expect(paper1.did).toBeDefined();
    expect(paper2.paperUri).toBeDefined();
    expect(paper3.status).toBe("registered");
  });
});
