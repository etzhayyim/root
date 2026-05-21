import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import { fixSignal, getFixation } from "@etzhayyim/koke-rw-free";
import {
  startFerment,
  getFerment,
  updateFermentStatus,
} from "@etzhayyim/hakkou-rw-free";
import { absorb, synthesize, bloom, ring } from "@etzhayyim/ki-rw-free";

describe("bonsai-vascular end-to-end", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:multi-actor.test" });
  });

  it("traces complete koke → hakkou → ki vascular flow", async () => {
    // Stage 1: koke fixation (photosynthesis) — fix CO₂ into glucose
    const fixResult = await fixSignal(e, {
      fixationId: "fix-001",
      inputKind: "text",
      rawRef: "raw signal content from external source",
      signalHash: "sha256_placeholder",
      agentDid: "did:web:agent.test",
    });
    expect(fixResult.status).toBe("fixed");
    expect(fixResult.did).toBeDefined();
    expect(fixResult.fixationUri).toBeDefined();

    // Retrieve fixation to confirm persistence
    const fixRetrieve = await getFixation(e, { fixationId: "fix-001" });
    expect(fixRetrieve.fixation).toBeDefined();
    expect(fixRetrieve.fixation?.fixationId).toBe("fix-001");

    // Stage 2: hakkou fermentation — transform glucose into ethanol
    const fermentResult = await startFerment(e, {
      fermentId: "ferment-001",
      agentDid: "did:web:agent.test",
      inputKind: "text",
      inputRef: fixResult.fixationUri!,
      outputKind: "summary",
      sourceFixationDid: fixResult.did!,
    });
    expect(fermentResult.status).toBe("started");
    expect(fermentResult.did).toBeDefined();
    expect(fermentResult.fermentUri).toBeDefined();

    // Complete fermentation with result
    const fermentUpdate = await updateFermentStatus(e, {
      fermentId: "ferment-001",
      status: "done",
      resultRef: "synthesized knowledge payload",
    });
    expect(fermentUpdate.status).toBe("updated");

    // Verify fermentation is complete
    const fermentRetrieve = await getFerment(e, { fermentId: "ferment-001" });
    expect(fermentRetrieve.ferment?.status).toBe("done");

    // Stage 3: ki absorption — xylem tier
    const absorbResult = await absorb(e, {
      absorbId: "absorb-001",
      sourceVertexId: fermentResult.did!,
      inputKind: "ferment",
      content: "synthesized knowledge from fermentation",
    });
    expect(absorbResult.status).toBe("absorbed");
    expect(absorbResult.did).toBeDefined();

    // Stage 4: ki synthesis — photosynthesis tier (LLM inference)
    const synthResult = await synthesize(e, {
      artifactId: "art-001",
      absorbId: "absorb-001",
      synthesis: "knowledge artifact synthesized from absorbed ferment",
      confidencePermille: 870,
      model: "claude-opus-4-7",
    });
    expect(synthResult.status).toBe("synthesized");
    expect(synthResult.did).toBeDefined();

    // Stage 5: ki bloom — phloem tier
    const bloomResult = await bloom(e, {
      bloomId: "bloom-001",
      artifactId: synthResult.did!,
    });
    expect(bloomResult.status).toBe("bloomed");
    expect(bloomResult.did).toBeDefined();

    // Stage 6: ki ring — dendrochronology snapshot
    const ringResult = await ring(e, {
      ringId: "ring-q2-2026",
      period: "P1W",
    });
    expect(ringResult.status).toBe("snapshot");
    expect(ringResult.snapshotCount).toBeGreaterThanOrEqual(1);

    // Verify end-to-end traceability
    expect(fixResult.fixationUri).toContain("koke");
    expect(fermentResult.fermentUri).toContain("hakkou");
    expect(synthResult.did).toBeDefined();
    expect(bloomResult.did).toBeDefined();
  });
});
