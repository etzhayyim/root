import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424153100_seed_open_unispsc_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-unispsc/procurement.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-unispsc/supplier.bpmn"),
  "utf-8",
);

describe("Seed open-unispsc BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-unispsc-procurement-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_unispsc_procurement"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-unispsc/procurement.bpmn"');
    expect(migrationSource).toContain("open-unispsc-supplier-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_unispsc_supplier"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-unispsc/supplier.bpmn"');
  });

  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "app.etzhayyim.apps.openUnispsc.procurement"');
    expect(migrationSource).toContain('nsid: "app.etzhayyim.apps.openUnispsc.supplier"');
  });

  it("uses open-unispsc-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-unispsc"');
    expect(migrationSource).toContain("did:web:open-unispsc.etzhayyim.com");
  });

  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });

  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_unispsc_procurement"');
    expect(bpmn2).toContain('id="open_unispsc_supplier"');
  });
});
