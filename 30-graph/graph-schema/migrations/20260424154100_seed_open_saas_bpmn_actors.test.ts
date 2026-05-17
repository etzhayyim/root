import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424154100_seed_open_saas_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-saas/registerProduct.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-saas/mapToUnspsc.bpmn"),
  "utf-8",
);

describe("Seed open-saas BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-saas-register-product-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_saas_register_product"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-saas/registerProduct.bpmn"');
    expect(migrationSource).toContain("open-saas-map-to-unspsc-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_saas_map_to_unspsc"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-saas/mapToUnspsc.bpmn"');
  });

  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openSaas.registerProduct"');
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openSaas.mapToUnspsc"');
  });

  it("uses open-saas-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-saas"');
    expect(migrationSource).toContain("did:web:open-saas.etzhayyim.com");
  });

  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });

  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_saas_register_product"');
    expect(bpmn2).toContain('id="open_saas_map_to_unspsc"');
  });
});
