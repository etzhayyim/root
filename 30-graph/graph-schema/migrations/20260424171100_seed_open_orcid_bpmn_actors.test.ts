import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424171100_seed_open_orcid_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-orcid/registerResearcher.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-orcid/recordAffiliation.bpmn"),
  "utf-8",
);

describe("Seed open-orcid BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-orcid-register-researcher-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_orcid_register_researcher"');
    expect(migrationSource).toContain("open-orcid-record-affiliation-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_orcid_record_affiliation"');
  });
  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openOrcid.registerResearcher"');
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openOrcid.recordAffiliation"');
  });
  it("uses open-orcid-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('sys.bpmn.seed.open-orcid');
    expect(migrationSource).toContain("did:web:open-orcid.etzhayyim.com");
  });
  it("BPMN processes target Zeebe generic.* primitives", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });
  it("BPMN processIds match seed rows", () => {
    expect(bpmn1).toContain('id="open_orcid_register_researcher"');
    expect(bpmn2).toContain('id="open_orcid_record_affiliation"');
  });
});
