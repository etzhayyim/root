import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424170100_seed_open_patent_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-patent/registerPatent.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-patent/recordCitation.bpmn"),
  "utf-8",
);

describe("Seed open-patent BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-patent-register-patent-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_patent_register_patent"');
    expect(migrationSource).toContain("open-patent-record-citation-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_patent_record_citation"');
  });
  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openPatent.registerPatent"');
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openPatent.recordCitation"');
  });
  it("uses open-patent-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('sys.bpmn.seed.open-patent');
    expect(migrationSource).toContain("did:web:open-patent.etzhayyim.com");
  });
  it("BPMN processes target Zeebe generic.* primitives", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });
  it("BPMN processIds match seed rows", () => {
    expect(bpmn1).toContain('id="open_patent_register_patent"');
    expect(bpmn2).toContain('id="open_patent_record_citation"');
  });
});
