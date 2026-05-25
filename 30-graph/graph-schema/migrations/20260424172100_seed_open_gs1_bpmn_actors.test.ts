import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424172100_seed_open_gs1_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-gs1/registerGtin.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-gs1/mapToUnspsc.bpmn"),
  "utf-8",
);

describe("Seed open-gs1 BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-gs1-register-gtin-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_gs1_register_gtin"');
    expect(migrationSource).toContain("open-gs1-map-to-unspsc-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_gs1_map_to_unspsc"');
  });
  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "app.etzhayyim.apps.openGs1.registerGtin"');
    expect(migrationSource).toContain('nsid: "app.etzhayyim.apps.openGs1.mapToUnspsc"');
  });
  it("uses open-gs1-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('sys.bpmn.seed.open-gs1');
    expect(migrationSource).toContain("did:web:open-gs1.etzhayyim.com");
  });
  it("BPMN processes target Zeebe generic.* primitives", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });
  it("BPMN processIds match seed rows", () => {
    expect(bpmn1).toContain('id="open_gs1_register_gtin"');
    expect(bpmn2).toContain('id="open_gs1_map_to_unspsc"');
  });
});
