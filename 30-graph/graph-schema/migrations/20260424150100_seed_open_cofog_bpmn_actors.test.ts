import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424150100_seed_open_cofog_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-cofog/recordExpenditure.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-cofog/recordConcordance.bpmn"),
  "utf-8",
);

describe("Seed open-cofog BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-cofog-record-expenditure-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_cofog_record_expenditure"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/com/etzhayyim/open-cofog/recordExpenditure.bpmn"');
    expect(migrationSource).toContain("open-cofog-record-concordance-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_cofog_record_concordance"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/com/etzhayyim/open-cofog/recordConcordance.bpmn"');
  });

  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openCofog.recordExpenditure"');
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openCofog.recordConcordance"');
  });

  it("uses open-cofog-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-cofog"');
    expect(migrationSource).toContain("did:web:open-cofog.etzhayyim.com");
  });

  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });

  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_cofog_record_expenditure"');
    expect(bpmn2).toContain('id="open_cofog_record_concordance"');
  });
});
