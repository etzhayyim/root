import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424173100_seed_open_doi_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-doi/registerDoi.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-doi/recordCitation.bpmn"),
  "utf-8",
);

describe("Seed open-doi BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-doi-register-doi-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_doi_register_doi"');
    expect(migrationSource).toContain("open-doi-record-citation-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_doi_record_citation"');
  });
  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openDoi.registerDoi"');
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openDoi.recordCitation"');
  });
  it("uses open-doi-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('sys.bpmn.seed.open-doi');
    expect(migrationSource).toContain("did:web:open-doi.etzhayyim.com");
  });
  it("BPMN processes target Zeebe generic.* primitives", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });
  it("BPMN processIds match seed rows", () => {
    expect(bpmn1).toContain('id="open_doi_register_doi"');
    expect(bpmn2).toContain('id="open_doi_record_citation"');
  });
});
