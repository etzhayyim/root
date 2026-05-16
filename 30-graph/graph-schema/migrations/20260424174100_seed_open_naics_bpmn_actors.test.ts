import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424174100_seed_open_naics_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-naics/classifyEntity.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-naics/recordConcordance.bpmn"),
  "utf-8",
);

describe("Seed open-naics BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-naics-classify-entity-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_naics_classify_entity"');
    expect(migrationSource).toContain("open-naics-record-concordance-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_naics_record_concordance"');
  });
  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openNaics.classifyEntity"');
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openNaics.recordConcordance"');
  });
  it("uses open-naics-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('sys.bpmn.seed.open-naics');
    expect(migrationSource).toContain("did:web:open-naics.gftd.ai");
  });
  it("BPMN processes target Zeebe generic.* primitives", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });
  it("BPMN processIds match seed rows", () => {
    expect(bpmn1).toContain('id="open_naics_classify_entity"');
    expect(bpmn2).toContain('id="open_naics_record_concordance"');
  });
});
