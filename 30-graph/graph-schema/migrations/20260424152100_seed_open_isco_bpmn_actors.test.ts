import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424152100_seed_open_isco_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-isco/classifyWorker.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-isco/recordConcordance.bpmn"),
  "utf-8",
);

describe("Seed open-isco BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-isco-classify-worker-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_isco_classify_worker"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-isco/classifyWorker.bpmn"');
    expect(migrationSource).toContain("open-isco-record-concordance-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_isco_record_concordance"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-isco/recordConcordance.bpmn"');
  });

  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openIsco.classifyWorker"');
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openIsco.recordConcordance"');
  });

  it("uses open-isco-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-isco"');
    expect(migrationSource).toContain("did:web:open-isco.etzhayyim.com");
  });

  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });

  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_isco_classify_worker"');
    expect(bpmn2).toContain('id="open_isco_record_concordance"');
  });
});
